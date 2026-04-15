"""Paper inventory - correlates markdown, PDF, and isocpp.org sources.

Source priority (highest to lowest):
  1. Markdown front matter + body - authoritative for all metadata
  2. Rendered PDF - fallback when markdown is absent
  3. isocpp.org - remote status and form URLs only. Title and author
     from isocpp.org are used as last-resort fallback when neither
     markdown nor PDF exists for a paper.

D/P prefixes are interchangeable for matching: D4007R0 and P4007R0
refer to the same paper.
"""

import logging
import re
from pathlib import Path

import yaml

from .pdf_reader import read_pdf

_log = logging.getLogger(__name__)

_DOC_RE = re.compile(r"([DPN])(\d{3,5})(R(\d+))?", re.IGNORECASE)

_MD_STRIP_RE = re.compile(
    r"\[([^\]]*)\]\([^)]*\)"    # [text](url) -> text
    r"|<[^>]+>"                  # strip HTML tags
)


def _parse_doc_number(raw):
    """Parse a document number into (full, base, revision).

    D4100R0 -> ("D4100R0", "P4100", 0)
    P4003R1 -> ("P4003R1", "P4003", 1)
    """
    if not raw:
        return None, None, None
    m = _DOC_RE.match(raw.strip().upper())
    if not m:
        return None, None, None
    prefix, num, _, rev = m.groups()
    rev = int(rev) if rev else 0
    full = f"{prefix}{num}R{rev}"
    base_prefix = "P" if prefix == "D" else prefix
    base = f"{base_prefix}{num}"
    return full, base, rev


def _read_markdown_paper(path):
    """Read YAML front matter and extract the abstract from a markdown file.

    Returns (front_matter_dict, brutal_summary) or (None, None).
    The brutal_summary is the first sentence of the ## Abstract section,
    with markdown links and HTML tags stripped.
    """
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read(64_000)
    except Exception:
        _log.debug("Could not read %s", path, exc_info=True)
        return None, None

    if not content.startswith("---"):
        return None, None

    end = content.find("---", 3)
    if end < 0:
        return None, None

    try:
        fm = yaml.safe_load(content[3:end])
        if not isinstance(fm, dict):
            return None, None
    except Exception:
        _log.debug("Bad YAML in %s", path, exc_info=True)
        return None, None

    body = content[end + 3:]
    brutal = _extract_markdown_abstract(body)
    return fm, brutal


def _extract_markdown_abstract(body):
    """Find ## Abstract in the markdown body, return the first sentence.

    Skips fenced code blocks. Returns the brutal summary string or None.
    """
    lines = body.split("\n")
    collecting = False
    in_code_block = False
    abstract_lines = []

    for line in lines:
        stripped = line.strip()
        if not collecting:
            if re.match(r"^#{1,2}\s+abstract\s*$", stripped, re.IGNORECASE):
                collecting = True
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("##") or stripped == "---":
            break
        if stripped:
            abstract_lines.append(stripped)

    if not abstract_lines:
        return None

    full = " ".join(abstract_lines)
    full = _MD_STRIP_RE.sub(lambda m: m.group(1) or "", full)
    full = re.sub(r"\s+", " ", full).strip()

    if len(full) < 20:
        return None

    m = re.match(r"([^.]+\.)", full)
    return m.group(1).strip() if m else full[:200]


def scan_markdown_dirs(watch_dirs):
    """Scan configured watch directories for .md files with front matter.

    Returns dict keyed by normalized doc_number.
    """
    papers = {}
    for dir_idx, entry in enumerate(watch_dirs, 1):
        if not entry.get("enabled", True):
            continue
        dirpath = Path(entry["path"])
        if not dirpath.is_dir():
            continue
        recursive = entry.get("recursive", False)
        glob = dirpath.rglob("*.md") if recursive else dirpath.glob("*.md")
        for md_path in glob:
            if not md_path.is_file():
                continue
            fm, brutal = _read_markdown_paper(md_path)
            if not fm or "document" not in fm:
                continue
            doc_str = str(fm["document"])
            full, base, rev = _parse_doc_number(doc_str)
            if not base:
                _log.warning("Skipping %s: invalid document number %r", md_path, doc_str)
                continue

            reply_to = fm.get("reply-to", [])
            if isinstance(reply_to, list):
                authors = ", ".join(
                    re.sub(r"\s*<[^>]+>", "", str(a)).strip()
                    for a in reply_to
                )
            else:
                authors = str(reply_to)

            papers[full] = {
                "doc_number": full,
                "base": base,
                "revision": rev,
                "title": fm.get("title", ""),
                "authors": authors,
                "date": str(fm.get("date", "")),
                "audience": fm.get("audience", ""),
                "brutal_summary": brutal,
                "md_path": str(md_path),
                "md_mtime": md_path.stat().st_mtime,
                "folder_idx": dir_idx,
            }
    return papers


def scan_pdf_dir(output_dir):
    """Scan the PDF output directory.

    Returns dict keyed by normalized doc_number.
    """
    papers = {}
    dirpath = Path(output_dir)
    if not dirpath.is_dir():
        return papers

    for pdf_path in sorted(dirpath.glob("*.pdf")):
        if not pdf_path.is_file():
            continue
        meta = read_pdf(pdf_path)
        if not meta.get("doc_number"):
            continue
        full, base, rev = _parse_doc_number(meta["doc_number"])
        if not base:
            continue
        papers[full] = {
            "doc_number": full,
            "base": base,
            "revision": rev,
            "title": meta.get("title", ""),
            "authors": meta.get("authors", ""),
            "date": meta.get("date", ""),
            "audience": meta.get("audience", ""),
            "brutal_summary": meta.get("brutal_summary"),
            "pdf_path": str(pdf_path),
            "pdf_mtime": pdf_path.stat().st_mtime,
        }
    return papers


def build_inventory(watch_dirs, output_dir, remote_papers=None):
    """Build the unified paper inventory from all three sources.

    Merges markdown, PDF, and isocpp.org data for each paper.
    Markdown is the source of truth for all metadata (title, authors,
    date, audience, abstract). PDF is a fallback for papers without
    markdown. isocpp.org provides remote status only.

    Returns a list of paper dicts sorted by doc_number descending,
    with only the latest revision of each base number shown.
    """
    md_papers = scan_markdown_dirs(watch_dirs)
    pdf_papers = scan_pdf_dir(output_dir)

    remote_by_base = {}
    if remote_papers:
        for rp in remote_papers:
            full, base, rev = _parse_doc_number(rp.get("doc_number"))
            if base:
                rkey = f"{base}R{rev}"
                remote_by_base[rkey] = {**rp, "base": base, "revision": rev}

    # Normalize all keys to base form for matching
    md_by_base = {}
    for k, v in md_papers.items():
        _, base, rev = _parse_doc_number(k)
        if base:
            md_by_base[f"{base}R{rev}"] = v

    pdf_by_base = {}
    for k, v in pdf_papers.items():
        _, base, rev = _parse_doc_number(k)
        if base:
            pdf_by_base[f"{base}R{rev}"] = v

    all_keys = set()
    all_keys.update(md_by_base.keys())
    all_keys.update(pdf_by_base.keys())
    all_keys.update(remote_by_base.keys())

    records = {}
    for key in all_keys:
        md = md_by_base.get(key)
        pdf = pdf_by_base.get(key)
        remote = remote_by_base.get(key)

        full, base, rev = _parse_doc_number(key)
        if not base:
            continue

        # Markdown is source of truth for metadata
        title = (md or {}).get("title") or (pdf or {}).get("title") or (remote or {}).get("title", "")
        authors = (md or {}).get("authors") or (pdf or {}).get("authors") or (remote or {}).get("author", "")
        date = (md or {}).get("date") or (pdf or {}).get("date") or (remote or {}).get("date", "")
        audience = (md or {}).get("audience") or (pdf or {}).get("audience", "")
        brutal_summary = (md or {}).get("brutal_summary") or (pdf or {}).get("brutal_summary")

        warnings = []
        if md and not brutal_summary:
            warnings.append("Missing abstract")

        md_path = md["md_path"] if md else None
        md_mtime = md["md_mtime"] if md else None
        pdf_path = pdf["pdf_path"] if pdf else None
        pdf_mtime = pdf["pdf_mtime"] if pdf else None

        stale_pdf = False
        if md_mtime and pdf_mtime:
            stale_pdf = pdf_mtime < md_mtime

        remote_status = (remote or {}).get("status", "").lower() if remote else ""

        primary_author = authors.split(",")[0].strip() if authors else ""

        stale_remote_meta = False
        if remote and md:
            remote_title = " ".join((remote.get("title") or "").split()).lower()
            local_title = " ".join((title or "").split()).lower()
            if remote_title and local_title and remote_title != local_title:
                stale_remote_meta = True
            remote_author = " ".join((remote.get("author") or "").split()).lower()
            local_author = " ".join(primary_author.split()).lower()
            if remote_author and local_author and remote_author != local_author:
                stale_remote_meta = True

        # Derive status
        if remote_status == "mailed":
            status = "mailed"
        elif md_path and (not pdf_path or stale_pdf):
            status = "needs_render"
        elif remote_status in ("draft", "review"):
            status = remote_status
        elif pdf_path and not remote:
            status = "local"
        elif not md_path and pdf_path:
            status = "orphan"
        else:
            status = remote_status or "local"

        records[full] = {
            "doc_number": full,
            "base": base,
            "revision": rev,
            "title": title,
            "authors": authors,
            "date": date,
            "audience": audience,
            "brutal_summary": brutal_summary,
            "primary_author": primary_author,
            "md_path": md_path,
            "md_mtime": md_mtime,
            "pdf_path": pdf_path,
            "pdf_mtime": pdf_mtime,
            "remote": remote,
            "status": status,
            "stale_pdf": stale_pdf,
            "stale_remote_meta": stale_remote_meta,
            "warnings": warnings,
            "folder_idx": md.get("folder_idx") if md else None,
        }

    # Group by base, keep only latest revision, attach prior revisions
    by_base = {}
    for rec in records.values():
        base = rec["base"]
        if base not in by_base:
            by_base[base] = []
        by_base[base].append(rec)

    result = []
    for revs in by_base.values():
        revs.sort(key=lambda r: r["revision"], reverse=True)
        latest = revs[0]
        prior = []
        for r in revs[1:]:
            entry = {"doc_number": r["doc_number"], "revision": r["revision"]}
            if r.get("remote") and r["remote"].get("form_url"):
                entry["form_url"] = r["remote"]["form_url"]
            prior.append(entry)
        prior.sort(key=lambda r: r["revision"])
        latest["prior_revisions"] = prior
        result.append(latest)
    result = [r for r in result if r["status"] != "mailed"]
    def _sort_key(p):
        dn = p.get("doc_number", "")
        m = _DOC_RE.match(dn)
        if m:
            return (int(m.group(2)), int(m.group(4) or 0))
        return (0, 0)
    result.sort(key=_sort_key, reverse=True)

    return result


def compute_summary(papers):
    """Compute summary counts for the dashboard bar."""
    counts = {
        "total": len(papers),
        "draft": 0,
        "review": 0,
        "needs_render": 0,
        "local": 0,
    }
    for p in papers:
        s = p.get("status", "")
        if s in counts:
            counts[s] += 1
    return counts
