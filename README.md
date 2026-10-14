# riveraferran.com

Food & beverage portfolio of Adrian Rivera Ferran. Static site, generated in place.

- `python3 prepare_assets.py --check` — verify source media on the Selected Works volume
- `python3 prepare_assets.py` — compress selected photos/videos into `assets/`
- `python3 ingest_media.py` — append newly selected photos from MEDIA_ROOT into `assets/`
- `python3 build.py` — regenerate all HTML pages (commit the output)
- `python3 -m unittest discover -s tests -v` — run tests

Deploy: GitHub Pages serves this repo's `main` branch root at https://riveraferran.com.
Videos: Livid embeds when configured in projects.json, else self-hosted MP4.
Form: Formspree endpoint in site-config.json, mailto fallback when empty.

## Media, ingest and hidden projects

**MEDIA_ROOT** is `/Volumes/Scratch Disk/Projects/Websites/riveraferran.com-media` — a byte
copy of the F&B Selected Works folders, one folder per client. It is a SEPARATE folder from
the tech portfolio's media (`/Volumes/Scratch Disk/Projects/Websites/portfolio/`); never mix
the two.

`python3 ingest_media.py` appends new photos, per client folder, from MEDIA_ROOT. It
converts with `sips` (full max 2000px q72, thumb max 640px q70; never upscales), and numbering
continues after the existing photos. It is append-only: existing photos and assets are never
renumbered or regenerated (the homepage hero `assets/img/acai-express/01.jpg` and the masthead
cut-out depend on this). It skips exact-duplicate files and photos already on the site, writes
`projects.json` and `assets-manifest.json`, and is idempotent — a second run prints
`nothing to do`. Videos are ignored.

`"hidden": true` in `projects.json` keeps the project in the data and its assets on disk but
gives it no card, no number and no gallery page (`build.py` deletes a stale
`gallery/<slug>.html`), and `prepare_assets.py` does not regenerate it.

Livid-only videos may have `mp4 = ""` in the manifest: the page renders only the Livid iframe,
and tests and `prepare_assets.py` do not expect an mp4 file.

## Design system

Light editorial theme: warm paper ground, ink type, one bold accent. Everything is
driven by CSS custom properties at the top of `assets/css/styles.css`.

- **Ground / type**: `--paper #F7F5F0`, `--ink #131210`, `--muted #6B6960`, hairlines `--line`.
- **Accent**: `--accent #E2401C` (tomato). To switch to cobalt, change the three
  accent values at the top of `styles.css` to `#1B4DFF` / `#0F35D6` / `#EBEFFF`.
- **Fonts**: Fraunces (display) + Inter (body), self-hosted in `assets/fonts/` and
  declared in `assets/css/fonts.css`. No third-party font requests. To refresh them,
  run `python3 fetch_fonts.py`.
- **Photos are shown at their native ratios** — cards and photo grids use CSS
  masonry (`columns`), not fixed aspect-ratio boxes, so portrait food shots are not
  cropped.
- **Masthead (homepage hero)** — a full-bleed photograph with the name passing
  BEHIND its subject. Three layers: `assets/img/<project>/NN.jpg` as the back plate,
  the giant name, then `assets/img/masthead/front.webp` — the subject cut out with
  alpha — sitting ON TOP of the name (`z-index: 3`). The small labels sit above
  everything (`z-index: 4`). Both image layers use the same `cover` geometry, so the
  cut-out lands exactly over the subject in the back photo. To change the hero photo,
  set `hero_image` and `hero_cutout` in `site-config.json`; the cut-out is generated
  from the photo (ask Hermes — it uses macOS Vision, not a manual mask). The name is
  a two-line lockup sized as `min(calc((min(1240px, 100vw) - 2 * var(--gut)) / 7.263),
  240px)` — 7.263 is the measured width of "ADRIAN RIVERA" per 1px of font size, which
  is what makes the line fill the measure exactly. Re-measure if the name changes.
- **Nav over the photo** — the homepage body carries `has-masthead`; that makes the
  nav fixed, transparent and white until you scroll past the masthead, where JS adds
  `.scrolled` and it returns to the paper style. Other pages keep the light nav.
- **Social share card**: `assets/img/og-cover.jpg` (1200×630), referenced by the
  `og:image` tags on every page. Regenerate by rendering the card at 1200×630 and
  saving over it.
- **Favicon**: inline SVG tomato monogram in each page `<head>`.

