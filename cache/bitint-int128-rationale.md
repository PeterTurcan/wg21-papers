# Design Rationale: 128-Bit Integer Standardization

## Context

This document captures the design space and trade-offs for standardizing 128-bit integer support in C++. The central question is which vehicle the standard should use to provide portable 128-bit integers: a standalone `std::int128_t` that codifies existing compiler extensions, or the adoption of C23's `_BitInt(N)` as a new family of fundamental types. The analysis applies to five interrelated design decisions:

1. Which standardization vehicle to pursue.
2. How to resolve the type incompatibility between `_BitInt(128)` and `__int128_t`.
3. Whether 16-byte or 8-byte alignment is the correct default.
4. Whether 128-bit integers should be mandatory or optional on freestanding targets.
5. How to balance deployment urgency against specification generality.

The positions were articulated in an April 2026 exchange between Peter Dimov and Jan Schultke on the WG21 community channel. Dimov argues for codifying existing practice:

> "It's motivated by the feature actually existing. That's what standardization is supposed to be for. Not inventing things that don't exist."

Schultke, the author of P3666 (*Bit-precise integers*), argues for adopting the general C23 mechanism. The relevant papers are P3666R3 (C++ `_BitInt` adoption), P0989R0 (standalone `int128_t`, stalled), and N2763 (WG14 `_BitInt` specification).

## Current Landscape

### `__int128_t`

GCC, Clang, and ICC have provided `__int128_t` as a compiler extension on 64-bit targets for over two decades. The type is absent from MSVC. Microsoft's position is explicit. STL maintainer Stephan T. Lavavej closed the feature request with:

> "We draw a distinction between supporting Standard features and non-Standard extensions... Adding a non-Standard extension to `make_unsigned` recognizing `__int128` is therefore out of scope for our project." ([microsoft/STL #411](https://github.com/microsoft/STL/issues/411))

A subsequent request received the same answer:

> "I am not aware of any plans to do so in the absence of a Standard requirement." ([microsoft/STL #5354](https://github.com/microsoft/STL/issues/5354))

Microsoft built a library-level workaround instead: `_Signed128` and `_Unsigned128` in `<__msvc_int128.hpp>`, used internally for Lemire's fast integer generation in `<random>` ([microsoft/STL PR #3036](https://github.com/microsoft/STL/pull/3036)). These are not core language integral types.

### `_BitInt(N)`

`_BitInt(N)` was standardized in C23 via [N2763](https://open-std.org/JTC1/SC22/WG14/www/docs/n2763.pdf). Jan Schultke's P3666R3 proposes adopting it into C++ with alias templates `std::bit_int<N>` and `std::bit_uint<N>`. At the March 2026 Croydon meeting, EWG polled 17-29-3-2-0 (strong consensus) to forward P3666R3 to CWG and LEWG for C++29. LEWG reviewed the paper at the same meeting and returned it as "needs-revision" ([cplusplus/papers #2420](https://github.com/cplusplus/papers/issues/2420)).

MSVC 19.38 has no `_BitInt` support. GCC has not shipped `_BitInt(128)`. Clang is the only compiler with production `_BitInt` support ([P3639R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3639r0.html)).

## Background

### The Width Progression

The C++ standard has mandated integer types exceeding native width at every step of the progression. `int` is required to be at least 16 bits, which exceeds the native width on 8-bit architectures. `long` is required to be at least 32 bits, exceeding the native width on 16-bit architectures. `long long` is required to be at least 64 bits, exceeding the native width on 32-bit architectures. 128 bits is the natural next doubling.

> "In fact 32 bit already exceeds the native width, that's why int is required to be 16 bit and 32 bits is called 'long'." - Dimov

> "It's a natural step, similarly to how we got a standard 64 bit type, even on 8 bit." - Dimov

Schultke conceded the underlying principle:

> "At some point you just have to throw implementers under the bus and tell them to do it so that people can write portable code." - Schultke

### Production Dependencies

`__int128_t` has deep production dependencies across major codebases:

- **Abseil.** `absl::uint128` and `absl::int128` delegate to the compiler's `__int128` when `ABSL_HAVE_INTRINSIC_INT128` is defined. The type is used across Google's infrastructure. CMPXCHG16B requires 16-byte alignment ([abseil-cpp/int128.h](https://github.com/abseil/abseil-cpp/blob/master/absl/numeric/int128.h)).

- **Linux kernel.** `__int128` is gated behind `CONFIG_ARCH_SUPPORTS_INT128` (x86-64, arm64). It is used in BPF programs for IPv6 address representation, in BTF (BPF Type Format) for vmlinux type information, and in `include/linux/math64.h` for wide multiplication and division. BTF encodes `__int128` as a distinct integer kind ([kernel commit](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=b1e8818cabf407a5a2cec696411b0bdfd7fd12f0)).

- **LLVM.** The compiler infrastructure itself had to change `_BitInt(N)` to use opaque byte arrays (`[M x i8]`) in IR memory representation specifically because `_BitInt(128)` and `__int128` lower to the same LLVM `i128` but have different alignment and calling convention rules ([LLVM PR #91364](https://github.com/llvm/llvm-project/pull/91364)).

- **Folly.** Facebook's Folly library uses `unsigned __int128` in FarmHash, string conversion (`Conv.cpp`), and throughout its hash infrastructure, with a fallback to `pair<uint64_t, uint64_t>` when `__int128` is unavailable.

- **Rust.** The Rust project spent 2024-2025 fixing `i128`/`u128` alignment to match C's `__int128` across x86, PowerPC, SPARC, and MIPS. The Rust documentation explicitly notes that `i128` is not necessarily compatible with `_BitInt(128)` ([Rust blog](https://blog.rust-lang.org/2024/03/30/i128-layout-update.html)).

## The Standardization Vehicle Question

### Option S1: Standalone `std::int128_t`

**Arguments for:**

1. **Codifies existing practice.** `__int128_t` has been available on GCC, Clang, and ICC for over two decades on 64-bit targets. The production code that depends on it (Abseil, Linux kernel, Folly, Boost, LLVM) constitutes the strongest possible motivation for standardization.

   > "Wasn't the fact that `__int128_t` already exists enough of a justification?" - Dimov

2. **Immediately unblocks MSVC.** Microsoft's STL and compiler teams have stated they will not implement 128-bit integer support without a standard mandate. Dimov reports a specific deployment constraint:

   > "MSFT frontend engineers refuse to implement it unless it's made standard." - Dimov

3. **Simple specification surface.** A fixed-width integer type with known semantics is analogous to `int64_t`. The specification is a type alias and a set of `<cstdint>` entries, not a new type system.

   > "I'd have (naively) thought that `std::int128_t` would have been a slam dunk." - Dimov

4. **Does not create a parallel type.** Standardizing `__int128_t` as `std::int128_t` retires the non-standard spelling. Existing code migrates by changing the type name. No ABI break. No struct layout change.

**Arguments against:**

1. **Committee reception.** Schultke reports persistent pushback:

   > "You would have to justify why you're trying to standardize a feature that is not motivated by a C feature but is doing an entirely separate thing, and you'd constantly have to defend the proposal against the criticism of 'why don't you solve it more generally? what about 256 bits?'" - Schultke

2. **C23 compatibility.** A standalone `int128_t` does not address the existence of `_BitInt(N)` in C23. C++ code calling C functions that use `_BitInt` parameters would still need a separate mechanism.

3. **Optional-type mechanics.** If 128-bit must be optional on freestanding targets, the optionality mechanism needs specification regardless of which vehicle is chosen.

   > "There was also the early feedback during EWG telecon IIRC that freestanding should not mandate 128-bit." - Schultke

### Option S2: `_BitInt(N)` from C23

**Arguments for:**

1. **C compatibility.** `_BitInt(N)` is already standardized in C23. Adopting it in C++ would allow calling C functions with `_BitInt` parameters without a separate interop mechanism.

2. **General solution.** A single mechanism covers 128-bit, 256-bit, and arbitrary widths. There is no need for separate proposals for each width.

3. **Natural optionality.** `BITINT_MAXWIDTH` provides a built-in mechanism for implementations to declare the maximum supported width.

   > "If it's going to be an optional type anyway, then you may as well say that you standardize `_BitInt` with a low `BITINT_MAXWIDTH` like C; that is effectively making the feature optional which nicely aligns with what implementers request." - Schultke

**Arguments against:**

1. **Incompatible with existing practice.** `_BitInt(128)` and `__int128_t` are distinct types with distinct ABI in every compiler that implements both. The Itanium C++ ABI assigns `__int128` the mangling `n` (signed) / `o` (unsigned) and `_BitInt(128)` the mangling `DB128_`. Aaron Ballman filed the ABI issue specifically to ensure they remain separate types ([itanium-cxx-abi #128](https://github.com/itanium-cxx-abi/cxx-abi/issues/128)).

   > "The semantics of `_BitInt(128)` are incompatible with `__int128_t`." - Dimov

2. **Does not retire `__int128_t`.** Adopting `_BitInt` creates a parallel 128-bit integer type. Every codebase that uses `__int128_t` today would need to maintain both types or migrate with ABI-breaking struct layout changes due to the alignment difference.

3. **Massive specification surface.** P3666R3's wording changes span approximately 30 pages of standard diff, touching integer conversion rank, integer promotions, usual arithmetic conversions, `_Generic`, `va_arg`, `_Atomic`, `make_signed`/`make_unsigned`, enumeration underlying types, and bit-fields. R3 removed `std::simd` and `std::atomic` support from the minimum viable product to reduce scope. By contrast, `int128_t` is a fixed-width alias.

4. **Post-adoption defects.** C23's `_BitInt` required [N2960](https://open-std.org/JTC1/SC22/WG14/www/docs/n2960.pdf) to fix four specification defects: ambiguous integer promotion wording, prefix increment/decrement causing unintended type conversion, an impossible requirement that `intmax_t` be large enough to hold any `_BitInt` width, and a clarification that `stdint.h` types must not be bit-precise types.

5. **Conversion rank subtleties.** The original N2646 draft used "precision" for `_BitInt` conversion rank, which created inconsistent results where `unsigned _BitInt(16)` could outrank `short`. N2763 switched to "width" to ensure standard types always outrank bit-precise types at equal bit count ([Stack Overflow analysis](https://stackoverflow.com/questions/79379789/conversion-rank-of-bit-precise-integers)). This complexity does not arise for a simple `int128_t` typedef.

6. **`_Generic` expressiveness gap.** There is no way to write a `_Generic` association matching `_BitInt(N)` for arbitrary N without enumerating every width from 2 to `BITINT_MAXWIDTH`. [N3441](https://open-std.org/JTC1/SC22/WG14/www/docs/n3441.htm) proposes a fix for C2y; it does not exist in C23.

7. **No existing C++ practice.** MSVC has no `_BitInt` support. GCC has not shipped `_BitInt(128)`. Clang is the only compiler with production support.

8. **LEWG sent it back.** P3666R3 was reviewed at the Croydon meeting in March 2026 and marked "needs-revision" by LEWG ([cplusplus/papers #2420](https://github.com/cplusplus/papers/issues/2420)).

## The Type Compatibility Question

`_BitInt(128)` and `__int128_t` are incompatible at every level:

- **Type identity.** They are distinct types. Overloading on both in the same translation unit is valid.

- **Mangling.** The Itanium ABI mangles `__int128` as `n`/`o` and `_BitInt(128)` as `DB128_`. These manglings are intentional and permanent ([itanium-cxx-abi #128](https://github.com/itanium-cxx-abi/cxx-abi/issues/128)).

- **Alignment.** `__int128` has 16-byte alignment on x86-64. `_BitInt(128)` has 8-byte alignment on Clang x86-64. The x86-64 psABI maintainer acknowledged this divergence as a "wart" but considered it potentially too late to change since compilers already implement the 2021 specification. AArch64 plans to unify the alignment; x86-64 does not ([x86-64 psABI #11](https://gitlab.com/x86-psABIs/x86-64-ABI/-/issues/11)).

- **Stack passing.** The alignment difference means `#define __int128 _BitInt(128)` silently produces incorrect code approximately 10% of the time when values are passed on the stack ([x86-64 ABI mailing list](https://groups.google.com/g/x86-64-abi/c/-JeR9HgUU20)).

- **Promotion rules.** `_BitInt` types are exempt from default integer promotions by design. `__int128_t` participates in implementation-defined promotion behavior.

Schultke suggested unification was possible:

> "Nothing is stopping the implementation from making `__int128_t` an alternative spelling for `_BitInt(128)`." - Schultke

> "It's probably not a good idea, but hey, it could." - Schultke

Dimov's rebuttal was immediate:

> "The semantics of `_BitInt(128)` are incompatible with `__int128_t`." - Dimov

> "You can tell the difference in C++." - Dimov

LLVM's own implementation confirms the incompatibility. PR #91364 changed `_BitInt(N)` to use opaque byte arrays in IR specifically because the two types cannot share ABI rules despite lowering to the same `i128` at the register level ([LLVM PR #91364](https://github.com/llvm/llvm-project/pull/91364)).

## The Alignment Question

### Option A1: 16-Byte Alignment (current `__int128_t`)

**Arguments for:**

1. **SSE register alignment.** 16-byte alignment matches the natural alignment of SSE registers. SIMD codegen does not require fallback paths for unaligned access.

2. **Atomic operations.** CMPXCHG16B on x86-64 requires 16-byte alignment. Code using 128-bit atomics gets correct alignment by default without `alignas`.

3. **Cache-line safety.** 16-byte-aligned 128-bit values never straddle a cache-line boundary on architectures with 64-byte cache lines.

   > "Unaligned accesses that straddle a cache line are a problem on x86." - Dimov

4. **Wide instruction selection.** `memcpy` and `memset` can unconditionally select the widest instruction for aligned data.

5. **Existing ecosystem.** Abseil, the Linux kernel, and Folly all depend on 16-byte alignment for `__int128` values.

   > "That's a matter of taste. Others consider the 16 byte alignment a feature." - Dimov

**Arguments against:**

1. **Struct padding.** A struct containing `__int128` and a `bool` wastes 15 bytes of padding.

   > "It really sucks when you want to make a struct containing it, plus a bool or something and now you eat 15 bytes of padding." - Schultke

2. **Arithmetic does not benefit.** 128-bit loads compile to two 64-bit register accesses regardless of alignment.

   > "Despite being aligned to 16 bytes, `__int128` loads compile to 2x 64-bit access for any kind of arithmetic since the instructions work on register pairs." - Schultke

### Option A2: 8-Byte Alignment (current `_BitInt(128)` on Clang)

**Arguments for:**

1. **Compact structs.** Users who need 16-byte alignment can apply `alignas(16)` explicitly.

   > "Whereas `alignas(16)` gives you the choice." - Schultke

**Arguments against:**

1. **Cache-line straddling.** 8-byte-aligned 128-bit values may straddle cache-line boundaries on x86-64, incurring a performance penalty.

2. **Atomic operations require manual alignment.** Every use of 128-bit atomics must add `alignas(16)`, an error-prone obligation that the 16-byte default avoids.

3. **Cross-language FFI regression.** Rust spent 2024-2025 fixing `i128` alignment to match `__int128`'s 16-byte alignment. If C++ standardizes only `_BitInt(128)` with 8-byte alignment, Rust's interop work is partially invalidated ([Rust blog](https://blog.rust-lang.org/2024/03/30/i128-layout-update.html)).

## The Freestanding Question

Schultke reported EWG feedback:

> "Freestanding should not mandate 128-bit; it would be unreasonable to require multiprecision on every microcontroller." - Schultke

Dimov challenged the "multiprecision" framing:

> "128 bit is not multiprecision. It's double the previous max width." - Dimov

The standard already mandates types exceeding native width at every level of the progression. `int` (16-bit minimum) on 8-bit targets. `long` (32-bit minimum) on 16-bit targets. `long long` (64-bit minimum) on 32-bit targets. Each addition was once considered unreasonable for small targets and is now taken for granted.

Schultke conceded the principle:

> "Even int can exceed the native width on 8-bit, but at some point you just have to throw implementers under the bus and tell them to do it so that people can write portable code." - Schultke

This concession is the argument for `int128_t`. Making it optional via the same mechanism as other optional fixed-width types (`int64_t` on platforms without 64-bit support) resolves the freestanding concern without requiring the full `_BitInt` specification machinery.

## The Practical Urgency Question

The exchange concluded with a sharp exchange about deployment reality:

> "If you have `_BitInt(128)`, why is a separate 128-bit type worth pursuing?" - Schultke

> "That's a good question. Do I?" - Dimov

> "Not yet." - Schultke

Neither `_BitInt(128)` nor `__int128_t` exists in the C++ standard. Neither exists on MSVC. The difference is in existing practice: `__int128_t` is available on every 64-bit compiler except MSVC and has 25 years of production code depending on it. `_BitInt(128)` is available on Clang only; GCC has not shipped it.

Standardizing the type with existing practice would immediately unblock MSVC with a simple specification. Standardizing the type without existing practice defers unblocking until a 30-page specification completes committee review, a process that LEWG has already sent back for revision.

Dimov pressed the practical overlap:

> "In practice, do all compilers that have `__int128_t` also have `_BitInt(128)`?" - Dimov

> "Yes." - Schultke

> "MAXWIDTH being 64 is theoretical, then?" - Dimov

> "On 64-bit targets at least." - Schultke

The open question Dimov identified at the thread's close is whether `_BitInt(128)` is actually usable as a drop-in for `__int128_t` in generic library code:

> "The answer would require more research. I'm not quite sure how things stand with respect to the extended integer-ness of `_BitInt`, `numeric_limits`, etc. Whether it's useful as the difference type of `views::iota`." - Dimov

## Areas of Agreement

1. `__int128_t` exists, is useful, and has deep production dependencies across major codebases including Abseil, the Linux kernel, LLVM, and Folly.

2. `int128_t` vs. nothing is, in Schultke's words, "a slam dunk."

3. The C++ standard already mandates integer types that exceed the native width on small targets at every level of the width progression.

4. MSVC will not implement 128-bit integer support without a standard mandate.

5. `_BitInt(128)` and `__int128_t` are incompatible types. Both participants acknowledge the semantic, mangling, and alignment differences.

6. On 64-bit targets, every compiler that provides `__int128_t` also provides `_BitInt(128)` in practice.

## Areas of Disagreement

1. Whether `_BitInt(128)` makes a standalone `int128_t` unnecessary, given the type incompatibility and ABI divergence between the two 128-bit integer types.

2. Whether the 30-page specification surface of `_BitInt` is justified by the marginal utility of arbitrary-width integers over `int128_t` alone.

3. Whether 16-byte alignment is a feature (atomics, SIMD, cache-line safety, existing ecosystem) or a mistake (struct padding waste).

4. Whether process viability (committee reception) should drive the choice of standardization vehicle, or whether existing practice should.

5. Whether `numeric_limits`, `views::iota` difference type, and other library integration for `_BitInt(128)` are sufficiently specified for production use.

## Summary

| Question | Option A | Option B | Key differentiator |
|---|---|---|---|
| Standardization vehicle | `std::int128_t` (codify practice) | `_BitInt(N)` (adopt from C23) | 25 years of practice vs. 30 pages of new specification |
| Type compatibility | `int128_t` retires `__int128_t` | `_BitInt(128)` creates parallel type | Itanium ABI: distinct manglings, no unification path |
| Alignment | 16-byte (current `__int128`) | 8-byte (current `_BitInt(128)`) | Atomics/SIMD require 16; struct packing prefers 8 |
| Freestanding | Optional `int128_t` | Optional via `BITINT_MAXWIDTH` | Same outcome, different mechanism |
| Deployment timeline | Immediate (simple spec) | Deferred (LEWG needs-revision) | MSVC blocked until one of them ships |
