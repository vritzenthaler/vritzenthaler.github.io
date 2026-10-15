# valentin-r.xyz

Personal website of Valentin Ritzenthaler: home, scientific publications and blog, in English and French.

Built with Jekyll, deployed to GitHub Pages by GitHub Actions, edited with [Pages CMS](https://pagescms.org) (`.pages.yml`).

## Local development

```sh
bundle config set --local path vendor/bundle
bundle install
bundle exec jekyll serve --livereload
```

## Content

- `_data/home.yml` — home page texts (FR / EN).
- `_data/publications.yml` — publications, displayed in file order within each category (`preprint`, `published`).
- `_data/site.yml` — name, LinkedIn and default descriptions.
- `_data/i18n.yml` — interface strings.
- `fr/_posts/`, `en/_posts/` — articles. The `ref` field links the two language versions; `published: false` keeps a draft out of the public site.
- `assets/images/blog/` — illustrations (3:2, 1200 × 800). `python3 tools/illustrations.py` regenerates the default ones.
- `assets/papers/` — downloadable PDFs.

Article bodies are raw Markdown (Pages CMS `code` field) so LaTeX is never escaped. Equations are rendered at build time with KaTeX (`kramdown-math-katex`, needs Node for ExecJS): `$$...$$` inside a sentence is inline, `$$...$$` alone in its own paragraph is displayed. The KaTeX stylesheet (`assets/katex/`) is only loaded on pages containing math; no JavaScript is shipped.

English is the default language: `/` renders the English home page, with `/en/` as canonical URL.

## HTML reader for articles

Reader pages display approved LaTeX articles as static HTML (LaTeXML structure + KaTeX math rendered at export time; no JavaScript). Exporting is a manual, local step run on trusted sources (the exporter is not a sandbox). Prerequisites: Python 3.10+, Node, the vendored bundle (`bundle install`), and LaTeXML on PATH for `--source` exports.

```sh
# From a frozen LaTeXML conversion (no LaTeXML needed):
python3 tools/reader/export.py --slug my-paper --xhtml /path/to/article.xhtml --diagnostics /path/to/diagnostics.json
python3 tools/reader/export.py --slug my-paper --source /path/to/article
```

Conversion and validation finish before any public file is updated; each file is replaced atomically (review the diff and run the tests/build before committing). `--source` expects the known preprint layout: `body.tex`, `preamble/macros-math.tex`, `sections/`, `bib/references.bib` and the compiled `build/aux/preprint-ams/main.bbl`. On success the exporter writes `_includes/reader/<slug>.html`, `_data/readers/<slug>.json` and any referenced files under `assets/reader/<slug>/`. To publish: commit the generated files, add a `reader: <slug>` field to the matching entry in `_data/publications.yml`, and add `en/reader/<slug>.html` / `fr/reader/<slug>.html` pages with `layout: reader`, `reader`, `ref`, `permalink` and `title` in front matter (see the existing `cdo-maxwell` pages). Intermediate logs and diagnostics stay in `build/reader/` (git-ignored, never shipped). Always compare the generated page against the article PDF before publishing.
