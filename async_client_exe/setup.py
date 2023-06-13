import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["common", "logs", "client", "sqlite3"],
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="async_chat_client",
    version="0.0.1",
    description="async_chat_client",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('client.py', base=base)],
)
