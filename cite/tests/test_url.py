"""Tests for wg21.link detection, URL construction, and URL replacement."""
from helpers import _lines
from cite import (
    find_wg21_links,
    _construct_open_std_url,
    apply_wg21_replacements,
    build_exclusion_ranges,
)


class TestFindWg21Links:
    def test_finds_links(self):
        lines = _lines("""\
See [P2300R10](https://wg21.link/p2300r10) for details.
Also https://wg21.link/p3552r3 here.""")
        excluded = build_exclusion_ranges(lines)
        results = find_wg21_links(lines, excluded)
        assert len(results) == 2
        assert results[0].slug.lower() == 'p2300r10'
        assert results[1].slug.lower() == 'p3552r3'

    def test_skips_code_blocks(self):
        lines = _lines("""\
Body https://wg21.link/p2300r10.
```
Code https://wg21.link/p3552r3.
```""")
        excluded = build_exclusion_ranges(lines)
        results = find_wg21_links(lines, excluded)
        assert len(results) == 1
        assert results[0].slug.lower() == 'p2300r10'

    def test_no_wg21_links(self):
        lines = _lines("See https://open-std.org/paper.html for details.")
        excluded = build_exclusion_ranges(lines)
        results = find_wg21_links(lines, excluded)
        assert len(results) == 0


class TestConstructOpenStdUrl:
    def test_versioned_slug(self):
        url = _construct_open_std_url('p4100r0')
        assert 'p4100r0.pdf' in url
        assert 'open-std.org' in url

    def test_unversioned_p_slug_appends_r0(self):
        url = _construct_open_std_url('p4100')
        assert 'p4100r0.pdf' in url

    def test_n_paper_no_revision(self):
        url = _construct_open_std_url('n2406')
        assert 'n2406.pdf' in url
        assert 'r0' not in url

    def test_uses_current_year(self):
        import datetime
        year = str(datetime.datetime.now().year)
        url = _construct_open_std_url('p4100r0')
        assert f'/papers/{year}/' in url

    def test_d_paper_unversioned(self):
        url = _construct_open_std_url('d4171')
        assert 'd4171r0.pdf' in url


class TestApplyWg21Replacements:
    def test_replaces_urls(self):
        lines = _lines("""\
See [P2300R10](https://wg21.link/p2300r10)<sup>[1]</sup>.
Also https://wg21.link/p2300r10 in refs.""")
        replacements = {
            'https://wg21.link/p2300r10':
                'https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html',
        }
        result = apply_wg21_replacements(lines, replacements, set())
        for line in result:
            assert 'wg21.link' not in line
            if 'P2300R10' in line or 'p2300r10' in line:
                assert 'open-std.org' in line

    def test_no_replacements(self):
        lines = _lines("No wg21 links here.")
        result = apply_wg21_replacements(lines, {}, set())
        assert result == lines

    def test_skips_excluded_lines(self):
        lines = _lines("""\
Body https://wg21.link/p2300r10 here.
```
https://wg21.link/p2300r10
```
After.""")
        replacements = {
            'https://wg21.link/p2300r10':
                'https://www.open-std.org/.../p2300r10.html',
        }
        excluded = {1, 2, 3}
        result = apply_wg21_replacements(lines, replacements, excluded)
        assert 'open-std.org' in result[0]
        assert 'wg21.link' in result[2]

    def test_no_substring_collision(self):
        """Replacing wg21.link/p4100 must not corrupt wg21.link/p4100r0."""
        lines = _lines("""\
[Network Endeavor](https://wg21.link/p4100) ([P4100R0](https://wg21.link/p4100r0))<sup>[1]</sup>""")
        replacements = {
            'https://wg21.link/p4100':
                'https://isocpp.org/files/papers/P4100R0.pdf',
            'https://wg21.link/p4100r0':
                'https://isocpp.org/files/papers/P4100R0.pdf',
        }
        result = apply_wg21_replacements(lines, replacements, set())
        assert 'P4100R0R0' not in result[0]
        assert 'P4100R0.pdf' in result[0]
