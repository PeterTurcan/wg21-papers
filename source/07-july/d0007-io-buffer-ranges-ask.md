---
title: "I/O Buffer Ranges"
document: D0007R0
date: 2026-05-15
intent: ask
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

This paper asks the committee to advance a buffer descriptor vocabulary - two byte-region types, two range concepts, and four algorithms - as standard library vocabulary for I/O.

The vocabulary is `const_buffer`, `mutable_buffer`, `ConstBufferSequence`, `MutableBufferSequence`, `buffer_size`, `buffer_empty`, `buffer_length`, and `buffer_copy`. It is the [Networking TS](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup> shape, deployed for over twenty years in [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html)<sup>[3]</sup>, shipping today in [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup>, consumed by every Boost library above Capy.

The companion paper *I/O Buffer Ranges: Design Rationale*<sup>[7]</sup> provides the design rationale, the convergence record across seven ecosystems, anticipated objections, and the implementation inventory. Read this paper for the proposal; read the companion when you need the audit trail.

This paper is Paper 4 in the series defined by [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[4]</sup>. It has no async dependency. Dynamic buffers (the prepare/commit growable buffer concept) are the subject of a separate companion pair, *Dynamic Buffer*<sup>[8]</sup> and *Dynamic Buffer: Design Rationale*<sup>[9]</sup>.

---

## Revision History

### R0: May 2026 (post-Brno mailing)

* Initial Version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author maintains [Boost.Beast](https://github.com/boostorg/beast)<sup>[5]</sup> and develops [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[6]</sup>, plus three further Boost libraries built on them. Each defines or consumes buffer abstractions. The body of work creates a bias toward dedicated buffer types.

This paper is the proposal-only ask paper for the buffer descriptor and sequence vocabulary. The design rationale lives in the companion *I/O Buffer Ranges: Design Rationale*<sup>[7]</sup>. The argument that `std::span<std::byte>` is structurally insufficient for I/O buffer descriptors lives in [P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf)<sup>[10]</sup>.

---

## 2. What This Paper Asks

The committee is asked to advance the following vocabulary for the standard library:

```cpp
namespace std::io {

  class const_buffer;
  class mutable_buffer;

  template<class T> concept ConstBufferSequence    = /* see Section 4 */;
  template<class T> concept MutableBufferSequence  = /* see Section 4 */;

  template<ConstBufferSequence CB>
  constexpr std::size_t buffer_size(CB const& bs) noexcept;

  template<ConstBufferSequence CB>
  constexpr bool buffer_empty(CB const& bs) noexcept;

  template<ConstBufferSequence CB>
  std::size_t buffer_length(CB const& bs);

  template<MutableBufferSequence MB, ConstBufferSequence CB>
  std::size_t buffer_copy(
      MB const& dest,
      CB const& src,
      std::size_t at_most = std::size_t(-1)) noexcept;

}
```

Two types. Two concepts. Four algorithms.

---

## 3. The Types

### 3.1 `mutable_buffer`

A pointer-and-size descriptor for a writable byte region.

```cpp
class mutable_buffer
{
public:
    constexpr mutable_buffer() noexcept;
    constexpr mutable_buffer(mutable_buffer const&) noexcept;
    constexpr mutable_buffer(void* data, std::size_t size) noexcept;

    constexpr mutable_buffer& operator=(mutable_buffer const&) noexcept;
    constexpr mutable_buffer& operator+=(std::size_t n) noexcept;

    constexpr void* data() const noexcept;
    constexpr std::size_t size() const noexcept;
};
```

`data()` returns `void*`. `size()` returns the byte count. `operator+=` advances the region start and shrinks the size.

### 3.2 `const_buffer`

A pointer-and-size descriptor for a read-only byte region. `mutable_buffer` converts implicitly to `const_buffer`; the reverse is not provided.

```cpp
class const_buffer
{
public:
    constexpr const_buffer() noexcept;
    constexpr const_buffer(const_buffer const&) noexcept;
    constexpr const_buffer(void const* data, std::size_t size) noexcept;
    constexpr const_buffer(mutable_buffer const& b) noexcept;

    constexpr const_buffer& operator=(const_buffer const&) noexcept;
    constexpr const_buffer& operator+=(std::size_t n) noexcept;

    constexpr void const* data() const noexcept;
    constexpr std::size_t size() const noexcept;
};
```

---

## 4. The Concepts

A buffer sequence is either a single buffer or a bidirectional range whose value type is a buffer.

```cpp
template<class T>
concept ConstBufferSequence =
    std::is_convertible_v<T, const_buffer> || (
        std::ranges::bidirectional_range<T> &&
        std::is_convertible_v<
            std::ranges::range_value_t<T>, const_buffer>);

template<class T>
concept MutableBufferSequence =
    std::is_convertible_v<T, mutable_buffer> || (
        std::ranges::bidirectional_range<T> &&
        std::is_convertible_v<
            std::ranges::range_value_t<T>, mutable_buffer>);
```

The disjunction admits both single buffers and ranges of buffers under one signature. The cost - that a single `const_buffer` is not a `std::ranges::range` - is recorded in *I/O Buffer Ranges: Design Rationale*<sup>[7]</sup> Section 4.3.

---

## 5. The Algorithms

Four free function templates over `ConstBufferSequence` or `MutableBufferSequence`.

### 5.1 `buffer_size`

Sums bytes across a buffer sequence.

```cpp
template<ConstBufferSequence CB>
constexpr std::size_t buffer_size(CB const& bs) noexcept;

// Effects: returns the sum of size() over each buffer in the sequence.
// Complexity: O(n) in the number of elements.
```

### 5.2 `buffer_empty`

Tests whether every buffer in the sequence has zero size.

```cpp
template<ConstBufferSequence CB>
constexpr bool buffer_empty(CB const& bs) noexcept;

// Effects: returns true if no buffer in the sequence has nonzero size.
// Complexity: O(n) in the number of elements; may short-circuit on the
// first nonzero buffer.
```

### 5.3 `buffer_length`

Counts buffer elements (not bytes).

```cpp
template<ConstBufferSequence CB>
std::size_t buffer_length(CB const& bs);

// Effects: returns the iterator distance from begin to end of the
// sequence. For a single buffer, returns 1.
```

### 5.4 `buffer_copy`

Copies bytes from a `ConstBufferSequence` into a `MutableBufferSequence`, stopping at the smaller total or at the optional `at_most` limit.

```cpp
template<MutableBufferSequence MB, ConstBufferSequence CB>
std::size_t buffer_copy(
    MB const& dest,
    CB const& src,
    std::size_t at_most = std::size_t(-1)) noexcept;

// Effects: copies bytes from src to dest, walking both sequences with
// cursors that track partially-consumed buffers. Byte boundaries do
// not need to align with buffer boundaries.
// Returns: min(buffer_size(dest), buffer_size(src), at_most).
// Complexity: linear in the number of bytes copied.
```

---

## 6. Suggested Straw Poll

> LEWG agrees that the buffer descriptor vocabulary `const_buffer`, `mutable_buffer`, `ConstBufferSequence`, `MutableBufferSequence`, `buffer_size`, `buffer_empty`, `buffer_length`, and `buffer_copy` documented in this paper and its companion *I/O Buffer Ranges: Design Rationale* should be advanced as standard library vocabulary for I/O.

---

## Acknowledgments

Christopher Kohlhoff designed the Asio buffer types and the `ConstBufferSequence` and `MutableBufferSequence` named requirements that this paper recovers as C++20 concepts.

The Networking TS authors codified the operational semantics in [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup>.

Neil MacIntosh's [P0298R3](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2017/p0298r3.pdf)<sup>[11]</sup> established the precedent for adding a distinct type when a generic type performs double duty.

Peter Dimov's review of the Capy buffer code surfaced the contract-tightening questions tracked in capy issues 257, 258, 260, 261, 262, and 263.

---

## References

[1] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[2] [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf) - "Working Draft, C++ Extensions for Networking" (Jonathan Wakely, 2018).

[3] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - Buffer types and buffer sequence requirements (Christopher Kohlhoff, 2003-2026).

[4] [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[5] [Boost.Beast](https://github.com/boostorg/beast) - HTTP and WebSocket built on Boost.Asio (Vinnie Falco, 2017-2026).

[6] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[7] *I/O Buffer Ranges: Design Rationale* (Vinnie Falco, 2026). Companion design paper. D0008R0.

[8] *Dynamic Buffer* (Vinnie Falco, 2026). Companion ask paper for the growable buffer concept. D0009R0.

[9] *Dynamic Buffer: Design Rationale* (Vinnie Falco, 2026). Companion design paper for the growable buffer concept. D0010R0.

[10] [P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf) - "Why Span Is Not Enough" (Vinnie Falco, 2026).

[11] [P0298R3](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2017/p0298r3.pdf) - "A byte type definition" (Neil MacIntosh, Botond Ballo, 2017).
