#!/usr/bin/env python3
"""
Sanitize a browser HAR capture of a web UI so it can be attached to an issue
or mirrored into a project's API docs without leaking secrets or PII.

  * Secrets → "<REDACTED>": Cookie / Set-Cookie, Authorization, X-CSRF-TOKEN,
    X-XSRF-TOKEN, x-xdr-auth-id / -nonce / -timestamp (advanced-key signing),
    plus any JSON key that looks like a credential (password, token, apiKey,
    secret, session, csrf, …) in request/response bodies.
  * PII: every email address → default-admin@example.com. With --domain, that
    domain (case-insensitive; subdomain labels kept) → example.com, the RFC 2606
    reserved domain, so URLs stay valid. Applied to
    URLs, headers, and bodies. No domain is replaced unless --domain is given.
  * Field names and JSON structure are left intact.
  * Static assets (HTML/JS/CSS/images/fonts) are dropped so the HAR is just the
    API traffic. Use --keep-static to retain them.

Only the standard library is used. Python ≥ 3.8.

Usage:
  scripts/sanitize-har.py capture.har                        # → capture.sanitized.har
  scripts/sanitize-har.py capture.har -o out.har
  scripts/sanitize-har.py capture.har --domain corp.internal # also replace your own domain
  scripts/sanitize-har.py capture.har --replace 'jsmith=user1' --replace 'HOST-42=host'
  scripts/sanitize-har.py capture.har --only-path /api/      # keep only matching URLs
  scripts/sanitize-har.py capture.har --list                 # print kept requests, no write

Review the output before attaching it. Hostnames outside --domain, record
names, and other free-text content are NOT redacted automatically — use --replace for
anything tenant-specific the script cannot know about.
"""

import argparse
import base64
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

REDACTED = "<REDACTED>"
SAFE_DOMAIN = "example.com"
SAFE_EMAIL = "default-admin@example.com"

# Header names (lower-cased) whose values are always replaced.
SECRET_HEADERS = {
    "cookie",
    "set-cookie",
    "authorization",
    "proxy-authorization",
    "x-csrf-token",
    "x-xsrf-token",
    "x-xdr-auth-id",
    "x-xdr-nonce",
    "x-xdr-timestamp",
    "x-xdr-signature",
    "x-api-key",
}

# Query-string / JSON key fragments that mark a value as a credential.
SECRET_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "apikey",
    "api_key",
    "api-key",
    "authorization",
    "cookie",
    "session",
    "csrf",
    "xsrf",
    "nonce",
    "signature",
    "credential",
    "private",
)

# Response MIME types that are static assets, not API traffic.
STATIC_MIME_PREFIXES = ("text/html", "text/css", "image/", "font/", "audio/", "video/")
STATIC_MIME_EXACT = {
    "application/javascript",
    "text/javascript",
    "application/x-javascript",
    "application/font-woff",
    "application/font-woff2",
    "application/x-font-ttf",
    "application/octet-stream",
    "application/wasm",
}
STATIC_PATH_SUFFIXES = (
    ".js", ".mjs", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".webp", ".html",
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Long opaque tokens (JWT-like or ≥40 chars of base64/hex) embedded in free text.
OPAQUE_TOKEN_RE = re.compile(r"\b(?:eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|[A-Fa-f0-9]{40,}|[A-Za-z0-9+/=_-]{64,})\b")


class Stats:
    def __init__(self):
        self.c = Counter()

    def hit(self, key, n=1):
        self.c[key] += n


def is_secret_key(key):
    k = key.lower()
    return any(frag in k for frag in SECRET_KEY_FRAGMENTS)


class Sanitizer:
    def __init__(self, domain, replacements, stats, scrub_opaque):
        self.stats = stats
        self.scrub_opaque = scrub_opaque
        # Emails first (so an address at the domain is redacted whole, local part
        # included), then the optional domain, then explicit replacements
        # (longest first so partial overlaps behave).
        self.literal = sorted(replacements, key=lambda p: -len(p[0]))
        # Case-insensitive match on the domain; exact-case on user replacements.
        self.domain_re = re.compile(re.escape(domain), re.IGNORECASE) if domain else None

    # ── strings ────────────────────────────────────────────────────────────
    def text(self, s):
        if not isinstance(s, str) or not s:
            return s
        out, n = EMAIL_RE.subn(SAFE_EMAIL, s)
        self.stats.hit("email", n)
        if self.domain_re:
            out, n = self.domain_re.subn(SAFE_DOMAIN, out)
            self.stats.hit("domain", n)
        for old, new in self.literal:
            if old in out:
                self.stats.hit("replace:" + old, out.count(old))
                out = out.replace(old, new)
        if self.scrub_opaque:
            out, n = OPAQUE_TOKEN_RE.subn(REDACTED, out)
            self.stats.hit("opaque-token", n)
        return out

    # ── JSON trees ─────────────────────────────────────────────────────────
    def tree(self, node, parent_key=None):
        if isinstance(node, dict):
            return {k: (self._redact_value(v, k) if is_secret_key(k) else self.tree(v, k))
                    for k, v in node.items()}
        if isinstance(node, list):
            return [self.tree(v, parent_key) for v in node]
        if isinstance(node, str):
            return self.text(node)
        return node

    def _redact_value(self, v, key):
        # Redact scalars/strings under a secret-looking key; recurse into
        # containers so structure survives (e.g. "sessionInfo": {...}).
        if isinstance(v, (dict, list)):
            return self.tree(v, key)
        if v is None or isinstance(v, bool):
            return v
        self.stats.hit("json-key:" + key)
        return REDACTED

    # ── body text (JSON if possible, else plain text) ──────────────────────
    def body_text(self, text):
        if text is None:
            return None
        stripped = text.lstrip()
        if stripped[:1] in "{[":
            try:
                parsed = json.loads(text)
            except ValueError:
                return self.text(text)
            return json.dumps(self.tree(parsed), ensure_ascii=False, separators=(",", ":"))
        return self.text(text)


def is_static(entry):
    resp = entry.get("response", {})
    mime = (resp.get("content", {}) or {}).get("mimeType", "") or ""
    mime = mime.split(";")[0].strip().lower()
    if mime in STATIC_MIME_EXACT or mime.startswith(STATIC_MIME_PREFIXES):
        return True
    path = urlsplit(entry.get("request", {}).get("url", "")).path.lower()
    return path.endswith(STATIC_PATH_SUFFIXES)


def sanitize_headers(headers, san, stats):
    out = []
    for h in headers or []:
        name = h.get("name", "")
        if name.lower() in SECRET_HEADERS:
            stats.hit("header:" + name.lower())
            out.append({**h, "value": REDACTED})
        else:
            out.append({**h, "value": san.text(h.get("value", ""))})
    return out


def sanitize_cookies(cookies, stats):
    out = []
    for c in cookies or []:
        stats.hit("cookie")
        out.append({**c, "value": REDACTED})
    return out


def sanitize_query(params, san, stats):
    out = []
    for p in params or []:
        name = p.get("name", "")
        if is_secret_key(name):
            stats.hit("query:" + name)
            out.append({**p, "value": REDACTED})
        else:
            out.append({**p, "value": san.text(p.get("value", ""))})
    return out


def sanitize_url(url, san, stats):
    parts = urlsplit(url)
    if parts.query:
        # Rebuild the query, redacting secret-looking params by name.
        kept = []
        for piece in parts.query.split("&"):
            name = piece.split("=", 1)[0]
            if is_secret_key(name):
                stats.hit("query:" + name)
                kept.append(name + "=" + REDACTED)
            else:
                kept.append(san.text(piece))
        parts = parts._replace(query="&".join(kept))
    return urlunsplit(parts._replace(netloc=san.text(parts.netloc), path=san.text(parts.path),
                                     fragment=san.text(parts.fragment)))


def sanitize_post_data(post, san, stats):
    if not post:
        return post
    out = dict(post)
    if "text" in out:
        out["text"] = san.body_text(out["text"])
    if "params" in out:
        out["params"] = sanitize_query(out["params"], san, stats)
    return out


def sanitize_content(content, san, stats):
    if not content:
        return content
    out = dict(content)
    text = out.get("text")
    if text is None:
        return out
    if out.get("encoding") == "base64":
        mime = (out.get("mimeType") or "").lower()
        if "json" in mime or mime.startswith("text/"):
            try:
                text = base64.b64decode(text).decode("utf-8")
                out.pop("encoding", None)
            except (ValueError, UnicodeDecodeError):
                stats.hit("dropped-binary-body")
                out["text"] = ""
                out["comment"] = "binary body dropped by sanitize-har"
                return out
        else:
            stats.hit("dropped-binary-body")
            out["text"] = ""
            out.pop("encoding", None)
            out["comment"] = "binary body dropped by sanitize-har"
            return out
    out["text"] = san.body_text(text)
    return out


def sanitize_entry(entry, san, stats):
    e = dict(entry)
    req = dict(e.get("request", {}))
    resp = dict(e.get("response", {}))

    req["url"] = sanitize_url(req.get("url", ""), san, stats)
    req["headers"] = sanitize_headers(req.get("headers"), san, stats)
    req["cookies"] = sanitize_cookies(req.get("cookies"), stats)
    req["queryString"] = sanitize_query(req.get("queryString"), san, stats)
    if "postData" in req:
        req["postData"] = sanitize_post_data(req["postData"], san, stats)

    resp["headers"] = sanitize_headers(resp.get("headers"), san, stats)
    resp["cookies"] = sanitize_cookies(resp.get("cookies"), stats)
    if "redirectURL" in resp and resp["redirectURL"]:
        resp["redirectURL"] = sanitize_url(resp["redirectURL"], san, stats)
    if "content" in resp:
        resp["content"] = sanitize_content(resp["content"], san, stats)

    e["request"] = req
    e["response"] = resp
    # Chrome adds these; they carry stack traces/URLs of the page, not needed.
    for noisy in ("_initiator", "_webSocketMessages"):
        e.pop(noisy, None)
    if "comment" in e:
        e["comment"] = san.text(e["comment"])
    return e


def sanitize_log(har, san, stats, keep_static, only_path):
    log = har.get("log", {})
    entries = log.get("entries", [])
    kept = []
    for entry in entries:
        url = entry.get("request", {}).get("url", "")
        if only_path and only_path not in urlsplit(url).path:
            stats.hit("dropped-path-filter")
            continue
        if not keep_static and is_static(entry):
            stats.hit("dropped-static")
            continue
        kept.append(sanitize_entry(entry, san, stats))

    pages = []
    for p in log.get("pages", []) or []:
        q = dict(p)
        if "title" in q:
            q["title"] = san.text(q["title"])
        pages.append(q)

    out = dict(har)
    out["log"] = {**log, "entries": kept, "pages": pages}
    if "creator" in out["log"]:
        out["log"]["creator"] = {**out["log"]["creator"], "comment": "sanitized by scripts/sanitize-har.py"}
    return out


def parse_replacements(items):
    pairs = []
    for item in items or []:
        if "=" not in item:
            sys.exit(f"--replace expects OLD=NEW, got: {item!r}")
        old, new = item.split("=", 1)
        if not old:
            sys.exit(f"--replace OLD must be non-empty: {item!r}")
        pairs.append((old, new))
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("har", type=Path, help="input .har file (browser export)")
    ap.add_argument("-o", "--output", type=Path, help="output path (default: <name>.sanitized.har)")
    ap.add_argument("--domain", default=None,
                    help=f"your own domain to replace with {SAFE_DOMAIN} (default: none — no domain replacement)")
    ap.add_argument("--replace", action="append", metavar="OLD=NEW",
                    help="extra literal substitution, repeatable (usernames, hostnames, incident names…)")
    ap.add_argument("--only-path", metavar="SUBSTR",
                    help="keep only entries whose URL path contains SUBSTR (e.g. /api/)")
    ap.add_argument("--keep-static", action="store_true", help="keep HTML/JS/CSS/image/font entries")
    ap.add_argument("--no-opaque-scrub", action="store_true",
                    help="don't replace long opaque tokens (JWTs, ≥40-char hex, ≥64-char base64) found in free text")
    ap.add_argument("--list", action="store_true", help="print the kept requests (method, status, URL) and exit without writing")
    ap.add_argument("--indent", type=int, default=1, help="JSON indent for the output (default 1; 0 = compact)")
    args = ap.parse_args(argv)

    try:
        har = json.loads(args.har.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        sys.exit(f"cannot read HAR {args.har}: {exc}")
    if "log" not in har or "entries" not in har.get("log", {}):
        sys.exit(f"{args.har} does not look like a HAR (missing log.entries)")

    stats = Stats()
    san = Sanitizer(args.domain, parse_replacements(args.replace), stats, scrub_opaque=not args.no_opaque_scrub)
    out = sanitize_log(har, san, stats, keep_static=args.keep_static, only_path=args.only_path)

    entries = out["log"]["entries"]
    if args.list:
        for e in entries:
            r, s = e["request"], e["response"]
            print(f"{r.get('method', '?'):6} {s.get('status', '?'):>3}  {r.get('url', '')}")
        print(f"\n{len(entries)} entries kept, {stats.c['dropped-static']} static dropped, "
              f"{stats.c['dropped-path-filter']} filtered by path", file=sys.stderr)
        return 0

    output = args.output or args.har.with_name(args.har.stem + ".sanitized.har")
    if output.resolve() == args.har.resolve():
        sys.exit("refusing to overwrite the input file; pass a different -o")
    output.write_text(json.dumps(out, ensure_ascii=False, indent=args.indent or None), encoding="utf-8")

    print(f"wrote {output}  ({len(entries)} entries kept, "
          f"{stats.c['dropped-static']} static dropped, {stats.c['dropped-path-filter']} filtered by path)")
    interesting = {k: v for k, v in sorted(stats.c.items()) if not k.startswith("dropped-") and v}
    if interesting:
        width = max(len(k) for k in interesting)
        for k, v in interesting.items():
            print(f"  {k:<{width}}  {v}")
    if not args.domain:
        print("\nNo --domain given: hostnames were left as captured. Pass --domain to replace your own domain.")
    print("\nReview before attaching: hostnames outside --domain, record names, and free text are not auto-redacted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
