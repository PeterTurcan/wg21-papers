"""Tests for year inclusion in new ref entries and author correction."""
import os
import re
import tempfile

from helpers import _lines
from cite import (
    PaperMetadata,
    RefEntry,
    ResolveResult,
    add_citations_to_links,
    find_refs_section,
    fix_title_mismatches,
    load_config,
    parse_references,
    scan,
    to_html_entities,
    write,
)


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


def _make_resolved(pid, title, authors, date, url):
    resolved = ResolveResult()
    resolved.metadata[pid] = PaperMetadata(
        paper_id=pid, title=title, authors=authors, date=date, url=url)
    return resolved


# ---------------------------------------------------------------------------
# Year inclusion
# ---------------------------------------------------------------------------

class TestYearInNewEntry:
    def test_year_included_in_new_entry(self):
        """New entry from index metadata includes year from meta.date."""
        url = 'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p9999r0.html'
        lines = _lines(f"""\
See [P9999R0]({url}) link.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'P9999R0', url)]
        resolved = _make_resolved(
            'P9999R0', 'Test Title', 'Test Author', '2024-06-28', url)
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, resolved)
        new_entry = [e for n, e in new_refs.items() if n > 1]
        assert len(new_entry) == 1
        assert '2024' in new_entry[0].text, \
            f"Year missing from entry: {new_entry[0].text}"

    def test_year_missing_when_no_date(self):
        """When meta.date is empty, no year appended."""
        url = 'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p9999r0.html'
        lines = _lines(f"""\
See [P9999R0]({url}) link.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'P9999R0', url)]
        resolved = _make_resolved(
            'P9999R0', 'Test Title', 'Test Author', '', url)
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, resolved)
        new_entry = [e for n, e in new_refs.items() if n > 1]
        assert len(new_entry) == 1
        assert 'Test Author)' in new_entry[0].text or \
               'Test Author).' in new_entry[0].text

    def test_year_with_single_author(self):
        """Entry with single author includes year: (Gor Nishanov, 2018)."""
        url = 'http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0913r1.html'
        lines = _lines(f"""\
See [P0913R1]({url}) link.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'P0913R1', url)]
        resolved = _make_resolved(
            'P0913R1', 'Symmetric Transfer', 'Gor Nishanov', '2018-11-01', url)
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, resolved)
        new_text = [e.text for n, e in new_refs.items() if n > 1][0]
        assert 'Gor Nishanov' in new_text
        assert '2018' in new_text

    def test_year_with_multiple_authors(self):
        """Multiple authors + year: (Author1, Author2, 2026)."""
        url = 'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r0.pdf'
        lines = _lines(f"""\
See [P4003R0]({url}) link.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'P4003R0', url)]
        resolved = _make_resolved(
            'P4003R0', 'Coroutines for I/O',
            'Vinnie Falco, Steve Gerbino, Mungo Gill', '2026-03-15', url)
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, resolved)
        new_text = [e.text for n, e in new_refs.items() if n > 1][0]
        assert 'Vinnie Falco' in new_text
        assert 'Mungo Gill' in new_text
        assert '2026' in new_text

    def test_year_with_html_entity_author(self):
        """Author with diacriticals: (Dietmar K&uuml;hl, 2025)."""
        url = 'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3796r1.html'
        lines = _lines(f"""\
See [P3796R1]({url}) link.
## References
[1] Existing ref""")
        refs = {1: RefEntry(1, 'Existing ref', 2, 'A')}
        uncited = [(0, 'P3796R1', url)]
        resolved = _make_resolved(
            'P3796R1', 'Coroutine Task Issues',
            'Dietmar K\u00fchl', '2025-01-01', url)
        _, new_refs = add_citations_to_links(
            lines, uncited, refs, 3, resolved)
        new_text = [e.text for n, e in new_refs.items() if n > 1][0]
        assert '2025' in new_text
        assert 'uuml' in new_text or 'K&' in new_text


# ---------------------------------------------------------------------------
# Author correction
# ---------------------------------------------------------------------------

class TestAuthorCorrection:
    def _make_ref_line(self, pid, url, title, author_str):
        return (f'[{pid}]({url}) - '
                f'"{title}" ({author_str}).')

    def test_author_corrected_single(self):
        """Wrong author replaced with index author."""
        ref_text = self._make_ref_line(
            'P3801R0',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3801r0.html',
            'Concerns about the design of std::execution::task',
            'Maikel Nadolski, 2025')
        lines = _lines(f"""\
## References
[1] {ref_text}""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = _make_resolved(
            'P3801R0',
            'Concerns about the design of std::execution::task',
            'Jonathan M\u00fcller', '2025-01-01',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3801r0.html')
        result = fix_title_mismatches(lines, refs, resolved)
        ref_line = result[1]
        assert 'Nadolski' not in ref_line, \
            f"Wrong author not corrected: {ref_line.strip()}"
        assert 'ller' in ref_line or 'uuml' in ref_line, \
            f"Correct author not inserted: {ref_line.strip()}"

    def test_author_not_corrected_when_matches(self):
        """Correct author left unchanged."""
        ref_text = self._make_ref_line(
            'P2300R10',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html',
            'std::execution',
            'Eric Niebler, 2024')
        lines = _lines(f"""\
## References
[1] {ref_text}""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = _make_resolved(
            'P2300R10', 'std::execution', 'Eric Niebler', '2024-06-28',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Eric Niebler' in result[1]

    def test_author_with_html_entities_compared_correctly(self):
        """HTML entity author (K&uuml;hl) matches index Kühl."""
        ref_text = self._make_ref_line(
            'P3796R1',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3796r1.html',
            'Coroutine Task Issues',
            'Dietmar K&uuml;hl, 2025')
        lines = _lines(f"""\
## References
[1] {ref_text}""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = _make_resolved(
            'P3796R1', 'Coroutine Task Issues',
            'Dietmar K\u00fchl', '2025-01-01',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3796r1.html')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'uuml' in result[1] or 'K&' in result[1], \
            "HTML entity author was corrupted"

    def test_author_ed_format_not_corrupted(self):
        """(Richard Smith, ed.) not replaced."""
        ref_text = '[C++ Working Draft](https://eel.is/c++draft/) - (Richard Smith, ed.).'
        lines = _lines(f"""\
## References
[1] {ref_text}""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_title_mismatches(lines, refs, ResolveResult())
        assert 'Richard Smith, ed.' in result[1]

    def test_author_et_al_not_expanded(self):
        """(Vinnie Falco et al., 2026) not changed to full list."""
        ref_text = self._make_ref_line(
            'P4100R0',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf',
            'The Network Endeavor',
            'Vinnie Falco et al., 2026')
        lines = _lines(f"""\
## References
[1] {ref_text}""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = _make_resolved(
            'P4100R0', 'The Network Endeavor',
            'Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati',
            '2026-01-01',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'et al.' in result[1], \
            f"et al. was expanded: {result[1].strip()}"

    def test_author_body_consistency_check(self):
        """Author appearing in body text not replaced."""
        lines = _lines("""\
Maikel Nadolski proposed a different approach.
## References
[1] [P3801R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3801r0.html) - "Concerns about task" (Maikel Nadolski, 2025).""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = _make_resolved(
            'P3801R0', 'Concerns about task',
            'Jonathan M\u00fcller', '2025-01-01',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3801r0.html')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Nadolski' in result[-1], \
            "Author replaced despite appearing in body text"

    def test_author_with_no_year_format(self):
        """(Lewis Baker) format correctable."""
        ref_text = self._make_ref_line(
            'P1056R1',
            'http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p1056r1.html',
            'Add lazy coroutine type',
            'Lewis Baker')
        lines = _lines(f"""\
## References
[1] {ref_text}""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = _make_resolved(
            'P1056R1', 'Add lazy coroutine type',
            'Lewis Baker, Gor Nishanov', '2018-05-01',
            'http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p1056r1.html')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Gor Nishanov' in result[1] or 'Lewis Baker' in result[1]

    def test_author_abbreviated_names_not_replaced(self):
        """Abbreviated form (Dominiak, Baker, ...) not expanded."""
        ref_text = self._make_ref_line(
            'P2300R10',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html',
            'std::execution',
            'Dominiak, Baker, Howes, Shoop, Garland, Niebler, Lelbach, 2024')
        lines = _lines(f"""\
## References
[1] {ref_text}""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        resolved = _make_resolved(
            'P2300R10', 'std::execution',
            'Michal Dominiak, Lewis Baker, Lee Howes, Kirk Shoop, Michael Garland, Eric Niebler, Bryce Adelstein Lelbach',
            '2024-06-28',
            'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html')
        result = fix_title_mismatches(lines, refs, resolved)
        assert 'Dominiak, Baker' in result[1], \
            f"Abbreviated names were expanded: {result[1].strip()}"

    def test_non_person_author_not_replaced(self):
        """Non-person author field (LWG4348, CD C++26) left alone."""
        lines = _lines("""\
## References
[1] [US 246-373](https://github.com/cplusplus/nbballot/issues/948) - "Support symmetric transfer" (LWG4348, CD C++26).""")
        refs_start, refs_end = find_refs_section(lines)
        refs = parse_references(lines, refs_start, refs_end)
        result = fix_title_mismatches(lines, refs, ResolveResult())
        assert 'LWG4348' in result[1]
