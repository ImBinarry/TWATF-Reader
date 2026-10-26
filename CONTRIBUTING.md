# Correcting a chapter

1. Choose the correct edition under `chapters/first` or `chapters/revised/`.
2. Open the numbered file, such as `chapters/revised/0001.xhtml`.
3. Edit the text inside the existing paragraphs. Keep tags paired (`<p>…</p>`, `<em>…</em>`, `<strong>…</strong>`). Escape literal ampersands as `&amp;`, less-than as `&lt;`, and greater-than as `&gt;`. Unicode quotation marks can be entered directly.
4. If changing a title, update both the `<title>` and displayed heading as appropriate.
5. Run `python3 -m unittest discover -s tests -v` and `python3 scripts/build.py`.
6. Preview the chapter and its corresponding downloaded EPUB, then submit a pull request explaining the correction.

Only edit the affected edition unless the same correction is justified in both. Keep chapter numbers stable. New chapters must continue the numeric sequence. Do not edit or commit `dist/`; it is generated. GitHub Actions rebuilds both EPUBs and the reader on every push and pull request. After a maintainer merges the change, the connected Cloudflare build produces the updated site and downloads.

Supported chapter formatting includes paragraphs, headings, emphasis, strong text, blockquotes, line breaks, horizontal rules, lists, and superscript/subscript. Chapter elements do not accept attributes or scripts. Unsupported markup fails clearly rather than silently dropping content.

For website changes, edit `website/`. For community and Giscus URLs, edit `website/config.js`. Both still require a build.
