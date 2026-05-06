---
title: "Is `std::execution` a Universal Async Model?"
document: P4041R0
date: 2026-05-01
intent: info
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

C++20 standardized coroutines. C++26 adds `std::execution`. Both are asynchronous models. The question is whether the C++26 model subsumes the C++20 model, or whether they serve different domains. This paper collects publicly available evidence.

---

## Revision History

### R0: May 2026 (pre-Brno mailing)

* Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author developed and maintains [Capy](https://github.com/cppalliance/capy) and [Corosio](https://github.com/cppalliance/corosio) and believes coroutine-native I/O is a practical foundation for networking in C++.

Coroutine-native I/O and `std::execution` are complementary. Each serves the domain where its design choices pay off.

This paper examines the published record. That effort requires re-examining consequential papers, including papers written by people the author respects.

The author developed [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf)<sup>[1]</sup> ("A Minimal Coroutine Execution Model"), [P4007R3](https://isocpp.org/files/papers/P4007R3.pdf)<sup>[2]</sup> ("Open Issues in `std::execution::task`"), [P4014R2](https://isocpp.org/files/papers/P4014R2.pdf)<sup>[3]</sup> ("The Sender Sub-Language For Beginners"), and [P2583R4](https://isocpp.org/files/papers/P2583R4.pdf)<sup>[4]</sup> ("Symmetric Transfer and Sender Composition"). A coroutine-only design cannot express compile-time work graphs, does not support heterogeneous dispatch, and assumes cooperative scheduling. This paper does not cite those libraries or P4003R3 as evidence for any claim. They are disclosed as context for the author's perspective.

This paper asks for nothing.

---

## 2. Two Standard Async Models

C++20 standardized coroutines ([P0912R5](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p0912r5.html)<sup>[5]</sup>, [P0913R1](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0913r1.html)<sup>[6]</sup>). They are ISO C++.

C++26 adds `std::execution` ([P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)<sup>[7]</sup>, "std::execution"). Schedulers, senders, receivers, and composable algorithms for asynchronous computation.

Both are standard facilities. Both are async models. The question is the relationship between them.

Eric Niebler wrote in ["Structured Concurrency"](https://ericniebler.com/2020/11/08/structured-concurrency/)<sup>[45]</sup> (2020):

> *"I think that 90% of all async code in the future should be coroutines simply for maintainability."*

Niebler wrote in ["What Are Senders Good For, Anyway?"](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/)<sup>[46]</sup> (2024):

> *"If your library exposes asynchrony, then returning a sender is a great choice: your users can await the sender in a coroutine if they like."*

The framework's architect placed 90% of async code in the coroutine column.

---

## 3. What `std::execution` Does Well

`std::execution` provides zero-allocation sender pipelines for compile-time work graphs. The `connect`/`start` protocol collapses a sender chain into a single operation state with no heap allocation and no virtual dispatch. Domain customization allows a CUDA scheduler to customize `bulk` to emit a kernel launch instead of a loop. Type-level completion signatures enable compile-time routing without runtime inspection. NVIDIA's CUDA compiler does not support C++20 coroutines in device code<sup>[57]</sup>; [stdexec](https://github.com/NVIDIA/stdexec)<sup>[48]</sup> - the reference implementation - was built at NVIDIA.

Herb Sutter [reported](https://herbsutter.com/2025/04/23/living-in-the-future-using-c26-at-work)<sup>[47]</sup> that Citadel Securities uses `std::execution` in production: *"We already use C++26's `std::execution` in production for an entire asset class, and as the foundation of our new messaging infrastructure."*

---

## 4. The Post-Adoption Record

[P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)<sup>[7]</sup> was adopted into the C++26 working draft at St. Louis in July 2024. The following is our attempt at a complete enumeration of post-adoption changes, compiled from published WG21 mailings<sup>[58]</sup>, the LWG issues list<sup>[59]</sup>, and the C++26 NB ballot repository<sup>[60]</sup>.

### 4.1 Changes by Category

| Category            | Papers / Issues                                                                                                                                                                                                                                                      | Count |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------:|
| Removals            | [P3682R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3682r0.pdf)<sup>[8]</sup>, [P3149R11](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3149r11.html)<sup>[9]</sup> (replacing `ensure_started`)                                                                                                                            |     2 |
| Rewrites            | [P3481R5](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3481r5.html)<sup>[10]</sup> (`bulk`)                                                                                                                                                                                                        |     1 |
| Architectural fixes | [P3887R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3887r1.pdf)<sup>[11]</sup>, [P3557R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3557r3.html)<sup>[12]</sup>                                                                                                                                                            |     2 |
| Wording omnibus     | [P3396R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3396r1.html)<sup>[13]</sup>                                                                                                                                                                                                                 |     1 |
| Post-adoption adds  | [P3433R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3433r1.pdf)<sup>[14]</sup>, [P3284R4](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3284r4.html)<sup>[15]</sup>, [P3570R2](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3570r2.html)<sup>[16]</sup>, [P3552R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3552r3.html)<sup>[17]</sup>, [P2079R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p2079r10.html)<sup>[18]</sup>, [P3149R11](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3149r11.html)<sup>[9]</sup>, [P3927R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3927r0.html)<sup>[19]</sup> |     7 |
| LWG defects         | [4190](https://cplusplus.github.io/LWG/issue4190)<sup>[36]</sup>, [4206](https://cplusplus.github.io/LWG/issue4206)<sup>[37]</sup>, [4215](https://cplusplus.github.io/LWG/issue4215)<sup>[38]</sup>, [4356](https://cplusplus.github.io/LWG/issue4356)<sup>[39]</sup>, [4368](https://cplusplus.github.io/LWG/issue4368)<sup>[40]</sup> |     5 |
| NB ballot           | [US 255-384](https://github.com/cplusplus/nbballot/issues/959)<sup>[41]</sup>, [US 253-386](https://github.com/cplusplus/nbballot/issues/961)<sup>[42]</sup>, [US 254-385](https://github.com/cplusplus/nbballot/issues/960)<sup>[43]</sup>, [US 261-391](https://github.com/cplusplus/nbballot/issues/966)<sup>[44]</sup> |     4 |

### 4.2 Direction of Change

Every post-adoption item falls into one of three categories.

| Origin              | Items                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Count |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----: |
| Sender Sub-Language | [P2855R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2855r1.html), [P2999R3](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p2999r3.html), [P3175R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3175r3.html), [P3187R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3187r1.pdf), [P3303R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3303r1.html), [P3373R2](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3373r2.pdf), [P3557R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3557r3.html), [P3570R2](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3570r2.html), [P3682R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3682r0.pdf), [P3718R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3718r0.html), [P3826R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3826r3.html), [P3941R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3941r1.html), LWG 4190, 4206, 4215, 4368 |    16 |
| Sender Integration  | [P3927R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3927r0.html), [P3950R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3950r0.pdf), [D3980R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3980r0.html)<sup>[20]</sup>, LWG 4356, US 255-384, US 253-386, US 254-385, US 261-391                                                                                                                                                                                                                                                                                                          |     8 |
| Coroutine-Intrinsic | -                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |     0 |

**Twenty-four post-adoption items modified the sender sub-language or its integration. Zero modified coroutines.**

---

## 5. Published Findings

Dietmar K&uuml;hl catalogued sixteen open concerns with `task` in [P3796R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3796r1.html)<sup>[21]</sup> ("Coroutine Task Issues," 2025). On symmetric transfer:

> *"The specification doesn't mention any use of symmetric transfer."*

K&uuml;hl reworked the allocator model in [D3980R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3980r0.html)<sup>[20]</sup> (2026-01-25) - six months after [P3552R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3552r3.html)<sup>[17]</sup>'s adoption at Sofia.

Jonathan M&uuml;ller identified a stack overflow vulnerability in [P3801R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3801r0.html)<sup>[22]</sup> ("Concerns about the design of std::execution::task," 2025):

> *"Having iterative code that is actually recursive is a potential security vulnerability."*

M&uuml;ller confirmed the cause:

> *"The reason `co_yield` is used, is that a coroutine promise can only specify `return_void` or `return_value`, but not both. If we want to allow `co_return;`, we cannot have `co_return with_error(error_code);`. This is unfortunate, but could be fixed by changing the language to drop that restriction."*

Robert Leahy proposed a core language change in [P3950R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3950r0.pdf)<sup>[23]</sup> (2025):

> *"Disallowing it either disadvantages coroutines vis-a-vis `std::execution` or necessitates library workarounds."*

Chris Kohlhoff identified the partial success tension in [P2430R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2430r0.pdf)<sup>[24]</sup> ("Partial success scenarios with P2300," 2021):

> *"Due to the limitations of the `set_error` channel (which has a single 'error' argument) and `set_done` channel (which takes no arguments), partial results must be communicated down the `set_value` channel."*

---

## 6. Structural Observations

These are not design defects. They are tradeoffs the sender model makes for compile-time work graphs. The question is whether those tradeoffs should also bind I/O.

| Boundary           | Sender Model Requires                    | Coroutine/I/O Cost                                                |
| ------------------ | ---------------------------------------- | ----------------------------------------------------------------- |
| Error channels     | Compile-time channel routing             | `(error_code, size_t)` cannot route through three channels        |
| Error returns      | Separate `set_error` channel             | `co_yield with_error(ec);` reverses established `co_yield` semantics |
| Frame allocator    | Deferred execution via `connect`/`start` | `promise_type::operator new` fires before sender machinery        |
| Symmetric transfer | Struct composition with void completions | `coroutine_handle<>`-returning `await_suspend` unreachable        |

Both [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)<sup>[7]</sup> bridges - `sender-awaitable` and `connect-awaitable` - use `void await_suspend`.

**Senders get the allocator they do not need. Coroutines need the frame allocator they do not get.**

### 6.1 The Error Channel Timeline

| Date                          | Event                                                                                                                         |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| February 2020 (Prague)        | Partial success raised during [P1678R2](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p1678r2.pdf)<sup>[25]</sup> review. LEWG polls SF:7/F:14/N:9/A:3/SA:0. No resolution. |
| February 2021 (SG4 telecon)   | Participant states sender/receivers have a loss: no success/partial-success.                                                   |
| July-October 2021 (LEWG)      | Debated across five telecons. LEWG outcome document: *"Better explain how partial success works with senders/receivers."*      |
| August 2021                   | Kohlhoff publishes [P2430R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2430r0.pdf)<sup>[24]</sup>.                                                       |
| 2022-2024                     | Six revisions through [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)<sup>[7]</sup>. Three-channel model unchanged. |
| 2023                          | K&uuml;hl's [P2762R2](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p2762r2.pdf)<sup>[26]</sup> preserves Asio's `(error_code, size_t)` convention.          |
| November 2023 (Kona)          | SG4 polls that networking must use the sender model (SF:5/F:5/N:1/A:0/SA:1).                                                 |
| November 2024 (Wroclaw)       | Channel question resurfaces during P0260 (Concurrent Queues). Debated across two face-to-face meetings.                       |
| February 2025 (Hagenberg)     | Concurrent queue channel question remained open. Poll to reopen withdrawn.                                                    |
| 2025-2026                     | [P3570R2](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3570r2.html)<sup>[16]</sup> documents `optional<T>` / channel model mismatch.                        |

---

## 7. Established Practice

| Library                                                           | Symmetric Transfer   | Error Delivery            | Async Model      |
| ----------------------------------------------------------------- | -------------------- | ------------------------- | ---------------- |
| [cppcoro](https://github.com/lewissbaker/cppcoro)<sup>[49]</sup> (Baker)      | `coroutine_handle<>` | `co_return` / exceptions  | Coroutine-native |
| [folly::coro](https://github.com/facebook/folly/tree/main/folly/coro)<sup>[50]</sup> (Meta)  | `coroutine_handle<>` | Exceptions                | Coroutine-native |
| [Boost.Cobalt](https://github.com/boostorg/cobalt)<sup>[51]</sup> (Morgenstern) | `coroutine_handle<>` | `co_return` / exceptions  | Coroutine-native |
| [libcoro](https://github.com/jbaldwin/libcoro)<sup>[52]</sup> (Baldwin)       | `coroutine_handle<>` | `co_return` / exceptions  | Coroutine-native |
| Boost.Asio (Kohlhoff)                                             | N/A                  | Error codes via `as_tuple` | Completion-token |
| [asyncpp](https://github.com/petiaccja/asyncpp)<sup>[53]</sup> (Kardos)       | Event-based          | `co_return` / exceptions  | Coroutine-native |

SG14 (February 2026 mailing): *"SG14 advise that Networking (SG4) should not be built on top of P2300. The allocation patterns required by P2300 are incompatible with low-latency networking requirements."*

**Six independent libraries converged on `coroutine_handle<>`-returning `await_suspend`. The standard uses `void`.**

---

## 8. Ecosystem Adoption

The sender/receiver model has been public since [P2300R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2300r0.html)<sup>[61]</sup> (2021). [stdexec](https://github.com/NVIDIA/stdexec)<sup>[48]</sup> has existed as a reference implementation throughout. These results may not be exhaustive; additions are welcome.

| Domain                | Project                                                                                     | Status                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| TCP networking        | [senders-io](https://github.com/maikel/senders-io)<sup>[54]</sup>                          | 19 stars. "Still very experimental." Requires non-main stdexec branch.   |
| HTTP                  | [fuchsia](https://github.com/ColdOrange/fuchsia)<sup>[55]</sup>                            | 2 stars, 0 forks. Last commit August 2023.                               |
| TLS                   | (none found)                                                                                 |                                                                          |
| File I/O              | [senders-io](https://github.com/maikel/senders-io)<sup>[54]</sup>                          | Experimental. Documentation sections empty.                              |
| Database clients      | (none found)                                                                                 |                                                                          |
| DNS resolution        | (none found)                                                                                 |                                                                          |
| Signal handling       | (none found)                                                                                 |                                                                          |
| Bare metal / embedded | [Intel cpp-baremetal-senders-and-receivers](https://github.com/intel/cpp-baremetal-senders-and-receivers)<sup>[56]</sup> | 288 stars. P2300 subset. "Coroutines are not considered at all."          |
| GPU / heterogeneous   | [stdexec](https://github.com/NVIDIA/stdexec)<sup>[48]</sup>                                | 1,300+ stars. Reference implementation. Active.                          |
| HFT / low-latency     | (reported, proprietary)                                                                      | Cannot be independently verified.                                        |

Rub&eacute;n P&eacute;rez Hidalgo, author of [Boost.MySQL](https://github.com/boostorg/mysql)<sup>[62]</sup>, offered this assessment:

> *"This whole S/R thing is as if someone had seen Asio and said 'too simple'."*

**The reference implementation has 1,300 stars. The I/O ecosystem built on it has 21.**

Ben FrantzDale, who [called](https://benfrantzdale.github.io/blog/2024/10/01/sender-intuition-senders-dont-send.html)<sup>[63]</sup> P2300 "amazing promise," also wrote:

> *"I've been keeping an eye on the P2300 'Senders' proposal for generic asynchrony for many years, but felt like I never quite 'got' it. I know I'm not the only one who has found it challenging to grok... if you step into implementations, you quickly find yourself in a sea of underscores, namespaces, and customization-point objects."*

Sean Baxter, author of the Circle compiler, [reported](https://github.com/NVIDIA/stdexec/issues/856)<sup>[64]</sup> that swapping the order of a single constraint in the `sender` concept caused Clang to produce an error message so long (5,500 lines) that it triggered an internal compiler error.

Rainer Grimm, author of *Modernes C++*, [abandoned](https://www.modernescpp.com/index.php/stdexecution/)<sup>[65]</sup> his planned C++26 library coverage: *"The implementation status of the library is not good enough. Therefore, I decided to continue with concurrency and `std::execution`. I will present the remaining C++26 features if a compiler implements them."*

---

## 9. Open Question

The domains where sender-based I/O could be publicly verified show no production implementations. The domains where deployment is reported are proprietary.

---

## Acknowledgments

The author thanks Dietmar K&uuml;hl, Jonathan M&uuml;ller, Chris Kohlhoff,
Eric Niebler, and Lewis Baker for their published observations cited in
this paper.

---

## References

### WG21 Papers

[1] [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf) - "A Minimal Coroutine Execution Model" (Vinnie Falco, Steve Gerbino, Mungo Gill, 2026).

[2] [P4007R3](https://isocpp.org/files/papers/P4007R3.pdf) - "Open Issues in `std::execution::task`" (Vinnie Falco, Mungo Gill, 2026).

[3] [P4014R2](https://isocpp.org/files/papers/P4014R2.pdf) - "The Sender Sub-Language For Beginners" (Vinnie Falco, Mungo Gill, 2026).

[4] [P2583R4](https://isocpp.org/files/papers/P2583R4.pdf) - "Symmetric Transfer and Sender Composition" (Mungo Gill, Vinnie Falco, 2026).

[5] [P0912R5](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p0912r5.html) - "Merge Coroutines TS into C++20 working draft" (Gor Nishanov, 2018).

[6] [P0913R1](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0913r1.html) - "Add symmetric coroutine control transfer" (Gor Nishanov, 2018).

[7] [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) - "std::execution" (Micha&lstrok; Dominiak, Georgy Evtushenko, Lewis Baker, Lucian Radu Teodorescu, Lee Howes, Kirk Shoop, Michael Garland, Eric Niebler, Bryce Adelstein Lelbach, 2024).

[8] [P3682R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3682r0.pdf) - "Remove std::execution::split" (Robert Leahy, 2025).

[9] [P3149R11](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3149r11.html) - "async_scope &mdash; Creating scopes for non-sequential concurrency" (Ian Petersen, Jessica Wong, Kirk Shoop, et al., 2025).

[10] [P3481R5](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3481r5.html) - "std::execution::bulk() issues" (Eric Niebler, 2025).

[11] [P3887R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3887r1.pdf) - "Make when_all a Ronseal Algorithm" (Lewis Baker, 2025).

[12] [P3557R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3557r3.html) - "High-Quality Sender Diagnostics with Constexpr Exceptions" (Eric Niebler, 2025).

[13] [P3396R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3396r1.html) - "std::execution wording fixes" (Eric Niebler, 2025).

[14] [P3433R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3433r1.pdf) - "Allocator Support for Operation States" (Eric Niebler, 2025).

[15] [P3284R4](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3284r4.html) - "`write_env` and `unstoppable` Sender Adaptors" (Eric Niebler, 2025).

[16] [P3570R2](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3570r2.html) - "Optional variants in sender/receiver" (Fabio Fracassi, 2025).

[17] [P3552R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3552r3.html) - "Add a Coroutine Task Type" (Dietmar K&uuml;hl, Maikel Nadolski, 2025).

[18] [P2079R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p2079r10.html) - "System execution context" (Lee Howes, 2025).

[19] [P3927R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3927r0.html) - "task_scheduler Support for Parallel Bulk Execution" (Lee Howes, 2026).

[20] [D3980R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3980r0.html) - "Task's Allocator Use" (Dietmar K&uuml;hl, 2026).

[21] [P3796R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3796r1.html) - "Coroutine Task Issues" (Dietmar K&uuml;hl, 2025).

[22] [P3801R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3801r0.html) - "Concerns about the design of std::execution::task" (Jonathan M&uuml;ller, 2025).

[23] [P3950R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3950r0.pdf) - "return_value & return_void Are Not Mutually Exclusive" (Robert Leahy, 2025).

[24] [P2430R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2430r0.pdf) - "Partial success scenarios with P2300" (Chris Kohlhoff, 2021).

[25] [P1678R2](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p1678r2.pdf) - "Callbacks and Composition" (Kirk Shoop, 2020).

[26] [P2762R2](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p2762r2.pdf) - "Sender/Receiver Interface For Networking" (Dietmar K&uuml;hl, 2023).

[27] [P2855R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2855r1.html) - "Member customization points for Senders and Receivers" (Ville Voutilainen, 2024).

[28] [P2999R3](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/p2999r3.html) - "Sender Algorithm Customization" (Eric Niebler, 2024).

[29] [P3175R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3175r3.html) - "Reconsidering the std::execution::on algorithm" (Eric Niebler, 2024).

[30] [P3187R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3187r1.pdf) - "Remove ensure_started and start_detached from P2300" (Kirk Shoop, Lewis Baker, 2024).

[31] [P3303R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3303r1.html) - "Fixing Lazy Sender Algorithm Customization" (Eric Niebler, 2024).

[32] [P3373R2](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3373r2.pdf) - "Of Operation States and Their Lifetimes" (Robert Leahy, 2025).

[33] [P3718R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3718r0.html) - "Fixing Lazy Sender Algorithm Customization, Again" (Eric Niebler, 2025).

[34] [P3826R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3826r3.html) - "Fix Sender Algorithm Customization" (Eric Niebler, 2026).

[35] [P3941R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p3941r1.html) - "Scheduler Affinity" (Dietmar K&uuml;hl, 2026).

### LWG Issues

[36] [LWG 4190](https://cplusplus.github.io/LWG/issue4190) - "completion-signatures-for specification is recursive."

[37] [LWG 4206](https://cplusplus.github.io/LWG/issue4206) - "connect_result_t should be constrained with sender_to."

[38] [LWG 4215](https://cplusplus.github.io/LWG/issue4215) - "run_loop::finish should be noexcept."

[39] [LWG 4356](https://cplusplus.github.io/LWG/issue4356) - "connect() should use get_allocator(get_env(rcvr))."

[40] [LWG 4368](https://cplusplus.github.io/LWG/issue4368) - "Potential dangling reference from transform_sender."

### NB Ballot Comments

[41] [US 255-384](https://github.com/cplusplus/nbballot/issues/959).

[42] [US 253-386](https://github.com/cplusplus/nbballot/issues/961).

[43] [US 254-385](https://github.com/cplusplus/nbballot/issues/960).

[44] [US 261-391](https://github.com/cplusplus/nbballot/issues/966).

### Blog Posts

[45] Eric Niebler, ["Structured Concurrency"](https://ericniebler.com/2020/11/08/structured-concurrency/) (November 2020).

[46] Eric Niebler, ["What Are Senders Good For, Anyway?"](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) (February 2024).

[47] Herb Sutter, ["Living in the future: Using C++26 at work"](https://herbsutter.com/2025/04/23/living-in-the-future-using-c26-at-work) (April 2025).

### Libraries

[48] [stdexec](https://github.com/NVIDIA/stdexec) - NVIDIA reference implementation of std::execution (1,300+ stars).

[49] [cppcoro](https://github.com/lewissbaker/cppcoro) - C++ coroutine abstractions (Lewis Baker).

[50] [folly::coro](https://github.com/facebook/folly/tree/main/folly/coro) - Facebook coroutine library.

[51] [Boost.Cobalt](https://github.com/boostorg/cobalt) - Coroutine task types for Boost (Klemens Morgenstern).

[52] [libcoro](https://github.com/jbaldwin/libcoro) - C++20 coroutine library (Josh Baldwin).

[53] [asyncpp](https://github.com/petiaccja/asyncpp) - Async coroutine library (P&eacute;ter Kardos).

[54] [senders-io](https://github.com/maikel/senders-io) - Sender/receiver adaptation for async I/O (19 stars, "still very experimental").

[55] [fuchsia](https://github.com/ColdOrange/fuchsia) - Experimental async networking on stdexec (2 stars, last commit August 2023).

[56] [Intel cpp-baremetal-senders-and-receivers](https://github.com/intel/cpp-baremetal-senders-and-receivers) - P2300 subset for embedded (288 stars, "coroutines are not considered at all").

### Platform Documentation

[57] [NVIDIA CUDA Programming Guide, Section 5.3](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/cpp-language-support.html) - "C++ Language Support." Coroutines not listed for device code compilation.

### Other

[58] [WG21 paper mailings](https://open-std.org/jtc1/sc22/wg21/docs/papers/) - ISO C++ committee papers.

[59] [LWG issues list](https://cplusplus.github.io/LWG/lwg-toc.html) - Library Working Group active issues.

[60] [C++26 NB ballot comments](https://github.com/cplusplus/nbballot) - National body comments repository.

[61] [P2300R0](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2300r0.html) - "std::execution" (Eric Niebler, Kirk Shoop, Lewis Baker, Lee Howes, 2021).

[62] [Boost.MySQL](https://github.com/boostorg/mysql) - Async MySQL client library for Boost (Rub&eacute;n P&eacute;rez).

[63] [Sender Intuition: Senders Don't Send](https://benfrantzdale.github.io/blog/2024/10/01/sender-intuition-senders-dont-send.html) - Ben FrantzDale, Oct 2024.

[64] [NVIDIA/stdexec issue #856: sender concept has side effects, is order-dependent](https://github.com/NVIDIA/stdexec/issues/856) - Sean Baxter, March 2023.

[65] [std::execution - MC++ BLOG](https://www.modernescpp.com/index.php/stdexecution/) - Rainer Grimm, Nov 2024.
