"""Tests for find_uncited_links and add_citations_to_links: duplicate
superscript prevention, group-citation patterns, orphan entry prevention,
ref insertion points, entry format, subsection preservation, description
text preservation, and Acknowledgments orphan preservation.
"""
import os
import re
import tempfile

from helpers import _lines
from cite import (
    RefEntry,
    ResolveResult,
    add_citations_to_links,
    build_exclusion_ranges,
    find_refs_section,
    find_uncited_links,
    load_config,
    parse_references,
    scan,
    write,
)


def _default_config():
    return {'exempt_sections': [], 'exempt_links': [], 'exempt_orphans': []}


def _scan_and_write(content, fix=False, resolved=None, config=None):
    if config is None:
        config = load_config(None)
    fd, tmp = tempfile.mkstemp(suffix='.md')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        r = scan(tmp, config)
        output = write(r, resolved or ResolveResult(), fix=fix)
    finally:
        os.unlink(tmp)
    return output


# ---------------------------------------------------------------------------
# Duplicate superscript prevention
# ---------------------------------------------------------------------------

class TestDuplicateSuperscriptPrevention:
    def test_duplicate_superscript_not_inserted(self):
        lines = _lines("""\
See [P3552R3](https://example.com/p3552r3.html)<sup>[1]</sup> here.
## References
[1] P3552R3, example""")
        refs = {1: RefEntry(1, 'P3552R3, example', 2, 'A')}
        uncited = []
        result_lines, _ = add_citations_to_links(
            lines, uncited, refs, 3, ResolveResult())
        line = result_lines[0]
        count = line.count('<sup>[')
        assert count == 1

    def test_link_without_sup_gets_citation_added(self):
        lines = _lines("""\
See [P3552R3](https://example.com/p3552r3.html) here.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'P3552R3', 'https://example.com/p3552r3.html')]
        result_lines, _ = add_citations_to_links(
            lines, uncited, refs, 3, ResolveResult())
        assert '<sup>[' in result_lines[0]


# ---------------------------------------------------------------------------
# Group-citation pattern
# ---------------------------------------------------------------------------

class TestGroupCitationPattern:
    def test_group_citation_link_not_flagged_uncited(self):
        lines = _lines("""\
([link](https://example.com), text)<sup>[1]</sup> more.
## References
[1] Ref""")
        excluded = build_exclusion_ranges(lines)
        results = find_uncited_links(lines, excluded, 2, _default_config())
        urls = [r.url for r in results]
        assert 'https://example.com' not in urls

    def test_group_citation_with_description(self):
        lines = _lines("""\
([P2079R10](https://example.com/p2079r10.html), "Parallel Scheduler")<sup>[1]</sup> text.
## References
[1] Ref""")
        excluded = build_exclusion_ranges(lines)
        results = find_uncited_links(lines, excluded, 2, _default_config())
        urls = [r.url for r in results]
        assert 'https://example.com/p2079r10.html' not in urls

    def test_non_group_link_still_flagged(self):
        lines = _lines("""\
See [link](https://example.com) for details.
## References
[1] Other ref""")
        excluded = build_exclusion_ranges(lines)
        results = find_uncited_links(lines, excluded, 2, _default_config())
        urls = [r.url for r in results]
        assert 'https://example.com' in urls

    def test_link_directly_followed_by_sup_still_ok(self):
        lines = _lines("""\
[link](https://example.com)<sup>[1]</sup> text.
## References
[1] Ref""")
        excluded = build_exclusion_ranges(lines)
        results = find_uncited_links(lines, excluded, 2, _default_config())
        urls = [r.url for r in results]
        assert 'https://example.com' not in urls

    def test_nested_parens_do_not_false_skip(self):
        lines = _lines("""\
[link](https://example.com) some text (unrelated note)<sup>[1]</sup>.
## References
[1] Ref""")
        excluded = build_exclusion_ranges(lines)
        results = find_uncited_links(lines, excluded, 2, _default_config())
        urls = [r.url for r in results]
        assert 'https://example.com' in urls


# ---------------------------------------------------------------------------
# Description-then-sup pattern
# ---------------------------------------------------------------------------

class TestDescriptionThenSup:
    def test_link_followed_by_description_sup_not_flagged(self):
        lines = _lines("""\
[P3796R1](https://example.com/p3796r1.html) ("Coroutine Task Issues")<sup>[1]</sup> catalogs concerns.
## References
[1] Ref""")
        excluded = build_exclusion_ranges(lines)
        results = find_uncited_links(lines, excluded, 2, _default_config())
        urls = [r.url for r in results]
        assert 'https://example.com/p3796r1.html' not in urls

    def test_link_followed_by_plain_text_is_flagged(self):
        lines = _lines("""\
[link](https://example.com) some text here.
## References
[1] Ref""")
        excluded = build_exclusion_ranges(lines)
        results = find_uncited_links(lines, excluded, 2, _default_config())
        urls = [r.url for r in results]
        assert 'https://example.com' in urls


# ---------------------------------------------------------------------------
# Orphan entry prevention
# ---------------------------------------------------------------------------

class TestOrphanEntryPrevention:
    def test_no_orphan_entry_when_sup_exists(self):
        lines = _lines("""\
See [link](https://example.com)<sup>[1]</sup> here.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'link', 'https://example.com')]
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, ResolveResult())
        assert len(new_refs) == 1

    def test_entry_created_when_no_sup_exists(self):
        lines = _lines("""\
See [link](https://example.com) here.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'link', 'https://example.com')]
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, ResolveResult())
        assert len(new_refs) > 1

    def test_ref_count_unchanged_when_all_links_already_cited(self):
        lines = _lines("""\
[a](https://a.com)<sup>[1]</sup> [b](https://b.com)<sup>[2]</sup>.
## References
[1] Ref A
[2] Ref B""")
        refs = {
            1: RefEntry(1, 'Ref A', 2, 'A'),
            2: RefEntry(2, 'Ref B', 3, 'A'),
        }
        uncited = [(0, 'a', 'https://a.com'), (0, 'b', 'https://b.com')]
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 4, ResolveResult())
        assert len(new_refs) == 2


# ---------------------------------------------------------------------------
# Ref insertion point and format
# ---------------------------------------------------------------------------

class TestRefInsertionPoint:
    def test_ref_insertion_after_last_entry(self):
        lines = _lines("""\
See [example](https://example.com)<sup>[1]</sup>.
See [other](https://other.com) link.
## References
[1] Example ref

---
## Acknowledgments
Thanks.""")
        refs = {1: RefEntry(1, 'Example ref', 3, 'A')}
        uncited = [(1, 'other', 'https://other.com')]
        result_lines, _ = add_citations_to_links(
            lines, uncited, refs, 5, ResolveResult())
        content = ''.join(result_lines)
        hr_pos = content.find('---\n## Acknowledgments')
        new_ref_pos = content.find('[2]')
        assert new_ref_pos < hr_pos


class TestNewRefEntryFormat:
    def test_new_ref_entry_uses_markdown_link(self):
        lines = _lines("""\
See [P9999R0](https://example.com/p9999r0.pdf) link.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'P9999R0', 'https://example.com/p9999r0.pdf')]
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, ResolveResult())
        for num, entry in new_refs.items():
            if num > 1:
                assert '](https://' in entry.text or '](http://' in entry.text


# ---------------------------------------------------------------------------
# Subsection miscategorisation (orphan/uncited cross-reference)
# ---------------------------------------------------------------------------

class TestSubsectionMiscategorisation:
    PAPER_WITH_SUBSECTIONS = """\
Body [lib](https://github.com/example/lib) text.

## References

### WG21 Papers

[1] [P2300R10](https://example.com/p2300r10.html) - "std::execution"

### Libraries

[2] [lib](https://github.com/example/lib) - A great library (Author).

### Other

[3] [C++ Draft](https://eel.is/c++draft/) - Working draft.
"""

    def test_orphan_with_uncited_link_not_removed(self):
        output = _scan_and_write(self.PAPER_WITH_SUBSECTIONS, fix=True)
        assert 'A great library' in output

    def test_orphan_without_uncited_link_still_removed(self):
        content = """\
Body <sup>[1]</sup> text.

## References

[1] Cited ref

[2] Pure orphan with no body link at all
"""
        output = _scan_and_write(content, fix=True)
        assert 'Pure orphan' not in output

    def test_preserved_orphan_gets_sup_tag(self):
        output = _scan_and_write(self.PAPER_WITH_SUBSECTIONS, fix=True)
        m = re.search(
            r'\[lib\]\(https://github\.com/example/lib\)<sup>\[\d+\]</sup>',
            output)
        assert m is not None

    def test_preserved_orphan_stays_in_subsection(self):
        output = _scan_and_write(self.PAPER_WITH_SUBSECTIONS, fix=True)
        libs_pos = output.find('### Libraries')
        lib_entry_pos = output.find('A great library')
        assert libs_pos >= 0
        assert libs_pos < lib_entry_pos

    def test_resolved_url_matching(self):
        content = """\
Body [P9999R0](https://wg21.link/p9999r0) text.

## References

[1] [P9999R0](https://wg21.link/p9999r0) - "Paper" (Author, 2024).
"""
        resolved = ResolveResult()
        resolved.url_map['https://wg21.link/p9999r0'] = \
            'https://www.open-std.org/papers/2024/p9999r0.html'
        output = _scan_and_write(content, fix=True, resolved=resolved)
        assert '"Paper"' in output


# ---------------------------------------------------------------------------
# Description text preserved
# ---------------------------------------------------------------------------

class TestDescriptionTextPreserved:
    LIBRARY_PAPER = """\
Body [mylib](https://github.com/example/mylib) text <sup>[1]</sup>.

## References

[1] Cited ref

[2] [mylib](https://github.com/example/mylib) - A fantastic library (Great Author).
"""

    def test_library_description_preserved_after_fix(self):
        output = _scan_and_write(self.LIBRARY_PAPER, fix=True)
        assert 'A fantastic library' in output

    def test_description_not_replaced_by_bare_link(self):
        output = _scan_and_write(self.LIBRARY_PAPER, fix=True)
        for line in output.splitlines():
            if 'mylib' in line and re.match(r'\[\d+\]', line.strip()):
                assert 'A fantastic library' in line
                break
        else:
            assert False, "No mylib reference entry found in output"


# ---------------------------------------------------------------------------
# Acknowledgments orphan preservation
# ---------------------------------------------------------------------------

class TestAcknowledgmentOrphanPreservation:
    def test_acknowledgment_link_preserves_orphan(self):
        content = """\
Body <sup>[1]</sup>.

## Acknowledgments

Thanks to [P4014R0](https://example.com/p4014r0.pdf) authors.

## References

[1] Cited ref

[2] [P4014R0](https://example.com/p4014r0.pdf) - "The Sender Sub-Language" (Author, 2026).
"""
        config = {
            'exempt_sections': ['Acknowledgments'],
            'exempt_links': [],
            'exempt_orphans': [],
        }
        output = _scan_and_write(content, fix=True, config=config)
        assert 'The Sender Sub-Language' in output

    def test_pure_orphan_still_removed(self):
        content = """\
Body <sup>[1]</sup>.

## References

[1] Cited ref

[2] Pure orphan no link anywhere
"""
        output = _scan_and_write(content, fix=True)
        assert 'Pure orphan' not in output
