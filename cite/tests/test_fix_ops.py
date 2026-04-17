"""Tests for fix operations: orphan removal, versioning, title mismatches,
format normalisation, URL stripping, spacing, heading demotion, blank line
collapse, empty subsection removal, and period cleanup.
"""
import io
import os
import sys
import tempfile

from helpers import _lines
from cite import (
    RefEntry,
    ResolveResult,
    PaperMetadata,
    remove_orphan_refs,
    add_missing_ref_entries,
    fix_unversioned_refs,
    fix_title_mismatches,
    normalize_ref_format,
    normalize_title,
    strip_trailing_urls,
    space_ref_entries,
    demote_h1_refs,
    load_config,
    find_refs_section,
    parse_references,
    scan,
    write,
)


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


class TestRemoveOrphanRefs:
    def test_blanks_orphan_lines(self):
        lines = _lines("""\
## References

[1] First ref
[2] Second ref
[3] Third ref""")
        refs = {
            1: RefEntry(1, 'First ref', 2, 'A'),
            2: RefEntry(2, 'Second ref', 3, 'A'),
            3: RefEntry(3, 'Third ref', 4, 'A'),
        }
        result = remove_orphan_refs(lines, [2], refs)
        assert result[3] == '\n'
        assert '[1] First ref' in result[2]
        assert '[3] Third ref' in result[4]

    def test_no_orphans(self):
        lines = _lines("## References\n[1] Ref")
        refs = {1: RefEntry(1, 'Ref', 1, 'A')}
        result = remove_orphan_refs(lines, [], refs)
        assert result == lines

    def test_does_not_mutate_input(self):
        lines = _lines("## References\n[1] Ref\n[2] Orphan")
        refs = {
            1: RefEntry(1, 'Ref', 1, 'A'),
            2: RefEntry(2, 'Orphan', 2, 'A'),
        }
        original = list(lines)
        remove_orphan_refs(lines, [2], refs)
        assert lines == original


class TestFixUnversionedRefs:
    def test_uses_ref_lookup_with_citation_context(self):
        """Bare P2300 next to <sup>[1]</sup> is versioned via ref lookup."""
        lines = _lines("See P2300<sup>[1]</sup> for details.\n## References\n[1] P2300R10, stuff")
        refs = {1: RefEntry(1, 'P2300R10, stuff', 2, 'A')}
        result = fix_unversioned_refs(
            lines, [(0, 'P2300')], refs, ResolveResult())
        assert 'P2300R10' in result[0]

    def test_uses_metadata_fallback(self):
        lines = _lines("See P1234 for details.\n## References")
        resolved = ResolveResult()
        resolved.metadata['P1234R3'] = PaperMetadata(
            paper_id='P1234R3', title='Test', authors='A', date='', url='')
        result = fix_unversioned_refs(
            lines, [(0, 'P1234')], {}, resolved)
        assert 'P1234R3' in result[0]

    def test_no_match_unchanged(self):
        lines = _lines("See P9999 for details.\n## References")
        result = fix_unversioned_refs(
            lines, [(0, 'P9999')], {}, ResolveResult())
        assert 'P9999' in result[0]


class TestNormalizeTitle:
    def test_strips_quotes(self):
        assert normalize_title('"std::execution"') == 'std::execution'

    def test_strips_backticks(self):
        assert normalize_title('`std::execution`') == 'std::execution'

    def test_strips_trailing_punct(self):
        assert normalize_title('std::execution,') == 'std::execution'

    def test_collapses_whitespace(self):
        assert normalize_title('a   b  c') == 'a b c'

    def test_case_insensitive(self):
        assert normalize_title('Std::Execution') == 'std::execution'


class TestFixTitleMismatches:
    def test_updates_title(self):
        lines = _lines("""\
## References

[1] P2300R10, "old title," Eric, https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html""")
        refs = {1: RefEntry(1, lines[2].strip()[4:], 2, 'A')}
        resolved = ResolveResult()
        resolved.metadata['P2300R10'] = PaperMetadata(
            paper_id='P2300R10', title='new title',
            authors='Eric', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert '"new title"' in result[2]

    def test_no_mismatch_unchanged(self):
        lines = _lines("""\
## References

[1] P2300R10, "std::execution," Eric, https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html""")
        refs = {1: RefEntry(1, lines[2].strip()[4:], 2, 'A')}
        resolved = ResolveResult()
        resolved.metadata['P2300R10'] = PaperMetadata(
            paper_id='P2300R10', title='std::execution',
            authors='Eric', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert result[2] == lines[2]

    def test_correct_index_title_applied(self):
        """Index.json has correct titles, so updates should apply when similar enough."""
        lines = _lines("""\
## References

[1] N2406, "Mutex Lock Condition Variable," Hinnant, https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2007/n2406.html""")
        refs = {1: RefEntry(1, lines[2].strip()[4:], 2, 'A')}
        resolved = ResolveResult()
        resolved.metadata['N2406'] = PaperMetadata(
            paper_id='N2406',
            title='Mutex, Lock, Condition Variable Rationale',
            authors='Hinnant', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Mutex, Lock, Condition Variable Rationale' in result[2]


class TestNormalizeRefFormat:
    def test_converts_b_to_a(self):
        lines = _lines("""\
## References

1. First ref
2. Second ref""")
        result = normalize_ref_format(lines, 0, len(lines))
        assert '[1] First ref' in result[2]
        assert '[2] Second ref' in result[3]

    def test_leaves_a_unchanged(self):
        lines = _lines("""\
## References

[1] First ref
[2] Second ref""")
        result = normalize_ref_format(lines, 0, len(lines))
        assert result == lines

    def test_skips_blank_lines(self):
        lines = _lines("""\
## References

1. First ref

2. Second ref""")
        result = normalize_ref_format(lines, 0, len(lines))
        assert '[1] First ref' in result[2]
        assert result[3] == '\n'
        assert '[2] Second ref' in result[4]


class TestStripTrailingUrls:
    def test_removes_duplicate_url(self):
        lines = _lines("""\
## References

[1] [P2300R10](https://example.com/p2300r10.html) - title. https://example.com/p2300r10.html""")
        result = strip_trailing_urls(lines, 0, len(lines))
        assert 'https://example.com' not in result[2].split(')', 1)[-1]
        assert '[P2300R10](https://example.com/p2300r10.html)' in result[2]

    def test_wraps_bare_url(self):
        lines = _lines("""\
## References

[1] Capy, https://github.com/cppalliance/capy""")
        result = strip_trailing_urls(lines, 0, len(lines))
        assert '[Capy](https://github.com/cppalliance/capy)' in result[2]

    def test_no_url_unchanged(self):
        lines = _lines("""\
## References

[1] Some reference without a URL""")
        result = strip_trailing_urls(lines, 0, len(lines))
        assert result == lines


class TestSpaceRefEntries:
    def test_inserts_blank_lines(self):
        lines = _lines("""\
## References

[1] First ref
[2] Second ref
[3] Third ref""")
        result = space_ref_entries(lines, 0, len(lines))
        content = ''.join(result)
        assert '[1] First ref\n\n[2] Second ref' in content
        assert '[2] Second ref\n\n[3] Third ref' in content

    def test_no_double_spacing(self):
        lines = _lines("""\
## References

[1] First ref

[2] Second ref

[3] Third ref""")
        result = space_ref_entries(lines, 0, len(lines))
        assert result == lines

    def test_mixed_spacing(self):
        lines = _lines("""\
## References

[1] First ref
[2] Second ref

[3] Third ref""")
        result = space_ref_entries(lines, 0, len(lines))
        content = ''.join(result)
        assert '[1] First ref\n\n[2] Second ref' in content
        assert '[2] Second ref\n\n[3] Third ref' in content


class TestDemoteH1Refs:
    def test_demotes_h1(self):
        lines = _lines("""\
# References

[1] Ref""")
        result = demote_h1_refs(lines, 0)
        assert result[0].startswith('## References')

    def test_leaves_h2_unchanged(self):
        lines = _lines("""\
## References

[1] Ref""")
        result = demote_h1_refs(lines, 0)
        assert result[0] == lines[0]

    def test_handles_extra_whitespace(self):
        lines = _lines("""\
#  References

[1] Ref""")
        result = demote_h1_refs(lines, 0)
        assert result[0].startswith('##  References')


class TestAddMissingRefEntries:
    def test_creates_stub(self):
        lines = _lines("""\
Body <sup>[1]</sup> text.

## References
""")
        result = add_missing_ref_entries(
            lines, [1], [(0, 1)], 3, ResolveResult())
        content = ''.join(result)
        assert '[1] [TODO: Add reference]' in content

    def test_creates_from_link_context(self):
        lines = _lines("""\
See [example](https://example.com)<sup>[1]</sup>.

## References
""")
        result = add_missing_ref_entries(
            lines, [1], [(0, 1)], 3, ResolveResult())
        content = ''.join(result)
        assert '[1] [example](https://example.com)' in content


# ---------------------------------------------------------------------------
# Title confidence check
# ---------------------------------------------------------------------------

class TestTitleConfidenceCheck:
    def _make_lines_and_refs(self, ref_title):
        lines = _lines(f"""\
## References
[1] [P9999R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p9999r0.html) - "{ref_title}" """)
        refs = {1: RefEntry(1, lines[1].strip()[4:], 1, 'A')}
        return lines, refs

    def test_title_wildly_different_skipped(self):
        lines, refs = self._make_lines_and_refs(
            'Profile invalidation - eliminating dangling pointers')
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0',
            title='thread_local means fiber-specific',
            authors='Test', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Profile invalidation' in result[1]
        assert 'thread_local' not in result[1]

    def test_title_minor_typo_preserved(self):
        lines, refs = self._make_lines_and_refs(
            'Coroutines belong in a TS')
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0',
            title='Couroutines belong in a TS',
            authors='Test', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Coroutines' in result[1]
        assert 'Couroutines' not in result[1]

    def test_title_legitimate_correction_applied(self):
        lines, refs = self._make_lines_and_refs(
            'A Proposal to Add Networking')
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0',
            title='Networking proposal for TR2 (rev. 1)',
            authors='Test', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Networking proposal for TR2' in result[1]

    def test_title_identical_no_change(self):
        lines, refs = self._make_lines_and_refs('std::execution')
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0', title='std::execution',
            authors='Test', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert result[1] == lines[1]


# ---------------------------------------------------------------------------
# Title body consistency
# ---------------------------------------------------------------------------

class TestTitleBodyConsistency:
    def _make_paper(self, ref_title, body_contains_title=False):
        body = '| Paper | Description |\n'
        if body_contains_title:
            body += f'| P9999R0 | {ref_title} |\n'
        else:
            body += '| P9999R0 | Some other description |\n'
        body += '\n## References\n\n'
        body += (f'[1] [P9999R0](https://www.open-std.org/jtc1/sc22/wg21/'
                 f'docs/papers/2024/p9999r0.html) - "{ref_title}"\n')
        return body

    def test_title_skip_when_appears_in_body(self):
        content = self._make_paper(
            'Language and implementation impact', body_contains_title=True)
        lines = _lines(content)
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0',
            title='Different canonical title',
            authors='A', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Language and implementation impact' in result[-1]

    def test_title_applied_when_not_in_body(self):
        content = self._make_paper('old title', body_contains_title=False)
        lines = _lines(content)
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0',
            title='Correct new title for this paper',
            authors='A', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Correct new title' in result[-1]

    def test_title_skip_partial_match_not_triggered(self):
        content = """\
| P9999R0 | The networking field |

## References

[1] [P9999R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p9999r0.html) - "networking proposal"
"""
        lines = _lines(content)
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0',
            title='Networking proposal for TR2 (rev. 1)',
            authors='A', date='', url='')
        result = fix_title_mismatches(lines, refs, resolved)
        ref_line = [l for l in result if 'P9999R0' in l and l.strip().startswith('[')]
        assert ref_line and 'Networking proposal for TR2' in ref_line[0]


# ---------------------------------------------------------------------------
# Spurious title-skip warning
# ---------------------------------------------------------------------------

class TestSpuriousTitleSkipWarning:
    def test_no_warning_when_titles_identical(self):
        lines = _lines("""\
The paper "std::execution" is important.
## References
[1] [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) - "std::execution" (Author, 2024).""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = ResolveResult()
        resolved.metadata['P2300R10'] = PaperMetadata(
            paper_id='P2300R10', title='std::execution',
            authors='Author', date='2024', url='')
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            fix_title_mismatches(lines, refs, resolved)
        finally:
            sys.stderr = old_stderr
        assert 'Title SKIP' not in captured.getvalue()

    def test_warning_when_titles_differ_and_in_body(self):
        lines = _lines("""\
The paper has "old title" description.
## References
[1] [P9999R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p9999r0.html) - "old title" (Author).""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = ResolveResult()
        resolved.metadata['P9999R0'] = PaperMetadata(
            paper_id='P9999R0', title='new different title for this paper',
            authors='Author', date='2024', url='')
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            fix_title_mismatches(lines, refs, resolved)
        finally:
            sys.stderr = old_stderr
        assert 'Title SKIP' in captured.getvalue()


# ---------------------------------------------------------------------------
# Blank line collapse
# ---------------------------------------------------------------------------

class TestBlankLineCollapse:
    def test_consecutive_blanks_collapsed(self):
        content = """\
Body <sup>[1]</sup> and <sup>[2]</sup>.

## References

[1] Kept ref



[2] Also kept



[3] Orphan ref
"""
        output = _scan_and_write(content, fix=True)
        ref_section = output[output.index('## References'):]
        assert '\n\n\n' not in ref_section

    def test_single_blank_preserved(self):
        content = """\
Body <sup>[1]</sup> and <sup>[2]</sup>.

## References

[1] First ref

[2] Second ref
"""
        output = _scan_and_write(content, fix=False)
        ref_section = output[output.index('## References'):]
        assert '\n\n[' in ref_section

    def test_blanks_outside_refs_untouched(self):
        content = """\
Body text.



More body <sup>[1]</sup>.

## References

[1] Ref
"""
        output = _scan_and_write(content, fix=True)
        body = output[:output.index('## References')]
        assert '\n\n\n' in body

    def test_blanks_after_orphan_removal(self):
        content = """\
Body <sup>[1]</sup>.

## References

[1] Kept ref

[2] Orphan one

[3] Orphan two

[4] Orphan three
"""
        output = _scan_and_write(content, fix=True)
        ref_section = output[output.index('## References'):]
        assert '\n\n\n' not in ref_section


# ---------------------------------------------------------------------------
# Empty subsection heading removal
# ---------------------------------------------------------------------------

class TestEmptySubsectionHeadingRemoval:
    def test_empty_subsection_heading_removed(self):
        content = """\
Body <sup>[1]</sup>.

## References

### WG21 Papers

[1] Cited paper

### Other

[2] Orphan entry
"""
        output = _scan_and_write(content, fix=True)
        assert '### Other' not in output
        assert '### WG21 Papers' in output

    def test_nonempty_subsection_heading_preserved(self):
        content = """\
Body <sup>[1]</sup> and <sup>[2]</sup>.

## References

### WG21 Papers

[1] Cited paper

### Other

[2] Cited other
"""
        output = _scan_and_write(content, fix=True)
        assert '### Other' in output


# ---------------------------------------------------------------------------
# Period in link text
# ---------------------------------------------------------------------------

class TestPeriodInLinkText:
    def test_period_stripped_from_link_text(self):
        lines = _lines("""\
## References

[1] C++ Core Guidelines. https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines""")
        result = strip_trailing_urls(lines, 0, len(lines))
        ref_line = result[2]
        assert '[C++ Core Guidelines](' in ref_line
        assert '[C++ Core Guidelines.](' not in ref_line
