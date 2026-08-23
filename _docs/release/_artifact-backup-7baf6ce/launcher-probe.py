"""
Two questions, one run, no artifact and no install needed.

  1. Which .bat dispatch shape carries an exit code back to a PROGRAMMATIC caller?
     `run.bat` currently uses `goto :eof` inside a parenthesized if-block. That was
     validated with `call` from inside another batch, which is not how the verifier
     invokes it - subprocess spawns `cmd /c run.bat ...`. The two are not the same.

  2. What actually arrives in `%~3` when subprocess passes a JSON argument?
     `run.bat tool ping <json>` returned 255. Python's list2cmdline escapes for the
     MSVCRT convention; a .bat puts cmd.exe in the middle, and cmd does not read
     backslash-escaped quotes the same way. This prints what survived.

Run:  python launcher-probe.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

W = Path(tempfile.mkdtemp(prefix="launcher-probe-"))
PY = sys.executable

SHAPE_1 = f'''@echo off
setlocal
if /I "%~1"=="go" (
    "{PY}" -c "import sys; sys.exit(3)"
    goto :eof
)
'''

SHAPE_2 = f'''@echo off
setlocal
if /I "%~1"=="go" goto :mode_go
goto :eof
:mode_go
"{PY}" -c "import sys; sys.exit(3)"
exit /b %ERRORLEVEL%
'''

ECHO_BAT = '''@echo off
setlocal
echo ARG2=[%~2]
echo ARG3=[%~3]
'''


def write(name: str, text: str) -> Path:
    p = W / name
    p.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    return p


def rc(path: Path, *args: str) -> int:
    return subprocess.run([str(path), *args], capture_output=True, text=True).returncode


print()
print("  1. exit code through a .bat, as subprocess invokes it")
print("  " + "-" * 58)
r1 = rc(write("shape1.bat", SHAPE_1), "go")
r2 = rc(write("shape2.bat", SHAPE_2), "go")
print(f"     goto :eof inside the if-block   -> {r1}     want 3")
print(f"     goto :label + exit /b at top    -> {r2}     want 3")
print()
if r1 == 3:
    print("     Both work. The rc=0 is NOT the dispatch shape - look at the CLI.")
elif r2 == 3:
    print("     goto :eof LOSES it here. The restructure is the fix.")
else:
    print("     Neither works. Something else is eating the code.")

print()
print("  2. what a JSON argument looks like by the time %~3 sees it")
print("  " + "-" * 58)
payload = json.dumps({"message": 'nested "quotes" and C:\\win\\style\\path',
                      "arr": [1, {"k": True}]})
echo = write("echo.bat", ECHO_BAT)
out = subprocess.run([str(echo), "ping", payload], capture_output=True, text=True)
print(f"     sent    : {payload}")
for line in out.stdout.splitlines():
    print(f"     {line.strip()}")
got = ""
for line in out.stdout.splitlines():
    if line.strip().startswith("ARG3="):
        got = line.strip()[6:-1]
print()
print("     INTACT" if got == payload else "     CORRUPTED - cmd.exe re-parsed it in transit")
print()
print(f"  (scratch: {W})")
