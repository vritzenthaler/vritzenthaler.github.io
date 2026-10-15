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
