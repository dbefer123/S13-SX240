"""Relaxed JSON parser for BeamNG .jbeam / .pc / materials.json files.

JBeam is JSON with a few relaxations that the game accepts and vanilla files use:
  * // line comments and /* block */ comments
  * trailing commas
  * missing commas between array elements and between object members
    (e.g. ``["a","b"]\n["c","d"]`` or ``{"x":1 "y":2}``)

The parser keeps insertion order (dicts are ordered) and returns plain Python
objects: dict, list, str, int/float, bool, None.
"""
from __future__ import annotations

import math
import os


class JBeamParseError(ValueError):
    pass


_WS = set(" \t\r\n\f\v﻿")


class _Parser:
    def __init__(self, text: str, source: str = "<string>"):
        self.s = text
        self.n = len(text)
        self.i = 0
        self.source = source

    # -- helpers -----------------------------------------------------------
    def error(self, msg: str):
        line = self.s.count("\n", 0, self.i) + 1
        col = self.i - (self.s.rfind("\n", 0, self.i) + 1) + 1
        raise JBeamParseError(f"{self.source}:{line}:{col}: {msg}")

    def skip(self, commas: bool = False):
        s, n = self.s, self.n
        while self.i < n:
            c = s[self.i]
            if c in _WS or (commas and c == ","):
                self.i += 1
            elif c == "/" and self.i + 1 < n and s[self.i + 1] == "/":
                j = s.find("\n", self.i)
                self.i = n if j < 0 else j + 1
            elif c == "/" and self.i + 1 < n and s[self.i + 1] == "*":
                j = s.find("*/", self.i + 2)
                if j < 0:
                    self.error("unterminated block comment")
                self.i = j + 2
            else:
                break

    # -- values ------------------------------------------------------------
    def value(self):
        self.skip()
        if self.i >= self.n:
            self.error("unexpected end of input")
        c = self.s[self.i]
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c == '"':
            return self.string()
        if c in "-+.0123456789":
            return self.number()
        for word, val in (("true", True), ("false", False), ("null", None), ("nil", None)):
            if self.s.startswith(word, self.i):
                self.i += len(word)
                return val
        for word, val in (("FLT_MAX", "FLT_MAX"), ("inf", math.inf), ("-inf", -math.inf)):
            if self.s.startswith(word, self.i):
                self.i += len(word)
                return val
        self.error(f"unexpected character {c!r}")

    def obj(self):
        self.i += 1  # {
        out = {}
        while True:
            self.skip(commas=True)
            if self.i >= self.n:
                self.error("unterminated object")
            if self.s[self.i] == "}":
                self.i += 1
                return out
            if self.s[self.i] != '"':
                self.error("expected string key")
            key = self.string()
            self.skip()
            if self.i >= self.n or self.s[self.i] != ":":
                self.error("expected ':' after key")
            self.i += 1
            out[key] = self.value()

    def arr(self):
        self.i += 1  # [
        out = []
        while True:
            self.skip(commas=True)
            if self.i >= self.n:
                self.error("unterminated array")
            if self.s[self.i] == "]":
                self.i += 1
                return out
            out.append(self.value())

    def string(self):
        s = self.s
        self.i += 1
        buf = []
        while True:
            if self.i >= self.n:
                self.error("unterminated string")
            c = s[self.i]
            if c == '"':
                self.i += 1
                return "".join(buf)
            if c == "\\":
                self.i += 1
                e = s[self.i]
                if e == "u":
                    buf.append(chr(int(s[self.i + 1:self.i + 5], 16)))
                    self.i += 5
                    continue
                buf.append({"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f"}.get(e, e))
                self.i += 1
                continue
            buf.append(c)
            self.i += 1

    def number(self):
        s = self.s
        j = self.i
        if s[j] in "+-":
            j += 1
        while j < self.n and (s[j].isdigit() or s[j] in ".eE+-"):
            if s[j] in "+-" and s[j - 1] not in "eE":
                break
            j += 1
        tok = s[self.i:j]
        self.i = j
        try:
            if any(ch in tok for ch in ".eE"):
                return float(tok)
            return int(tok)
        except ValueError:
            self.error(f"bad number {tok!r}")


def loads(text: str, source: str = "<string>"):
    p = _Parser(text, source)
    v = p.value()
    p.skip(commas=True)
    if p.i < p.n:
        p.error("trailing data after top-level value")
    return v


def load(path: str):
    with open(path, "r", encoding="utf-8-sig") as f:
        return loads(f.read(), os.path.basename(path))
