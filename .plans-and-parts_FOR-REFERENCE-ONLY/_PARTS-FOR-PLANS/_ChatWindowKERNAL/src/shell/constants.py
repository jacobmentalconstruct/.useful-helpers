"""
Owns: shared shell constants that need consistent naming across subsystems.
Does not own: runtime state, UI composition, or persistence behavior.
Collaborates with: shell orchestrators and UI modules that consume stable defaults.
"""

DEFAULT_QUEUE_POLL_INTERVAL_MS = 75
DEFAULT_TASK_POOL_SIZE = 4
MAX_RECENT_EVENTS = 100
MAX_RECENT_TASKS = 50
MAX_CONTENT_PREVIEW = 280
MAX_ACTIVITY_EVENTS = 250
MAX_DATA_HOOKS = 64

STATUS_INFO = "info"
STATUS_READY = "ready"
STATUS_BUSY = "busy"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"
STATUS_SHUTTING_DOWN = "shutting_down"

PRIMARY_PANEL_ID = "chat"
SECONDARY_PANEL_ID = "workspace"
WORKSPACE_PANEL_ID = "workspace"
WORKSPACE_TAB_AGENT = "agent_hud"
WORKSPACE_TAB_TOOLS = "tools"
WORKSPACE_TAB_EVENTS = "events"
WORKSPACE_TAB_INSPECTOR = "inspector"

THEME_HARBOR_MIST = "harbor_mist"
THEME_CINDER_TIDE = "cinder_tide"

ACTIVITY_UI_INTERACTION = "ui.interaction"
ACTIVITY_AGENT_TURN = "agent.turn"
ACTIVITY_AGENT_STEP = "agent.step"
ACTIVITY_AGENT_HITL_WAIT = "agent.hitl_wait"
ACTIVITY_AGENT_HITL_RESOLVED = "agent.hitl_resolved"
ACTIVITY_TOOL_REQUESTED = "tool.requested"
ACTIVITY_TOOL_STARTED = "tool.started"
ACTIVITY_TOOL_COMPLETED = "tool.completed"
ACTIVITY_TOOL_FAILED = "tool.failed"
ACTIVITY_SYSTEM_STATUS = "system.status"
ACTIVITY_SYSTEM_ERROR = "system.error"
