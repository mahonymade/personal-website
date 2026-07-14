# Personal Website

A simple, hand-written personal site. No build step, no frameworks — just HTML and CSS.

## Structure

- `index.html` — home page
- `projects.html` — things I've built
- `writing.html` — essay index (essays live in `essays/`)
- `reading.html` — book log
- `style.css` — one shared stylesheet for every page

## Editing

Open any `.html` file in a text editor, change the text, save. To add an entry
on the Projects, Writing, or Reading pages, copy an existing
`<article class="entry">...</article>` block and edit it.

To preview locally, just open `index.html` in a browser.

## Adding an essay from a Word doc

`scripts/docx_to_essay.py` converts a `.docx` into a draft essay page:

```
python3 scripts/docx_to_essay.py "~/Downloads/My Essay.docx" my-essay-slug
```

This writes `essays/my-essay-slug.html`, already wrapped in the site's nav/footer,
with Word's formatting cruft stripped out. Any hyperlinks found in the doc are
listed in a comment at the top (`text -> URL`) since Word doesn't export them
as visible links — wire them into `<a>` tags by hand.

Still needs a manual pass after: set the real `<h1>` title and `.meta` line,
link up citations from the comment block, add an entry on `writing.html`, and
proofread against the original. Requires macOS (uses the built-in `textutil`).
