import subprocess
import traceback

outpath = r"c:\Users\kwilde\Documents\GitHub\KW_Codebook\run_output.txt"
with open(outpath, "w", encoding="utf-8") as f:
    f.write("START\n")

try:
    r = subprocess.run(
        [r"C:\Users\kwilde\AppData\Local\Python\bin\python.exe",
         r"c:\Users\kwilde\Documents\GitHub\KW_Codebook\TK2_s40.lidar.z01.00_SEPT19_pull_Demo.py"],
        capture_output=True, text=True, timeout=180
    )
    with open(outpath, "a", encoding="utf-8") as f:
        f.write("STDOUT:\n" + r.stdout + "\nSTDERR:\n" + r.stderr + "\nRC:" + str(r.returncode))
except Exception:
    with open(outpath, "a", encoding="utf-8") as f:
        f.write("EXCEPTION:\n" + traceback.format_exc())
