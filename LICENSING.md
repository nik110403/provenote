# Licensing map

| Path | Licence | File |
|---|---|---|
| `plugins/`, `tests/`, `.claude-plugin/` (code, skills, agents, templates) | MIT | `LICENSE` |
| `README.md`, `Makefile`, `scripts/`, `.githooks/`, `.github/` | MIT | `LICENSE` |
| `docs/` | CC BY 4.0 | `LICENSE-docs` |
| `examples/*/02_sources/` (third-party papers and their conversions) | CC BY 4.0, by their authors; attribution in `examples/*/SOURCES.md` | — |
| rest of `examples/` (notes, RUN.md, CLAUDE.md written for this kit) | CC BY 4.0 | `LICENSE-docs` |
| `tools/banner/fonts/` and the `assets/banner-*.svg` images (Fraunces, Space Grotesk, Atkinson Hyperlegible) | SIL Open Font License 1.1, by their authors; notices in `tools/banner/fonts/OFL.txt` | `tools/banner/fonts/OFL.txt` |
| `assets/transcript-*.svg` | MIT; no font is embedded, the text names a system monospace font stack | `LICENSE` |
| `site/` (landing page; self-hosted copies of the three typefaces are added at deploy time) | MIT for the page; fonts SIL Open Font License 1.1 | `LICENSE`, `tools/banner/fonts/OFL.txt` |

The three typefaces are embedded as WOFF2 data in the banner SVGs only so they render
on GitHub. They stay under the SIL Open Font License 1.1 and are not relicensed under MIT.
