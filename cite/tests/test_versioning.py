"""Tests for paper versioning: fix_unversioned_refs, _resolve_paper_version,
check_unversioned_refs, extract_paper_id_from_url, compound citations,
linked citation format, URL context, pipeline ordering, and resolve gap.
"""
import io
import os
import re
import sys
import tempfile

from helpers import _lines
from cite import (
    PaperMetadata,
    RefEntry,
    ResolveResult,
    _resolve_paper_version,
    build_exclusion_ranges,
    check_unversioned_refs,
    extract_body_citations,
    extract_paper_id_from_url,
    find_refs_section,
    fix_unversioned_refs,
    load_config,
    lookup_paper_metadata,
    parse_references,
    resolve,
    scan,
    write,
)


# ---------------------------------------------------------------------------
# _resolve_paper_version unit tests
# ---------------------------------------------------------------------------

class TestResolvePaperVersion:
    def _resolve(self, paper, url=None, ref_entry=None, resolved=None):
        return _resolve_paper_version(
            paper, url, ref_entry, resolved or ResolveResult())

    def test_url_and_ref_agree(self):
        url = ('https://www.open-std.org/jtc1/sc22/wg21/'
               'docs/papers/2024/p2300r10.html')
        ref = RefEntry(1, 'P2300R10, std::execution', 0, 'A')
        versioned, diag = self._resolve('P2300', url=url, ref_entry=ref)
        assert versioned == 'P2300R10'
        assert diag is None

    def test_url_and_ref_disagree(self):
        url = ('https://www.open-std.org/jtc1/sc22/wg21/'
               'docs/papers/2021/p2300r2.html')
        ref = RefEntry(1, 'P2300R10, std::execution', 0, 'A')
        versioned, diag = self._resolve('P2300', url=url, ref_entry=ref)
        assert versioned is None
        assert diag is not None

    def test_both_unversioned_with_metadata(self):
        resolved = ResolveResult()
        resolved.metadata['P2300R10'] = PaperMetadata(
            paper_id='P2300R10', title='std::execution',
            authors='A', date='', url='')
        versioned, diag = self._resolve(
            'P2300', url=None, ref_entry=None, resolved=resolved)
        assert versioned == 'P2300R10'

    def test_both_unversioned_no_metadata(self):
        versioned, diag = self._resolve('P2300')
        assert versioned is None
        assert diag is not None

    def test_url_versioned_ref_unversioned(self):
        url = ('https://www.open-std.org/jtc1/sc22/wg21/'
               'docs/papers/2024/p2300r10.html')
        ref = RefEntry(1, 'std::execution, some desc', 0, 'A')
        versioned, diag = self._resolve('P2300', url=url, ref_entry=ref)
        assert versioned == 'P2300R10'

    def test_url_unversioned_ref_versioned(self):
        ref = RefEntry(1, 'P2300R10, std::execution', 0, 'A')
        versioned, diag = self._resolve(
            'P2300', url=None, ref_entry=ref)
        assert versioned == 'P2300R10'

    def test_version_from_ref_url(self):
        ref = RefEntry(
            1,
            '[P4100](https://isocpp.org/files/papers/P4100R0.pdf) - desc',
            0, 'A')
        versioned, diag = self._resolve('P4100', ref_entry=ref)
        assert versioned == 'P4100R0'

    def test_version_from_open_std_ref_url(self):
        ref = RefEntry(
            1,
            '[P4100R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf) - desc',
            0, 'A')
        versioned, diag = self._resolve('P4100', ref_entry=ref)
        assert versioned == 'P4100R0'


# ---------------------------------------------------------------------------
# fix_unversioned_refs integration
# ---------------------------------------------------------------------------

class TestFixUnversionedRefsIntegration:
    def test_quoted_title_not_modified(self):
        lines = _lines("""\
Falco identified this in "Partial success scenarios with P2300" paper.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - "std::execution" """)
        refs = {1: RefEntry(1, lines[2].strip()[4:], 2, 'A')}
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert '"Partial success scenarios with P2300"' in result[0]

    def test_prose_bare_number_not_versioned_without_context(self):
        lines = _lines("""\
See P2300 for details.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - "std::execution" """)
        refs = {1: RefEntry(1, lines[2].strip()[4:], 2, 'A')}
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300 for details' in result[0]

    def test_versioned_ref_not_double_versioned(self):
        lines = _lines("""\
See P2300R10 for details.
## References
[1] [P2300R10](https://example.com) - desc""")
        refs = {1: RefEntry(1, lines[2].strip()[4:], 2, 'A')}
        result = fix_unversioned_refs(lines, [], refs, ResolveResult())
        assert 'P2300R10R10' not in result[0]

    def test_fix_unversioned_does_not_modify_urls(self):
        lines = _lines("""\
See [P2300](https://example.com/p2300r10.html)<sup>[1]</sup>.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - "std::execution" """)
        refs = {1: RefEntry(1, lines[2].strip()[4:], 2, 'A')}
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'https://example.com/p2300r10.html' in result[0]

    def test_multiple_bare_papers_on_one_line(self):
        lines = _lines("""\
See P2300 and P0443 for details.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc
[2] [P0443R14](https://example.com/p0443r14.html) - desc""")
        refs = {
            1: RefEntry(1, lines[2].strip()[4:], 2, 'A'),
            2: RefEntry(2, lines[3].strip()[4:], 3, 'A'),
        }
        unversioned = [(0, 'P2300'), (0, 'P0443')]
        result = fix_unversioned_refs(
            lines, unversioned, refs, ResolveResult())
        assert 'P2300R10' in result[0] or 'P2300' in result[0]
        assert 'P0443R14' in result[0] or 'P0443' in result[0]


# ---------------------------------------------------------------------------
# Over-versioning prevention
# ---------------------------------------------------------------------------

class TestOverVersioningPrevention:
    def test_bare_prose_not_versioned_without_context(self):
        lines = _lines("""\
P2300 has been refined since 2021.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300 has been refined' in result[0]

    def test_bare_in_link_still_versioned(self):
        lines = _lines("""\
See [P2300](https://example.com/p2300r10.html)<sup>[1]</sup>.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300R10' in result[0]

    def test_bare_with_adjacent_sup_still_versioned(self):
        lines = _lines("""\
P2300 details here<sup>[1]</sup>.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300R10' in result[0]


# ---------------------------------------------------------------------------
# Backward citation search
# ---------------------------------------------------------------------------

class TestBackwardCitationSearch:
    def test_version_from_backward_citation(self):
        lines = _lines("""\
[P2470R0](https://example.com/p2470r0.pdf)<sup>[1]</sup> the P2300 slides.
## References
[1] [P2470R0](https://example.com/p2470r0.pdf) - "Slides for P2300R2" (Niebler)""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300R2' in result[0]

    def test_forward_citation_still_preferred_when_closer(self):
        lines = _lines("""\
P2300 text <sup>[1]</sup>.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300R10' in result[0]

    def test_backward_preferred_when_closer_than_forward(self):
        lines = _lines("""\
<sup>[1]</sup> P2300 long gap text text text text text text <sup>[2]</sup>.
## References
[1] [P2300R2](https://example.com) - desc
[2] [P2300R10](https://example.com) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300R2' in result[0]

    def test_no_citation_either_direction_leaves_bare(self):
        lines = _lines("""\
See P2300 for details.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300 for details' in result[0]


# ---------------------------------------------------------------------------
# Table versioning
# ---------------------------------------------------------------------------

class TestTableVersioning:
    def test_bare_number_in_table_link_versioned(self):
        lines = _lines("""\
| Col | [P2300](https://example.com/p2300r10.html)<sup>[1]</sup> |
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc""")
        excluded = build_exclusion_ranges(lines)
        results = check_unversioned_refs(lines, excluded, 2)
        papers = [p for _, p in results]
        assert 'P2300' in papers

    def test_bare_number_in_plain_table_cell_skipped(self):
        lines = _lines("""\
| P2300 never deployed | other |
## References""")
        excluded = build_exclusion_ranges(lines)
        results = check_unversioned_refs(lines, excluded, 1)
        papers = [p for _, p in results]
        assert 'P2300' not in papers

    def test_table_with_mixed_content(self):
        lines = _lines("""\
| P0443 data | [P2300](https://example.com/p2300r10.html)<sup>[1]</sup> |
## References""")
        excluded = build_exclusion_ranges(lines)
        results = check_unversioned_refs(lines, excluded, 1)
        papers = [p for _, p in results]
        assert 'P2300' in papers
        assert 'P0443' not in papers


# ---------------------------------------------------------------------------
# isocpp.org URL support
# ---------------------------------------------------------------------------

class TestIsocppUrls:
    def test_extract_paper_id_from_isocpp_url(self):
        url = 'https://isocpp.org/files/papers/P4100R0.pdf'
        result = extract_paper_id_from_url(url)
        assert result is not None
        pid, year = result
        assert pid == 'P4100R0'

    def test_version_from_isocpp_url(self):
        lines = _lines("""\
See [P4100](https://isocpp.org/files/papers/P4100R0.pdf)<sup>[1]</sup>.
## References
[1] [P4100R0](https://isocpp.org/files/papers/P4100R0.pdf) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P4100')], refs, ResolveResult())
        assert 'P4100R0' in result[0]

    def test_isocpp_url_in_check_unversioned_skipped(self):
        lines = _lines("""\
See [P4100R0](https://isocpp.org/files/papers/P4100R0.pdf)<sup>[1]</sup>.
## References""")
        excluded = build_exclusion_ranges(lines)
        results = check_unversioned_refs(lines, excluded, 2)
        papers = [p for _, p in results]
        assert 'P4100' not in papers


# ---------------------------------------------------------------------------
# URL context from second link on line
# ---------------------------------------------------------------------------

class TestUrlContextSecondLink:
    def test_url_context_finds_second_link(self):
        lines = _lines("""\
[Network Endeavor](https://example.com/endeavor) ([P4100](https://isocpp.org/files/papers/P4100R0.pdf)<sup>[1]</sup>).
## References
[1] [P4100](https://isocpp.org/files/papers/P4100R0.pdf) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_unversioned_refs(
            lines, [(0, 'P4100')], refs, ResolveResult())
        assert 'P4100R0' in result[0]

    def test_no_warning_when_version_resolved_from_link(self):
        lines = _lines("""\
[P4100](https://isocpp.org/files/papers/P4100R0.pdf)<sup>[1]</sup> text.
## References
[1] [P4100](https://isocpp.org/files/papers/P4100R0.pdf) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            fix_unversioned_refs(
                lines, [(0, 'P4100')], refs, ResolveResult())
        finally:
            sys.stderr = old_stderr
        assert 'Warning' not in captured.getvalue()
        assert 'Skipping' not in captured.getvalue()


# ---------------------------------------------------------------------------
# Warning messages
# ---------------------------------------------------------------------------

class TestWarningMessages:
    def test_prose_skip_message(self):
        lines = _lines("""\
P2300 has been refined since 2021.
## References
[1] [P2300R10](https://example.com/p2300r10.html) - desc""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            fix_unversioned_refs(
                lines, [(0, 'P2300')], refs, ResolveResult())
        finally:
            sys.stderr = old_stderr
        assert 'Skipping' in captured.getvalue()
        assert 'cannot determine' not in captured.getvalue()

    def test_no_source_message(self):
        ref = RefEntry(1, 'P9999 - some paper', 0, 'A')
        _, diag = _resolve_paper_version(
            'P9999', None, ref, ResolveResult())
        assert diag is not None
        assert 'no version source' in diag

    def test_disagree_message(self):
        url = ('https://www.open-std.org/jtc1/sc22/wg21/'
               'docs/papers/2021/p2300r2.html')
        ref = RefEntry(1, 'P2300R10 - std::execution', 0, 'A')
        _, diag = _resolve_paper_version(
            'P2300', url, ref, ResolveResult())
        assert 'disagrees' in diag
        assert 'P2300R2' in diag
        assert 'P2300R10' in diag


# ---------------------------------------------------------------------------
# Compound citations
# ---------------------------------------------------------------------------

class TestCompoundCitations:
    def test_compound_citation_numbers_extracted(self):
        lines = _lines("""\
Text <sup>[10,11]</sup> here.
## References
[10] Ref ten
[11] Ref eleven""")
        excluded = build_exclusion_ranges(lines)
        refs_start, _ = find_refs_section(lines)
        cites, first_app, old_to_new = extract_body_citations(
            lines, excluded, refs_start)
        assert 10 in old_to_new
        assert 11 in old_to_new

    def test_compound_citation_three_numbers(self):
        lines = _lines("""\
Text <sup>[1,2,3]</sup> here.
## References""")
        excluded = build_exclusion_ranges(lines)
        refs_start, _ = find_refs_section(lines)
        _, _, old_to_new = extract_body_citations(
            lines, excluded, refs_start)
        assert set(old_to_new.keys()) == {1, 2, 3}

    def test_compound_citation_not_treated_as_orphan(self):
        content = """\
Text <sup>[1,2]</sup> here.

## References

[1] First ref

[2] Second ref
"""
        fd, tmp = tempfile.mkstemp(suffix='.md')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            r = scan(tmp, {'exempt_sections': [], 'exempt_links': [], 'exempt_orphans': []})
        finally:
            os.unlink(tmp)
        assert 1 not in r.orphans
        assert 2 not in r.orphans

    def test_compound_citation_not_dropped_in_fix_mode(self):
        content = """\
Text <sup>[1,2]</sup> here.

## References

[1] First ref

[2] Second ref
"""
        config = load_config(None)
        fd, tmp = tempfile.mkstemp(suffix='.md')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            r = scan(tmp, config)
            output = write(r, ResolveResult(), fix=True)
        finally:
            os.unlink(tmp)
        assert 'First ref' in output
        assert 'Second ref' in output

    def test_compound_and_simple_on_same_line(self):
        lines = _lines("""\
See <sup>[1]</sup> and <sup>[2,3]</sup>.
## References""")
        excluded = build_exclusion_ranges(lines)
        refs_start, _ = find_refs_section(lines)
        _, _, old_to_new = extract_body_citations(
            lines, excluded, refs_start)
        assert set(old_to_new.keys()) == {1, 2, 3}


# ---------------------------------------------------------------------------
# Linked citation format
# ---------------------------------------------------------------------------

class TestLinkedCitationFormat:
    def test_linked_citation_recognized(self):
        lines = _lines("""\
See <sup>[[28]](https://corosio.org)</sup> for details.
## References
[28] Corosio website""")
        excluded = build_exclusion_ranges(lines)
        refs_start, _ = find_refs_section(lines)
        _, first_app, old_to_new = extract_body_citations(
            lines, excluded, refs_start)
        assert 28 in old_to_new

    def test_linked_citation_not_treated_as_orphan(self):
        content = """\
See <sup>[[1]](https://corosio.org)</sup> for details.

## References

[1] Corosio website
"""
        config = load_config(None)
        fd, tmp = tempfile.mkstemp(suffix='.md')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            r = scan(tmp, config)
        finally:
            os.unlink(tmp)
        assert 1 not in r.orphans


# ---------------------------------------------------------------------------
# Pipeline ordering
# ---------------------------------------------------------------------------

class TestPipelineOrdering:
    def test_write_pipeline_resolves_url_then_versions(self):
        content = """\
See P2300 for details on [P2300R10](https://wg21.link/p2300r10)<sup>[1]</sup>.

## References

[1] [P2300R10](https://wg21.link/p2300r10) - "std::execution"
"""
        config = load_config(None)
        fd, tmp = tempfile.mkstemp(suffix='.md')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            r = scan(tmp, config)
            resolved = ResolveResult()
            resolved.url_map['https://wg21.link/p2300r10'] = (
                'https://www.open-std.org/jtc1/sc22/wg21/'
                'docs/papers/2024/p2300r10.html')
            resolved.metadata['P2300R10'] = PaperMetadata(
                paper_id='P2300R10', title='std::execution',
                authors='Eric Niebler', date='2024', url='')
            output = write(r, resolved, fix=True)
        finally:
            os.unlink(tmp)
        assert 'wg21.link' not in output
        assert 'open-std.org' in output


# ---------------------------------------------------------------------------
# Resolve gap: uncited link metadata
# ---------------------------------------------------------------------------

class TestResolveGap:
    def test_uncited_link_metadata_populated(self):
        content = """\
Body [P9999R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p9999r0.html) text.

## References

[1] Existing ref
"""
        config = load_config(None)
        fd, tmp = tempfile.mkstemp(suffix='.md')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            r = scan(tmp, config)
        finally:
            os.unlink(tmp)

        assert len(r.uncited_links) > 0
        uncited_url = r.uncited_links[0].url

        info = extract_paper_id_from_url(uncited_url)
        assert info is not None
        pid = info[0]

        mock_index = {
            pid: {
                'type': 'paper',
                'title': 'Test Paper Title',
                'author': 'Test Author',
                'date': '2024-01-01',
                'long_link': uncited_url,
                'link': f'https://wg21.link/{pid.lower()}',
            }
        }

        from unittest.mock import patch
        with patch('cite.load_paper_index', return_value=mock_index):
            from pathlib import Path
            resolved = resolve(
                [r], Path(__file__).parent / '.cache',
                skip_resolve=False, skip_guess=True)

        assert pid in resolved.metadata
        assert resolved.metadata[pid].title == 'Test Paper Title'
