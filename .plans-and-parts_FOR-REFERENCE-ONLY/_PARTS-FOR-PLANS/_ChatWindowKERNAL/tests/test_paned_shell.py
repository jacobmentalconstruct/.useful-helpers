from __future__ import annotations

import tkinter as tk
import unittest

from src.ui.paned_shell import PanedShell


class PanedShellTests(unittest.TestCase):
    def test_secondary_pane_can_reopen_after_being_hidden(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk unavailable: {exc}")

        try:
            root.geometry("1000x700")
            root.grid_rowconfigure(0, weight=1)
            root.grid_columnconfigure(0, weight=1)

            paned_shell = PanedShell(root)
            paned_shell.grid(row=0, column=0, sticky="nsew")

            tk.Frame(paned_shell.primary_host).grid(row=0, column=0, sticky="nsew")
            tk.Frame(paned_shell.secondary_host).grid(row=0, column=0, sticky="nsew")

            root.update()
            paned_shell.set_secondary_width(340)
            root.update()

            paned_shell.hide_secondary()
            root.update()
            self.assertFalse(paned_shell.secondary_host.winfo_ismapped())

            paned_shell.show_secondary()
            root.update()
            root.update()

            self.assertTrue(paned_shell.secondary_host.winfo_ismapped())
            self.assertEqual(paned_shell.get_secondary_width(), 340)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
