"""Tests for renumbering, reordering, orphan numbering, subsection
preservation, duplicate entry unification, and ref integrity.
"""
import os
import re
import tempfile

from helpers import _lines
from cite import (
    RefEntry,
    ResolveResult,
    build_exclusion_ranges,
    extract_body_citations,
    find_refs_section,
    load_config,
    parse_references,
    renumber_content,
    reorder_refs,
    scan,
    write,
)


class TestRenumberContent:
    def test_identity(self):
        lines = _lines("See <sup>[1]</sup> and <sup>[2]</sup>.")
        old_to_new = {1: 1, 2: 2}
        result = renumber_content(old_to_new, set(), lines)
        assert '<sup>[1]</sup>' in result
        assert '<sup>[2]</sup>' in result

    def test_swap(self):
        lines = _lines("First <sup>[3]</sup> then <sup>[1]</sup>.")
        old_to_new = {3: 1, 1: 2}
        result = renumber_content(old_to_new, set(), lines)
        assert 'First <sup>[1]</sup>' in result
        assert 'then <sup>[2]</sup>' in result

    def test_skips_excluded_lines(self):
        lines = _lines("""\
Body <sup>[2]</sup>.
```
Code <sup>[2]</sup>.
```""")
        excluded = {1, 2, 3}
        old_to_new = {2: 1}
        result = renumber_content(old_to_new, excluded, lines)
        result_lines = result.split('\n')
        assert '<sup>[1]</sup>' in result_lines[0]
        assert '<sup>[2]</sup>' in result_lines[2]

    def test_no_collision(self):
        """Renumbering [1]->[2] and [2]->[1] must not collide."""
        lines = _lines("<sup>[1]</sup> and <sup>[2]</sup>.")
        old_to_new = {1: 2, 2: 1}
        result = renumber_content(old_to_new, set(), lines)
        assert '<sup>[2]</sup> and <sup>[1]</sup>' in result

    def test_multiple_on_one_line(self):
        lines = _lines("See <sup>[3]</sup><sup>[1]</sup><sup>[2]</sup>.")
        old_to_new = {3: 1, 1: 2, 2: 3}
        result = renumber_content(old_to_new, set(), lines)
        assert '<sup>[1]</sup><sup>[2]</sup><sup>[3]</sup>' in result


class TestReorderRefs:
    def test_basic_reorder_format_a(self):
        lines = _lines("""\
## References

[3] Third ref
[1] First ref
[2] Second ref""")
        refs = {
            3: RefEntry(3, 'Third ref', 2, 'A'),
            1: RefEntry(1, 'First ref', 3, 'A'),
            2: RefEntry(2, 'Second ref', 4, 'A'),
        }
        old_to_new = {3: 1, 1: 2, 2: 3}
        result = reorder_refs(lines, refs, old_to_new)
        assert '[1] Third ref' in result[2]
        assert '[2] First ref' in result[3]
        assert '[3] Second ref' in result[4]

    def test_format_b_emits_format_a(self):
        """reorder_refs always emits [N] format regardless of input."""
        lines = _lines("""\
## References

3. Third ref
1. First ref
2. Second ref""")
        refs = {
            3: RefEntry(3, 'Third ref', 2, 'B'),
            1: RefEntry(1, 'First ref', 3, 'B'),
            2: RefEntry(2, 'Second ref', 4, 'B'),
        }
        old_to_new = {3: 1, 1: 2, 2: 3}
        result = reorder_refs(lines, refs, old_to_new)
        assert '[1] Third ref' in result[2]
        assert '[2] First ref' in result[3]
        assert '[3] Second ref' in result[4]

    def test_preserves_non_entry_lines(self):
        lines = _lines("""\
## References

### Papers

[1] First
[2] Second

### Other

[3] Third""")
        refs = {
            1: RefEntry(1, 'First', 4, 'A'),
            2: RefEntry(2, 'Second', 5, 'A'),
            3: RefEntry(3, 'Third', 9, 'A'),
        }
        old_to_new = {1: 1, 2: 2, 3: 3}
        result = reorder_refs(lines, refs, old_to_new)
        content = ''.join(result)
        assert '### Papers' in content
        assert '### Other' in content
        assert '[1] First' in content
        assert '[3] Third' in content


def _scan_and_write(content, fix=False, resolved=None):
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


class TestOrphanRenumbering:
    def test_orphan_gets_unique_number_after_renumber(self):
        lines = _lines("""\
First <sup>[3]</sup> then <sup>[1]</sup>.
## References
[1] First ref
[2] Orphan ref
[3] Third ref""")
        refs = {
            1: RefEntry(1, 'First ref', 2, 'A'),
            2: RefEntry(2, 'Orphan ref', 3, 'A'),
            3: RefEntry(3, 'Third ref', 4, 'A'),
        }
        old_to_new = {3: 1, 1: 2}
        result = reorder_refs(lines, refs, old_to_new)
        ref_numbers = []
        for line in result:
            m = re.match(r'\[(\d+)\]\s', line.strip())
            if m:
                ref_numbers.append(int(m.group(1)))
        assert len(ref_numbers) == len(set(ref_numbers))
        assert 1 in ref_numbers
        assert 2 in ref_numbers

    def test_multiple_orphans_sequential(self):
        lines = _lines("""\
Body <sup>[1]</sup> and <sup>[5]</sup>.
## References
[1] Active one
[2] Orphan A
[3] Orphan B
[4] Orphan C
[5] Active two""")
        refs = {
            1: RefEntry(1, 'Active one', 2, 'A'),
            2: RefEntry(2, 'Orphan A', 3, 'A'),
            3: RefEntry(3, 'Orphan B', 4, 'A'),
            4: RefEntry(4, 'Orphan C', 5, 'A'),
            5: RefEntry(5, 'Active two', 6, 'A'),
        }
        old_to_new = {1: 1, 5: 2}
        result = reorder_refs(lines, refs, old_to_new)
        ref_numbers = []
        for line in result:
            m = re.match(r'\[(\d+)\]\s', line.strip())
            if m:
                ref_numbers.append(int(m.group(1)))
        assert len(ref_numbers) == 5
        assert len(set(ref_numbers)) == 5

    def test_orphan_with_subsections(self):
        lines = _lines("""\
Body <sup>[1]</sup> and <sup>[3]</sup>.
## References
### WG21 Papers
[1] Active paper
[2] Orphan paper
### Libraries
[3] Active library""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        old_to_new = {1: 1, 3: 2}
        result = reorder_refs(lines, refs, old_to_new)
        ref_numbers = []
        for line in result:
            m = re.match(r'\[(\d+)\]\s', line.strip())
            if m:
                ref_numbers.append(int(m.group(1)))
        assert len(ref_numbers) == len(set(ref_numbers))


class TestSubsectionPreservation:
    def test_reorder_preserves_subsection_membership(self):
        lines = _lines("""\
Body <sup>[2]</sup> then <sup>[1]</sup>.
## References
### WG21 Papers
[1] Paper ref
### Libraries
[2] Library ref""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        old_to_new = {2: 1, 1: 2}
        result = reorder_refs(lines, refs, old_to_new)
        content = ''.join(result)
        papers_pos = content.find('### WG21 Papers')
        libraries_pos = content.find('### Libraries')
        paper_ref_pos = content.find('Paper ref')
        library_ref_pos = content.find('Library ref')
        assert papers_pos < paper_ref_pos < libraries_pos
        assert libraries_pos < library_ref_pos

    def test_orphan_stays_in_original_subsection(self):
        lines = _lines("""\
Body <sup>[1]</sup>.
## References
### WG21 Papers
[1] Active paper
### Other
[2] Orphan other""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        old_to_new = {1: 1}
        result = reorder_refs(lines, refs, old_to_new)
        content = ''.join(result)
        other_pos = content.find('### Other')
        orphan_pos = content.find('Orphan other')
        assert other_pos < orphan_pos

    def test_subsection_level_not_hardcoded(self):
        lines = _lines("""\
Body <sup>[2]</sup> then <sup>[1]</sup>.
# References
## Papers
[1] Paper ref
## Libraries
[2] Library ref""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        old_to_new = {2: 1, 1: 2}
        result = reorder_refs(lines, refs, old_to_new)
        content = ''.join(result)
        papers_pos = content.find('## Papers')
        libraries_pos = content.find('## Libraries')
        paper_ref_pos = content.find('Paper ref')
        library_ref_pos = content.find('Library ref')
        assert papers_pos < paper_ref_pos < libraries_pos
        assert libraries_pos < library_ref_pos


class TestSubsectionSequentialNumbering:
    def test_subsection_numbering_sequential(self):
        content = """\
See <sup>[3]</sup> then <sup>[1]</sup> then <sup>[2]</sup>.

## References

### WG21 Papers

[1] Paper A

[3] Paper C

### Libraries

[2] Library B
"""
        output = _scan_and_write(content, fix=False)
        refs_section = output[output.index('## References'):]
        wg21_pos = refs_section.find('### WG21 Papers')
        libs_pos = refs_section.find('### Libraries')
        wg21_refs = re.findall(
            r'^\[(\d+)\]', refs_section[wg21_pos:libs_pos], re.MULTILINE)
        libs_refs = re.findall(
            r'^\[(\d+)\]', refs_section[libs_pos:], re.MULTILINE)
        wg21_nums = [int(n) for n in wg21_refs]
        libs_nums = [int(n) for n in libs_refs]
        assert wg21_nums == list(range(wg21_nums[0], wg21_nums[0] + len(wg21_nums)))
        assert libs_nums == list(range(libs_nums[0], libs_nums[0] + len(libs_nums)))


class TestLinkedCitationRenumbering:
    def test_linked_citation_renumbered(self):
        lines = _lines("""\
See <sup>[[28]](https://corosio.org)</sup> for details.
## References
[28] Corosio website""")
        old_to_new = {28: 1}
        excluded = build_exclusion_ranges(lines)
        result = renumber_content(old_to_new, excluded, lines)
        assert '[[1]]' in result
        assert '[[28]]' not in result

    def test_standard_citation_still_renumbered(self):
        lines = _lines("""\
See <sup>[28]</sup> for details.
## References
[28] Ref""")
        old_to_new = {28: 1}
        excluded = build_exclusion_ranges(lines)
        result = renumber_content(old_to_new, excluded, lines)
        assert '<sup>[1]</sup>' in result


class TestDuplicateEntryUnification:
    def test_duplicate_url_entries_unified(self):
        content = """\
See <sup>[1]</sup> and <sup>[2]</sup>.

## References

[1] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - short

[2] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - "Executors and Async Ops" (Kohlhoff, 2015).
"""
        output = _scan_and_write(content, fix=False)
        p0113_entries = []
        for line in output.splitlines():
            if 'p0113r0' in line.lower() and re.match(r'\[\d+\]', line.strip()):
                p0113_entries.append(line.strip())
        assert len(p0113_entries) == 1

    def test_different_url_entries_not_unified(self):
        content = """\
See <sup>[1]</sup> and <sup>[2]</sup>.

## References

[1] [P0113R0](http://example.com/p0113r0.html) - first

[2] [P2300R10](http://example.com/p2300r10.html) - second
"""
        output = _scan_and_write(content, fix=False)
        ref_entries = re.findall(r'^\[(\d+)\]\s', output, re.MULTILINE)
        assert len(ref_entries) == 2

    def test_entry_with_more_metadata_kept(self):
        content = """\
See <sup>[1]</sup> and <sup>[2]</sup>.

## References

[1] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - short

[2] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - "Executors and Async Ops, Revision 2" (Christopher Kohlhoff, 2015).
"""
        output = _scan_and_write(content, fix=False)
        assert 'Executors and Async Ops' in output

    def test_body_citations_updated_after_unify(self):
        content = """\
First <sup>[1]</sup> then <sup>[2]</sup>.

## References

[1] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - short

[2] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - "Full title" (Author, 2015).
"""
        output = _scan_and_write(content, fix=False)
        body = output[:output.index('## References')]
        cite_nums = re.findall(r'<sup>\[(\d+)\]</sup>', body)
        assert len(set(cite_nums)) == 1


class TestGapClosureAfterUnification:
    def test_no_gap_after_unification(self):
        content = """\
See <sup>[1]</sup> and <sup>[2]</sup> and <sup>[3]</sup>.

## References

[1] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - short

[2] [P0113R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2015/p0113r0.html) - "Full title" (Author, 2015).

[3] [P2300R10](https://example.com/p2300r10.html) - "std::execution"
"""
        output = _scan_and_write(content, fix=False)
        ref_nums = re.findall(r'^\[(\d+)\]\s', output, re.MULTILINE)
        nums = [int(n) for n in ref_nums]
        assert nums == list(range(1, len(nums) + 1))


class TestRenumberRegression:
    def test_all_cited_no_orphans_unchanged(self):
        lines = _lines("""\
## References
[3] Third ref
[1] First ref
[2] Second ref""")
        refs = {
            3: RefEntry(3, 'Third ref', 1, 'A'),
            1: RefEntry(1, 'First ref', 2, 'A'),
            2: RefEntry(2, 'Second ref', 3, 'A'),
        }
        old_to_new = {3: 1, 1: 2, 2: 3}
        result = reorder_refs(lines, refs, old_to_new)
        assert '[1] Third ref' in result[1]
        assert '[2] First ref' in result[2]
        assert '[3] Second ref' in result[3]

    def test_orphan_removal_in_fix_mode_unaffected(self):
        content = """\
Body <sup>[1]</sup> and <sup>[3]</sup>.

## References

[1] First ref

[2] Orphan ref

[3] Third ref
"""
        output = _scan_and_write(content, fix=True)
        assert '[2] Orphan ref' not in output
        assert '<sup>[1]</sup>' in output
        assert '<sup>[2]</sup>' in output

    def test_exempt_orphans_get_unique_numbers(self):
        content = """\
Body <sup>[2]</sup>.

## References

[1] Orphan github ref, https://github.com/cppalliance/capy

[2] Cited ref
"""
        config = {
            'exempt_sections': [],
            'exempt_links': [],
            'exempt_orphans': ['*github.com/cppalliance*'],
        }
        fd, tmp = tempfile.mkstemp(suffix='.md')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            r = scan(tmp, config)
            output = write(r, ResolveResult(), fix=True)
        finally:
            os.unlink(tmp)
        ref_numbers = re.findall(r'^\[(\d+)\]\s', output, re.MULTILINE)
        assert len(ref_numbers) == len(set(ref_numbers))

    def test_idempotency_with_orphans(self):
        content = """\
First <sup>[3]</sup> then <sup>[1]</sup>.

## References

[1] First ref

[2] Orphan ref

[3] Third ref
"""
        config = load_config(None)
        fd, tmp = tempfile.mkstemp(suffix='.md')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            r1 = scan(tmp, config)
            output1 = write(r1, ResolveResult(), fix=False)
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(output1)
            r2 = scan(tmp, config)
            output2 = write(r2, ResolveResult(), fix=False)
        finally:
            os.unlink(tmp)
        assert output1 == output2

    def test_renumber_identity_when_already_ordered(self):
        content = """\
First <sup>[1]</sup> then <sup>[2]</sup> then <sup>[3]</sup>.

## References

[1] First ref

[2] Second ref

[3] Third ref
"""
        output = _scan_and_write(content, fix=False)
        assert output == content


class TestRefNeverDropped:
    def test_cited_ref_never_dropped(self):
        content = """\
See <sup>[1]</sup> and <sup>[2]</sup> and <sup>[3]</sup>.

## References

[1] First ref

[2] Second ref

[3] Third ref
"""
        output = _scan_and_write(content, fix=False)
        output_lines = output.splitlines(keepends=True)
        excluded = build_exclusion_ranges(output_lines)
        refs_start, refs_end = find_refs_section(output_lines)
        _, _, out_old_to_new = extract_body_citations(
            output_lines, excluded, refs_start)
        out_refs = parse_references(output_lines, refs_start, refs_end)
        for cite_num in out_old_to_new.keys():
            assert cite_num in out_refs

    def test_cited_ref_survives_renumber_with_orphans(self):
        content = """\
See <sup>[3]</sup> and <sup>[5]</sup>.

## References

[1] Orphan A

[2] Orphan B

[3] Cited one

[4] Orphan C

[5] Cited two
"""
        output = _scan_and_write(content, fix=False)
        assert 'Cited one' in output
        assert 'Cited two' in output
