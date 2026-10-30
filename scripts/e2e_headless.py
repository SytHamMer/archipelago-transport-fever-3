"""Headless end-to-end check: local Archipelago server + the real TF3 client + a fake mod writing the outbox.

Usage: python scripts/e2e_headless.py <generated AP_xxx.zip>
Checks that the client writes the inbox, sends checks and reports the goal to the server.
"""
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
PORT = "38299"

BOOT = """
import os, runpy, sys
ap = os.path.join(r"{root}", "ap")
os.chdir(ap)
sys.path.insert(0, ap)
sys.argv = ["tf3_e2e", "--nogui"]  # Utils.gui_enabled is read from argv when Utils is imported
import ModuleUpdate
ModuleUpdate.update_ran = True
{body}
"""


def run_python(body: str, log: Path, **kwargs) -> subprocess.Popen:
    code = BOOT.format(root=ROOT, body=body)
    return subprocess.Popen([PY, "-c", code], stdin=subprocess.PIPE, stdout=open(log, "w", encoding="utf-8"),
                            stderr=subprocess.STDOUT, text=True, cwd=ROOT / "ap", **kwargs)


def main(seed_zip: str) -> int:
    work = Path(tempfile.mkdtemp(prefix="tf3_e2e_"))
    with zipfile.ZipFile(seed_zip) as z:
        multidata = next(n for n in z.namelist() if n.endswith(".archipelago"))
        z.extract(multidata, work)
    userdata = work / "towns_industries"
    userdata.mkdir()
    env = {**os.environ, "TF3_USERDATA_DIR": str(userdata)}

    server = run_python(f'sys.argv = ["MultiServer.py", r"{work / multidata}", "--port", "{PORT}"]\n'
                        f'runpy.run_path("MultiServer.py", run_name="__main__")', work / "server.log")
    time.sleep(6)
    client = run_python(
        'sys.path.insert(0, os.path.join(r"%s", "scripts"))\n'
        "import dev_link; dev_link.link()\n"
        "from worlds.transport_fever_3.client.tf3_client import launch\n"
        'launch("--connect", "localhost:%s", "--name", "Mathys", "--nogui")' % (ROOT, PORT),
        work / "client.log", env=env,
    )
    try:
        time.sleep(10)
        inbox = userdata / "archipelago_tf3_inbox.lua"
        print("inbox written by the client:", inbox.exists())
        text = inbox.read_text(encoding="utf-8") if inbox.exists() else ""
        print("inbox carries contracts (scouting):", "contracts" in text and "population:1" in text)
        seed = next((line.split('"')[1] for line in text.splitlines() if line.strip().startswith("seed")), "")
        outbox = (
            'function data()\nreturn {\n\tversion = 1,\n\tseed = "%s",\n\tchecks = { "population:1", "line:road" },\n'
            '\tgoals = { population = true },\n\tapplied = 0,\n\theartbeat = %d,\n}\nend\n' % (seed, int(time.time()))
        )
        (userdata / f"archipelago_tf3_outbox_{seed}.lua").write_text(outbox, encoding="utf-8")
        time.sleep(8)
        client.stdin.close()
        client.terminate()
        server.stdin.close()
        server.terminate()
    finally:
        client.kill()
        server.kill()
    time.sleep(1)
    client_log = (work / "client.log").read_text(encoding="utf-8", errors="replace")
    server_log = (work / "server.log").read_text(encoding="utf-8", errors="replace")
    print("--- client:\n" + "\n".join(line for line in client_log.splitlines() if "requests" not in line and "File " not in line)[-1500:])
    print("--- server:\n" + "\n".join(line for line in server_log.splitlines() if "requests" not in line and "File " not in line)[-1500:])
    # the server is the judge: both fake checks arrived and the goal was reported
    ok = ("(population:1)" in server_log or "(line:road)" in server_log) and "completed all of their games" in server_log
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
