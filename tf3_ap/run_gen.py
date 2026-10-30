"""Runs Archipelago's Generate.py without ModuleUpdate installing the GUI requirements."""
import os
import runpy
import sys

ap = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ap"))
os.chdir(ap)
sys.path.insert(0, ap)
import ModuleUpdate

ModuleUpdate.update_ran = True
sys.argv = ["Generate.py", "--player_files_path", "../players", "--outputpath", "../out"] + sys.argv[1:]
runpy.run_path("Generate.py", run_name="__main__")
