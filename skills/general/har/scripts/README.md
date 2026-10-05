# scripts/

Helpers for the `har` skill. Stdlib only, Python ≥ 3.8. Neither is on `PATH`; invoke by absolute path from the skill directory.

## `sanitize-har.py` — raw HAR → sanitized HAR

```
sanitize-har.py <raw>.har [-o OUT] [--domain D] [--replace OLD=NEW ...]
                [--only-path SUBSTR] [--keep-static] [--no-opaque-scrub] [--list] [--indent N]
```

- Default output: `<name>.sanitized.har` next to the input. Refuses to overwrite the input.
- `--list` prints the kept requests (method, status, URL) and writes nothing — safe preview.
- Redaction summary is printed on every run (`header:cookie 1`, `email 63`, …). A zero where you expected hits means a header/key name the script doesn't know — extend `SECRET_HEADERS` / `SECRET_KEY_FRAGMENTS` and commit.

What is redacted / replaced:

| Class | Rule |
|---|---|
| Headers | `Cookie`, `Set-Cookie`, `Authorization`, `Proxy-Authorization`, `X-CSRF-TOKEN`, `X-XSRF-TOKEN`, `x-xdr-auth-id`, `x-xdr-nonce`, `x-xdr-timestamp`, `x-xdr-signature`, `X-API-Key` → `<REDACTED>` |
| Cookies | every `cookies[].value` on request and response → `<REDACTED>` |
| Query params / JSON keys | name containing `password`, `passwd`, `secret`, `token`, `apikey`, `api_key`, `api-key`, `authorization`, `cookie`, `session`, `csrf`, `xsrf`, `nonce`, `signature`, `credential`, `private` → value `<REDACTED>` (containers under such a key are recursed, not dropped, so structure survives) |
| Domain | only with `--domain D`: `D` (case-insensitive; subdomain labels kept) → `example.com` (RFC 2606 reserved, so URLs stay valid) everywhere: URLs, headers, bodies. No default — without the flag, hostnames are left as captured |
| Emails | every RFC-ish email → `default-admin@example.com` (applied before the domain rule, so local parts never survive) |
| Opaque tokens | JWT-shaped strings, ≥40-char hex, ≥64-char base64 in free text → `<REDACTED>` (disable with `--no-opaque-scrub`) |
| Bodies | JSON bodies parsed and walked (base64 JSON decoded first); non-JSON text gets the string rules; binary bodies dropped with a `comment` |
| Entries | static assets by MIME/extension dropped unless `--keep-static`; `--only-path` keeps just one prefix; Chrome `_initiator` and `_webSocketMessages` stripped |

Not redacted (by design — they're content, not secrets): record names, indicator values, hostnames that don't match `--domain` (all hostnames when it isn't given), free text. Use `--replace` for those.

## `har-digest.py` — read a sanitized HAR in small views

```
har-digest.py <sanitized>.har list    [--api] [--path SUBSTR] [--method M]
har-digest.py <sanitized>.har show N  [--headers|--all-headers] [--depth D] [--max-chars C]
har-digest.py <sanitized>.har keys N
har-digest.py <sanitized>.har diff A B [--side req|resp|cross] [--depth D]
har-digest.py <sanitized>.har extract N --side req|resp [-o FILE]
har-digest.py <sanitized>.har grep PATTERN [--api]
```

- Entry indexes are 0-based over **all** entries and stable across subcommands, whether or not `--api` hides some in `list`.
- `--api` hides static assets and known chatter (`/api-messages/`, `/notification_banner/`, heartbeats, sockets). Extend `NOISE_PATH_FRAGMENTS` for a new platform.
- `diff --side cross` (the default) compares **A's response** to **B's request** — the read-modify-write idiom: `diff <GET> <POST>` lists exactly the keys the UI added before posting the object back.
- `diff --side resp` between a pre-write GET and the write's response shows what the server derived (appended history, bumped version).
- `show` collapses containers below `--depth` to `<object{n}>` / `<list[n]>` and clips long strings, so a 3 KB object prints as a screenful.
- `extract` writes pretty-printed JSON suitable as a test fixture. Run it only on the sanitized file.
