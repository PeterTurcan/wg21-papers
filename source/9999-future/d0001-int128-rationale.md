---
title: "The Case for std::int128_t"
document: D0001R0
date: 2026-04-29
intent: info
audience: EWG, SG22
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

Every major 64-bit compiler ships `__int128_t`. One will not implement it without a standard. The standard does not have it.

This paper documents the evidence for standardizing `std::int128_t` and `std::uint128_t` as extended integer types in `<cstdint>`. [D0000R0] contains the proposed wording. This paper is the design record: why the type belongs in the standard, what alternatives were considered, and where the evidence lives. Read D0000R0 for specification text; read this paper for the audit trail.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author is a Boost maintainer and is not a compiler vendor. [P3666R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3666r3.html)<sup>[1]</sup> ("Bit-precise integers," Jan Schultke) proposes a complementary general solution for arbitrary-width integers by adopting C23's `_BitInt(N)`. P3666 provides three genuine achievements: C compatibility for all bit-precise widths, a natural optionality mechanism via `BITINT_MAXWIDTH`, and alias templates `std::bit_int<N>` and `std::bit_uint<N>` that integrate into the C++ type system. This paper does not compete with P3666.

This paper does not solve arbitrary-width integers. It does not address C23 `_BitInt` compatibility. It documents the case for one type at one width.

This paper asks for nothing.

---

## 2. The Type That Already Exists

GCC, Clang, and ICC have provided `__int128_t` and `unsigned __int128_t` as compiler extensions on 64-bit targets for over two decades.

| Codebase | Usage | Alignment dependency |
|---|---|---|
| Abseil | `absl::uint128` / `absl::int128` delegate to `__int128`; used across Google infrastructure<sup>[2]</sup> | CMPXCHG16B requires 16-byte |
| Linux kernel | BPF IPv6, BTF type encoding, `math64.h` wide multiply; gated behind `CONFIG_ARCH_SUPPORTS_INT128`<sup>[3]</sup> | BTF encodes `__int128` as distinct kind |
| LLVM | Internal compiler use; had to change `_BitInt(N)` IR representation because the two types cannot share ABI rules<sup>[4]</sup> | Distinct calling conventions |
| Folly | FarmHash, `Conv.cpp` string conversion, hash infrastructure | Fallback to `pair<uint64_t, uint64_t>` without `__int128` |
| Rust | Spent 2024-2025 fixing `i128` alignment to match `__int128`; docs state `i128` is not necessarily compatible with `_BitInt(128)`<sup>[5]</sup> | 16-byte alignment on x86-64 |

MSVC does not provide `__int128_t`. Microsoft's position is explicit:

> "We draw a distinction between supporting Standard features and non-Standard extensions... Adding a non-Standard extension to `make_unsigned` recognizing `__int128` is therefore out of scope for our project." - Stephan T. Lavavej<sup>[6]</sup>

> "I am not aware of any plans to do so in the absence of a Standard requirement." - MSVC STL team<sup>[7]</sup>

Microsoft built a library shim instead: `_Signed128` and `_Unsigned128` in `<__msvc_int128.hpp>`, used internally for `<random>`.<sup>[8]</sup> These are not core language integral types. MSVC 19.38 also has no `_BitInt` support.<sup>[9]</sup>

The current standard already permits implementations to provide `__int128_t` as an optional extended integer type. Schultke observes:

> "It's an optional but standard feature already... think of it like `std::float32_t`."

Borland identifies the consequence:

> "We're basically in a situation where optional things are only provided by those who already offered it. Unhelpful." - Matt Borland

Dimov observes:

> "It's motivated by the feature actually existing. That's what standardization is supposed to be for. Not inventing things that don't exist."

> "MSFT frontend engineers refuse to implement it unless it's made standard."

**Every 64-bit compiler ships it. One will not implement it without a standard. The standard does not have it.**

---

## 3. The Width Progression

| Standard type | Minimum width | Exceeds native on |
|---|---|---|
| `int` | 16 bits | 8-bit architectures |
| `long` | 32 bits | 16-bit architectures |
| `long long` | 64 bits | 32-bit architectures |
| `int128_t` (proposed) | 128 bits | 64-bit architectures |

> "In fact 32 bit already exceeds the native width, that's why int is required to be 16 bit and 32 bits is called 'long'." - Dimov

> "It's a natural step, similarly to how we got a standard 64 bit type, even on 8 bit." - Dimov

Schultke observes:

> "At some point you just have to throw implementers under the bus and tell them to do it so that people can write portable code."

---

## 4. Two Types, One Width

`_BitInt(128)` and `__int128_t` are incompatible at every level:

| Property | `__int128_t` | `_BitInt(128)` |
|---|---|---|
| Itanium mangling | `n` (signed) / `o` (unsigned) | `DB128_` |
| Alignment (x86-64) | 16 bytes | 8 bytes |
| Integer promotion | implementation-defined | exempt by design |
| Type identity | distinct | distinct |
| Stack passing (x86-64) | 16-byte aligned | 8-byte aligned |

The Itanium C++ ABI assigned these manglings intentionally. Aaron Ballman filed the ABI issue to ensure they remain separate types.<sup>[10]</sup> The x86-64 psABI maintainer acknowledged the alignment divergence as a "wart" but considered it potentially too late to change.<sup>[11]</sup> The alignment difference means `#define __int128 _BitInt(128)` silently produces incorrect code when values are passed on the stack.<sup>[12]</sup>

LLVM confirmed the incompatibility at the compiler level. PR #91364 changed `_BitInt(N)` to use opaque byte arrays in IR because the two types cannot share ABI rules despite lowering to the same `i128`.<sup>[4]</sup>

Schultke suggested unification was possible:

> "Nothing is stopping the implementation from making `__int128_t` an alternative spelling for `_BitInt(128)`."

> "It's probably not a good idea, but hey, it could."

Dimov's rebuttal:

> "The semantics of `_BitInt(128)` are incompatible with `__int128_t`."

> "You can tell the difference in C++."

**Adopting `_BitInt` does not retire `__int128_t`. It creates a second 128-bit integer type.**

---

## 5. The Specification Surface

| Metric | `int128_t` (extended integer) | `_BitInt(N)` (P3666R3) |
|---|---|---|
| Core clauses modified | 0 | 10 |
| Library clauses modified | 7 | 15 |
| Pages of normative diff | ~3 | ~25-30 |
| Post-adoption defect fixes (C23) | 0 | 5 |
| Areas deferred from MVP | 0 | 5 |
| `_Generic` expressiveness gap | N/A | open (N3695 pending) |
| C2y papers still in flight | 0 | 3+ |

The 128-bit types are extended integer types. [basic.fundamental] already permits them. [conv.rank] already ranks them. `numeric_limits`, `make_signed`, `make_unsigned`, `to_chars`, `from_chars`, and `format` already handle extended integer types without wording changes.<sup>[13]</sup> The work is entirely in the library: `[cstdint.syn]`, `[cinttypes.syn]`, `[version.syn]`, `[template.bitset]`, `[string.conversions]`, `[cmath.syn]`, `[atomics.syn]`.

P3666R3 modifies 10 core language clauses (`[lex.icon]`, `[basic.fundamental]`, `[conv.rank]`, `[conv.prom]`, `[dcl.type.general]`, `[dcl.type.simple]`, `[dcl.enum]`, `[temp.deduct.general]`, `[temp.deduct.type]`, `[cpp.predefined]`) and 15 library clauses.<sup>[1]</sup> R3 deferred five areas from the minimum viable product: `std::atomic`, `std::simd`, `<random>`, `<stdckdint.h>`, and `utility.intcmp`.

C23's `_BitInt` required five post-adoption defect fixes ([N2960](https://www.open-std.org/JTC1/SC22/WG14/www/docs/n2960.pdf)<sup>[14]</sup> / N3035):

1. **Promotion ambiguity** (6.3.1.1p2) - unclear whether `_BitInt(16)` promotes to `int`; N2960 inserts "if the original type is not a bit-precise integer type"
2. **Prefix increment forced conversion** (6.5.3.1) - `++x` on `_BitInt(128)` implied conversion through `int` via the literal `1`
3. **`intmax_t` impossibility** (7.20.1.5p1) - no fixed-width `intmax_t` can represent `_BitInt(BITINT_MAXWIDTH)`; N2960 exempts bit-precise types
4. **`<stdint.h>` typedef constraint** - incomplete list of types prohibited from being bit-precise
5. **Enum compatibility prohibition** - `_BitInt` could serve as enum compatible type, interacting badly with promotion rules

The `_BitInt` specification continues to evolve in C2y. At the February/March 2026 WG14 meeting alone, three papers were voted in or are pending: [N3747](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3747.pdf)<sup>[15]</sup> (integer type taxonomy reorganization, accepted), [N3705](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3705.htm)<sup>[16]</sup> (bit-precise enum, accepted), and [N3695](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3695.htm)<sup>[17]</sup> (strict `_Generic` matching for `_BitInt`, pending).

**Zero core language changes. Seven library clauses. Three pages of diff.**

---

## 6. The Alignment Question

### 16-Byte Alignment (current `__int128_t`)

| Provides | Costs |
|---|---|
| SSE register alignment; SIMD codegen needs no fallback | 15 bytes padding in structs with small members |
| CMPXCHG16B works by default | |
| No cache-line straddling on 64-byte lines | |
| `memcpy`/`memset` select widest instruction | |
| Abseil, kernel, Folly depend on this alignment | |

> "Unaligned accesses that straddle a cache line are a problem on x86." - Dimov

### 8-Byte Alignment (current `_BitInt(128)` on Clang)

| Provides | Costs |
|---|---|
| Compact structs; user adds `alignas(16)` when needed | Cache-line straddling on x86-64 |
| | CMPXCHG16B requires manual `alignas` at every use site |
| | Rust spent 2024-2025 fixing `i128` to match `__int128` alignment<sup>[5]</sup> |

Schultke observes that arithmetic does not benefit from 16-byte alignment:

> "Despite being aligned to 16 bytes, `__int128` loads compile to 2x 64-bit access for any kind of arithmetic since the instructions work on register pairs."

Dimov observes:

> "That's a matter of taste. Others consider the 16 byte alignment a feature."

The 16-byte column has five entries. The 8-byte column has one.

---

## 7. The Freestanding Question

Schultke reports:

> "Freestanding should not mandate 128-bit; it would be unreasonable to require multiprecision on every microcontroller."

Dimov:

> "128 bit is not multiprecision. It's double the previous max width."

The standard already mandates `int` (16-bit) on 8-bit targets, `long` (32-bit) on 16-bit targets, `long long` (64-bit) on 32-bit targets. Each was once considered unreasonable.

Schultke:

> "Even int can exceed the native width on 8-bit, but at some point you just have to throw implementers under the bus and tell them to do it so that people can write portable code."

The proposed types are optional. A freestanding implementation that does not support 128-bit integers does not provide them.

---

## 8. Prior Art

Three prior attempts to standardize 128-bit integers:

| Paper | Approach | Outcome |
|---|---|---|
| [P0539R5](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p0539r5.html)<sup>[18]</sup> (2017-2019) | `wide_integer<Bits, S>` template | Stalled. Library type could not act like a fundamental type. |
| [P3140R1](https://eisenwave.github.io/cpp-proposals/int-least128.html)<sup>[13]</sup> (2024) | `int_least128_t` as extended integer | Withdrawn June 2025. Author pivoted to P3666. |
| [P3666R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3666r3.html)<sup>[1]</sup> (2025-2026) | C23 `_BitInt(N)` adoption | Active. EWG forwarded for C++29. LEWG needs-revision.<sup>[19]</sup> |

P3140R1 was withdrawn because its author concluded the problem is "worth solving more generally." The general solution is now before LEWG with 25 clauses of wording changes. The narrow solution - an extended integer type alias in `<cstdint>` - has never been tried.

[LWG 3828](https://timsong-cpp.github.io/lwg-issues/3828)<sup>[20]</sup>, adopted in C++23, removed the `intmax_t` blocker that historically prevented implementations from exposing `__int128` as a conforming extended integer type.<sup>[21]</sup> The path is clear.

---

## 9. The Timeline

> "If you have `_BitInt(128)`, why is a separate 128-bit type worth pursuing?" - Schultke

> "That's a good question. Do I?" - Dimov

> "Not yet." - Schultke

| Type | GCC | Clang | MSVC | Standard |
|---|---|---|---|---|
| `__int128_t` | 20+ years | 20+ years | never | not standardized |
| `_BitInt(128)` | GCC 14 (2024, 3 targets)<sup>[22]</sup> | yes | never<sup>[9]</sup> | C23 only |

> "In practice, do all compilers that have `__int128_t` also have `_BitInt(128)`?" - Dimov

> "Yes." - Schultke

> "MAXWIDTH being 64 is theoretical, then?" - Dimov

> "On 64-bit targets at least." - Schultke

Dimov identifies the open integration question:

> "The answer would require more research. I'm not quite sure how things stand with respect to the extended integer-ness of `_BitInt`, `numeric_limits`, etc. Whether it's useful as the difference type of `views::iota`."

C23 adopted `%w128d` and `%wf128d` format specifiers via [N2680](https://www.open-std.org/JTC1/SC22/WG14/www/docs/n2680.pdf)<sup>[23]</sup>, providing `printf` support for 128-bit types. SG22 reviewed [P3140R1](https://eisenwave.github.io/cpp-proposals/int-least128.html)<sup>[13]</sup> and found no C/C++ compatibility concerns. WG14 expressed interest in a corresponding C paper.<sup>[24]</sup>

**`__int128_t` has been deployed for 25 years. `_BitInt` has been specified for 3 and is still accumulating fixes.**

---

## 10. Both Proposals Serve

P3666 provides arbitrary-width integers and C23 compatibility. `int128_t` provides the one width that 25 years of practice has demonstrated is needed. The `_BitInt` specification is still evolving - three C2y papers at the most recent WG14 meeting, LEWG revisions pending on the C++ side. `int128_t` can ship while `_BitInt` matures.

The two proposals are not mutually exclusive. `_BitInt(128)` and `__int128_t` coexist today in every compiler that implements both. They have distinct manglings. They have distinct alignment. They would continue to coexist after both are standardized.

Schultke himself observes:

> "`int128_t` vs nothing is a slam dunk."

> "It's effectively raising the BITINT_MAXWIDTH anyway so we would get both forms of 128-bit integers, and that's fine."

Dimov:

> "You don't need to 'hack it into the language' because it's already there."

> "That's exactly what the concept of extended integer type is for."

> "And what is there for us to do in that area is to add it to `stdint.h`."

Schultke:

> "`__int128` is already in the standard as an extended integer type."

> "Providing the `int128_t` alias for `__int128` is permitted and optional."

Dimov:

> "What's the issue of standardizing `std::int128_t`, then?"

**The general solution and the specific solution are not competitors. They are companions with different delivery dates.**

---

## Acknowledgements

**Peter Dimov** identified the MSVC deployment constraint, the `_BitInt(128)` / `__int128_t` type incompatibility, the width progression argument, and the extended-integer-type framing. The technical backbone of this paper originates in an exchange between Dimov and Schultke on the WG21 community channel.

**Jan Schultke** is the author of [P3666R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3666r3.html)<sup>[1]</sup> and [P3140R1](https://eisenwave.github.io/cpp-proposals/int-least128.html)<sup>[13]</sup>. P3140R1's section-by-section wording analysis is the model for D0000R0's proposed wording. Schultke's detailed responses to Dimov's questions provided the technical evidence on EWG telecon feedback, freestanding constraints, alignment tradeoffs, and implementation status that this paper documents.

---

## References

[1] [P3666R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3666r3.html) - "Bit-precise integers" (Jan Schultke, 2026).

[2] [abseil-cpp/int128.h](https://github.com/abseil/abseil-cpp/blob/master/absl/numeric/int128.h) - Abseil 128-bit integer implementation (Google).

[3] [Linux kernel commit b1e8818](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b1e8818cabf407a5a2cec696411b0bdfd7fd12f0) - `__int128` support in BPF/BTF.

[4] [LLVM PR #91364](https://github.com/llvm/llvm-project/pull/91364) - `_BitInt(N)` IR representation change for ABI separation from `__int128`.

[5] [Rust i128 Layout Update](https://blog.rust-lang.org/2024/03/30/i128-layout-update.html) - "Layout of Primitives: i128/u128" (Rust Blog, 2024).

[6] [microsoft/STL #411](https://github.com/microsoft/STL/issues/411) - Feature request for `__int128` type traits support (closed, wontfix).

[7] [microsoft/STL #5354](https://github.com/microsoft/STL/issues/5354) - Request for 128-bit integer type traits.

[8] [microsoft/STL PR #3036](https://github.com/microsoft/STL/pull/3036) - Library-level `_Signed128` / `_Unsigned128` workaround.

[9] [P3639R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3639r0.html) - "The _BitInt Debate" (2025).

[10] [itanium-cxx-abi #128](https://github.com/itanium-cxx-abi/cxx-abi/issues/128) - Mangling for `_BitInt` types (Aaron Ballman, 2021).

[11] [x86-64 psABI #11](https://gitlab.com/x86-psABIs/x86-64-ABI/-/issues/11) - `_BitInt(128)` alignment divergence from `__int128`.

[12] [x86-64 ABI mailing list](https://groups.google.com/g/x86-64-abi/c/-JeR9HgUU20) - `_BitInt(128)` / `__int128` stack passing incompatibility.

[13] [P3140R1](https://eisenwave.github.io/cpp-proposals/int-least128.html) - "`std::int_least128_t`" (Jan Schultke, 2024).

[14] [N2960](https://www.open-std.org/JTC1/SC22/WG14/www/docs/n2960.pdf) - "_BitInt Fixes" (WG14, 2022).

[15] [N3747](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3747.pdf) - "Integer Sets, v5" (Robert Seacord, 2025). Accepted into C2y working draft.

[16] [N3705](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3705.htm) - "Bit-precise enum" (Jan Krause, 2025). Accepted into C2y working draft.

[17] [N3695](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3695.htm) - "Strict Compatibility for Translation-Time Type Matching Improvements" (JeanHeyd Meneide, 2026). Pending.

[18] [P0539R5](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p0539r5.html) - "A Proposal to add wide_integer" (Boris Rasin, 2019).

[19] [cplusplus/papers #2420](https://github.com/cplusplus/papers/issues/2420) - P3666 committee tracking (LEWG needs-revision, March 2026).

[20] [LWG 3828](https://timsong-cpp.github.io/lwg-issues/3828) - "`intmax_t` / `uintmax_t` should not mandate widest type" (adopted C++23, Issaquah 2023).

[21] [is-int128-integral](https://quuxplusone.github.io/blog/2019/02/28/is-int128-integral/) - "Is `__int128` an integral type?" (Arthur O'Dwyer, 2019).

[22] [GCC 14 Release Notes](https://gcc.gnu.org/gcc-14/changes.html) - `_BitInt` support on IA-32, x86-64, and AArch64.

[23] [N2680](https://www.open-std.org/JTC1/SC22/WG14/www/docs/n2680.pdf) - "Specific-width length modifier" (Robert Seacord, 2021). Adds `%wNd` to C23.

[24] [SG22 compatibility issue #39](https://github.com/sg22-c-cpp-standard-compatibility/sg-compatibility/issues/39) - SG22 review of P3140, WG14 interest noted.
