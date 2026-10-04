"""Minimal Collada reader: node names -> geometry vertex positions + material names."""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import numpy as np

NS = {"c": "http://www.collada.org/2005/11/COLLADASchema"}


class DaeIndex:
    """All mesh nodes of all DAE files below the given folders."""

    def __init__(self, *folders, load_vertices=True):
        self.meshes = {}   # node name -> dict(file, materials, verts (N,3) in node space, matrix)
        self.files = []
        for folder in folders:
            if not os.path.isdir(folder):
                continue
            for root, _, files in os.walk(folder):
                for fn in sorted(files):
                    if fn.lower().endswith(".dae"):
                        self._load(os.path.join(root, fn), load_vertices)

    def _load(self, path, load_vertices):
        self.files.append(path)
        tree = ET.parse(path)
        r = tree.getroot()
        mat_names = {}
        for m in r.iterfind(".//c:library_materials/c:material", NS):
            mat_names[m.get("id")] = m.get("name") or m.get("id")
        geoms = {}
        if load_vertices:
            for g in r.iterfind(".//c:library_geometries/c:geometry", NS):
                mesh = g.find("c:mesh", NS)
                if mesh is None:
                    continue
                vin = mesh.find("c:vertices/c:input[@semantic='POSITION']", NS)
                src_id = vin.get("source")[1:] if vin is not None else None
                pts = None
                for s in mesh.iterfind("c:source", NS):
                    if s.get("id") == src_id:
                        fa = s.find("c:float_array", NS)
                        pts = np.fromstring(fa.text or "", sep=" ").reshape(-1, 3)
                geoms[g.get("id")] = pts
        for node in r.iter(f"{{{NS['c']}}}node"):
            ig = node.find("c:instance_geometry", NS)
            if ig is None:
                continue
            name = node.get("name") or node.get("id")
            mats = [mat_names.get(im.get("target", "")[1:], im.get("target", "")[1:])
                    for im in ig.iterfind(".//c:instance_material", NS)]
            mtx = node.find("c:matrix", NS)
            M = np.eye(4)
            if mtx is not None and mtx.text:
                M = np.fromstring(mtx.text, sep=" ").reshape(4, 4)
            verts = geoms.get(ig.get("url", "")[1:]) if load_vertices else None
            if name in self.meshes:
                self.meshes[name]["dup"] = path
            self.meshes[name] = dict(file=path, materials=mats, verts=verts, matrix=M)

    def world_verts(self, name):
        m = self.meshes[name]
        v = m["verts"]
        if v is None:
            return None
        M = m["matrix"]
        return v @ M[:3, :3].T + M[:3, 3]
