<div align="center">
  <img src="website/assets/background.png" alt="The World After the Fall — Banner" width="100%" />
  <h1>The World After the Fall — Reader</h1>
  <p>A fan-made static reader for <strong>The World After the Fall</strong> by Sing Shong — first and revised editions.</p>

  <p>
    🌐 <strong><a href="https://twatf.pages.dev">twatf.pages.dev</a></strong> &nbsp;|&nbsp;
    📥 <a href="https://twatf.pages.dev">Download EPUBs</a> &nbsp;|&nbsp;
    ⭐ Star this repo if you enjoy it!
  </p>
</div>

---

## 📖 About TWATF

**The World After the Fall** is a Korean fantasy novel by Sing Shong. After all of humanity is given a chance to regress back in time, one man — Jaehwan — refuses. He chooses to walk forward alone into an unknown world beyond the tower, into *the world after the fall*.

There are two editions:

- **First Edition** — The original 2016 publication by Sing Shong (247 chapters).
- **Revised Edition** — After finishing Omniscient Reader's Viewpoint, Sing Shong revised TWATF to create a connected cosmology and republished it (267 chapters).

---

## ✨ Features

- **Two Editions** — Read the First or Revised edition side by side, each with independent progress tracking.
- **Custom Themes** — Forest Night, Warm Paper, Daylight, Nord, Dracula, Solarized Dark, Catppuccin Mocha, and OLED Black.
- **Reader Settings** — Adjustable font family, text size, and a full background customizer (image, URL, solid colour, blur, brightness, zoom, positioning).
- **EPUB Downloads** — Download either edition as a complete EPUB 3 file, regenerated fresh from the same chapter sources as the website.
- **Bookmarks & Progress** — Browser-local per edition; no account or sync required.
- **Chapter Comments** — Per-chapter discussions powered by [Giscus](https://giscus.app) (GitHub Discussions).
- **Privacy First** — No trackers, no ads. All settings and progress stay in your browser.

---

## 🤝 Contributing

Corrections and contributions are welcome!

- Edit `chapters/first/` or `chapters/revised/` — never `dist/`.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.
- Questions? Join our [Discord Server](https://discord.gg/mRKHnmQnYJ).

---

## 📥 Download EPUBs

Both EPUBs are built from the same XHTML sources as the website — every correction reaches both outputs simultaneously.

👉 **[Download from the reader](https://twatf.pages.dev)**

---

## 🔗 Links

| | |
|---|---|
| 🌐 **Reader** | [twatf.pages.dev](https://twatf.pages.dev) |
| 💬 **Discord** | [discord.gg/mRKHnmQnYJ](https://discord.gg/mRKHnmQnYJ) |
| 🐙 **GitHub** | [Meaow-Technologies/TWATF-Reader](https://github.com/Meaow-Technologies/TWATF-Reader) |
| ❤️ **Support** | [patreon.com/MrMeaow46](https://patreon.com/MrMeaow46) |
| 📖 **Novel (Webnovel)** | [The World After the Fall](https://www.webnovel.com/book/the-world-after-the-fall_19214952106533805) |

---

## 💖 Support the Project

If you enjoy the reader, consider supporting us on Patreon. It keeps the project alive and the servers running.

👉 [patreon.com/MrMeaow46](https://patreon.com/MrMeaow46)

---

## 🏗️ Project Structure

```text
chapters/
  first/   0001.xhtml … 0247.xhtml   ← First edition sources
  revised/ 0001.xhtml … 0267.xhtml   ← Revised edition sources
website/                              ← HTML templates, CSS, JS, assets
scripts/build.py                      ← Builds website chapters, catalog, index, and both EPUBs
tests/test_build.py                   ← Correction propagation and build-safety tests
.github/workflows/build.yml           ← CI: tests + build + artifact upload on every push/PR
package.json                          ← Convenience npm commands (no dependencies)
dist/                                 ← Generated static output — do not edit or commit
```

---

## 🛠️ Build & Preview

Requires **Python 3.9+** only — no third-party packages.

```sh
# Build
python3 scripts/build.py

# Preview locally
python3 -m http.server 8765 --directory dist
```

Open [http://localhost:8765](http://localhost:8765). You can also use `npm run build` and `npm run preview` when Node/npm is available.

The build reads all XHTML sources, regenerates chapter JSON and metadata, generates the chapter index, and writes new `dist/assets/first.epub` and `dist/assets/revised.epub`. `dist/` is replaced only after full generation and verification succeed.

---

## ✅ Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

Tests check that a correction reaches only its selected edition's site and EPUB, that stale generated chapters are removed, and that invalid source leaves the last successful build intact.

---

## ☁️ Cloudflare Hosting

For a GitHub-connected Cloudflare Pages project:

| Setting | Value |
|---|---|
| **Build command** | `python3 scripts/build.py` |
| **Build output directory** | `dist` |
| **Root directory** | `/` (repo root) |
| **Python version env var** | `PYTHON_VERSION = 3.12` |

No runtime backend, Worker, or database needed — fully static HTML/CSS/JS/JSON + EPUBs.

---

## 💡 Inspiration

This reader is inspired by [LOTM-Reader](https://beyonder.pages.dev) and [GSGW-Reader](https://ireum.pages.dev). The implementation is independent and uses Python's standard library rather than those projects' toolchains.
