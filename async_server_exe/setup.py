import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["common", "logs", "server", "sqlite3"],
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="mess_server",
    version="0.0.1",
    description="mess_server",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('server.py', base=base, )]
)
