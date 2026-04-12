---
title: "Info: Open Issues in `std::execution::task`"
document: P4007R1
date: 2026-04-08
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
  - "Mungo Gill <mungo.gill@me.com>"
audience: LEWG
---

## Abstract

`std::execution::task` ([P3552R3](https://wg21.link/p3552r3)<sup>[1]</sup>) had open issues identified by national ballot comments, LWG issues, and published papers. Croydon resolved several. This paper classifies each issue by whether it can be resolved after C++26 ships or whether shipping forecloses the fix, and notes which classified issues were addressed at Croydon.

---

## Revision History

### R2: April 2026 (post-Croydon)

* Updated classification to reflect Croydon motions 28-29, 33, 35-38.
  Acknowledged issues resolved by P3941R4, P3927R2, P3980R1, and P4151R1.
  Rewrote allocator descriptions to credit P3980R1 while preserving
  residual frame-allocator concerns.

### R1: March 2026 (prior to Croydon meeting)

* Complete rewrite as an informational classification of open issues.

### R0: February 2026 (pre-Croydon mailing)

* Original analysis of structural gaps. See [P4007R0](https://wg21.link/p4007r0)<sup>[2]</sup>.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

Coroutine-native I/O and `std::execution` are complementary. Each serves the domain where its design choices pay off.

The authors developed [P4007R0](https://wg21.link/p4007r0)<sup>[2]</sup> ("Senders and Coroutines"). The classification below holds regardless of whether any alternative design exists.

This paper asks for nothing.

---

## 2. Fixed After Ship

`task`'s `promise_type` is a class template instantiated in user code. Its `operator new`, allocator selection, stop token storage, environment forwarding, and destruction ordering can change between standard revisions without binary incompatibility. These issues are fixable post-ship: [Unusual Allocator Customisation](https://wg21.link/p3796r1)<sup>[3]</sup>, [Flexible Allocator Position](https://wg21.link/p3796r1)<sup>[3]</sup>, [Shadowing The Environment Allocator](https://wg21.link/p3796r1)<sup>[3]</sup>, [Stop Source Always Created](https://wg21.link/p3796r1)<sup>[3]</sup>, [Stop Token Default Constructible](https://wg21.link/p3796r1)<sup>[3]</sup>, [Task Not Actually Lazily Started](https://wg21.link/p3796r1)<sup>[3]</sup>, [Frame Destroyed Too Late](https://wg21.link/p3796r1)<sup>[3]</sup>, [No Default Arguments](https://wg21.link/p3796r1)<sup>[3]</sup>, [`unhandled_stopped` Not `noexcept`](https://wg21.link/p3796r1)<sup>[3]</sup>, [Environment Design Inefficient](https://wg21.link/p3796r1)<sup>[3]</sup>, [Non-Sender Awaitables Unsupported](https://wg21.link/p3796r1)<sup>[3]</sup>, [Future Language Feature Could Avoid `co_yield`](https://wg21.link/p3796r1)<sup>[3]</sup>, [No TLS Capture/Restore Hook](https://wg21.link/p3796r1)<sup>[3]</sup>, [`return_value`/`return_void` Have No Specification](https://wg21.link/p3796r1)<sup>[3]</sup>, [`co_return { args... }` Unsupported](https://wg21.link/p3796r1)<sup>[3]</sup>, [`change_coroutine_scheduler` Requires Assignable Scheduler](https://wg21.link/p3796r1)<sup>[3]</sup>, [Sender-Unaware Coroutines Cannot `co_await` a `task`](https://wg21.link/p3796r1)<sup>[3]</sup>, [Missing Rvalue Qualification](https://wg21.link/p3796r1)<sup>[3]</sup>, [Parameter Lifetime Is Surprising](https://wg21.link/p3801r0)<sup>[4]</sup>, [No Protection Against Dangling References](https://wg21.link/p3801r0)<sup>[4]</sup>, [`co_yield with_error` Is Clunky](https://wg21.link/p3801r0)<sup>[4]</sup>, [`co_await schedule(sch)` Is an Expensive No-Op](https://wg21.link/p3801r0)<sup>[4]</sup>, [Coroutine Cancellation Is Ad-Hoc](https://wg21.link/p3801r0)<sup>[4]</sup>.

Of these, Croydon resolved six: Unusual Allocator Customisation, Flexible Allocator Position, and Shadowing The Environment Allocator were addressed by [P3980R1](https://wg21.link/p3980r1)<sup>[5]</sup>; `unhandled_stopped` Not `noexcept`, `change_coroutine_scheduler` Requires Assignable Scheduler (the mechanism was removed entirely), and Missing Rvalue Qualification were addressed by [P3941R4](https://wg21.link/p3941r4)<sup>[15]</sup>. The remaining issues are still open and fixable post-ship.

`affine` semantics (formerly `affine_on`, renamed by [P4151R1](https://wg21.link/p4151r1)<sup>[16]</sup>), rescheduling behavior, and algorithm customization are specification-level concerns. Tightening requirements or adding default implementations does not change any published interface. These issues are fixable post-ship: [`affine_on` Default Implementation Lacks Specification](https://wg21.link/p3796r1)<sup>[3]</sup>, [`affine_on` Semantics Not Clear](https://wg21.link/p3796r1)<sup>[3]</sup>, [`affine_on` Shape May Not Be Correct](https://wg21.link/p3796r1)<sup>[3]</sup>, [`affine_on` Shouldn't Forward Stop Requests](https://wg21.link/p3796r1)<sup>[3]</sup>, [`affine_on` Customisation For Other Senders](https://wg21.link/p3796r1)<sup>[3]</sup>, [Starting a `task` Reschedules Unconditionally](https://wg21.link/p3796r1)<sup>[3]</sup>, [Resuming After a `task` Reschedules Unnecessarily](https://wg21.link/p3796r1)<sup>[3]</sup>, [`bulk` vs. `task_scheduler`](https://wg21.link/p3796r1)<sup>[3]</sup>, [No Completion Scheduler](https://wg21.link/p3796r1)<sup>[3]</sup>, [`with_awaitable_senders` Unused](https://wg21.link/p3796r1)<sup>[3]</sup>.

Of these, Croydon resolved eight. [P3941R4](https://wg21.link/p3941r4)<sup>[15]</sup> rewrote scheduler affinity from scratch - `affine_on` was made unary, `change_coroutine_scheduler` removed, and `get_start_scheduler` introduced - resolving the five `affine_on`/`affine` items and both rescheduling items. [P4151R1](https://wg21.link/p4151r1)<sup>[16]</sup> renamed `affine_on` to `affine`. [P3927R2](https://wg21.link/p3927r2)<sup>[17]</sup> resolved `bulk` vs. `task_scheduler` by giving `task_scheduler` parallel bulk support. Two items remain open: No Completion Scheduler and `with_awaitable_senders` Unused.

---

## 3. Not Fixable Post-Ship

The issues in this section are items where shipping forecloses the fix.

| Issue                 | References                                                                                                                                                                                                                                                                  | Fixed |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----:|
| Allocator Timing      | [P3980R1](https://wg21.link/p3980r1)<sup>[5]</sup>, [P3796R1](https://wg21.link/p3796r1)<sup>[3]</sup>, [LWG 4356](https://cplusplus.github.io/LWG/issue4356)<sup>[6]</sup>, [US 254-385](https://github.com/cplusplus/nbballot/issues/960)<sup>[7]</sup> | partial |
| Allocator Propagation | [P3980R1](https://wg21.link/p3980r1)<sup>[5]</sup>, [P3796R1](https://wg21.link/p3796r1)<sup>[3]</sup>                                                                                                                                                  | partial |
| Error Return          | [P3950R0](https://wg21.link/p3950r0)<sup>[8]</sup>, [P3801R0](https://wg21.link/p3801r0)<sup>[4]</sup>, [P1713R0](https://wg21.link/p1713r0)<sup>[9]</sup>                                                                                                                | no    |
| Symmetric Transfer    | [P2583R3](https://isocpp.org/files/papers/P2583R3.pdf)<sup>[10]</sup>, [US 246-373](https://github.com/cplusplus/nbballot/issues/948)<sup>[11]</sup>, [LWG 4348](https://cplusplus.github.io/LWG/issue4348)<sup>[12]</sup>, [P3801R0](https://wg21.link/p3801r0)<sup>[4]</sup>, [P3796R1](https://wg21.link/p3796r1)<sup>[3]</sup> | no    |

- **Allocator Timing.** [P3980R1](https://wg21.link/p3980r1)<sup>[5]</sup> separates frame allocation from environment allocation: the environment allocator is now sourced from `get_allocator(get_env(rcvr))` at `connect` time, resolving environment-based injection. The frame allocator, however, remains call-site-specified via `allocator_arg` in the coroutine parameter list. This is a structural consequence of coroutine allocation timing - the frame is allocated by `operator new` before `connect`/`start` runs, so the receiver's environment is unavailable. Shipping standardizes the two-tier split. A design where frame allocation participates in environment-based propagation is foreclosed without a language change to coroutine allocation.

- **Allocator Propagation.** [P3980R1](https://wg21.link/p3980r1)<sup>[5]</sup> provides environment allocator propagation: each `task` obtains its environment allocator from `get_allocator(get_env(rcvr))`, so a parent's environment allocator flows to children through the receiver chain. Frame allocator propagation remains absent. Each coroutine call site must independently specify `allocator_arg` to use a non-default frame allocator. In a deep coroutine call tree where frame allocation matters - arena-per-request, pool allocators, device memory - every function signature must carry `allocator_arg` explicitly. Shipping this design forecloses automatic frame allocator propagation through the coroutine call tree.

- **Error Return.** `task` requires `co_yield with_error(e)` to propagate an error to the caller. `co_return` cannot carry an error value because `return_value` and `return_void` are mutually exclusive in the current coroutine specification. Shipping this interface locks in the `co_yield` mechanism and forecloses `co_return`-based error propagation, which would require a language change.

- **Symmetric Transfer.** The completion functions (`set_value`, `set_error`, `set_stopped`) and `start()` return `void`, providing no channel to propagate a `coroutine_handle<>`. When a sender completes synchronously, the receiver calls `handle.resume()` on the caller's stack, adding a frame per completion with no upper bound. Shipping this protocol forecloses the `coroutine_handle<>`-returning completion protocol that would enable symmetric transfer.

---

## Acknowledgements

The authors thank Andrzej Krzemie&nacute;ski for feedback that sharpened the scope of this revision. Thanks are also due to Dietmar K&uuml;hl, Michael Hava, Mark Hoemmen, Ian Petersen, and Ville Voutilainen for technical discussion that informed the analysis.

---

## References

Papers, issues, and ballot comments referenced in this document.

### WG21 Papers

1. [P3552R3](https://wg21.link/p3552r3) - "Add a Coroutine Task Type" (Dietmar K&uuml;hl, Maikel Nadolski, 2025). https://wg21.link/p3552r3
2. [P4007R0](https://wg21.link/p4007r0) - "Senders and Coroutines" (Vinnie Falco, Mungo Gill, 2026). https://wg21.link/p4007r0
3. [P3796R1](https://wg21.link/p3796r1) - "Coroutine Task Issues" (Dietmar K&uuml;hl, 2025). https://wg21.link/p3796r1
4. [P3801R0](https://wg21.link/p3801r0) - "Concerns about the design of std::execution::task" (Jonathan M&uuml;ller, 2025). https://wg21.link/p3801r0
5. [P3980R1](https://wg21.link/p3980r1) - "Task's Allocator Use" (Dietmar K&uuml;hl, 2026). https://wg21.link/p3980r1
6. [LWG 4356](https://cplusplus.github.io/LWG/issue4356) - "connect() should use get_allocator(get_env(rcvr))". https://cplusplus.github.io/LWG/issue4356
7. [US 254-385](https://github.com/cplusplus/nbballot/issues/960) - C++26 NB ballot comment. https://github.com/cplusplus/nbballot/issues/960
8. [P3950R0](https://wg21.link/p3950r0) - "return_value & return_void Are Not Mutually Exclusive" (Robert Leahy, 2025). https://wg21.link/p3950r0
9. [P1713R0](https://wg21.link/p1713r0) - "Allowing both co_return; and co_return value; in the same coroutine" (Lewis Baker, 2019). https://wg21.link/p1713r0
10. [P2583R3](https://isocpp.org/files/papers/P2583R3.pdf) - "Symmetric Transfer and Sender Composition" (Mungo Gill, Vinnie Falco, 2026). https://isocpp.org/files/papers/P2583R3.pdf
11. [US 246-373](https://github.com/cplusplus/nbballot/issues/948) - C++26 NB ballot comment. https://github.com/cplusplus/nbballot/issues/948
12. [LWG 4348](https://cplusplus.github.io/LWG/issue4348) - "task doesn't support symmetric transfer". https://cplusplus.github.io/LWG/issue4348
13. [P2300R10](https://wg21.link/p2300r10) - "std::execution" (Micha&lstrok; Dominiak et al., 2024). https://wg21.link/p2300r10

### Other

14. [C++ Working Draft](https://eel.is/c++draft/) - (Richard Smith, ed.). https://eel.is/c++draft/

### Croydon Papers (R2)

15. [P3941R4](https://wg21.link/p3941r4) - "Scheduler Affinity" (Dietmar K&uuml;hl, 2026). https://wg21.link/p3941r4
16. [P4151R1](https://wg21.link/p4151r1) - "Rename affine_on" (Robert Leahy, 2026). https://wg21.link/p4151r1
17. [P3927R2](https://wg21.link/p3927r2) - "task_scheduler Bulk Execution" (Eric Niebler, 2026). https://wg21.link/p3927r2

