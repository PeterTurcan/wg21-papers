---
title: "Info: I/O Buffer Ranges"
document: D0000R0
date: 2026-05-15
intent: info
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

Every C++ project that does I/O invents its own buffer types.

Six other ecosystems do not. Each provides a vocabulary for the same operation: pass a contiguous region of bytes, or a sequence of such regions, into a syscall whose name is `readv`, `WSARecv`, or `io_uring_prep_writev`. The C++ standard has the byte. It does not have the descriptor. It does not have the sequence. It does not have the growable buffer with prepare and commit. This paper documents the shapes that ship in [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> today and that every Boost library above Capy consumes - the same shapes the [Networking TS](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup> codified, the same shapes [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html)<sup>[3]</sup> deployed for over twenty years, the same shapes seven independent ecosystems converged on without coordinating.

This paper is Paper 4 in the series defined by [P4100R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf)<sup>[4]</sup>. It has no async dependency, no coroutine dependency, no executor dependency. The vocabulary is reusable by [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) "`std::execution`"<sup>[5]</sup>, by Asio, by callback-based networking, and by any other I/O system that needs to point at bytes. Design rationale for the bespoke types - why `mutable_buffer` rather than `std::span<std::byte>` - lives in the companion paper [P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf)<sup>[6]</sup>.

---

## Revision History

### R0: May 2026 (post-Croydon mailing)

* Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author maintains [Boost.Beast](https://github.com/boostorg/beast)<sup>[7]</sup>, a published HTTP and WebSocket library built on Asio's buffer model, and develops [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[8]</sup>, plus three further Boost libraries built on them: Boost.Http, Boost.Beast2, and Boost.Burl. Each defines or consumes buffer abstractions. The author published [P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf)<sup>[6]</sup>, which argued for a separate buffer descriptor type. This paper is the successor that proposes the full vocabulary. The body of work creates a bias toward dedicated buffer types.

This paper documents the buffer vocabulary that ships in Capy and proposes it as standard library vocabulary. The vocabulary is consumed by every I/O operation in Corosio and by the higher-layer Boost libraries built on Capy. Appendix B lists each header.

The [Networking TS](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup> defined `const_buffer`, `mutable_buffer`, `ConstBufferSequence`, and `MutableBufferSequence`. The shapes in this paper are the same shapes. This paper recovers them on a parallel track to the Network Endeavor and adds the `DynamicBuffer` concept, which the Networking TS specified as a named requirement and which this paper proposes as a C++20 concept.

The alternative consensus is `std::span<std::byte>` for a single region and a hand-rolled approach for sequences of regions. [P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf)<sup>[6]</sup> sets out the structural problems with that approach. This paper inherits the conclusion and does not re-litigate it.

The proposed concept shape has one structural departure from `std::ranges`<sup>[9]</sup>: a single `const_buffer` satisfies `ConstBufferSequence` even though it is not a `std::ranges::range`. The convenience is that one signature accepts both a single buffer and a range of buffers. The cost is recorded in Section 4.3.

This paper is Paper 4 in the [Network Endeavor](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf) ([P4100R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf)<sup>[4]</sup>). It depends on nothing. It can advance independently of [P4003R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r1.pdf)<sup>[10]</sup>. The vocabulary is reusable by senders, by Asio, by callback-based networking, and by any I/O system that needs to point at bytes.

The companion papers are [P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf)<sup>[6]</sup> (rationale for bespoke types over `std::span<std::byte>`) and [P4100R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf)<sup>[4]</sup> (the umbrella paper that places this work in series).

Every concept and type proposed here ships in Capy. Every I/O operation in Corosio consumes them. Appendix B is the inventory.

The author asks for nothing.

---

## 2. What the Standard Needs

A library that does I/O wants four things. The C++ standard library provides one of them.

| Need                                              | What the C++ developer writes today                                          | What this paper documents                          |
| ------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------- |
| A descriptor for one contiguous byte region       | `std::span<std::byte>` (overloaded with `mdspan`, hashing, cryptography)      | `const_buffer`, `mutable_buffer`                   |
| A sequence of byte regions for scatter and gather | (none)                                                                        | `ConstBufferSequence`, `MutableBufferSequence`     |
| Algorithms over byte regions                      | `std::accumulate` over a hand-rolled lambda; a loop over `std::memcpy`        | `buffer_size`, `buffer_empty`, `buffer_length`, `buffer_copy` |
| A growable buffer with read and write phases      | `std::vector<std::byte>` plus discipline                                      | `DynamicBuffer` concept                            |

Each row is a vocabulary the standard library does not provide. Each row is the reason the C++ ecosystem reinvents buffers.

**Four needs. None met. Each is reinvented in every codebase that does I/O.**

---

## 3. Byte-Region Vocabulary

A buffer is a pointer and a size. The shape is forty years old<sup>[11]</sup>. The interface is small.

### 3.1 The Shape

```cpp
class mutable_buffer
{
    unsigned char* p_ = nullptr;
    std::size_t n_ = 0;
public:
    mutable_buffer() = default;
    constexpr mutable_buffer(void* data, std::size_t size) noexcept;
    constexpr void* data() const noexcept;
    constexpr std::size_t size() const noexcept;
    mutable_buffer& operator+=(std::size_t n) noexcept;
};

class const_buffer
{
    unsigned char const* p_ = nullptr;
    std::size_t n_ = 0;
public:
    const_buffer() = default;
    constexpr const_buffer(void const* data, std::size_t size) noexcept;
    constexpr const_buffer(mutable_buffer const& b) noexcept;
    constexpr void const* data() const noexcept;
    constexpr std::size_t size() const noexcept;
    const_buffer& operator+=(std::size_t n) noexcept;
};
```

`data()` returns `void*` or `void const*`. `size()` returns the byte count. `operator+=` advances the start and shrinks the region; the byte content does not move. There are no other operations.

These are the [Networking TS](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup> types. They ship in Capy<sup>[1]</sup>. They ship in Asio<sup>[3]</sup>.

### 3.2 Why `void*`, Not `byte*`

[P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf)<sup>[6]</sup> Section 9 sets out the case. The summary: `void*` is maximally accepting and minimally permissive. Any pointer converts to it implicitly. The user must perform an explicit cast to use it. `byte*` invites pointer arithmetic, accidental assignment to `std::span<std::byte>`, and `reinterpret_cast` round-trips that the buffer descriptor was meant to avoid. The asymmetry is by design.

### 3.3 `mutable_buffer` Is a `const_buffer` Source

`mutable_buffer` converts implicitly to `const_buffer`. The reverse is forbidden by construction.

```cpp
mutable_buffer mb(data, size);
const_buffer   cb = mb;   // OK: read what was written
mutable_buffer mb2 = cb;  // ill-formed
```

A read pipeline that consumes a write buffer is a natural shape - acquire a writable region, write into it, hand it on as a read-only region. The conversion captures that path in one direction and forbids it in the other. The type system records the difference.

**Five lines define a byte region. Forty years of practice define why.**

---

## 4. Buffer Sequences

I/O is not always one region. A message has a header and a body. A protocol has framing and payload. `readv` and `writev` exist because the operating system lets the user describe the message as a sequence of regions and complete the syscall once. The vocabulary needs a name for that sequence.

### 4.1 The Concept

```cpp
template<typename T>
concept ConstBufferSequence =
    std::is_convertible_v<T, const_buffer> || (
        std::ranges::bidirectional_range<T> &&
        std::is_convertible_v<
            std::ranges::range_value_t<T>, const_buffer>);

template<typename T>
concept MutableBufferSequence =
    std::is_convertible_v<T, mutable_buffer> || (
        std::ranges::bidirectional_range<T> &&
        std::is_convertible_v<
            std::ranges::range_value_t<T>, mutable_buffer>);
```

A type satisfies `ConstBufferSequence` if it converts to `const_buffer` (a one-element sequence) or if it is a bidirectional range whose value type converts to `const_buffer`. The disjunction is the shape that lets one signature accept both forms.

```cpp
co_await stream.write_some(const_buffer{p, n});             // one region
co_await stream.write_some(std::array{cb1, cb2});           // two regions
co_await stream.write_some(std::vector<const_buffer>{...}); // many regions
```

The same overload accepts each. The function does not branch on whether the argument is a single buffer or a range of buffers. The concept does the branching at the type system. Each algorithm in Section 5 handles both cases uniformly.

### 4.2 Why Bidirectional

Bidirectional is the iterator strength that includes the sequences I/O actually produces. `std::array<const_buffer, N>` is random-access. A linked list of buffer segments - the shape used by .NET's `ReadOnlySequence<T>`<sup>[12]</sup> for streaming - is bidirectional but not random-access. Forward-only sequences are not excluded by the algorithms in Section 5; the concept asks for bidirectional because it is the iterator strength buffer arrays publish in practice and because slicing a sequence from the back does not require random-access.

### 4.3 Single Buffer as Sequence

A single `const_buffer` is not a `std::ranges::range`<sup>[9]</sup>. It has no `begin` or `end` member, and the namespace-scope `begin` and `end` customization points the concept relies on are not the same as `std::ranges::begin` and `std::ranges::end`. The concept treats a single buffer as a one-element sequence by convention, not by ranges machinery.

This is the structural departure noted in the disclosure. The convenience is that one overload accepts both a single region and a range of regions. The cost is that `ConstBufferSequence` is not a refinement of any standard range concept. It is a sibling, not a child.

The alternative - require the caller to wrap a single buffer in `std::array<const_buffer, 1>` before passing it - was not selected. The wrapping is friction at every call site. The disjunction in the concept is friction at one point in the type system. Twenty years of Asio practice<sup>[3]</sup> indicates that the friction at the concept is invisible in user code. The friction at the call site would not be.

### 4.4 Ready-Made Sequences (Informative)

The vocabulary in this paper is two types and two concepts. In practice, two sequence types recur enough that Capy ships ready-made wrappers. They are informative, not proposed.

`buffer_pair` is a typedef for `std::array<const_buffer, 2>` (and the mutable form). The most common scatter-gather case - one header buffer, one body buffer - has a name.

`buffer_array<N, IsConst>` is a fixed-capacity stack-allocated buffer sequence. It satisfies `ConstBufferSequence` (or `MutableBufferSequence`), it caches its byte total for `O(1)` `buffer_size`, and it is the small-buffer optimization Capy uses to materialize an arbitrary sequence into the contiguous `iovec`-shaped span the platform syscall requires - no heap allocation per scatter/gather call. The shape is in `boost/capy/buffers/buffer_array.hpp`<sup>[1]</sup>. Standardizing it is not part of this paper.

**One concept. Single buffer or bidirectional range. Both are sequences.**

---

## 5. Algorithms

Four algorithms operate on `ConstBufferSequence` or `MutableBufferSequence`. They are spelled as customization point objects so that user-defined sequence types may specialize them.

### 5.1 `buffer_size`

Sums bytes across a buffer sequence. The default implementation iterates the sequence and sums `b.size()` for each element.

```cpp
template<ConstBufferSequence CB>
constexpr std::size_t buffer_size(CB const& bs) noexcept;
```

The default is `O(n)` in the number of elements. A sequence type that already knows its byte total - `buffer_array<N>` caches it; a flat single-region `dynamic_buffer` knows its size by definition - specializes via the customization point and reports `O(1)`. The CPO shape is the reason this is a free algorithm and not a member.

`buffer_size` counts bytes. `std::ranges::size`<sup>[9]</sup> counts elements. Both are useful. They answer different questions.

### 5.2 `buffer_empty`, `buffer_length`

```cpp
template<ConstBufferSequence CB>
constexpr bool buffer_empty(CB const& bs) noexcept;

template<ConstBufferSequence CB>
std::size_t buffer_length(CB const& bs);
```

`buffer_empty` is true when no buffer in the sequence has nonzero size. `buffer_length` is the number of buffer elements - the iterator distance, not the byte total. The two algorithms exist because the questions are common, and the spelling is short enough at the call site that nobody invents a private equivalent.

### 5.3 `buffer_copy`

Copies bytes from a `ConstBufferSequence` into a `MutableBufferSequence`, stopping at the smaller total or at the optional `at_most` limit.

```cpp
template<MutableBufferSequence MB, ConstBufferSequence CB>
std::size_t buffer_copy(
    MB const& dest,
    CB const& src,
    std::size_t at_most = std::size_t(-1)) noexcept;
```

Returns the minimum of `buffer_size(dest)`, `buffer_size(src)`, and `at_most`. The implementation walks both sequences with cursors that track partially-consumed buffers; when one buffer in either sequence is exhausted, the cursor advances to the next. The byte boundaries do not need to align with the buffer boundaries.

The implementation is in `boost/capy/buffers/buffer_copy.hpp`<sup>[1]</sup>. Sixty lines including comments.

### 5.4 Crossing Virtual Boundaries

Type-erased streams accept buffer sequences through a virtual function. The argument must be type-erased - the virtual cannot be a template - but `ConstBufferSequence` is a concept over arbitrary types. The two requirements meet at a span of `const_buffer` materialized from the user's sequence.

Capy's `buffer_param<BS>` is the windowed adapter. The templated entry point captures the user's `BS` by value (so it is copied into the coroutine frame and survives suspension), and `buffer_param` slides a fixed-capacity window of `const_buffer` descriptors over the underlying sequence. Each window is a `std::span<const_buffer>` that crosses the virtual.

```cpp
class base
{
public:
    task<> write(ConstBufferSequence auto buffers)
    {
        buffer_param bp(buffers);
        while(true)
        {
            auto bufs = bp.data();
            if(bufs.empty()) break;
            std::size_t n = 0;
            co_await write_impl(bufs, n);
            bp.consume(n);
        }
    }

protected:
    virtual task<> write_impl(
        std::span<const_buffer> buffers,
        std::size_t& bytes_written) = 0;
};
```

The shape is in `boost/capy/buffers/buffer_param.hpp`<sup>[1]</sup>. It is mentioned here for completeness - it is the technique that lets ABI-stable streams accept arbitrary buffer sequences. Standardizing it is the work of Paper 5 (Stream Concepts), where `any_stream` and friends are formally proposed. This paper does not propose it.

**Four CPOs. Two questions: how many bytes, and where do they go.**

---

## 6. Dynamic Buffers

Two-phase write, two-phase read. A growable buffer hands the caller writable space, the caller writes, the buffer accepts the writes; later, the buffer hands the caller readable bytes, the caller processes, the buffer discards.

### 6.1 The Concept

```cpp
template<class T>
concept DynamicBuffer =
    requires(T& t, T const& ct, std::size_t n) {
        typename T::const_buffers_type;
        typename T::mutable_buffers_type;
        { ct.size()     } -> std::convertible_to<std::size_t>;
        { ct.max_size() } -> std::convertible_to<std::size_t>;
        { ct.capacity() } -> std::convertible_to<std::size_t>;
        { ct.data()     } -> std::same_as<typename T::const_buffers_type>;
        { t.prepare(n)  } -> std::same_as<typename T::mutable_buffers_type>;
        t.commit(n);
        t.consume(n);
    } &&
    ConstBufferSequence<typename T::const_buffers_type> &&
    MutableBufferSequence<typename T::mutable_buffers_type>;
```

`prepare(n)` returns at least `n` bytes of writable space. `commit(n)` makes those bytes readable through `data()`. `data()` returns the readable portion. `consume(n)` discards `n` readable bytes from the front. `size()` is the readable byte count. `max_size()` is the largest the buffer can grow to. `capacity()` is the writable space available without reallocation.

### 6.2 Required Associated Types

`const_buffers_type` is what `data()` returns. `mutable_buffers_type` is what `prepare(n)` returns. They are member typedefs because the concrete sequence type depends on the buffer. A flat buffer returns a single `const_buffer`. A circular buffer returns a `const_buffer_pair` because the readable region may wrap. A linked-list buffer returns a range of regions. The associated types let the concept express this without naming a single sequence shape.

```cpp
class flat_dynamic_buffer
{
public:
    using const_buffers_type   = const_buffer;
    using mutable_buffers_type = mutable_buffer;
    // ...
};

class circular_dynamic_buffer
{
public:
    using const_buffers_type   = const_buffer_pair;
    using mutable_buffers_type = mutable_buffer_pair;
    // ...
};
```

### 6.3 Concrete Implementations (Informative)

Capy ships four `DynamicBuffer` implementations. They are informative, not proposed.

| Implementation              | Storage                                   | `const_buffers_type` |
| --------------------------- | ----------------------------------------- | -------------------- |
| `flat_dynamic_buffer`       | Caller-owned linear array                 | `const_buffer`       |
| `circular_dynamic_buffer`   | Caller-owned ring buffer                  | `const_buffer_pair`  |
| `vector_dynamic_buffer`     | Adapter over `std::vector<unsigned char>` | `const_buffer`       |
| `string_dynamic_buffer`     | Adapter over `std::basic_string`          | `const_buffer`       |

The header set lives at `boost/capy/buffers/`<sup>[1]</sup>. Each header is under three hundred lines. The pattern is twenty years old in Asio<sup>[3]</sup>.

### 6.4 Why Not Member Algorithms

`buffer_size`, `buffer_empty`, `buffer_length`, and `buffer_copy` are CPOs. They are not members of `DynamicBuffer`, of `mutable_buffer`, or of any sequence type. They operate over the concept.

The reason is that the same algorithm runs over a `flat_dynamic_buffer`, a `std::array<const_buffer, 2>`, a `std::vector<const_buffer>`, a single `const_buffer`, and any user-defined sequence that satisfies the concept. The algorithm is a property of the concept, not of any one type.

A type that knows a faster answer specializes the CPO. The default does the obvious thing. The user calls one name and gets either the obvious implementation or the specialized one, and the choice is invisible.

**Two phases for writes. Two phases for reads. The same concept covers all four.**

---

## 7. Relationship to `std::ranges`

`ConstBufferSequence` borrows the bidirectional-range concept from `std::ranges`<sup>[9]</sup>. The borrowing is partial. This section records what is shared, what is not, and what this paper does not extend.

### 7.1 Element Granularity vs Byte Granularity

`std::ranges::size` counts elements. `buffer_size` sums bytes. A buffer sequence with three elements of size 100 each has a `ranges::size` of 3 and a `buffer_size` of 300. Both numbers are correct. They answer different questions.

`std::ranges::drop_view`<sup>[9]</sup> drops elements. There is no standard view that drops bytes across element boundaries. A sequence holding `[100 bytes, 100 bytes]` cannot have its first 26 bytes removed by any standard range adaptor; `views::drop(_, 1)` removes the entire first element. The byte-granular operation has no element-granular spelling.

This paper does not propose a byte-granular range adaptor. Byte-granular consumption is the responsibility of `DynamicBuffer::consume(n)`. The dynamic buffer holds the storage and the bookkeeping, so consumption is a method on the buffer, not an adaptor over an arbitrary sequence.

### 7.2 A Single Buffer Is Not a Range

`const_buffer` and `mutable_buffer` have `data()` and `size()`. They do not have `begin()` and `end()`. They are not ranges in the `std::ranges` sense. The concept treats them as one-element sequences by convention.

A user who wants a range writes `std::array{cb}` or passes a `std::span<const_buffer, 1>`. The disjunction in `ConstBufferSequence` makes that wrapping unnecessary at every call site.

### 7.3 What This Paper Does Not Extend

- No new range adaptors. `std::ranges::views`<sup>[9]</sup> is unchanged.
- No new view types. There is no `std::io::byte_drop_view`.
- No byte-granular slicing CPO at the sequence level. Byte slicing happens inside `DynamicBuffer::consume`.
- No relationship between `mutable_buffer`/`const_buffer` and `std::span<std::byte>` beyond the conversions a user writes themselves.

The extension beyond `std::ranges` is two: a sequence concept that includes a single buffer as a one-element sequence, and a `buffer_size` CPO that sums bytes rather than counting elements. Two extensions. Both narrow.

**Ranges count elements. Buffers count bytes. Both are right; neither is the other.**

---

## 8. Convergence

Seven I/O ecosystems, designed independently, all arrived at the same shape.

| Ecosystem        | Region descriptor                                          | Sequence                                          | Growable                          | Byte algorithms              |
| ---------------- | ---------------------------------------------------------- | ------------------------------------------------- | --------------------------------- | ---------------------------- |
| POSIX (1989)     | `struct iovec`<sup>[13]</sup>                              | `iovec[]`                                         | (none)                            | (none)                       |
| Windows (1996)   | `WSABUF`<sup>[14]</sup>                                    | `WSABUF[]`                                        | (none)                            | (none)                       |
| Asio (2003)      | `const_buffer`, `mutable_buffer`<sup>[3]</sup>             | `ConstBufferSequence`, `MutableBufferSequence`    | `DynamicBuffer` named requirement | `buffer_size`, `buffer_copy` |
| libuv (2012)     | `uv_buf_t`<sup>[15]</sup>                                  | `uv_buf_t[]`                                      | (none)                            | (none)                       |
| Go (2012)        | `[]byte`                                                   | `net.Buffers`<sup>[16]</sup>                      | `bytes.Buffer`                    | (built-in slice)             |
| .NET (2018)      | `Memory<byte>`                                             | `ReadOnlySequence<T>`<sup>[12]</sup>              | `ArrayBufferWriter<T>`            | (built-in)                   |
| Networking TS    | `const_buffer`, `mutable_buffer`<sup>[2]</sup>             | `ConstBufferSequence`, `MutableBufferSequence`    | `DynamicBuffer` named requirement | `buffer_size`, `buffer_copy` |
| C++ standard     | (none)                                                     | (none)                                            | (none)                            | (none)                       |

The first six rows are platforms or libraries. The seventh row is a TS the committee adopted and then declined to advance. The eighth row is the standard.

The bottom row is empty. The empty cells are the finding.

**Seven ecosystems. Same shape. The C++ row is empty.**

---

## 9. Anticipated Objections

### 9.1 "But `std::span<std::byte>` Already Exists"

[P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf)<sup>[6]</sup> sets out the structural problems with `std::span<std::byte>` as a buffer descriptor: the type is overloaded with cryptography, hashing, and serialization needs; it is closed to implementation-defined diagnostic hooks; and a sequence of `std::span<std::byte>` is either a span-of-spans (dangling) or a range of spans (cannot represent byte-granular consumption). The conclusion is in P4036R0; this paper inherits it.

### 9.2 "But Ranges Already Do This"

`std::ranges`<sup>[9]</sup> operates on elements. Buffer sequences need to be iterated as elements (for scatter/gather syscalls) and consumed as bytes (for parsers, decompressors, and protocol framers). The element-granular operations come from `std::ranges` directly. The byte-granular operations - `buffer_size`, `buffer_copy`, and `DynamicBuffer::consume` - have no equivalent. Ranges does most of the work. The CPOs in this paper add what is missing.

### 9.3 "But the Networking TS Already Standardised These"

It did. The committee did not advance the Networking TS. The types it defined never reached the IS. The shapes are the same; the path is different. This paper is Paper 4 in a series whose entry point is the buffer vocabulary because it has the fewest dependencies and the most reuse outside networking. Standardizing the buffer vocabulary does not commit the standard library to anything else in the series. The commitment is to the byte vocabulary every C++ I/O system already speaks.

### 9.4 "But These Belong Inside `std::execution`"

[P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)<sup>[5]</sup> is a sender-and-receiver framework. It does not define byte buffers. A sender that produces bytes - a sender-based read operation, for instance - needs a buffer descriptor and a buffer sequence vocabulary as much as a coroutine-based one does. The vocabulary in this paper has no async dependency. It is reusable by `std::execution`-based I/O, by Asio, by callback-based networking, and by any other system that needs to point at bytes. Putting it inside one async framework would force every other consumer to depend on that framework for the byte vocabulary alone.

---

## 10. What This Paper Does Not Standardise

Five deferrals. Each is named so the scope is unambiguous.

### 10.1 Allocator-Aware `DynamicBuffer`

The proposed concept is allocation-agnostic. Concrete implementations may be allocator-aware - `vector_dynamic_buffer` inherits the allocator of the wrapped `std::vector`<sup>[9]</sup> - but the concept does not require it. An allocator-aware variant of the concept, or an allocator-parameterized standard implementation, is left to a later paper.

### 10.2 Async I/O Concepts

`BufferSource` and `BufferSink` (the callee-owned-buffer concepts in Capy that return `IoAwaitable`) belong in Paper 5 (Stream Concepts) of the series. They have an async dependency. This paper has none.

### 10.3 Range Adaptors over Byte-Granular Slicing

The reasoning is in Section 7.1. Byte-granular consumption is the responsibility of `DynamicBuffer::consume(n)`. A `std::ranges`-style adaptor that slices bytes across element boundaries is a possible future addition; this paper does not include one.

### 10.4 Zero-Copy and Kernel-Registered Buffers

`io_uring` registered buffers, Windows registered I/O, and `sendfile`-style kernel-mediated transfers are beyond the scope of a buffer descriptor vocabulary. The vocabulary in this paper is compatible with them - a registered buffer's address and size satisfy `mutable_buffer` - but the registration mechanism is platform-specific and lives in the platform layer of the series (Paper 9 onward).

### 10.5 Multidimensional Layout

`std::mdspan`<sup>[9]</sup> describes multidimensional indexed access with layout policies. A buffer descriptor describes one byte region. The two solve different problems. This paper does not address layout, strides, or multidimensional indexing.

---

## 11. Why Now

The committee has had this vocabulary in front of it before.

| Year | Paper                                                                                          | Outcome                                             |
| ---- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| 2005 | [N1925](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2005/n1925.pdf)<sup>[17]</sup>      | First networking proposal for TR2                   |
| 2018 | [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup>       | Networking TS draft with these buffer types         |
| 2022 | [P0592R5](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2022/p0592r5.html)<sup>[18]</sup> | Committee priorities revisited                      |
| 2026 | [P4100R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf)<sup>[4]</sup>  | Network Endeavor frames the buffer paper as Paper 4 |

The vocabulary in this paper has been deployed for over twenty years in [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html)<sup>[3]</sup>. It is in the Networking TS<sup>[2]</sup>. It is in [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> today. It is the vocabulary every C++ I/O system already speaks.

**The standard library is the place that does not have it.**

---

## 12. Closing

```cpp
namespace std::io {

  class const_buffer;
  class mutable_buffer;

  template<class T> concept ConstBufferSequence;
  template<class T> concept MutableBufferSequence;

  inline constexpr /* unspecified */ buffer_size;
  inline constexpr /* unspecified */ buffer_empty;
  inline constexpr /* unspecified */ buffer_length;
  inline constexpr /* unspecified */ buffer_copy;

  template<class T> concept DynamicBuffer;

}
```

We built this. It works. We are reporting what we found.

---

## Appendix A. `<std::io>` Synopsis (Informative)

```cpp
namespace std::io {

  // 3.1 Byte-region vocabulary
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

  // 4.1 Sequence concepts
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

  // 5 Algorithms (customization point objects)
  inline constexpr /* unspecified */ buffer_size;     // sum of bytes
  inline constexpr /* unspecified */ buffer_empty;    // bool
  inline constexpr /* unspecified */ buffer_length;   // element count
  inline constexpr /* unspecified */ buffer_copy;     // bytes copied

  // 6 Dynamic buffers
  template<class T>
  concept DynamicBuffer =
      requires(T& t, T const& ct, std::size_t n) {
          typename T::const_buffers_type;
          typename T::mutable_buffers_type;
          { ct.size()     } -> std::convertible_to<std::size_t>;
          { ct.max_size() } -> std::convertible_to<std::size_t>;
          { ct.capacity() } -> std::convertible_to<std::size_t>;
          { ct.data()     } -> std::same_as<typename T::const_buffers_type>;
          { t.prepare(n)  } -> std::same_as<typename T::mutable_buffers_type>;
          t.commit(n);
          t.consume(n);
      } &&
      ConstBufferSequence<typename T::const_buffers_type> &&
      MutableBufferSequence<typename T::mutable_buffers_type>;

}
```

---

## Appendix B. Capy Header Inventory

The vocabulary in this paper ships in the following headers in [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup>. The list is a pointer to the implementation for the reader who wants to inspect it.

| Header                                            | Provides                                                                                  |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `boost/capy/buffers.hpp`                          | `const_buffer`, `mutable_buffer`, `ConstBufferSequence`, `MutableBufferSequence`, `buffer_size`, `buffer_empty`, `buffer_length` |
| `boost/capy/buffers/buffer_copy.hpp`              | `buffer_copy`                                                                             |
| `boost/capy/buffers/buffer_pair.hpp`              | `const_buffer_pair`, `mutable_buffer_pair`                                                |
| `boost/capy/buffers/buffer_array.hpp`             | `buffer_array<N, IsConst>` (informative)                                                  |
| `boost/capy/buffers/buffer_param.hpp`             | `buffer_param<BS>` (informative; deferred to Paper 5)                                     |
| `boost/capy/concept/dynamic_buffer.hpp`           | `DynamicBuffer`                                                                           |
| `boost/capy/buffers/flat_dynamic_buffer.hpp`      | `flat_dynamic_buffer` (informative)                                                       |
| `boost/capy/buffers/circular_dynamic_buffer.hpp`  | `circular_dynamic_buffer` (informative)                                                   |
| `boost/capy/buffers/vector_dynamic_buffer.hpp`    | `vector_dynamic_buffer` (informative)                                                     |
| `boost/capy/buffers/string_dynamic_buffer.hpp`    | `basic_string_dynamic_buffer`, `string_dynamic_buffer` (informative)                      |

Total: under one thousand five hundred lines of header for the buffer vocabulary plus four shipping `DynamicBuffer` implementations.

---

## Acknowledgments

Christopher Kohlhoff designed the Asio buffer types, the `ConstBufferSequence` and `MutableBufferSequence` named requirements, and the `DynamicBuffer` named requirement that this paper recovers as a C++20 concept. Twenty years of production deployment in Asio<sup>[3]</sup> is the foundation this work builds on.

The Networking TS authors codified the operational semantics of the buffer vocabulary in [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup>. The shapes in this paper are the shapes they specified.

Neil MacIntosh's [P0298R3](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2017/p0298r3.pdf) "A byte type definition"<sup>[19]</sup> established the precedent that motivates the bespoke types: when a generic type performs double duty - byte addressing, arithmetic, character handling - the committee adds a distinct type so that the type system can express the distinction. `std::byte` was the precedent. `mutable_buffer` and `const_buffer` follow it.

---

## References

[1] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[2] [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf) - "Working Draft, C++ Extensions for Networking" (Jonathan Wakely, 2018).

[3] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - Buffer types and buffer sequence requirements (Christopher Kohlhoff, 2003-2026).

[4] [P4100R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r0.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[5] [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) - "`std::execution`" (Micha&lstrok; Dominiak, Georgy Evtushenko, Lewis Baker, Lucian Radu Teodorescu, Lee Howes, Kirk Shoop, Michael Garland, Eric Niebler, Bryce Adelstein Lelbach, 2024).

[6] [P4036R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4036r0.pdf) - "Why Span Is Not Enough" (Vinnie Falco, 2026).

[7] [Boost.Beast](https://github.com/boostorg/beast) - HTTP and WebSocket built on Boost.Asio (Vinnie Falco, 2017-2026).

[8] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[9] [C++ Working Draft](https://eel.is/c++draft/) - `<ranges>`, `<span>`, `<mdspan>`, `<vector>`.

[10] [P4003R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r1.pdf) - "A Minimal Coroutine Execution Model" (Vinnie Falco, Steve Gerbino, Mungo Gill, 2026).

[11] [The Single UNIX Specification, Version 4](https://pubs.opengroup.org/onlinepubs/9699919799/) - `readv`, `writev` (The Open Group, 2018).

[12] [.NET API: System.Buffers.ReadOnlySequence&lt;T&gt;](https://learn.microsoft.com/en-us/dotnet/api/system.buffers.readonlysequence-1) - Linked sequence of `Memory<T>` segments (Microsoft, 2018-2026).

[13] [POSIX `<sys/uio.h>`](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/sys_uio.h.html) - `struct iovec` (The Open Group, 2018).

[14] [`WSABUF` structure](https://learn.microsoft.com/en-us/windows/win32/api/winsock2/ns-winsock2-wsabuf) - Windows Sockets buffer descriptor (Microsoft, 1996-2026).

[15] [libuv](https://docs.libuv.org/en/v1.x/) - `uv_buf_t` buffer type (libuv contributors, 2012-2026).

[16] [Go standard library: `net.Buffers`](https://pkg.go.dev/net#Buffers) - Scatter/gather over `[][]byte` (The Go Authors, 2012-2026).

[17] [N1925](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2005/n1925.pdf) - "Networking proposal for TR2 (rev. 1)" (Gerhard Wesp, 2005).

[18] [P0592R5](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2022/p0592r5.html) - "To boldly suggest an overall plan for C++23" (Ville Voutilainen, 2022).

[19] [P0298R3](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2017/p0298r3.pdf) - "A byte type definition" (Neil MacIntosh, Botond Ballo, 2017).
