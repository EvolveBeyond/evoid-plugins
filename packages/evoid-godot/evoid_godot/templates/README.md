# Templates

Default templates are embedded in `hosting.py`. To override, place your custom files here:

- `instant.html` — splash screen + loader (template variables: `{title}`, `{subtitle}`, `{bg_color}`, `{text_color}`, `{accent_color}`, `{logo_url}`, `{game_id}`)
- `sw.js` — Service Worker (template variables: `{game_id}`, `{version}`)

Override via `GameHost`:

```python
host = GameHost(template_dir="path/to/custom/templates/")
```
