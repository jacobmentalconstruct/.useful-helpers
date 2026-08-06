"""
Owns: chat-surface composition, session/runtime header rendering, and input event capture.
Does not own: task execution, persistence files, or vendored runtime imports.
Collaborates with: the app kernel, session controller, and UI registry.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.ui.panels.base_panel import BasePanel
from src.ui.registry_hooks import register_widget


class ChatPanel(BasePanel):
    def __init__(
        self,
        theme_manager,
        *,
        on_send,
        on_stop=None,
        on_pause=None,
        on_resume=None,
        on_model_change=None,
        on_loop_change=None,
        on_open_session_manager=None,
    ) -> None:
        super().__init__(panel_id="chat", title="Conversation", parent_widget_id="main.primary_host")
        self._theme_manager = theme_manager
        self._on_send = on_send
        self._on_stop = on_stop
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_model_change = on_model_change
        self._on_loop_change = on_loop_change
        self._on_open_session_manager = on_open_session_manager
        self._transcript = None
        self._input = None
        self._send_button = None
        self._stop_button = None
        self._pause_button = None
        self._model_picker = None
        self._loop_picker = None
        self._session_label = None
        self._session_meta = None
        self._runtime_line = None
        self._hardware_line = None
        self._command_hint = None
        self._settings_button = None
        self._current_agent_snapshot = None
        self._suspend_picker_events = False

    def build(self, parent) -> None:
        self.frame = ttk.Frame(parent, style="Surface.TFrame", padding=(18, 18))
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self.frame, style="Surface.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        heading = ttk.Frame(header, style="Surface.TFrame")
        heading.grid(row=0, column=0, sticky="ew")
        heading.grid_columnconfigure(0, weight=1)

        self._session_label = ttk.Label(heading, text="Session", style="PanelTitle.TLabel")
        self._session_label.grid(row=0, column=0, sticky="w")

        self._settings_button = ttk.Button(
            heading,
            text="Session",
            style="Ghost.TButton",
            command=self._handle_open_session_manager,
        )
        self._settings_button.grid(row=0, column=1, sticky="e")

        self._session_meta = ttk.Label(
            header,
            text="Session metadata will appear here.",
            style="Muted.TLabel",
        )
        self._session_meta.grid(row=1, column=0, sticky="w", pady=(4, 0))

        controls = ttk.Frame(header, style="Surface.TFrame")
        controls.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        for column in range(6):
            controls.grid_columnconfigure(column, weight=0)
        controls.grid_columnconfigure(5, weight=1)

        ttk.Label(controls, text="Model", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self._model_picker = ttk.Combobox(controls, state="readonly", width=20)
        self._model_picker.grid(row=0, column=1, sticky="w", padx=(8, 12))
        self._model_picker.bind("<<ComboboxSelected>>", self._handle_model_changed)

        ttk.Label(controls, text="Loop", style="Muted.TLabel").grid(row=0, column=2, sticky="w")
        self._loop_picker = ttk.Combobox(controls, state="readonly", width=20)
        self._loop_picker.grid(row=0, column=3, sticky="w", padx=(8, 12))
        self._loop_picker.bind("<<ComboboxSelected>>", self._handle_loop_changed)

        self._runtime_line = ttk.Label(
            controls,
            text="Model status and turn state will appear here.",
            style="Muted.TLabel",
        )
        self._runtime_line.grid(row=0, column=5, sticky="e")

        self._hardware_line = ttk.Label(
            header,
            text="CPU / RAM / GPU telemetry will appear here.",
            style="Muted.TLabel",
        )
        self._hardware_line.grid(row=3, column=0, sticky="w", pady=(8, 0))

        self._command_hint = ttk.Label(
            header,
            text="Slash commands: /run <task>, /tool list, /tool <id> {json}",
            style="Muted.TLabel",
        )
        self._command_hint.grid(row=4, column=0, sticky="w", pady=(4, 0))

        transcript_frame = ttk.Frame(self.frame, style="Surface.TFrame")
        transcript_frame.grid(row=1, column=0, sticky="nsew", pady=(18, 12))
        transcript_frame.grid_rowconfigure(0, weight=1)
        transcript_frame.grid_columnconfigure(0, weight=1)

        self._transcript = tk.Text(transcript_frame, wrap="word", height=18, padx=12, pady=12)
        self._transcript.grid(row=0, column=0, sticky="nsew")
        self._transcript.configure(state="disabled")
        transcript_scrollbar = ttk.Scrollbar(
            transcript_frame,
            orient="vertical",
            command=self._transcript.yview,
        )
        transcript_scrollbar.grid(row=0, column=1, sticky="ns")
        self._transcript.configure(yscrollcommand=transcript_scrollbar.set)

        self._input = tk.Text(self.frame, wrap="word", height=6, padx=12, pady=12)
        self._input.grid(row=2, column=0, sticky="ew")
        self._input.bind("<Control-Return>", self._handle_send_shortcut)

        actions = ttk.Frame(self.frame, style="Surface.TFrame")
        actions.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        actions.grid_columnconfigure(0, weight=1)

        buttons = ttk.Frame(actions, style="Surface.TFrame")
        buttons.grid(row=0, column=1, sticky="e")

        self._send_button = ttk.Button(
            buttons,
            text="Send",
            style="Accent.TButton",
            command=self._handle_send_clicked,
        )
        self._send_button.grid(row=0, column=0, padx=(0, 8))

        self._stop_button = ttk.Button(
            buttons,
            text="Stop",
            style="Ghost.TButton",
            command=self._handle_stop_clicked,
        )
        self._stop_button.grid(row=0, column=1, padx=(0, 8))

        self._pause_button = ttk.Button(
            buttons,
            text="Pause",
            style="Ghost.TButton",
            command=self._handle_pause_clicked,
        )
        self._pause_button.grid(row=0, column=2)

        self.apply_theme()
        self.render_agent_state(None)

    def register_widgets(self, registry) -> None:
        register_widget(
            registry,
            widget_id="chat.panel",
            widget=self.frame,
            role="chat_panel",
            panel_id=self.panel_id,
            parent_id=self.parent_widget_id,
        )
        register_widget(
            registry,
            widget_id="chat.session_label",
            widget=self._session_label,
            role="chat_session_label",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=lambda: self._session_label.cget("text"),
        )
        register_widget(
            registry,
            widget_id="chat.session_meta",
            widget=self._session_meta,
            role="chat_session_meta",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=lambda: self._session_meta.cget("text"),
        )
        register_widget(
            registry,
            widget_id="chat.model_picker",
            widget=self._model_picker,
            role="chat_model_picker",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=lambda: self._model_picker.get(),
        )
        register_widget(
            registry,
            widget_id="chat.loop_picker",
            widget=self._loop_picker,
            role="chat_loop_picker",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=lambda: self._loop_picker.get(),
        )
        register_widget(
            registry,
            widget_id="chat.runtime_line",
            widget=self._runtime_line,
            role="chat_runtime_line",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=lambda: self._runtime_line.cget("text"),
        )
        register_widget(
            registry,
            widget_id="chat.hardware_line",
            widget=self._hardware_line,
            role="chat_hardware_line",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=lambda: self._hardware_line.cget("text"),
        )
        register_widget(
            registry,
            widget_id="chat.settings_button",
            widget=self._settings_button,
            role="chat_session_settings_button",
            panel_id=self.panel_id,
            parent_id="chat.panel",
        )
        register_widget(
            registry,
            widget_id="chat.transcript",
            widget=self._transcript,
            role="chat_transcript",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=self._get_transcript_preview,
        )
        register_widget(
            registry,
            widget_id="chat.input",
            widget=self._input,
            role="chat_input",
            panel_id=self.panel_id,
            parent_id="chat.panel",
            content_getter=self.get_draft_text,
        )
        register_widget(
            registry,
            widget_id="chat.send_button",
            widget=self._send_button,
            role="chat_send_button",
            panel_id=self.panel_id,
            parent_id="chat.panel",
        )
        register_widget(
            registry,
            widget_id="chat.stop_button",
            widget=self._stop_button,
            role="chat_stop_button",
            panel_id=self.panel_id,
            parent_id="chat.panel",
        )
        register_widget(
            registry,
            widget_id="chat.pause_button",
            widget=self._pause_button,
            role="chat_pause_button",
            panel_id=self.panel_id,
            parent_id="chat.panel",
        )

    def update_session_snapshot(self, session_snapshot) -> None:
        name = session_snapshot.active_session.name or "Untitled Session"
        session_id = session_snapshot.active_session.session_id or "pending"
        self._session_label.configure(text=name)
        self._session_meta.configure(
            text=(
                f"{session_id}  |  "
                f"{session_snapshot.active_session.message_count} memories  |  "
                f"Updated {session_snapshot.active_session.updated_at or '--'}"
            )
        )
        self._runtime_line.configure(
            text=(
                f"{session_snapshot.current_model or 'No model'}  |  "
                f"{session_snapshot.model_status or 'Model status unavailable'}  |  "
                f"Loop {session_snapshot.current_loop or '--'}"
            )
        )
        self._hardware_line.configure(
            text=(
                f"{session_snapshot.hardware.cpu_label}  |  "
                f"{session_snapshot.hardware.ram_summary}  |  "
                f"{session_snapshot.hardware.gpu_label}  |  "
                f"{session_snapshot.hardware.vram_summary}"
            )
        )

        self._suspend_picker_events = True
        self._model_picker.configure(values=tuple(session_snapshot.available_models))
        if session_snapshot.current_model:
            self._model_picker.set(session_snapshot.current_model)
        self._loop_picker.configure(values=tuple(session_snapshot.available_loops))
        if session_snapshot.current_loop:
            self._loop_picker.set(session_snapshot.current_loop)
        self._suspend_picker_events = False

    def render_agent_state(self, agent_snapshot) -> None:
        self._current_agent_snapshot = agent_snapshot
        active = agent_snapshot is not None and agent_snapshot.active_turn_id is not None
        paused = bool(agent_snapshot and agent_snapshot.can_resume)
        can_pause = bool(agent_snapshot and agent_snapshot.can_pause)

        if self._on_stop is None:
            self._stop_button.state(["disabled"])
        elif active:
            self._stop_button.state(["!disabled"])
        else:
            self._stop_button.state(["disabled"])

        if paused:
            self._pause_button.configure(text="Resume")
            if self._on_resume is not None:
                self._pause_button.state(["!disabled"])
            else:
                self._pause_button.state(["disabled"])
        else:
            self._pause_button.configure(text="Pause")
            if can_pause and self._on_pause is not None:
                self._pause_button.state(["!disabled"])
            else:
                self._pause_button.state(["disabled"])

        if agent_snapshot is None:
            return

        runtime_text = self._runtime_line.cget("text")
        turn_state = agent_snapshot.controller_state.replace("_", " ")
        mode = agent_snapshot.current_turn_mode or "chat"
        if "  |  " in runtime_text:
            base = "  |  ".join(runtime_text.split("  |  ")[:3])
        else:
            base = runtime_text
        self._runtime_line.configure(text=f"{base}  |  Turn {turn_state} ({mode})")

    def append_message(self, role: str, text: str) -> None:
        self._transcript.configure(state="normal")
        self._transcript.insert("end", f"{role}\n", ("role",))
        self._transcript.insert("end", f"{text}\n\n")
        self._transcript.tag_configure("role", font=("Segoe UI Semibold", 10))
        self._transcript.configure(state="disabled")
        self._transcript.see("end")

    def clear_transcript(self) -> None:
        self._transcript.configure(state="normal")
        self._transcript.delete("1.0", "end")
        self._transcript.configure(state="disabled")

    def focus_input(self) -> None:
        self._input.focus_set()

    def get_draft_text(self) -> str:
        return self._input.get("1.0", "end-1c")

    def clear_input(self) -> None:
        self._input.delete("1.0", "end")

    def get_state(self) -> dict:
        return {"draft_text": self.get_draft_text()}

    def restore_state(self, state: dict) -> None:
        draft_text = str(state.get("draft_text", ""))
        self._input.delete("1.0", "end")
        if draft_text:
            self._input.insert("1.0", draft_text)

    def get_snapshot(self) -> dict:
        return {
            "panel_id": self.panel_id,
            "draft_length": len(self.get_draft_text()),
            "selected_model": self._model_picker.get(),
            "selected_loop": self._loop_picker.get(),
            "session_label": self._session_label.cget("text"),
            "transcript_preview": self._get_transcript_preview(),
        }

    def apply_theme(self) -> None:
        self._theme_manager.configure_text(self._transcript, variant="transcript")
        self._theme_manager.configure_text(self._input, variant="input")

    def _get_transcript_preview(self) -> str:
        content = self._transcript.get("1.0", "end-1c")
        return content[-500:]

    def _handle_send_clicked(self) -> None:
        draft = self.get_draft_text().strip()
        if not draft:
            return
        self._on_send(draft)

    def _handle_send_shortcut(self, _event) -> str:
        self._handle_send_clicked()
        return "break"

    def _handle_stop_clicked(self) -> None:
        if self._on_stop is not None:
            self._on_stop()

    def _handle_pause_clicked(self) -> None:
        if self._current_agent_snapshot is not None and self._current_agent_snapshot.can_resume:
            if self._on_resume is not None:
                self._on_resume()
            return
        if self._on_pause is not None:
            self._on_pause()

    def _handle_model_changed(self, _event) -> None:
        if self._suspend_picker_events or self._on_model_change is None:
            return
        value = self._model_picker.get().strip()
        if value:
            self._on_model_change(value)

    def _handle_loop_changed(self, _event) -> None:
        if self._suspend_picker_events or self._on_loop_change is None:
            return
        value = self._loop_picker.get().strip()
        if value:
            self._on_loop_change(value)

    def _handle_open_session_manager(self) -> None:
        if self._on_open_session_manager is not None:
            self._on_open_session_manager()
