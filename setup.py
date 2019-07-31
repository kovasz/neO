import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
	"packages": ["os", "sys", "numpy.core._methods", "numpy.lib.format"],
	"excludes": [ "matplotlib", "email", "scipy", "sqlite3", "xml" ]
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "networkOptimizer",
        version = "1.0",
        description = "Sensor network optimizer by portfolio SAT+SMT solving",
        options = {"build_exe": build_exe_options},
        executables = [Executable("networkOptimizer.py", base=base)])