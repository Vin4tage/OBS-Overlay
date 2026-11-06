"""Erstellt das Release-Archiv: RAR (falls rar/WinRAR gefunden wird), sonst ZIP.
Builds the release archive: RAR if rar/WinRAR is found, otherwise ZIP.   Usage: python scripts/package_release.py"""
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = os.path.basename(ROOT)
sys.path.insert(0, ROOT)
from shadowplay_overlay import __version__  # noqa: E402

SKIP_DIRS = {"__pycache__", ".git", ".idea", ".vscode"}
SKIP_TOP = {os.path.join("runtime", "python")}
SKIP_FILES = {os.path.join("config", "user_config.json")}


def collect():
    for base, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(base, ROOT)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and os.path.join(rel, d).lstrip("./") not in SKIP_TOP]
        for f in files:
            path = os.path.join(base, f)
            r = os.path.relpath(path, ROOT)
            if f.endswith((".pyc", ".zip", ".rar")) or r in SKIP_FILES:
                continue
            yield path, r


def find_rar():
    for cand in ("rar", "rar.exe", r"C:\Program Files\WinRAR\Rar.exe", r"C:\Program Files (x86)\WinRAR\Rar.exe"):
        found = shutil.which(cand) or (cand if os.path.isfile(cand) else None)
        if found:
            return found
    return None


def main():
    out_dir = os.path.join(ROOT, "releases")
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(collect())
    rar = find_rar()
    if rar:
        target = os.path.join(out_dir, "%s-v%s.rar" % (NAME, __version__))
        if os.path.exists(target):
            os.remove(target)
        listing = os.path.join(out_dir, ".filelist.txt")
        with open(listing, "w", encoding="utf-8") as fh:
            fh.write("\n".join(r for _, r in files))
        subprocess.check_call([rar, "a", "-ep0", "-r-", "-scul", target, "@" + listing], cwd=ROOT)
        os.remove(listing)
    else:
        target = os.path.join(out_dir, "%s-v%s.zip" % (NAME, __version__))
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, r in files:
                zf.write(path, os.path.join(NAME, r))
        print("Hinweis: rar nicht gefunden -> ZIP erstellt / rar not found -> ZIP created.")
    print("Archiv / archive:", target)


if __name__ == "__main__":
    main()
