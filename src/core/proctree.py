"""
FILE:       src/core/proctree.py
ROLE:       Durable ownership of a spawned process tree.
DOMAIN:     core
DOES:       Gives the seam one handle that owns a child AND everything it spawns, so
            the tree can be stopped as a unit and cannot outlive its owner.
DEPENDS ON: stdlib only (ctypes on Windows)
WIRES TO:   src/core/invoke.py
NOTES:      Written for 0023, after the workflow's first Windows run showed a tool
            process surviving the seam that started it.

            THE DEFECT THIS REPLACES was not one bug but one wrong idea: the tree was
            RECONSTRUCTED AT KILL TIME instead of being HELD. Two symptoms followed
            from it, and only the second was observable before Windows CI existed.

            1. `_terminate()` sent CTRL_BREAK_EVENT, waited 5s for the direct child,
               and RETURNED if it exited - so `taskkill /T` was skipped exactly when
               the direct child was well behaved. Politeness defeated the escalation,
               and the better-behaved the child, the more reliably its grandchildren
               were orphaned.

            2. `install_shutdown_handlers()` registered SIGTERM/SIGINT handlers.
               Windows `TerminateProcess` - which is what `Popen.terminate()` calls -
               delivers no signal and runs no atexit, so neither the handler nor
               `reap_all()` ever ran. This is what the gate caught: pid 19364 outlived
               the seam.

            A Job Object fixes both by inverting the relationship. Membership is
            assigned at spawn and is inherited by descendants; KILL_ON_JOB_CLOSE means
            the OS destroys the tree when the last handle to the job closes - including
            when the owner is terminated abruptly, which no user-space handler can
            intercept.

            ONE JOB PER OPERATION, matching invoke's `_RUNNING` map. A single job for
            the whole seam would make cancelling one operation kill every other
            operation in flight.

            AN HONEST ASYMMETRY: this makes Windows stronger than POSIX. Nothing can
            catch SIGKILL, so a POSIX seam killed with -9 still orphans its process
            group. That limit is irreducible, and `posix_sigkill_orphans_group()`
            states it rather than leaving it to be discovered.
"""
from __future__ import annotations

import os
import signal
import subprocess

__all__ = ["spawn_kwargs", "ProcessTree", "contain_self",
           "posix_sigkill_orphans_group"]

# Held for the process lifetime. If this handle is closed or garbage-collected the
# job closes, and with KILL_ON_JOB_CLOSE that would kill our own descendants early.
_SELF_JOB = None

_IS_WINDOWS = os.name == "nt"

# Win32 constants. Named rather than inlined so the intent survives a reader who
# does not have the SDK headers to hand.
_JobObjectExtendedLimitInformation = 9
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000


def posix_sigkill_orphans_group() -> bool:
    """True where a SIGKILL'd owner cannot reap its own group. Documents a limit.

    POSIX only. SIGKILL is uncatchable, so nothing runs to tear the group down. On
    Windows the job object survives this case, which is the one place the Windows
    path is strictly stronger.
    """
    return not _IS_WINDOWS


def _extended_limit_struct():
    """JOBOBJECT_EXTENDED_LIMIT_INFORMATION. Shared by both job users.

    Defined once: two hand-written copies of a binary layout is the same
    one-authority defect as two copies of a rule, and a mismatch here corrupts
    memory rather than merely disagreeing.
    """
    import ctypes
    from ctypes import wintypes

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [("ReadOperationCount", ctypes.c_ulonglong),
                    ("WriteOperationCount", ctypes.c_ulonglong),
                    ("OtherOperationCount", ctypes.c_ulonglong),
                    ("ReadTransferCount", ctypes.c_ulonglong),
                    ("WriteTransferCount", ctypes.c_ulonglong),
                    ("OtherTransferCount", ctypes.c_ulonglong)]

    class _BASIC_LIMIT(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                    ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _EXTENDED_LIMIT(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _BASIC_LIMIT),
                    ("IoInfo", _IO_COUNTERS),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    return _EXTENDED_LIMIT()


def contain_self() -> bool:
    """Put THIS process in a kill-on-close job, so nothing outlives it. Windows only.

    WHY THIS IS SEPARATE FROM ProcessTree. Per-operation jobs cannot close the
    shutdown hole, and the first Windows run proved it: the direct child died with
    the seam but its GRANDCHILD survived.

    Job membership is not retroactive. The seam calls Popen, then assigns the child
    to a job - and in the window between those two statements the child is already
    running and can spawn its own children. Those grandchildren are never in the job.
    The fixture spawns its grandchild as its FIRST statement, so it lost that race
    every time.

    Containing the seam itself has no such window: the job exists before any tool is
    launched, and Windows places every descendant in it automatically. When the seam
    dies by ANY means - including TerminateProcess, which runs no handler and no
    atexit - the job closes and the whole tree goes with it.

    ProcessTree stays for CANCEL, where per-operation granularity is the point:
    cancelling one operation must not kill every other one in flight.

    Returns True if containment is in force. Degrades honestly: a host that refuses
    nested jobs gets False and the weaker guarantee, never an exception.
    """
    global _SELF_JOB
    if not _IS_WINDOWS or _SELF_JOB is not None:
        return _SELF_JOB is not None
    try:
        import ctypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        job = k32.CreateJobObjectW(None, None)
        if not job:
            return False
        info = _extended_limit_struct()
        info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(
                job, _JobObjectExtendedLimitInformation,
                ctypes.byref(info), ctypes.sizeof(info)):
            k32.CloseHandle(job)
            return False
        if not k32.AssignProcessToJobObject(job, k32.GetCurrentProcess()):
            k32.CloseHandle(job)
            return False
        _SELF_JOB = job
        return True
    except Exception:
        return False


def spawn_kwargs() -> dict:
    """Popen kwargs that place a child in its own controllable tree.

    Windows keeps CREATE_NEW_PROCESS_GROUP so CTRL_BREAK_EVENT remains deliverable
    for the polite stop; the job object provides the guarantee behind it.
    """
    if _IS_WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


class ProcessTree:
    """Owns one child and its descendants for the lifetime of this object.

    Windows: a job object with KILL_ON_JOB_CLOSE.
    POSIX:   the child's process group.

    Degrades honestly. If the job object cannot be created or assigned - an older
    host, a restrictive job policy, a missing API - `durable` is False and the caller
    still gets group-based termination. It never raises for that reason; a sidecar
    that will not start because it could not obtain a stronger guarantee is worse
    than one that reports the weaker guarantee it has.
    """

    def __init__(self, proc: "subprocess.Popen") -> None:
        self.proc = proc
        self._job = None
        self.durable = False
        if _IS_WINDOWS:
            self._adopt_windows()
        else:
            self.durable = True          # the process group is the tree

    # ---------------------------------------------------------------- windows
    def _adopt_windows(self) -> None:
        import ctypes

        try:
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            job = k32.CreateJobObjectW(None, None)
            if not job:
                return

            info = _extended_limit_struct()
            info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not k32.SetInformationJobObject(
                    job, _JobObjectExtendedLimitInformation,
                    ctypes.byref(info), ctypes.sizeof(info)):
                k32.CloseHandle(job)
                return

            # Popen keeps the process HANDLE on Windows. Using it avoids reopening by
            # PID, which is racy: a PID can be recycled between spawn and adoption.
            handle = int(getattr(self.proc, "_handle", 0))
            if not handle or not k32.AssignProcessToJobObject(job, handle):
                k32.CloseHandle(job)
                return

            self._job = job
            self.durable = True
        except Exception:
            self._job = None             # honest degradation, never fatal

    # ----------------------------------------------------------------- stop
    def terminate(self, grace_s: float = 5.0) -> None:
        """Stop the child and every descendant. Polite first, then certain.

        The escalation is UNCONDITIONAL. The previous implementation returned as soon
        as the direct child exited, which skipped tree teardown precisely when the
        child behaved well - so a cooperative tool orphaned its own grandchildren.
        """
        try:
            if _IS_WINDOWS:
                self.proc.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except (OSError, ValueError, AttributeError):
            try:
                self.proc.terminate()
            except OSError:
                pass

        try:
            self.proc.wait(timeout=grace_s)
        except subprocess.TimeoutExpired:
            pass

        # Runs whether or not the direct child exited. Descendants are the point.
        self._kill_tree()

    def _kill_tree(self) -> None:
        if _IS_WINDOWS:
            if self._job is not None:
                try:
                    import ctypes
                    ctypes.WinDLL("kernel32").TerminateJobObject(self._job, 1)
                    return
                except Exception:
                    pass
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                               capture_output=True, timeout=15)
                return
            except (OSError, subprocess.SubprocessError):
                pass
        else:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                return
            except (OSError, ValueError):
                pass
        try:
            self.proc.kill()
        except OSError:
            pass

    def close(self) -> None:
        """Release the job handle. With KILL_ON_JOB_CLOSE this ends the tree.

        Called when an operation finishes normally. Not calling it is not a leak of
        processes - it is a leak of a handle - because process death is what closing
        guarantees, not what it requires.
        """
        if self._job is not None:
            try:
                import ctypes
                ctypes.WinDLL("kernel32").CloseHandle(self._job)
            except Exception:
                pass
            self._job = None
