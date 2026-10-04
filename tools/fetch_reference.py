"""Download reference material into .cache/ (never shipped in the mod).

* BeamNG documentation pages used while writing the JBeam generators
* the official BeamNG modding template (working JBeam examples)
* orthographic blueprints of the S13 / S14 used only to trace proportions
"""
import os
import re
import html
import io
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache")
UA = {"User-Agent": "Mozilla/5.0"}
DOCS = "https://documentation.beamng.com"
TEMPLATE = DOCS + "/modding/vehicle/tutorials/basic_car_tutorial/BeamNGModdingTemplate%28BasicJbeamProject%29.zip"
BLUEPRINTS = {
    "s13_hatch_go.gif": "https://getoutlines.com/blueprints/car/nissan/nissan-180sx-1989.gif",
    "s13_hatch_tb.gif": "https://www.the-blueprints.com/blueprints-depot/cars/nissan/nissan-180sx-1990.gif",
    "s13_coupe_tb.png": "https://www.the-blueprints.com/blueprints-depot/cars/nissan/nissan-silvia-s13.png",
    "s14_dim_tb.gif": "https://www.the-blueprints.com/blueprints-depot/cars/nissan/nissan-200sx.gif",
    "s14_tb.gif": "https://www.the-blueprints.com/blueprints-depot/cars/nissan/nissan-200sx-2.gif",
}
DOC_PAGES = [
    "/modding/vehicle/sections/" + s + "/" for s in (
        "nodes", "beams", "beams/bounded", "triangles", "hydros", "rails", "torsionbars", "slots", "slots2",
        "flexbodies", "glowmaps", "camera", "props", "wheels", "variables", "refnodes", "controller",
        "energystorage", "mirrors", "skins", "licenseplates", "sounds", "sounds/engine_audio", "components",
        "electrics", "information")
] + ["/modding/vehicle/smooth_lighting/", "/modding/materials/texture_cooker/",
     "/modding/materials/materials_1.5/", "/modding/materials/vehicle/typicalmaterials/",
     "/modding/vehicle/vehicle_paints/paint_definition/", "/modding/vehicle/vehicle_paints/multi_paint_setup/",
     "/modding/vehicle/tutorials/configs/", "/modding/vehicle/coordinate_systems/"]


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def page_text(raw):
    s = raw.decode("utf8", "replace")
    m = re.search(r"<main.*?</main>", s, re.S)
    s = m.group(0) if m else s
    s = re.sub(r"<(script|style|nav).*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<pre[^>]*>", "\n```\n", s).replace("</pre>", "\n```\n")
    s = re.sub(r"</(p|div|h\d|li|tr)>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    return "\n".join(l.rstrip() for l in s.splitlines() if l.strip())


def main():
    os.makedirs(os.path.join(CACHE, "docs"), exist_ok=True)
    os.makedirs(os.path.join(CACHE, "blueprints"), exist_ok=True)
    tdir = os.path.join(CACHE, "ref", "template")
    if not os.path.isdir(tdir):
        zipfile.ZipFile(io.BytesIO(get(TEMPLATE))).extractall(tdir)
    for p in DOC_PAGES:
        out = os.path.join(CACHE, "docs", p.strip("/").replace("/", "_") + ".txt")
        if not os.path.exists(out):
            open(out, "w").write(page_text(get(DOCS + p)))
    for name, url in BLUEPRINTS.items():
        out = os.path.join(CACHE, "blueprints", name)
        if not os.path.exists(out):
            open(out, "wb").write(get(url))
    print("reference cache ready:", CACHE)


if __name__ == "__main__":
    main()
