---
title: "Dynamic Buffer"
document: D0009R0
date: 2026-05-15
intent: ask
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

This paper asks the committee to advance the `DynamicBuffer` concept - a growable byte buffer with two-phase write and two-phase read semantics - as standard library vocabulary.

The concept is the [Networking TS](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup> `DynamicBuffer` named requirement, recovered as a C++20 concept, deployed for over twenty years in [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html)<sup>[3]</sup>, with four shipping implementations in [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup>.

The companion paper *Dynamic Buffer: Design Rationale*<sup>[7]</sup> provides the design rationale, the four-implementation tour, the convergence record across three ecosystems, anticipated objections, and the deferrals. Read this paper for the proposal; read the companion when you need the audit trail.

This paper is Paper 5 in the series defined by [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[4]</sup>. It depends on Paper 4 (the buffer-ranges concepts) - the dynamic buffer's associated typedefs satisfy `ConstBufferSequence` and `MutableBufferSequence`, defined in *I/O Buffer Ranges*<sup>[8]</sup> and *I/O Buffer Ranges: Design Rationale*<sup>[9]</sup>.

---

## Revision History

### R0: May 2026 (post-Brno mailing)

* Initial Version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author maintains [Boost.Beast](https://github.com/boostorg/beast)<sup>[5]</sup> and develops [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[6]</sup>, plus three further Boost libraries that consume dynamic buffers for protocol parsing. The body of work creates a bias toward dedicated dynamic-buffer concepts.

This paper is the proposal-only ask paper for the `DynamicBuffer` concept. The design rationale, the four-implementation tour, and the convergence record live in the companion *Dynamic Buffer: Design Rationale*<sup>[7]</sup>. The byte-region descriptors and sequence concepts the dynamic buffer's associated types satisfy live in *I/O Buffer Ranges*<sup>[8]</sup> and *I/O Buffer Ranges: Design Rationale*<sup>[9]</sup>.

---

## 2. What This Paper Asks

The committee is asked to advance the following concept for the standard library:

```cpp
namespace std::io {

  template<class T> concept DynamicBuffer = /* see Section 3 */;

}
```

One concept. Two associated typedefs. Seven operations.

---

## 3. The Concept

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

`ConstBufferSequence` and `MutableBufferSequence` are defined in *I/O Buffer Ranges*<sup>[8]</sup>. The dynamic buffer's `const_buffers_type` and `mutable_buffers_type` must satisfy them.

---

## 4. Required Associated Types

`const_buffers_type` is what `data()` returns. `mutable_buffers_type` is what `prepare(n)` returns. They are member typedefs because the concrete sequence type depends on the buffer.

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
    using const_buffers_type   = std::array<const_buffer, 2>;
    using mutable_buffers_type = std::array<mutable_buffer, 2>;
    // ...
};
```

A flat buffer returns a single `const_buffer`. A circular buffer returns a `std::array<const_buffer, 2>` because the readable region may wrap. Generic algorithms write `typename T::const_buffers_type` and the right shape arrives.

---

## 5. Operation Semantics

### 5.1 `prepare`

```cpp
// t.prepare(n) -> mutable_buffers_type
//
// Effects: returns a buffer sequence representing at least n bytes
// of writable space. The returned region begins after the last
// committed byte. The same writable region remains valid until the
// next call to prepare, commit, consume, or destruction.
//
// Throws: an implementation-defined exception type if the buffer
// cannot grow to at least size() + n bytes.
```

### 5.2 `commit`

```cpp
// t.commit(n)
//
// Effects: makes the first n bytes of the most recent prepare call's
// writable region readable through data(). After commit, size()
// increases by n; capacity() decreases by n; the readable region
// extends by n bytes at the end.
//
// Preconditions: n is at most the size of the most recent prepare
// call's returned region.
```

### 5.3 `data`

```cpp
// ct.data() -> const_buffers_type
//
// Effects: returns a buffer sequence representing the readable bytes.
// The returned sequence remains valid until the next call to prepare,
// commit, consume, or destruction.
```

### 5.4 `consume`

```cpp
// t.consume(n)
//
// Effects: discards the first n readable bytes from the front of the
// readable region. After consume, size() decreases by min(n, size()).
// Whether the discarded space is reused for future prepare calls or
// released is unspecified.
```

### 5.5 `size`, `max_size`, `capacity`

```cpp
// ct.size()     -> the readable byte count
// ct.max_size() -> the largest the buffer can grow to (size + capacity bound)
// ct.capacity() -> the writable space available without reallocation
```

---

## 6. Suggested Straw Poll

> LEWG agrees that the `DynamicBuffer` concept documented in this paper and its companion *Dynamic Buffer: Design Rationale* should be advanced as standard library vocabulary for growable byte buffers used in I/O.

---

## Acknowledgments

Christopher Kohlhoff designed the Asio `DynamicBuffer` named requirement that this paper recovers as a C++20 concept.

The Networking TS authors codified the operational semantics in [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[2]</sup>.

The .NET runtime team's `IBufferWriter<T>`<sup>[10]</sup> and `ReadOnlySequence<T>`<sup>[11]</sup> informed the producer/consumer-split rationale recorded in *Dynamic Buffer: Design Rationale*<sup>[7]</sup>.

---

## References

[1] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[2] [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf) - "Working Draft, C++ Extensions for Networking" (Jonathan Wakely, 2018).

[3] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - `DynamicBuffer` named requirement (Christopher Kohlhoff, 2003-2026).

[4] [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[5] [Boost.Beast](https://github.com/boostorg/beast) - HTTP and WebSocket built on Boost.Asio (Vinnie Falco, 2017-2026).

[6] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[7] *Dynamic Buffer: Design Rationale* (Vinnie Falco, 2026). Companion design paper. D0010R0.

[8] *I/O Buffer Ranges* (Vinnie Falco, 2026). Companion ask paper for the byte-region vocabulary. D0007R0.

[9] *I/O Buffer Ranges: Design Rationale* (Vinnie Falco, 2026). Companion design paper for the byte-region vocabulary. D0008R0.

[10] [.NET API: System.Buffers.IBufferWriter&lt;T&gt;](https://learn.microsoft.com/en-us/dotnet/api/system.buffers.ibufferwriter-1) - Producer interface for incremental writes (Microsoft, 2018-2026).

[11] [.NET API: System.Buffers.ReadOnlySequence&lt;T&gt;](https://learn.microsoft.com/en-us/dotnet/api/system.buffers.readonlysequence-1) - Consumer-side linked sequence of `Memory<T>` segments (Microsoft, 2018-2026).
