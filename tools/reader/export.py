#!/usr/bin/env python3
"""Export an approved LaTeXML XHTML conversion into the Jekyll reader.

Trusted inputs only (this is not a sandbox). Conversion and validation
finish before public files are updated; each file is replaced atomically.
Review the diff and run the tests/build before committing.

Usage:
  python3 tools/reader/export.py --slug SLUG --xhtml FILE.xhtml [--diagnostics FILE.json]
  python3 tools/reader/export.py --slug SLUG --source /path/to/analyse-cdo
"""
import argparse
import functools
import hashlib
import html.entities
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parents[1]
BUILD = SITE / "build" / "reader"
ADAPTER = ROOT / "preprint.tex"
RENDERER = ROOT / "render_math.cjs"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_CONTENT = [
    "/home/", "/Users/", "file://", "ltx_ERROR",
    'encoding="application/x-tex"',
]
UNSAFE_TAGS = {"script", "iframe", "object", "embed", "base"}
ALLOWED_SCHEMES = {"", "http", "https"}
UNSAFE_CLASSES = {"ltx_contact", "ltx_email", "ltx_address"}
XLINK_NS = "{http://www.w3.org/1999/xlink}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"
EQUATION_CLASSES = ("ltx_equation", "ltx_equationgroup")

SOURCE_FILES = [
    ("body.tex", "body.tex"),
    ("preamble/macros-math.tex", "preamble/macros-math.tex"),
    ("bib/references.bib", "bib/references.bib"),
    ("build/aux/preprint-ams/main.bbl", "main.bbl"),
]
SOURCE_DIRS = ["sections", "figures"]


class ConversionError(RuntimeError):
    pass


@functools.lru_cache(maxsize=1)
def katex_js_path() -> str:
    env = os.environ.copy()
    env["BUNDLE_GEMFILE"] = str(SITE / "Gemfile")
    try:
        proc = subprocess.run(
            ["bundle", "exec", "ruby", "-rkatex", "-e",
             "print Katex.katex_js_path"], cwd=SITE, env=env,
            capture_output=True, text=True, errors="replace", timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConversionError(f"cannot resolve katex.js: {exc}") from exc
    if proc.returncode == 0 and Path(proc.stdout.strip()).is_file():
        return proc.stdout.strip()
    candidates = sorted(SITE.glob(
        "vendor/bundle/ruby/*/gems/katex-*/vendor/katex/javascripts/katex.js"))
    if len(candidates) == 1:
        return str(candidates[0])
    raise ConversionError(
        f"katex.js resolution failed (bundle error: "
        f"{proc.stderr.strip()[:200]}; candidates: {len(candidates)})")


def latexml_env() -> dict:
    return os.environ.copy()


def normalize_attrs(elem: ET.Element) -> None:
    for key in list(elem.attrib):
        if not key.startswith("{"):
            continue
        local = key.split("}", 1)[1]
        value = elem.attrib.pop(key)
        if local == "lang":
            elem.set("lang", value)
        elif key.startswith(XML_NS):
            elem.set("xml:" + local, value)
        else:
            elem.set(local, value)


def strip_ns(elem: ET.Element) -> None:
    if "}" in elem.tag:
        elem.tag = elem.tag.split("}", 1)[1]
    normalize_attrs(elem)
    for child in elem:
        strip_ns(child)


def remove_elements(elem: ET.Element, tag: str, attr: tuple = None) -> None:
    for child in list(elem):
        if child.tag == tag and (attr is None or
                                 child.get(attr[0]) == attr[1]):
            elem.remove(child)
        else:
            remove_elements(child, tag, attr)


def find_document(root: ET.Element) -> ET.Element:
    for elem in root.iter():
        if "ltx_document" in elem.get("class", "").split():
            return elem
    for elem in root.iter():
        if elem.tag == "body":
            return elem
    raise ConversionError("no ltx_document element in XHTML output")


def parent_map(root: ET.Element) -> dict:
    return {child: parent for parent in root.iter() for child in parent}


def has_ancestor(elem, parents, predicate) -> bool:
    node = parents.get(elem)
    while node is not None:
        if predicate(node):
            return True
        node = parents.get(node)
    return False


def is_equation_table(elem) -> bool:
    if elem.tag != "table":
        return False
    cls = elem.get("class", "").split()
    return any(c in cls for c in EQUATION_CLASSES)


def wrap_element(elem, parents, wrapper: ET.Element) -> None:
    parent = parents[elem]
    index = list(parent).index(elem)
    wrapper.tail = elem.tail
    elem.tail = None
    parent.remove(elem)
    wrapper.append(elem)
    parent.insert(index, wrapper)


def wrap_display_equations(doc: ET.Element) -> None:
    parents = parent_map(doc)
    for elem in list(doc.iter("table")):
        if not is_equation_table(elem):
            continue
        if has_ancestor(elem, parents, is_equation_table):
            continue
        wrapper = ET.Element("div", {
            "class": "reader-equation",
            "tabindex": "0", "role": "region", "aria-label": "Equation"})
        wrap_element(elem, parents, wrapper)


def wrap_inline_math(doc: ET.Element) -> None:
    parents = parent_map(doc)
    in_svg = ("svg", "foreignObject")
    for elem in list(doc.iter("math")):
        if elem.get("display") == "block":
            continue
        if has_ancestor(elem, parents, lambda n: n.tag in in_svg):
            continue
        wrapper = ET.Element("span", {"class": "reader-inline-math"})
        wrap_element(elem, parents, wrapper)


def entities_to_numeric(text: str) -> str:
    def rep(match):
        ent = match.group(1)
        if ent in ("amp", "lt", "gt", "quot", "apos"):
            return "&" + ent + ";"
        chars = html.entities.html5.get(ent + ";",
                                        html.entities.html5.get(ent))
        if chars is None:
            raise ConversionError(f"unknown entity &{ent};")
        return "".join(f"&#{ord(c)};" for c in chars)
    return re.sub(r"&([a-zA-Z][a-zA-Z0-9]*);", rep, text)


def render_document_math(doc: ET.Element) -> None:
    parents = parent_map(doc)
    maths = []
    for elem in doc.iter("math"):
        if has_ancestor(elem, parents,
                        lambda n: n.tag in ("svg", "foreignObject")):
            continue
        alt = elem.get("alttext")
        if not alt or not alt.strip():
            raise ConversionError("math element without usable alttext")
        maths.append((elem, alt))
    if not maths:
        return
    items = [{"id": m.get("id") or f"math-{i}",
              "tex": alt,
              "display": m.get("display") == "block"}
             for i, (m, alt) in enumerate(maths)]
    try:
        proc = subprocess.run(
            ["node", str(RENDERER), katex_js_path()],
            input=json.dumps(items), capture_output=True, text=True,
            errors="replace", timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConversionError(f"KaTeX render failed: {exc}") from exc
    if proc.returncode != 0:
        raise ConversionError(f"KaTeX render failed: "
                              + proc.stderr.strip()[:500])
    try:
        results = json.loads(proc.stdout)
    except ValueError as exc:
        raise ConversionError("KaTeX returned invalid JSON") from exc
    if len(results) != len(maths) or \
            [r["id"] for r in results] != [i["id"] for i in items]:
        raise ConversionError("KaTeX output does not match input items")
    for (m, alt), result in zip(maths, results):
        try:
            kspan = ET.fromstring(entities_to_numeric(result["html"]))
        except ET.ParseError as exc:
            raise ConversionError(
                f"KaTeX HTML not parseable for {result['id']}: {exc}") from exc
        strip_ns(kspan)
        remove_elements(kspan, "annotation",
                        ("encoding", "application/x-tex"))
        remove_elements(kspan, "annotation-xml")
        for inner in kspan.iter("math"):
            inner.set("alttext", alt)
            break
        classes = "reader-math"
        if m.get("display") == "block":
            classes += " reader-math-display"
        attrib = {"class": classes, "data-renderer": "katex",
                  "data-tex": alt}
        if m.get("id"):
            attrib["id"] = m.get("id")
        wrapper = ET.Element("span", attrib)
        wrapper.append(kspan)
        parent = parents[m]
        index = list(parent).index(m)
        wrapper.tail = m.tail
        m.tail = None
        parent.remove(m)
        parent.insert(index, wrapper)


def rewrite_resources(doc: ET.Element, xhtml: Path, slug: str) -> list:
    outdir = xhtml.parent.resolve()
    resources = []
    for elem in doc.iter():
        for attr in ("src", "href", "data", "poster"):
            url = elem.get(attr)
            if not url:
                continue
            parts = urlsplit(url)
            if parts.scheme or url.startswith("#") or url.startswith("//"):
                continue
            rel = parts.path
            target = (outdir / rel).resolve()
            if target != outdir and outdir not in target.parents:
                raise ConversionError(
                    f"resource escapes output dir: {url}")
            if not target.is_file():
                raise ConversionError(f"missing resource file: {url}")
            newpath = f"/assets/reader/{slug}/{rel}"
            elem.set(attr, urlunsplit(("", "", newpath,
                                       parts.query, parts.fragment)))
            resources.append((target, Path(rel)))
    return resources


def extract_fragment(xhtml: Path, slug: str, workdir: Path) -> Path:
    tree = ET.parse(xhtml)
    strip_ns(tree.getroot())
    doc = find_document(tree.getroot())
    remove_elements(doc, "div", ("class", "ltx_classification"))
    remove_elements(doc, "annotation", ("encoding", "application/x-tex"))
    remove_elements(doc, "annotation-xml")
    wrap_display_equations(doc)
    wrap_inline_math(doc)
    render_document_math(doc)
    resources = rewrite_resources(doc, xhtml, slug)
    frag = workdir / "fragment.html"
    body = ET.tostring(doc, encoding="unicode", method="xml",
                       short_empty_elements=False)
    frag.write_text("{% raw %}\n" + body + "\n{% endraw %}\n")
    res_dir = workdir / "resources"
    for target, rel in resources:
        dest = res_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
    return frag


def parse_fragment(path: Path) -> ET.Element:
    text = path.read_text()
    text = text.replace("{% raw %}", "").replace("{% endraw %}", "")
    return ET.fromstring(text)


def validate_article(path: Path) -> None:
    text = path.read_text()
    for bad in FORBIDDEN_CONTENT:
        if bad in text:
            raise ConversionError(f"forbidden content {bad!r} in {path}")
    root = parse_fragment(path)
    pmap = parent_map(root)
    ids = {}
    problems = []
    for elem in root.iter():
        if elem.tag in UNSAFE_TAGS:
            problems.append(f"unsafe element <{elem.tag}>")
        for attr in elem.attrib:
            if attr.lower().startswith("on"):
                problems.append(f"event handler attribute {attr}")
        eid = elem.get("id")
        if eid:
            ids.setdefault(eid, []).append(elem.tag)
        for attr in ("href", "src", "data", "poster"):
            url = elem.get(attr)
            if url:
                scheme = urlsplit(url).scheme
                if scheme not in ALLOWED_SCHEMES:
                    problems.append(f"disallowed scheme in {attr}={url}")
        if elem.tag == "a" and (elem.get("href") or "").startswith("#"):
            elem.set("_check_ref", elem.get("href")[1:])
        if elem.tag == "math" and len(list(elem)) == 0:
            problems.append("math element without child markup")
        if elem.tag == "a" and (elem.text or "").strip() in {"?", "??", "(??)"}:
            problems.append("unresolved reference '?' link")
        if "ltx_ref" in (elem.get("class") or "") \
                and (elem.text or "").strip() == "?":
            problems.append("unresolved ltx_ref")
        cls = elem.get("class") or ""
        if UNSAFE_CLASSES & set(cls.split()):
            problems.append(f"contact markup class {cls}")
        if "ltx_math_unparsed" in cls \
                and not has_ancestor(elem, pmap,
                                     lambda n: n.tag in ("svg", "foreignObject")):
            problems.append("surviving ltx_math_unparsed markup")
        if "katex-error" in cls:
            problems.append("KaTeX error markup")
        if "reader-math" in cls.split() and not any(
                "katex-html" in (d.get("class") or "") for d in elem.iter()):
            problems.append("reader-math without katex-html")
    dup = [k for k, v in ids.items() if len(v) > 1]
    if dup:
        problems.append(f"duplicate ids: {dup[:5]}")
    missing = [elem.get("_check_ref") for elem in root.iter()
               if elem.get("_check_ref") and elem.get("_check_ref") not in ids]
    if missing:
        problems.append(f"anchors without target: {missing[:5]}")
    if problems:
        raise ConversionError(f"validation failed for {path}: "
                              + "; ".join(problems))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_latexml(source: Path, workdir: Path) -> Path:
    stage = workdir / "source"
    stage.mkdir(parents=True)
    for rel, dest_rel in SOURCE_FILES:
        srcfile = source / rel
        if not srcfile.is_file():
            raise ConversionError(f"missing source input: {srcfile}")
        dest = stage / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(srcfile, dest)
    for d in SOURCE_DIRS:
        if (source / d).is_dir():
            shutil.copytree(source / d, stage / d)
    shutil.copy2(ADAPTER, stage / "main.tex")
    outdir = workdir / "output"
    outdir.mkdir()
    dest = outdir / "article.xhtml"
    log = outdir / "latexml.log"
    exe = shutil.which("latexmlc")
    if not exe:
        raise ConversionError("latexmlc not found on PATH; "
                              "set PERL5LIB/PATH for a local install")
    try:
        proc = subprocess.run(
            [exe, "--format=xhtml", f"--destination={dest}",
             f"--log={log}", "main.tex"],
            cwd=stage, env=latexml_env(), capture_output=True, text=True,
            errors="replace", timeout=900)
    except subprocess.TimeoutExpired as exc:
        raise ConversionError("latexmlc timed out") from exc
    errors = []
    warnings = []
    if log.is_file():
        for line in log.read_text(errors="replace").splitlines():
            if re.match(r"^(Error|Fatal)", line):
                errors.append(line.strip())
            elif line.startswith("Warning"):
                warnings.append(line.strip())
    diag = {"errors": errors, "warnings": warnings, "math_unparsed": 0}
    (workdir / "diagnostics.json").write_text(json.dumps(diag, indent=1))
    if proc.returncode != 0:
        raise ConversionError(
            f"latexmlc failed (rc={proc.returncode}): "
            + "; ".join(errors[:5] or [proc.stderr[-400:]]))
    if not dest.is_file():
        raise ConversionError("latexmlc produced no output")
    if errors:
        raise ConversionError("error diagnostics: " + "; ".join(errors[:5]))
    if dest.is_file():
        diag["math_unparsed"] = dest.read_text(
            errors="replace").count("ltx_math_unparsed")
        (workdir / "diagnostics.json").write_text(json.dumps(diag, indent=1))
    return dest


def warning_from_diagnostics(diag: dict) -> bool:
    if diag.get("errors"):
        raise ConversionError("diagnostics contain errors: "
                              + "; ".join(diag["errors"][:3]))
    return any(not w.startswith("Warning:not_parsed:")
               for w in diag.get("warnings", []))


def export_reader(xhtml: Path, slug: str, site: Path = SITE,
                  diagnostics: dict = None) -> Path:
    if not SLUG_RE.match(slug):
        raise ConversionError(f"invalid slug: {slug!r}")
    if not xhtml.is_file():
        raise ConversionError(f"xhtml not found: {xhtml}")
    warning = warning_from_diagnostics(dict(diagnostics or {}))
    work_root = site / "build" / "reader"
    work_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="export-", dir=work_root))
    try:
        frag = extract_fragment(xhtml, slug, work)
        validate_article(frag)
        digest = sha256(frag)
        manifest = {"fragment": f"reader/{slug}.html",
                    "warning": bool(warning),
                    "math_renderer": "katex",
                    "sha256": digest}
        manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
        res = work / "resources"
        if res.is_dir():
            assets_dir = site / "assets" / "reader" / slug
            assets_dir.mkdir(parents=True, exist_ok=True)
            for item in res.rglob("*"):
                if item.is_file():
                    dest = assets_dir / item.relative_to(res)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    tmp_dest = dest.with_name("." + dest.name + ".tmp")
                    shutil.copy2(item, tmp_dest)
                    os.replace(tmp_dest, dest)
        inc_dir = site / "_includes" / "reader"
        data_dir = site / "_data" / "readers"
        inc_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        frag_final = inc_dir / f"{slug}.html"
        tmp_frag = inc_dir / f".{slug}.html.tmp"
        shutil.copy2(frag, tmp_frag)
        os.replace(tmp_frag, frag_final)
        data_final = data_dir / f"{slug}.json"
        tmp_data = data_dir / f".{slug}.json.tmp"
        tmp_data.write_bytes(manifest_bytes)
        os.replace(tmp_data, data_final)
        return frag_final
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--xhtml", type=Path)
    group.add_argument("--source", type=Path)
    parser.add_argument("--diagnostics", type=Path)
    args = parser.parse_args()
    if not SLUG_RE.match(args.slug):
        print(f"invalid slug: {args.slug!r}", file=sys.stderr)
        sys.exit(1)
    if args.source and args.diagnostics:
        print("--diagnostics only valid with --xhtml", file=sys.stderr)
        sys.exit(1)
    BUILD.mkdir(parents=True, exist_ok=True)
    try:
        if args.source:
            work = Path(tempfile.mkdtemp(prefix="reader-latexml-",
                                         dir=BUILD))
            xhtml = run_latexml(args.source, work)
        else:
            xhtml = args.xhtml
            work = None
        diagnostics = None
        if args.diagnostics:
            if args.source:
                raise ConversionError("--diagnostics only with --xhtml")
            diagnostics = json.loads(args.diagnostics.read_text())
        elif args.source:
            diagnostics = json.loads(
                (work / "diagnostics.json").read_text())
        frag = export_reader(xhtml, args.slug, diagnostics=diagnostics)
        print(f"exported -> {frag}")
    except ConversionError as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
