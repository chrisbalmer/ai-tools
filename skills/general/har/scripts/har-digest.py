#!/usr/bin/env python3
"""
Read a HAR without dumping it into the conversation.

A browser HAR is hundreds of KB of mostly noise (assets, heartbeats, base64
bodies). This tool gives small, targeted views so the transcript only carries
what matters. Run it against a SANITIZED HAR (scripts/sanitize-har.py) —
`show`/`extract`/`grep` print body content verbatim.

Stdlib only. Python ≥ 3.8.

Subcommands:
  list     [--api] [--path SUBSTR] [--method M]     index of entries
  show N   [--headers] [--depth D] [--max-chars C]  one entry: url, headers, bodies
  keys N                                             top-level keys/types of both bodies
  diff A B [--side req|resp|cross]                   key-level diff between two bodies
  extract N --side req|resp [-o FILE]                write one body as JSON (fixture)
  grep PATTERN [--api]                               entries whose url/body match a regex

Typical flow after sanitizing (the HAR path comes first, then the subcommand):
  har-digest.py x.sanitized.har list --api                  # find the interesting calls
  har-digest.py x.sanitized.har keys 9                      # what does the write send/return?
  har-digest.py x.sanitized.har diff 0 9 --side cross       # GET body vs POST body → write-only keys
  har-digest.py x.sanitized.har show 9 --depth 1            # skim the bodies
  har-digest.py x.sanitized.har extract 9 --side resp -o docs/api/foo-sample.json

Entry numbers are the indexes printed by `list` (0-based, over ALL entries, so
they stay stable whether or not you pass --api).
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

STATIC_MIME_PREFIXES = ("text/html", "text/css", "image/", "font/", "audio/", "video/")
STATIC_MIME_EXACT = {
    "application/javascript", "text/javascript", "application/x-javascript",
    "application/font-woff", "application/font-woff2", "application/x-font-ttf",
    "application/octet-stream", "application/wasm",
}
STATIC_PATH_SUFFIXES = (
    ".js", ".mjs", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".webp", ".html",
)
# Chatter that is never the call you're looking for. Extend per project if needed.
NOISE_PATH_FRAGMENTS = (
    "/api-messages/", "/notification_banner/", "/heartbeat", "/ping", "/telemetry",
    "/analytics", "/sockjs", "/socket.io", "/ws/",
)
INTERESTING_HEADERS = (
    "content-type", "accept", "host", "origin", "referer", "x-csrf-token",
    "x-xsrf-token", "authorization", "cookie", "set-cookie", "location",
)


def load(path):
    try:
        har = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        sys.exit(f"cannot read HAR {path}: {exc}")
    entries = har.get("log", {}).get("entries")
    if entries is None:
        sys.exit(f"{path} does not look like a HAR (missing log.entries)")
    return entries


def mime_of(entry):
    m = (entry.get("response", {}).get("content", {}) or {}).get("mimeType", "") or ""
    return m.split(";")[0].strip().lower()


def is_static(entry):
    m = mime_of(entry)
    if m in STATIC_MIME_EXACT or m.startswith(STATIC_MIME_PREFIXES):
        return True
    return urlsplit(entry.get("request", {}).get("url", "")).path.lower().endswith(STATIC_PATH_SUFFIXES)


def is_noise(entry):
    path = urlsplit(entry.get("request", {}).get("url", "")).path
    return any(frag in path for frag in NOISE_PATH_FRAGMENTS)


def body_text(entry, side):
    if side == "req":
        return (entry.get("request", {}).get("postData") or {}).get("text")
    content = entry.get("response", {}).get("content") or {}
    text = content.get("text")
    if text and content.get("encoding") == "base64":
        try:
            return base64.b64decode(text).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None
    return text


def body_json(entry, side):
    text = body_text(entry, side)
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def short_url(url):
    p = urlsplit(url)
    return p.path + ("?" + p.query if p.query else "")


def type_name(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return f"list[{len(v)}]"
    if isinstance(v, dict):
        return f"object{{{len(v)}}}"
    return type(v).__name__


def truncate_tree(node, depth, max_chars):
    """Return a copy of node with containers below `depth` collapsed to a summary."""
    if depth < 0:
        return f"<{type_name(node)}>" if isinstance(node, (dict, list)) else _clip(node, max_chars)
    if isinstance(node, dict):
        return {k: truncate_tree(v, depth - 1, max_chars) for k, v in node.items()}
    if isinstance(node, list):
        out = [truncate_tree(v, depth - 1, max_chars) for v in node[:5]]
        if len(node) > 5:
            out.append(f"<… {len(node) - 5} more>")
        return out
    return _clip(node, max_chars)


def _clip(v, max_chars):
    if isinstance(v, str) and len(v) > max_chars:
        return v[:max_chars] + f"<… +{len(v) - max_chars} chars>"
    return v


# ── subcommands ─────────────────────────────────────────────────────────────

def cmd_list(entries, args):
    shown = 0
    for i, e in enumerate(entries):
        if args.api and (is_static(e) or is_noise(e)):
            continue
        r, s = e.get("request", {}), e.get("response", {})
        url = r.get("url", "")
        if args.path and args.path not in urlsplit(url).path:
            continue
        if args.method and r.get("method", "").upper() != args.method.upper():
            continue
        req_len = len((r.get("postData") or {}).get("text") or "")
        resp_len = (s.get("content") or {}).get("size") or len((s.get("content") or {}).get("text") or "")
        t = (e.get("startedDateTime") or "")[11:23]
        print(f"[{i:3}] {t} {r.get('method', '?'):6} {s.get('status', '?'):>3} {mime_of(e):24} "
              f"req={req_len:<7} resp={resp_len:<8} {short_url(url)}")
        shown += 1
    print(f"\n{shown} of {len(entries)} entries shown", file=sys.stderr)


def cmd_show(entries, args):
    e = pick(entries, args.n)
    r, s = e.get("request", {}), e.get("response", {})
    print(f"[{args.n}] {e.get('startedDateTime')}")
    print(f"{r.get('method')} {r.get('url')}")
    print(f"→ {s.get('status')} {s.get('statusText', '')}  {mime_of(e)}")
    if args.headers:
        print("\nrequest headers:")
        for h in r.get("headers", []):
            if args.all_headers or h["name"].lower() in INTERESTING_HEADERS:
                print(f"  {h['name']}: {h.get('value', '')}")
        print("response headers:")
        for h in s.get("headers", []):
            if args.all_headers or h["name"].lower() in INTERESTING_HEADERS:
                print(f"  {h['name']}: {h.get('value', '')}")
    if r.get("queryString"):
        print("\nquery:", {q["name"]: q.get("value") for q in r["queryString"]})
    for side, label in (("req", "REQUEST BODY"), ("resp", "RESPONSE BODY")):
        j = body_json(e, side)
        if j is not None:
            print(f"\n{label} (json, depth {args.depth}):")
            print(json.dumps(truncate_tree(j, args.depth, args.max_chars), indent=1, ensure_ascii=False))
        else:
            t = body_text(e, side)
            if t:
                print(f"\n{label} (text, {len(t)} chars):")
                print(_clip(t, args.max_chars * 4))


def cmd_keys(entries, args):
    e = pick(entries, args.n)
    for side, label in (("req", "request"), ("resp", "response")):
        j = body_json(e, side)
        print(f"{label}:", end=" ")
        if j is None:
            t = body_text(e, side)
            print("(no json body)" if not t else f"(non-json, {len(t)} chars)")
            continue
        if isinstance(j, dict):
            print(f"object with {len(j)} keys")
            for k in sorted(j):
                print(f"  {k:<28} {type_name(j[k])}")
        elif isinstance(j, list):
            print(f"list[{len(j)}]", "of", type_name(j[0]) if j else "-")
            if j and isinstance(j[0], dict):
                for k in sorted(j[0]):
                    print(f"  [0].{k:<24} {type_name(j[0][k])}")
        else:
            print(type_name(j), j)


def flatten(node, prefix="", out=None, max_depth=3):
    if out is None:
        out = {}
    if isinstance(node, dict) and max_depth > 0:
        for k, v in node.items():
            flatten(v, f"{prefix}.{k}" if prefix else k, out, max_depth - 1)
    else:
        out[prefix] = node
    return out


def cmd_diff(entries, args):
    a, b = pick(entries, args.a), pick(entries, args.b)
    if args.side == "cross":
        ja, jb, la, lb = body_json(a, "resp"), body_json(b, "req"), f"[{args.a}] response", f"[{args.b}] request"
    else:
        ja, jb, la, lb = body_json(a, args.side), body_json(b, args.side), f"[{args.a}] {args.side}", f"[{args.b}] {args.side}"
    if ja is None or jb is None:
        sys.exit("both entries need a JSON body on the chosen side (try --side cross for GET-response vs POST-request)")
    fa, fb = flatten(ja, max_depth=args.depth), flatten(jb, max_depth=args.depth)
    added = sorted(set(fb) - set(fa))
    removed = sorted(set(fa) - set(fb))
    changed = sorted(k for k in set(fa) & set(fb) if fa[k] != fb[k])
    print(f"comparing {la}  →  {lb}\n")
    if added:
        print(f"keys only in {lb} ({len(added)}):")
        for k in added:
            print(f"  + {k:<32} {type_name(fb[k])}  {_clip(json.dumps(fb[k], ensure_ascii=False), 80)}")
    if removed:
        print(f"\nkeys only in {la} ({len(removed)}):")
        for k in removed:
            print(f"  - {k:<32} {type_name(fa[k])}")
    if changed:
        print(f"\nchanged ({len(changed)}):")
        for k in changed:
            print(f"  ~ {k:<32} {_clip(json.dumps(fa[k], ensure_ascii=False), 60)}  →  {_clip(json.dumps(fb[k], ensure_ascii=False), 60)}")
    if not (added or removed or changed):
        print("no differences at this depth")


def cmd_extract(entries, args):
    e = pick(entries, args.n)
    j = body_json(e, args.side)
    if j is None:
        sys.exit(f"entry {args.n} has no JSON {args.side} body")
    text = json.dumps(j, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output} ({len(text)} chars) from [{args.n}] {args.side} "
              f"{e['request'].get('method')} {short_url(e['request'].get('url', ''))}")
    else:
        sys.stdout.write(text)


def cmd_grep(entries, args):
    rx = re.compile(args.pattern, re.IGNORECASE)
    hits = 0
    for i, e in enumerate(entries):
        if args.api and (is_static(e) or is_noise(e)):
            continue
        url = e.get("request", {}).get("url", "")
        where = []
        if rx.search(url):
            where.append("url")
        for side in ("req", "resp"):
            t = body_text(e, side) or ""
            m = rx.search(t)
            if m:
                start = max(0, m.start() - 40)
                snippet = t[start:m.end() + 40].replace("\n", " ")
                where.append(f"{side}: …{snippet}…")
        if where:
            hits += 1
            print(f"[{i:3}] {e['request'].get('method'):6} {short_url(url)}")
            for w in where:
                print(f"       {w}")
    print(f"\n{hits} matching entries", file=sys.stderr)


def pick(entries, n):
    if n < 0 or n >= len(entries):
        sys.exit(f"entry {n} out of range (0..{len(entries) - 1})")
    return entries[n]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("har", type=Path, help="HAR file (use the SANITIZED one)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="index of entries")
    p.add_argument("--api", action="store_true", help="hide static assets and known chatter")
    p.add_argument("--path", help="only URLs whose path contains this substring")
    p.add_argument("--method", help="only this HTTP method")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("show", help="one entry in detail")
    p.add_argument("n", type=int)
    p.add_argument("--headers", action="store_true", help="print the interesting headers")
    p.add_argument("--all-headers", action="store_true", help="print every header (implies --headers)")
    p.add_argument("--depth", type=int, default=2, help="JSON nesting depth to expand (default 2)")
    p.add_argument("--max-chars", type=int, default=200, help="clip strings longer than this")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("keys", help="top-level keys/types of request and response bodies")
    p.add_argument("n", type=int)
    p.set_defaults(fn=cmd_keys)

    p = sub.add_parser("diff", help="key-level diff between two bodies")
    p.add_argument("a", type=int)
    p.add_argument("b", type=int)
    p.add_argument("--side", choices=("req", "resp", "cross"), default="cross",
                   help="req/resp compares the same side; cross compares A's response to B's request (default)")
    p.add_argument("--depth", type=int, default=2, help="flatten nested objects to this depth (default 2)")
    p.set_defaults(fn=cmd_diff)

    p = sub.add_parser("extract", help="write one body as a JSON fixture")
    p.add_argument("n", type=int)
    p.add_argument("--side", choices=("req", "resp"), required=True)
    p.add_argument("-o", "--output", help="output path (default: stdout)")
    p.set_defaults(fn=cmd_extract)

    p = sub.add_parser("grep", help="entries whose URL or body matches a regex")
    p.add_argument("pattern")
    p.add_argument("--api", action="store_true", help="hide static assets and known chatter")
    p.set_defaults(fn=cmd_grep)

    args = ap.parse_args(argv)
    if getattr(args, "all_headers", False):
        args.headers = True
    entries = load(args.har)
    args.fn(entries, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
