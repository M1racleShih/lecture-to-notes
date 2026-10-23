#!/usr/bin/env python3
"""Static HTML lecture gate; actual browser/prose review is a separate requirement."""
from __future__ import annotations
import argparse
import csv
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
try:
    from .extract_claims import claim_in_notes
    from .verify_notes import Report, layout_gate
except ImportError:
    from extract_claims import claim_in_notes
    from verify_notes import Report, layout_gate

CJK = re.compile(r"[\u4e00-\u9fff]")
FIELDS = ("audience", "central_question", "reader_outcome",
          "visual_teaching_atoms", "formula_teaching_atoms")

class Article(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main = 0
        self.ignored = 0
        self.hidden = []
        self.text = []
        self.header_text = []
        self.h1 = 0
        self.h2 = 0
        self.display_math = 0
        self.ids = []
        self.hrefs = []
        self.assets = []
        self.images = []
        self.figures = []
        self.current = None
        self.problems = []

    def handle_starttag(self, tag, pairs):
        a = dict(pairs)
        void = tag in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
        if self.hidden:
            if not void:
                self.hidden.append(tag)
            return
        invisible = ("hidden" in a or a.get("aria-hidden") == "true" or
                     re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", a.get("style", ""), re.I))
        if invisible:
            if not void:
                self.hidden.append(tag)
            return
        if tag in {"script", "style", "template"}:
            self.ignored += 1
        if self.ignored:
            return
        if tag == "main":
            self.main += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "h2" and self.main:
            self.h2 += 1
        if tag == "math" and self.main and a.get("display") == "block":
            self.display_math += 1
        if a.get("id"):
            self.ids.append(a["id"])
        if tag in {"iframe", "object", "embed", "base"}:
            self.problems.append(f"{tag} is not a portable offline lecture component")
        if any(k.lower().startswith("on") for k in a):
            self.problems.append("inline event attribute; use authored script listeners")
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
        if tag == "figure":
            self.current = {"attrs": a, "images": [], "caption": "", "links": [], "in_caption": False}
        if tag == "figcaption" and self.current:
            self.current["in_caption"] = True
        if tag == "img":
            self.images.append(a)
            self.assets.append(a.get("src", ""))
            if not a.get("alt", "").strip():
                self.problems.append("image needs descriptive alt text")
            if self.current:
                self.current["images"].append(a.get("src", ""))
        if tag == "link" and a.get("rel") == "stylesheet":
            self.assets.append(a.get("href", ""))
        if self.current and self.current["in_caption"] and tag == "a":
            self.current["links"].append(a.get("href", ""))

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag in {"script", "style", "template"} and self.ignored:
            self.ignored -= 1
            return
        if self.ignored:
            return
        if tag == "main":
            self.main = max(0, self.main - 1)
        if tag == "figcaption" and self.current:
            self.current["in_caption"] = False
        if tag == "figure" and self.current:
            self.figures.append(self.current)
            self.current = None

    def handle_data(self, data):
        if self.ignored or self.hidden:
            return
        (self.text if self.main else self.header_text).append(data)
        if self.current and self.current["in_caption"]:
            self.current["caption"] += data

def rows(path, required):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not set(required).issubset(reader.fieldnames or []):
            raise ValueError(f"{path.name} has an invalid header")
        return list(reader)

def local_asset(root, url):
    parts = urlsplit(url)
    if parts.scheme == "data" and url.startswith("data:image/"):
        return True
    if parts.scheme or parts.netloc or not parts.path or parts.path.startswith(("/", "\\")):
        return False
    path = (root / unquote(parts.path)).resolve()
    return path.is_relative_to(root.resolve()) and path.is_file()

def seconds(text):
    parts = text.strip().split(":")
    if len(parts) not in (2, 3) or not all(x.isdigit() for x in parts):
        raise ValueError(f"invalid source time: {text}")
    nums = [int(x) for x in parts]
    if any(x >= 60 for x in nums[-2:]):
        raise ValueError(f"invalid source time: {text}")
    return sum(x * 60**i for i, x in enumerate(reversed(nums)))

def verify(root, html_name="notes.html", write_claims=False):
    report = Report()
    def check(ok, message):
        report.emit("PASS" if ok else "FAIL", message)
    root = Path(root)
    try:
        raw = (root / html_name).read_text(encoding="utf-8")
        doc = Article()
        doc.feed(raw)
        check(doc.h1 == 1 and doc.h2 > 0 and bool(doc.text),
              "one title and a structured main article")
        check(not re.search(r"\{\{[A-Z_]+\}\}", "".join(doc.header_text)),
              "metadata placeholders filled")
        check(len(set(doc.ids)) == len(doc.ids), "unique heading/component IDs")
        check(not doc.problems, "portable semantic components and image alternatives")
        for problem in doc.problems:
            print("  HTML", problem)
        assets = list(doc.assets)
        # Script src attributes are inspected separately because script text is ignored.
        class ScriptSources(HTMLParser):
            def handle_starttag(self, tag, pairs):
                attrs = dict(pairs)
                if tag in {"script", "img"} and attrs.get("src"):
                    assets.append(attrs["src"])
                if tag == "link" and attrs.get("rel") == "stylesheet":
                    assets.append(attrs.get("href", ""))
        ScriptSources().feed(raw)
        bad_assets = [x for x in assets if not local_asset(root, x)]
        check(not bad_assets, "referenced image/style/script assets are local and present")
        for asset in bad_assets:
            print("  ASSET", asset)
        bad_links = [h for h in doc.hrefs
                     if (h.startswith("#") and unquote(h[1:]) not in doc.ids)
                     or (urlsplit(h).scheme not in ("", "https", "http", "mailto"))]
        check(not bad_links, "source links and internal anchors")
        check(any("cover" in x.get("class", "").split() for x in doc.images),
              "original cover appears in the document")
        for name in ("metadata.json", "audio.srt", "audio_corrected.srt", "cover.jpg",
                     "bands.json", "layout.json", "figure_manifest.tsv",
                     "figure_verification.txt", "browser_verification.txt"):
            path = root / name
            check(path.is_file() and path.stat().st_size > 0, f"{name} present")
        profile = json.loads((root / "lecture_profile.json").read_text(encoding="utf-8"))
        meta = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
        mode = profile["mode"]
        check(mode in ("technical-slide", "mixed", "conceptual-talk")
              and all(k in profile for k in FIELDS), "source-fit reader profile")
        minutes = float(meta["duration"]) / 60
        visual, formula = int(profile["visual_teaching_atoms"]), int(profile["formula_teaching_atoms"])
        check(minutes > 0 and visual >= 0 and formula >= 0, "valid source duration and atom counts")
        floor, rate = {"technical-slide": (5000, 70), "mixed": (3500, 55),
                       "conceptual-talk": (2500, 45)}[mode]
        cjk = len(CJK.findall("".join(doc.text)))
        manifest = rows(root / "figure_manifest.tsv", ("figure", "frame", "start", "end", "topic", "panel"))
        need_fig = min(visual, max(20, round(minutes / 3.5)))
        need_math = min(formula, max(10, round(minutes / 4)))
        need_sections = {"technical-slide": 8, "mixed": 6, "conceptual-talk": 5}[mode] if minutes >= 60 else 1
        print(f"CJK_chars={cjk} source_figures={len(manifest)} chapters={doc.h2} display_math={doc.display_math}")
        check(cjk >= max(floor, round(rate * minutes)) and len(manifest) >= need_fig
              and doc.display_math >= need_math and doc.h2 >= need_sections,
              "source-fit density (no script/style/template text counted)")
        atoms = rows(root / "teaching_atoms.tsv", ("atom", "status", "evidence"))
        check(bool(atoms) and all(x["status"] == "ok" and x["evidence"].strip() for x in atoms),
              "teaching atoms mapped")
        claims_path = root / "numerical_claims.tsv"
        claims = rows(claims_path, ("claim", "value", "source_time", "in_notes"))
        flat = re.sub(r"\s+", "", "".join(doc.text))
        for claim in claims:
            claim["in_notes"] = "yes" if claim_in_notes(claim["value"], flat) else "no"
        check(all(x["in_notes"] == "yes" for x in claims),
              "all numerical claims appear in article text")
        if write_claims:
            with claims_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=("claim", "value", "source_time", "in_notes"), delimiter="\t", lineterminator="\n")
                writer.writeheader()
                writer.writerows(claims)
        expected = {x["figure"] for x in manifest}
        actual = {Path(unquote(urlsplit(src).path)).name for f in doc.figures
                  if "data-authored" not in f["attrs"] for src in f["images"]}
        check(actual == expected and len(expected) == len(manifest),
              "every source figure corresponds to the audited manifest")
        for row in manifest:
            figures = [f for f in doc.figures if row["figure"] in
                       [Path(unquote(urlsplit(x).path)).name for x in f["images"]]]
            ok = len(figures) == 1
            if ok:
                fig = figures[0]
                a = fig["attrs"]
                visible = {seconds(x) for x in re.findall(r"(?<!\d)(?:\d{1,2}:)?\d{1,2}:\d{2}(?!\d)", fig["caption"])}
                ok = (a.get("data-source-start") == row["start"] and
                      a.get("data-source-end") == row["end"] and
                      seconds(row["start"]) in visible and seconds(row["end"]) in visible and
                      any(urlsplit(x).scheme in ("https", "http") for x in fig["links"]))
            check(ok, f"{row['figure']} visible caption range and source link")
        layout_gate(root, report)
        print("NOTE Static gate does not certify browser behavior or source truth; inspect the browser and prose reports.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        report.emit("FAIL", str(error))
    print("OVERALL PASS" if report.ok else "OVERALL FAIL")
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", default=".")
    parser.add_argument("--html", default="notes.html")
    parser.add_argument("--write-claims", action="store_true")
    args = parser.parse_args(argv)
    return 0 if verify(Path(args.workdir), args.html, args.write_claims).ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
