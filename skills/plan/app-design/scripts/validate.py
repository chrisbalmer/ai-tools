#!/usr/bin/env python3
"""Validate an app-design project directory.

Checks traceability, ID uniqueness, orphan references, and scope tags
against the conventions in the app-design skill. Stdlib only.

Subcommands:
  traceability  <project-path>  Every MVP AC has >=1 story; stories reference
                                valid ACs; ACs reference valid [V-NNN].
  ids           <project-path>  No duplicate definitions across all ID prefixes.
  orphans       <project-path>  Every [XYZ-NNN] reference resolves.
  scope         <project-path>  Every AC has a mvp/v2/future scope tag.
  migrations    <project-path>  No Issue file still contains the literal
                                `M_NEXT` placeholder (Phase 8 substitution).
  ujt-coverage  <project-path>  Every MVP AC has >=1 UJT covering it (opt-in:
                                soft-passes when no UJTs exist).
  vocab         <project-path> --repo <repo>
                                Every Phase 8 issue body uses at least one term
                                from <repo>/CONTEXT.md (opt-in: soft-passes
                                without --repo or without CONTEXT.md).
  all           <project-path>  Run traceability/ids/orphans/scope/migrations;
                                aggregate exit codes. ujt-coverage and vocab
                                are NOT included (both opt-in).

Exit codes:
  0  PASS
  >0 number of failures (aggregated across subcommands for `all`)
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Files / directories that are treated as REFERENCE-ONLY by default:
# their contents are scanned for references and orphan-checked, but they
# cannot introduce new ID definitions. This prevents Phase 8 issue files
# (which list dependencies in list-item form) and review/index documents
# (which list IDs in summary tables) from being misread as definitions.
DEFAULT_REFERENCE_ONLY_GLOBS: tuple[str, ...] = (
    "Issues*/**",
    "Issues - */**",
    "Design Review*.md",
    "*Index*.md",        # matched case-insensitively
    "**/*Index*.md",     # also inside subdirectories
    "**/00-*.md",        # numbered-index files (00-index.md, etc.)
    "*Sweep*.md",
    "Open Questions.md",
    "*Rollout Plan*.md",
    "Dependency Graph*.md",
    "Ideas/**",
)

# Canonical locations for ID *definitions*, per prefix. A line that looks
# like a definition is only registered as one if the file matches one of
# these globs for the matching prefix.
DEFAULT_CANONICAL_DEF_LOCATIONS: dict[str, tuple[str, ...]] = {
    "V": ("Vision*.md",),
    "AC": ("Acceptance Criteria/**", "Acceptance Criteria - */**"),
    "S": ("Stories/**", "Stories - */**"),
    "SCR": ("Wireframes*.md", "Wireframes/**", "Wireframes - */**"),
    "D": ("Architecture*.md", "Decisions/**", "Decisions - */**"),
}

# ---------- ID conventions ----------
# Bracketed IDs: V, AC, S, D, SCR.
# Unbracketed IDs: T (tests), M (migrations).
BRACKETED_PREFIXES = ("V", "AC", "S", "D", "SCR")
UNBRACKETED_PREFIXES = ("T", "M")

# Match [PREFIX-NNN] tolerating surrounding **bold**, _italic_, etc.
BRACKETED_RE = re.compile(
    r"\[(" + "|".join(BRACKETED_PREFIXES) + r")-(\d{2,4})\]"
)
UNBRACKETED_RE = re.compile(
    r"(?<![A-Za-z0-9_\[])(" + "|".join(UNBRACKETED_PREFIXES) + r")-(\d{2,4})(?![A-Za-z0-9_\]])"
)

# Scope tags appear backtick-wrapped per skill: `mvp`, `v2`, `future`.
SCOPE_RE = re.compile(r"`(mvp|v2|future)`")

# Lines that look like a definition.
# A definition has the ID *immediately after* the heading marker, optionally
# wrapped in bold/italic. Lines like `## Feature: [V-001]` or
# `Implements: [V-001]` are references, not definitions.
#
# Accepted markers:
#   #{1,6} ...                  Markdown heading
#   - ... / * ...               Bullet list item
#   > [!type] ...               Obsidian callout (with explicit type)
DEFINITION_LINE_RE = re.compile(
    r"^\s*"
    r"(?:"
    r"#{1,6}\s+"                          # heading marker
    r"|[-*]\s+"                           # list marker
    r"|>\s+\[![A-Za-z]+\]\s+"             # callout marker (requires [!type])
    r")"
    r"(?:\*\*|__|_|\*)?"                  # optional bold/italic open
    r"\[("                                # capture prefix
    + "|".join(BRACKETED_PREFIXES)
    + r")-(\d{2,4})\]"                    # capture number
)

# Restricted form for AC definitions specifically.
AC_DEFINITION_LINE_RE = re.compile(
    r"^\s*"
    r"(?:#{1,6}\s+|[-*]\s+|>\s+\[![A-Za-z]+\]\s+)"
    r"(?:\*\*|__|_|\*)?"
    r"\[AC-(\d{2,4})\]"
)

# `## Feature: [V-NNN] ...` heading — the AC->V back-reference.
AC_TRACES_TO_V_RE = re.compile(
    r"^\s*#{1,6}\s+Feature:\s*\[V-(\d{2,4})\]", re.MULTILINE
)

# Story traces-to-AC line: `**Traces to:** [AC-001], [AC-002]`.
STORY_TRACES_TO_RE = re.compile(
    r"^\s*\*\*Traces to:\*\*\s*(.+)$", re.MULTILINE | re.IGNORECASE
)


# ---------- Result types ----------
@dataclass
class CheckResult:
    name: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 0 if self.passed else max(1, len(self.failures))


def fmt_result(r: CheckResult) -> str:
    head = f"[{'PASS' if r.passed else 'FAIL'}] {r.name}"
    if r.passed and not r.failures:
        if r.notes:
            return head + "\n" + "\n".join(f"  - {n}" for n in r.notes)
        return head
    body = "\n".join(f"  - {f}" for f in r.failures)
    if r.notes:
        body += "\n" + "\n".join(f"  ~ {n}" for n in r.notes)
    return head + "\n" + body


# ---------- Project model ----------
@dataclass
class ProjectIndex:
    """In-memory index of every ID definition and reference in the project."""

    definitions: dict[str, list[Path]] = field(default_factory=lambda: defaultdict(list))
    references: dict[str, list[Path]] = field(default_factory=lambda: defaultdict(list))
    # IDs that have at least one *unwrapped* reference (i.e., not inside a
    # `code span`). An ID whose every reference is backtick-wrapped is
    # treated as a literal mention rather than a real cross-link.
    refs_seen_unwrapped: set[str] = field(default_factory=set)
    ac_scope: dict[str, str | None] = field(default_factory=dict)
    ac_traces_to_v: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    story_traces_to_ac: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    # ACs defined in files that declare a `## Feature: [V-NNN]` heading
    # are required to trace; ACs in cross-cutting files are exempt.
    ac_requires_v_trace: set[str] = field(default_factory=set)
    files_scanned: list[Path] = field(default_factory=list)


def _glob_match(rel: str, pat: str) -> bool:
    """Case-insensitive glob match — Obsidian filenames vary in case."""
    return fnmatch.fnmatch(rel.lower(), pat.lower())


def discover_markdown_files(project_path: Path, ignore_globs: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for p in sorted(project_path.rglob("*.md")):
        if not p.is_file():
            continue
        rel = p.relative_to(project_path).as_posix()
        if any(_glob_match(rel, pat) for pat in ignore_globs):
            continue
        out.append(p)
    return out


def is_reference_only(path: Path, project_path: Path, ref_only_globs: Iterable[str]) -> bool:
    rel = path.relative_to(project_path).as_posix()
    return any(_glob_match(rel, pat) for pat in ref_only_globs)


def _matches_canonical(
    path: Path,
    project_path: Path,
    prefix: str,
    canonical: dict[str, tuple[str, ...]],
) -> bool:
    """True if path matches a canonical-definition glob for the given prefix.

    Prefixes not present in `canonical` are treated as unrestricted (any
    file may define them) — backwards compatible for custom prefixes.
    """
    globs = canonical.get(prefix)
    if globs is None:
        return True
    rel = path.relative_to(project_path).as_posix()
    return any(_glob_match(rel, g) for g in globs)


def index_project(
    project_path: Path,
    ignore_globs: Iterable[str] = (),
    ref_only_globs: Iterable[str] = DEFAULT_REFERENCE_ONLY_GLOBS,
    canonical_def_locations: dict[str, tuple[str, ...]] | None = None,
) -> ProjectIndex:
    idx = ProjectIndex()
    ref_only_globs = tuple(ref_only_globs)
    canonical = (
        dict(canonical_def_locations)
        if canonical_def_locations is not None
        else dict(DEFAULT_CANONICAL_DEF_LOCATIONS)
    )
    for md in discover_markdown_files(project_path, ignore_globs):
        idx.files_scanned.append(md)
        ref_only = is_reference_only(md, project_path, ref_only_globs)
        text = md.read_text(encoding="utf-8", errors="replace")

        # Definition pass: scan line by line. Only the *first* such line
        # for an ID in a file counts as a definition.
        seen_in_file: set[str] = set()
        if not ref_only:
            for line in text.splitlines():
                m = DEFINITION_LINE_RE.match(line)
                if m:
                    prefix, num = m.group(1), m.group(2)
                    if not _matches_canonical(md, project_path, prefix, canonical):
                        continue  # ref in non-canonical file — skip
                    ident = f"[{prefix}-{num}]"
                    if ident not in seen_in_file:
                        idx.definitions[ident].append(md)
                        seen_in_file.add(ident)

        # Reference pass: every bracketed/unbracketed ID anywhere in file.
        # Track whether each ID ever appears unwrapped (not inside backticks).
        for m in BRACKETED_RE.finditer(text):
            ident = f"[{m.group(1)}-{m.group(2)}]"
            idx.references[ident].append(md)
            start, end = m.start(), m.end()
            before = text[start - 1] if start > 0 else ""
            after = text[end] if end < len(text) else ""
            if not (before == "`" and after == "`"):
                idx.refs_seen_unwrapped.add(ident)
        for m in UNBRACKETED_RE.finditer(text):
            ident = f"{m.group(1)}-{m.group(2)}"
            idx.references[ident].append(md)

        # AC -> V trace. Walk the file line-by-line tracking the *current*
        # `## Feature: [V-NNN]` heading; bind each AC to whichever V was
        # last seen above it. A file with no Feature heading at all leaves
        # ACs unbound and unrequired (cross-cutting AC files are exempt);
        # a file with at least one Feature heading marks every AC in it as
        # requiring a trace — ACs sitting above the first heading will
        # therefore fail the V-trace check, which is intentional.
        if not ref_only:
            file_has_feature_heading = bool(AC_TRACES_TO_V_RE.search(text))
            current_v: str | None = None
            for line in text.splitlines():
                fm = AC_TRACES_TO_V_RE.match(line)
                if fm:
                    current_v = f"[V-{fm.group(1)}]"
                    continue
                am = AC_DEFINITION_LINE_RE.match(line)
                if am:
                    ac_id = f"[AC-{am.group(1)}]"
                    if current_v is not None:
                        idx.ac_traces_to_v[ac_id].add(current_v)
                    if file_has_feature_heading:
                        idx.ac_requires_v_trace.add(ac_id)

        # AC scope tags.
        if ref_only:
            scope_lines: list[str] = []
        else:
            scope_lines = text.splitlines()
        for line in scope_lines:
            m = AC_DEFINITION_LINE_RE.match(line)
            if not m:
                continue
            ac_id = f"[AC-{m.group(1)}]"
            scope_match = SCOPE_RE.search(line)
            if scope_match:
                tag = scope_match.group(1)
            else:
                # Bare form fallback: only accept the scope word when it sits
                # at the very end of the heading line (optionally in parens),
                # so titles like "[AC-007] Future-proof password hashing"
                # don't get mis-tagged as `future`.
                bare = re.search(r"\(?\b(mvp|v2|future)\)?\s*$", line.rstrip())
                tag = bare.group(1) if bare else None
            idx.ac_scope.setdefault(ac_id, tag)

        # Story traces-to.
        if ref_only:
            lines: list[str] = []
        else:
            lines = text.splitlines()
        current_story: str | None = None
        for line in lines:
            sm = DEFINITION_LINE_RE.match(line)
            if sm and sm.group(1) == "S":
                current_story = f"[S-{sm.group(2)}]"
                continue
            if current_story:
                tm = STORY_TRACES_TO_RE.match(line)
                if tm:
                    for am in BRACKETED_RE.finditer(tm.group(1)):
                        if am.group(1) == "AC":
                            idx.story_traces_to_ac[current_story].add(
                                f"[AC-{am.group(2)}]"
                            )
                    current_story = None
    return idx


# ---------- Subcommand: traceability ----------
def check_traceability(idx: ProjectIndex) -> CheckResult:
    failures: list[str] = []

    mvp_acs = {ac for ac, scope in idx.ac_scope.items() if scope == "mvp"}
    stories_dir_files = {p for p in idx.files_scanned if "Stories" in p.parts}
    covered_acs: set[str] = set()
    for ac_set in idx.story_traces_to_ac.values():
        covered_acs |= ac_set
    for f in stories_dir_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in BRACKETED_RE.finditer(text):
            if m.group(1) == "AC":
                covered_acs.add(f"[AC-{m.group(2)}]")

    for ac in sorted(mvp_acs):
        if ac not in covered_acs:
            failures.append(
                f"MVP {ac} has no story covering it (no story traces to it "
                "and no story file mentions it)"
            )

    defined_acs = {ac for ac in idx.definitions if ac.startswith("[AC-")}
    for story, ac_set in idx.story_traces_to_ac.items():
        for ac in ac_set:
            if ac not in defined_acs:
                failures.append(
                    f"{story} traces to {ac} but no AC definition for {ac} exists"
                )

    defined_vs = {v for v in idx.definitions if v.startswith("[V-")}
    defined_acs_all = sorted(ac for ac in idx.definitions if ac.startswith("[AC-"))
    for ac in defined_acs_all:
        v_set = idx.ac_traces_to_v.get(ac, set())
        if not v_set:
            if ac in idx.ac_requires_v_trace:
                failures.append(
                    f"{ac} does not reference any [V-NNN] (expected a "
                    "'## Feature: [V-NNN]' heading in the AC file)"
                )
            continue
        for v in v_set:
            if v not in defined_vs:
                failures.append(
                    f"{ac} traces to {v} but {v} is not defined in any file"
                )

    notes = [
        f"{len(defined_vs)} vision features, {len(defined_acs_all)} ACs "
        f"({len(mvp_acs)} mvp), {len(idx.story_traces_to_ac)} stories"
    ]
    return CheckResult("traceability", not failures, failures, notes)


# ---------- Subcommand: ids ----------
def check_ids(idx: ProjectIndex) -> CheckResult:
    failures: list[str] = []
    counts: dict[str, int] = defaultdict(int)
    for ident, files in idx.definitions.items():
        prefix = ident.strip("[]").split("-")[0]
        counts[prefix] += 1
        if len(files) > 1:
            file_list = ", ".join(f.name for f in files)
            failures.append(f"{ident} defined in multiple files: {file_list}")
    notes = [f"{prefix}: {n} unique ids" for prefix, n in sorted(counts.items())]
    return CheckResult("ids", not failures, failures, notes)


# ---------- Subcommand: orphans ----------
def check_orphans(idx: ProjectIndex) -> CheckResult:
    failures: list[str] = []
    notes: list[str] = []
    defined = set(idx.definitions.keys())
    for ident, files in idx.references.items():
        if not ident.startswith("["):
            continue  # T- / M- references — not required to be defined
        if ident in defined:
            continue
        if ident not in idx.refs_seen_unwrapped:
            notes.append(
                f"{ident} appears only in backtick code spans "
                f"({len({f.name for f in files})} file(s)) — "
                "treated as literal, not a real reference"
            )
            continue
        sample = ", ".join(sorted({f.name for f in files})[:3])
        failures.append(f"{ident} referenced in {sample} but never defined")
    return CheckResult("orphans", not failures, failures, notes)


# ---------- Subcommand: ujt-coverage ----------
# UJT files live under `User Journey Tests/`. They reference the ACs they
# prove via either a frontmatter `traces_to:` list (YAML, bare IDs) or a
# body `**Traces to:** [AC-NNN], [AC-NNN]` line (markdown, bracketed IDs).
UJT_DIR_NAMES = ("User Journey Tests", "User Journey Tests - v2")

# Capture an AC-NNN token whether or not it's bracketed.
ANY_AC_RE = re.compile(r"\[?AC-(\d{2,4})\]?")

# Capture the frontmatter `traces_to:` line in either inline-list form
# (`traces_to: [V-001, AC-002]`) or block-list form (multi-line `-` items).
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
TRACES_TO_INLINE_RE = re.compile(r"^traces_to:\s*\[([^\]]*)\]", re.MULTILINE)
TRACES_TO_BLOCK_RE = re.compile(
    r"^traces_to:\s*\n((?:\s+-\s*.+\n?)+)", re.MULTILINE
)
BODY_TRACES_TO_RE = re.compile(
    r"^\s*\*\*Traces to:\*\*\s*(.+)$", re.MULTILINE | re.IGNORECASE
)


def _find_ujt_files(project_path: Path) -> list[Path]:
    out: list[Path] = []
    for name in UJT_DIR_NAMES:
        d = project_path / name
        if d.is_dir():
            for p in sorted(d.rglob("*.md")):
                if p.is_file():
                    out.append(p)
    return out


def _extract_ac_refs_from_ujt(text: str) -> set[str]:
    refs: set[str] = set()
    fm = FRONTMATTER_RE.match(text)
    if fm:
        block = fm.group(1)
        for m in TRACES_TO_INLINE_RE.finditer(block):
            for am in ANY_AC_RE.finditer(m.group(1)):
                refs.add(f"[AC-{am.group(1)}]")
        for m in TRACES_TO_BLOCK_RE.finditer(block):
            for am in ANY_AC_RE.finditer(m.group(1)):
                refs.add(f"[AC-{am.group(1)}]")
    for m in BODY_TRACES_TO_RE.finditer(text):
        for am in ANY_AC_RE.finditer(m.group(1)):
            refs.add(f"[AC-{am.group(1)}]")
    return refs


def check_ujt_coverage(project_path: Path, idx: ProjectIndex) -> CheckResult:
    ujt_files = _find_ujt_files(project_path)
    if not ujt_files:
        return CheckResult(
            "ujt-coverage",
            True,
            [],
            ["no UJTs found — opt-in check, soft-passing"],
        )

    covered: set[str] = set()
    per_file: dict[Path, set[str]] = {}
    for p in ujt_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        refs = _extract_ac_refs_from_ujt(text)
        per_file[p] = refs
        covered |= refs

    mvp_acs = {ac for ac, scope in idx.ac_scope.items() if scope == "mvp"}
    defined_acs = {ac for ac in idx.definitions if ac.startswith("[AC-")}

    failures: list[str] = []
    uncovered = sorted(mvp_acs - covered)
    for ac in uncovered:
        failures.append(f"MVP {ac} has no UJT covering it (no UJT traces to it)")

    for p, refs in per_file.items():
        for ac in sorted(refs):
            if ac not in defined_acs:
                failures.append(
                    f"{p.name} traces to {ac} but no AC definition for {ac} exists"
                )

    notes = [
        f"{len(ujt_files)} UJT file(s); {len(covered)} AC(s) covered; "
        f"{len(mvp_acs)} MVP AC(s) total"
    ]
    return CheckResult("ujt-coverage", not failures, failures, notes)


# ---------- Subcommand: migrations ----------
# Phase 8 substitutes the `M_NEXT` placeholder with a concrete migration
# slot when generating Issue files. A stray `M_NEXT` in any Issue file
# means the substitution was skipped. Design artifacts (Architecture.md,
# Acceptance Criteria/, Stories/) legitimately keep `M_NEXT` until the
# slot is claimed, so we only flag the post-substitution surface (Issues).
M_NEXT_TOKEN = "M_NEXT"
ISSUES_DIR_GLOBS: tuple[str, ...] = ("Issues", "Issues - *")


def _find_issue_files(project_path: Path) -> list[Path]:
    out: list[Path] = []
    for entry in sorted(project_path.iterdir()) if project_path.is_dir() else ():
        if not entry.is_dir():
            continue
        rel = entry.name
        if not any(_glob_match(rel, g) for g in ISSUES_DIR_GLOBS):
            continue
        for p in sorted(entry.rglob("*.md")):
            if p.is_file():
                out.append(p)
    return out


def check_migrations(project_path: Path) -> CheckResult:
    issue_files = _find_issue_files(project_path)
    if not issue_files:
        return CheckResult(
            "migrations",
            True,
            [],
            ["no Issues directory found — nothing to check"],
        )
    failures: list[str] = []
    for p in issue_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        if M_NEXT_TOKEN in text:
            rel = p.relative_to(project_path).as_posix()
            failures.append(
                f"{rel} still contains `M_NEXT` — Phase 8 substitution was not performed"
            )
    return CheckResult(
        "migrations",
        not failures,
        failures,
        [f"{len(issue_files)} issue file(s) scanned"],
    )


# ---------- Subcommand: vocab ----------
# Verify that Phase 8 issue files (and story files) are written in the
# project's domain vocabulary as recorded in <repo>/CONTEXT.md.
#
# Opt-in: requires --repo pointing at the project repo root. Soft-passes
# if --repo is not provided or if CONTEXT.md is missing. The check is
# intentionally conservative — it flags issues whose body has *zero
# overlap* with the glossary, which is a strong signal of design drift
# without producing false positives on niche-term issues.
CONTEXT_TERM_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z0-9 \-]+)\*\*\s*:", re.MULTILINE)


def _parse_context_terms(context_md: Path) -> list[str]:
    """Extract bold-defined terms from a CONTEXT.md following the format
    in grill-with-docs/CONTEXT-FORMAT.md (`**TermName**:`)."""
    text = context_md.read_text(encoding="utf-8", errors="replace")
    return [m.group(1).strip() for m in CONTEXT_TERM_RE.finditer(text)]


def check_vocab(project_path: Path, idx: ProjectIndex, repo_path: Path | None) -> CheckResult:
    if repo_path is None:
        return CheckResult(
            "vocab",
            True,
            [],
            ["no --repo given — opt-in check, soft-passing"],
        )
    context_md = repo_path / "CONTEXT.md"
    if not context_md.exists():
        return CheckResult(
            "vocab",
            True,
            [],
            [f"no CONTEXT.md at {context_md} — soft-passing; create one via /grill-with-docs"],
        )
    terms = _parse_context_terms(context_md)
    if not terms:
        return CheckResult(
            "vocab",
            True,
            [],
            [f"CONTEXT.md at {context_md} has no `**Term**:` definitions — soft-passing"],
        )
    issue_files = _find_issue_files(project_path)
    if not issue_files:
        return CheckResult(
            "vocab",
            True,
            [],
            ["no Issues directory found — nothing to check"],
        )
    # Case-insensitive whole-word match against any glossary term.
    term_patterns = [
        (t, re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE)) for t in terms
    ]
    failures: list[str] = []
    for p in issue_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        if not any(pat.search(text) for _, pat in term_patterns):
            rel = p.relative_to(project_path).as_posix()
            failures.append(
                f"{rel} uses no terms from CONTEXT.md — likely vocabulary drift"
            )
    notes = [
        f"{len(terms)} glossary term(s); {len(issue_files)} issue file(s) scanned"
    ]
    return CheckResult("vocab", not failures, failures, notes)


# ---------- Subcommand: scope ----------
def check_scope(idx: ProjectIndex) -> CheckResult:
    failures: list[str] = []
    valid = {"mvp", "v2", "future"}
    for ac in sorted(idx.ac_scope):
        scope = idx.ac_scope[ac]
        if scope is None:
            failures.append(f"{ac} has no scope tag (expected `mvp`, `v2`, or `future`)")
        elif scope not in valid:
            failures.append(f"{ac} has invalid scope tag `{scope}`")
    notes: list[str] = []
    buckets: dict[str, int] = defaultdict(int)
    for s in idx.ac_scope.values():
        if s in valid:
            buckets[s] += 1
    for k in ("mvp", "v2", "future"):
        notes.append(f"{k}: {buckets.get(k, 0)}")
    return CheckResult("scope", not failures, failures, notes)


# ---------- CLI ----------
SUBCOMMANDS = {
    "traceability": check_traceability,
    "ids": check_ids,
    "orphans": check_orphans,
    "scope": check_scope,
}


def _build_index(args: argparse.Namespace) -> ProjectIndex | int:
    project_path: Path = args.project_path
    if not project_path.exists() or not project_path.is_dir():
        print(
            f"error: project path does not exist or is not a directory: {project_path}",
            file=sys.stderr,
        )
        return 2
    ignore_globs = tuple(args.ignore or ())
    ref_only_globs: tuple[str, ...]
    if args.no_default_ref_only:
        ref_only_globs = tuple(args.ref_only or ())
    else:
        ref_only_globs = DEFAULT_REFERENCE_ONLY_GLOBS + tuple(args.ref_only or ())
    idx = index_project(project_path, ignore_globs=ignore_globs, ref_only_globs=ref_only_globs)
    if not idx.files_scanned:
        print(f"warning: no markdown files found under {project_path}", file=sys.stderr)
    return idx


def run_subcommand(name: str, args: argparse.Namespace) -> int:
    built = _build_index(args)
    if isinstance(built, int):
        return built
    if name == "ujt-coverage":
        result = check_ujt_coverage(args.project_path, built)
    elif name == "migrations":
        result = check_migrations(args.project_path)
    elif name == "vocab":
        result = check_vocab(args.project_path, built, args.repo)
    else:
        result = SUBCOMMANDS[name](built)
    print(fmt_result(result))
    return result.exit_code


def run_all(args: argparse.Namespace) -> int:
    built = _build_index(args)
    if isinstance(built, int):
        return built
    total_failures = 0
    overall_pass = True
    for name in ("traceability", "ids", "orphans", "scope"):
        result = SUBCOMMANDS[name](built)
        print(fmt_result(result))
        if not result.passed:
            overall_pass = False
            total_failures += max(1, len(result.failures))
    migrations_result = check_migrations(args.project_path)
    print(fmt_result(migrations_result))
    if not migrations_result.passed:
        overall_pass = False
        total_failures += max(1, len(migrations_result.failures))
    print("---")
    print(
        f"OVERALL: {'PASS' if overall_pass else 'FAIL'} "
        f"({total_failures} failure{'s' if total_failures != 1 else ''})"
    )
    return 0 if overall_pass else total_failures


def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("project_path", type=Path)
    p.add_argument(
        "--ignore",
        action="append",
        metavar="GLOB",
        help="Glob (relative to project_path) of files to skip entirely. Repeatable.",
    )
    p.add_argument(
        "--ref-only",
        action="append",
        metavar="GLOB",
        help=(
            "Glob (relative to project_path) of files treated as reference-only "
            "(scanned for references but never as ID definitions). Repeatable. "
            "Adds to the defaults unless --no-default-ref-only is set."
        ),
    )
    p.add_argument(
        "--no-default-ref-only",
        action="store_true",
        help="Disable the built-in reference-only defaults (Issues/, Design Review*, Indexes, etc.).",
    )
    p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help=(
            "Path to the project repo root (where CONTEXT.md and docs/adr/ live). "
            "Used by the `vocab` subcommand. If omitted, vocab soft-passes."
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description="Validate an app-design project directory.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    # `ujt-coverage` and `vocab` are intentionally excluded from `all` —
    # both are opt-in. UJT coverage only matters on UI-heavy projects;
    # vocab requires --repo. Keeping them out of `all` makes the default
    # run identical regardless of project shape or repo presence.
    for name in (*SUBCOMMANDS.keys(), "migrations", "ujt-coverage", "vocab", "all"):
        p = sub.add_parser(name, help=f"Run the {name} check.")
        _add_common_args(p)
    args = parser.parse_args(argv)
    if args.cmd == "all":
        return run_all(args)
    return run_subcommand(args.cmd, args)


if __name__ == "__main__":
    sys.exit(main())
