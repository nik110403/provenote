# Landing page

Static page for GitHub Pages. No build step, no JavaScript framework, no third-party requests; the three typefaces are self-hosted.

- `index.html`, `style.css`: the page.
- `fonts/`, `demo-*.svg`: copied from `tools/banner/fonts/` and `assets/` by `.github/workflows/pages.yml` at deploy time (git-ignored here, so there is one source of truth).

Preview locally:

```sh
mkdir -p site/fonts && cp tools/banner/fonts/* site/fonts/ && cp assets/demo-*.svg site/
python3 -m http.server -d site 8000
```

Enabling Pages is a manual owner step: repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. The workflow then deploys on every push to `main`.

The fonts are SIL OFL 1.1; the notice ships as `fonts/OFL.txt`.
