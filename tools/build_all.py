"""Full build: textures -> jbeam -> meshes/materials -> configs -> validation -> thumbnails -> zip.

    python -m tools.build_all [--skip textures,meshes,thumbs] [--zip-only]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "mod")
DIST = os.path.join(ROOT, "dist")
ZIP_NAME = "nissan_240sx_s13_s14.zip"


def run(mod_args, title):
    t = time.time()
    print(f"--- {title}")
    r = subprocess.run([sys.executable, "-m", *mod_args], cwd=ROOT)
    print(f"    ({time.time() - t:.0f}s, exit {r.returncode})")
    return r.returncode


def write_jbeam():
    sys.path.insert(0, ROOT)
    from tools.vehicle.s13 import vehicle as V13
    from tools.vehicle.s14 import vehicle as V14
    V13.write(MOD)
    V14.write(MOD)


def write_configs():
    from tools.vehicle.s13 import configs as C13
    from tools.vehicle.s14 import configs as C14
    C13.write(MOD)
    C14.write(MOD)


def package():
    os.makedirs(DIST, exist_ok=True)
    path = os.path.join(DIST, ZIP_NAME)
    n = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(os.path.join(MOD, "vehicles")):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                arc = os.path.relpath(full, MOD).replace(os.sep, "/")
                z.write(full, arc)
                n += 1
    size = os.path.getsize(path) / 1e6
    print(f"--- packaged {n} files -> {os.path.relpath(path, ROOT)} ({size:.1f} MB)")
    if size > 95:
        print("WARNING: zip is close to GitHub's 100 MB limit")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip", default="")
    ap.add_argument("--zip-only", action="store_true")
    a = ap.parse_args(argv)
    skip = set(a.skip.split(","))
    if a.zip_only:
        package()
        return 0
    if "textures" not in skip:
        run(["tools.textures.gen", "--mod", MOD], "textures")
    print("--- jbeam")
    write_jbeam()
    if "meshes" not in skip:
        for veh in ("s13", "s14"):
            if run(["tools.model.build_meshes", "--vehicle", veh, "--mod", MOD], f"meshes + materials ({veh})"):
                print(f"mesh build reported problems ({veh})")
            if run(["tools.validate.normals", "--blend", f".cache/build/{veh}_meshes.blend"], f"normals ({veh})"):
                print(f"inside-out closed parts found ({veh})")
            if run(["tools.validate.clearance", "--vehicle", veh], f"windshield clearance ({veh})"):
                print(f"cockpit parts through the windshield ({veh})")
    print("--- configs")
    write_configs()
    rc = 0
    for veh in ("s13_240sx", "s14_240sx"):
        rc |= run(["tools.validate.run", "--mod", MOD, "--vehicle", veh], f"validation ({veh})")
        if "meshes" not in skip and run(["tools.validate.backfaces", "--mod", MOD, "--veh", veh, "--all", "--hide-hood",
                                         "--rays", "6000"], f"see-through surfaces ({veh})"):
            print(f"surfaces seen from behind ({veh})")
    if "thumbs" not in skip:
        for veh in ("s13_240sx", "s14_240sx"):
            run(["tools.render.thumbnails", "--mod", MOD, "--veh", veh], f"thumbnails ({veh})")
    package()
    return rc


if __name__ == "__main__":
    sys.exit(main())
