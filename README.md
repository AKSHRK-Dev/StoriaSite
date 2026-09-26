# Storia website

Source of https://storiamc.com: the Storia landing page, downloads and documentation in English (`/en-us/`) and Japanese (`/ja-jp/`).

```sh
python3 build.py          # needs python3-markdown and python3-pygments; writes dist/
./deploy/deploy.sh        # builds and uploads to the web server (HOST=user@host)
```

- `content/<lang>/*.md`: documentation pages. `[[slug]]` links to another page; `{{VERSION}}`, `{{MC}}`, `{{GITHUB}}` are replaced.
- `build.py`: page templates, UI strings (`T`) and the docs navigation (`DOCS_NAV`).
- `static/`: CSS, JavaScript and icons, published under `/assets/`.
- `deploy/nginx.conf`: sends `/` to `/ja-jp/` or `/en-us/` from the visitor's saved choice or Cloudflare's `CF-IPCountry`.
