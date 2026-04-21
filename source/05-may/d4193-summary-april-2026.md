---
title: "A Reader's Guide to the April 2026 Mailing"
document: D4193R0
date: 2026-04-30
intent: info
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

Twenty-three papers, two shipping libraries, and one production deployment audit twenty-one years of networking decisions, build the coroutine-native alternative, and lay a concrete path to standard networking in C++29.

This paper summarizes 23 papers published in the April 2026 mailing. It is a reading guide: an executive summary that identifies the logical series within the collection, describes what each series delivers, and provides individual summaries of every paper. It asks for nothing.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

This paper asks for nothing.

---

## 2. Executive Summary

Twenty-three papers by a single author span three registers - forensic history, working architecture, and practical tutorial - to assemble the most comprehensive evidential case yet published for a direction in C++ async programming. Every claim is backed by published committee records, benchmark data, or deployed code. Read individually, each paper delivers a self-contained finding, comparison, or tool. Read as clusters, the series within the collection build compound understandings no single paper achieves. Read as a whole, the collection traces a single causal arc from the committee decisions of the last decade through the architectural consequences of those decisions to a concrete, implemented, benchmarked alternative ready for standardization.

Six papers (P4094R0 through P4099R0) form a retrospective audit of the committee decisions that shaped C++ async programming over the past decade. Each paper reopens one pivotal moment - the unification of three deployed executor models into P0443, the elevation of `execute(F&&)` as a basis operation in P1525, the disposition of coroutine executors in P2464, the LEWG poll declaring sender/receiver "a good basis" for networking in P2453, and the broader pattern of claims and evidence across the async domain - and measures the published evidence that was available to the committee at the time of each decision. P4099R0, the series capstone, assembles the full causal chain and shows how four locally reasonable but under-evidenced decisions compounded into twenty-one years without standard networking. The compound payoff of the series is not any single finding but the end-to-end documentary trail: a reader who finishes all six papers will hold, for the first time in one place, the complete record of how C++ arrived at its current async impasse.

Five papers build the coroutine-native I/O architecture that emerged from that analysis. P4088R0 establishes the foundation by tracing a nine-step causal chain from C++20's single-allocation coroutine model to properties the committee could not deliver through prior networking attempts: concrete operation states, type-erased streams, zero per-operation allocation, separate compilation, and ABI stability. P4003R2 distills the execution model into the IoAwaitable protocol - an `io_env` struct, a two-argument `await_suspend` concept, a type-erased `executor_ref`, and a cached frame-allocator mechanism - benchmarked at 1.5x to 3.1x speedup over `std::allocator` with type-erasure overhead of roughly one to two nanoseconds per dispatch. P4172R0 supplies the full design audit trail behind the protocol. P4100R0 serves as the series umbrella, mapping a thirteen-paper dependency graph and charting the path to C++29 standardization. P4125R0 delivers the production evidence: a derivatives exchange porting its infrastructure from Boost.Asio callbacks to the coroutine-native model, with early performance and reliability data from a live deployment. Any one of these papers offers a specific technical tool; together, they deliver a complete, testable architecture with code running on three platforms today via the Capy and Corosio libraries.

Four papers examine the structural properties of `std::execution` that bear directly on coroutine integration. P4007R2 classifies every open issue filed against `std::execution::task` and identifies four - allocator timing, allocator propagation, error return via `co_yield`, and the absence of symmetric transfer - that become unfixable once C++26 ships. P4089R0 shows that the open `Environment` template parameter on `task` produces N incompatible task types the moment N libraries define their own query sets, undermining the lingua-franca promise. P4090R0 constructs four sender-based TCP echo servers from the published sender algorithms and measures each against a coroutine-native baseline. P4091R0 names the "abstraction floor" - the boundary where any async framework destroys compound data by forcing it through a single-field error or value path - and maps it in both the sender and coroutine models. Together, these four papers give the reader a precise technical map of where `std::execution` and coroutine-native I/O converge, where they diverge, and why the divergences are structural rather than incidental.

Four more papers build the bridges between the two models. P2583R3 proposes the protocol-level fix that would restore symmetric transfer to the sender model: completion functions and `start()` return `coroutine_handle<>` instead of `void`, with draft wording touching four concept-level expressions and twenty-five sender algorithms. P4092R0 presents `await_sender`, a single-class-template adapter that consumes any sender from inside a coroutine. P4093R0 presents `as_sender`, the reverse bridge wrapping any IoAwaitable as a sender. P4126R0 argues that senders should not have to pay a coroutine frame allocation for every I/O operation consumed through the awaitable protocol, and proposes a universal continuation model that eliminates that cost. A reader who works through all four papers will understand exactly what it would take to make `std::execution` and coroutine-native I/O coexist at zero overhead - and what the cost is of not doing so.

P4014R1 stands alone as the only existing document that explains all thirty C++26 sender algorithms. The paper is a progressive tutorial beginning with `just(42)` and escalating through monadic composition, structured concurrency, data parallelism, and async scopes to a four-layer sensor-fusion pipeline interleaving sender pipelines with coroutine task bodies. Every algorithm is paired with working code and its plain-C++ equivalent, and the theoretical foundations - continuation-passing style, monadic bind, algebraic effects - are mapped to the concrete sender primitives they inspired. The paper is dedicated to the public domain under CC0 and is designed to serve as the basis for future tutorials, documentation, and teaching materials.

Three standalone papers address safety and reference infrastructure. P4035R0 argues that safe-by-default interfaces require explicitly marked escape hatches for trusted boundaries, applying the pattern to P3655R3's `cstring_view` constructors with a validating default and a static `unsafe` factory. P4137R0 measures how much real code the type-safety profile's rules actually cover - a question the profile defines but no published paper has answered. P4182R0 delivers a single citable inventory of platforms, operating systems, and compiler toolchains, replacing the ad-hoc platform-capability recitations that recur across WG21 proposals.

Readers with limited time should choose an entry point that matches their role. Committee members evaluating the C++26 ship-or-slip decision for `std::execution::task` should start with P4007R2, which lays out exactly which defects become permanent upon shipping and requires no prior reading. Library authors building on `std::execution` or coroutine-native I/O should start with P4003R2, which provides a working, benchmarked protocol specification with self-contained code on Compiler Explorer. Anyone seeking to understand how C++ arrived at its current async situation - and what a coroutine-native model would change - should begin with P4099R0 and follow the cross-references forward into the architectural papers.

---

## 3. Individual Papers

### 3.1. P2583R3 - Symmetric Transfer and Sender Composition

C++20 added symmetric transfer so that coroutine chains execute in constant stack space, yet the `std::execution` sender protocol makes it structurally unreachable. P2583R3 traces the gap to its root cause - void-returning completion functions and struct-based receivers that provide no return channel for a `coroutine_handle<>` - and shows that five of six surveyed production coroutine libraries converge on the mechanism the sender model cannot use. The paper proposes a protocol-level fix in which `set_value`, `set_error`, `set_stopped`, and `start()` return `coroutine_handle<>` instead of `void`, preserving zero-allocation composition while restoring constant-stack execution, and supplies draft wording that touches four concept-level expressions, twenty-five sender algorithms, and every third-party type that models `receiver` or `operation_state`. If the fix is not adopted before `std::execution` ships, the change becomes ABI-breaking and the gap becomes permanent.

### 3.2. P4003R2 - A Minimal Coroutine Execution Model

Three concerns - executor affinity, stop-token propagation, and frame-allocator delivery - are all a C++ coroutine needs to suspend, resume, and allocate safely, and this paper distills them into the smallest protocol that can provide all three. P4003R2 specifies the _IoAwaitable_ protocol: an `io_env` struct, a two-argument `await_suspend` concept, a type-erased `executor_ref`, a service-oriented `execution_context` base class, and a cached frame-allocator delivery mechanism - nothing more. Benchmarks on MSVC and Apple Clang show a recycling frame allocator delivering a 1.5x-3.1x speedup over `std::allocator`, while type-erasure overhead lands at roughly 1-2 nanoseconds per dispatch - negligible against I/O latencies measured in tens of microseconds. The entire protocol compiles and runs today on three platforms via the Capy and Corosio libraries, with a self-contained demonstration on Compiler Explorer ready to clone.

### 3.3. P4007R2 - Open Issues in `std::execution::task`

Four issues in `std::execution::task` cannot be fixed after C++26 ships, and this paper names each one. P4007R2 classifies every open issue filed against the coroutine task type - from national ballot comments, LWG issues, and published papers - into two bins: fixable post-ship and foreclosed by shipping. Croydon resolved fourteen of the listed items through P3941R4, P3980R1, P4151R1, and P3927R2, but allocator timing, allocator propagation, error return via `co_yield`, and the absence of symmetric transfer remain structurally locked in. The paper asks for nothing; it simply makes the cost of the ship-or-slip decision visible.

### 3.4. P4014R1 - The Sender Sub-Language For Beginners

C++26 ships thirty sender algorithms, and P4014R1 is the only document that explains every single one of them. The paper is a progressive tutorial that starts with `just(42)`, escalates through monadic composition, structured concurrency, data parallelism, and async scopes, and finishes with a four-layer sensor-fusion pipeline that interleaves sender pipelines with coroutine `task` bodies. Each algorithm is demonstrated in working code and paired with its plain-C++ equivalent, and the theoretical foundations - continuation-passing style, monadic bind, algebraic effects - are mapped to the concrete sender primitives they inspired. The paper is dedicated to the public domain under CC0 and is designed to be reused as the basis for tutorials, documentation, and teaching materials.

### 3.5. P4035R0 - The Need for Escape Hatches

P4035R0 argues that safe-by-default interfaces in C++ must be paired with explicitly marked escape hatches for trusted boundaries where re-validation is pure overhead. The paper surveys four independent precedents — `std::condition_variable` versus `condition_variable_any`, Boost.URL's `pct_string_view` / `make_pct_string_view_unsafe`, BSD `dirent` directory iteration, and Capy's structured `run` versus `run_async` — to extract a recurring pattern: wide-contract defaults carry the short name, narrow-contract opt-ins carry the marked name. It then applies that pattern to P3655R3's `cstring_view` constructors, proposing a validating default constructor and a static `unsafe` factory for O(1) construction at proven boundaries. The paper also examines P3566R2's proposal to deprecate the implicit `char const*` constructor, cites LEWG poll results from Sofia and Croydon showing consensus against removal, and documents the migration costs that explain those outcomes.

### 3.6. P4088R0 - What C++20 Coroutines Already Buy The Standard

Five C++20 language mechanisms — the coroutine frame, type-erased `coroutine_handle<>`, the awaitable protocol, `promise_type`, and symmetric transfer — combine to produce properties the committee could not ship in twenty-one years of networking attempts. P4088R0 traces a nine-step causal chain from the single heap allocation every coroutine pays to concrete operation states, type-erased streams, zero per-operation allocation, separate compilation, and ABI stability, benchmarking the result against sender-based I/O at 100 million operations. The paper concedes every known cost of coroutines — frame allocation, opaque resume, reference lifetime hazards — and documents what each cost purchases, positioning coroutine-native I/O and `std::execution` as complementary models occupying distinct points on the design fork. It concludes that the serial I/O domain is the last of three asynchronous domains without a standard facility, and that the language C++20 already shipped is the substrate that fills it.

### 3.7. P4089R0 - On the Diversity of Coroutine Task Types

The C++26 `std::execution::task` may be structurally incapable of serving as the coroutine lingua franca it promises to be. P4089R0 traces, step by step through the P3552R3 specification, how the open `Environment` template parameter produces N incompatible task types the moment N libraries define their own query sets — and shows that the only adaptation mechanism, `write_env`, requires the caller to know every missing query by name. The paper grounds the risk in NVIDIA's deployed GPU environment, five independent Asio bug reports exhibiting the predicted symptoms, a nine-library survey in which seven converged on single-parameter designs, and Gor Nishanov's original layering model that placed environment customization in awaitables rather than in the coroutine return type. It concludes by presenting concept-constrained awaitables (exemplified by `IoAwaitable`) as the pattern that preserves task type diversity without fragmenting the ecosystem on contact.

### 3.8. P4090R0 - Sender I/O: A Constructed Comparison

P4090R0 constructs four sender-based TCP echo servers from P2300R10 and P3552R3 and measures each against a coroutine-native baseline to determine whether the sender composition algebra applies to compound I/O results. The paper demonstrates that `when_all` cancellation, `upon_error`, and `retry` cannot operate on `(error_code, size_t)` pairs without losing data, introducing shared mutable state, or converting routine errors to exceptions. The one construction that preserves all data - routing everything through `set_value` - bypasses the composition algebra entirely and produces code identical to the coroutine version. A detailed trade-off table, a Qt side-by-side comparison from Voutilainen, and an open invitation for a counter-construction that satisfies all four constraints round out the analysis.

### 3.9. P4091R0 - Error Models of Regular C++ and the Sender Sub-Language

P4091R0 names the "abstraction floor" — the boundary where any async framework destroys compound data by forcing it through a single-field error or value path — and shows that both coroutines and senders have one. The paper traces a March 2026 lib-ext reflector discussion (Voutilainen, Petersen, Maurer, Krzemieński) that produced a partition of operations into infrastructure results (binary pass/fail) and compound results (status plus associated data), then demonstrates that the sender three-channel model fits the first class cleanly but forces one of six documented trade-offs for the second. It catalogs those six positions in a concrete trade-off table, incorporating Petersen's proof that all four known sender constructions for compound dispatch reduce to the equivalent of a coroutine `co_await` plus `switch`. The structural finding is symmetric: coroutines default to below-floor composition where ordinary C++ statements handle dispatch, while senders default to above-floor composition where the generic algebra (`retry`, `when_all`, `upon_error`) lives — and neither paradigm escapes the floor without application-specific wiring.

### 3.10. P4092R0 - Consuming Senders from Coroutine-Native Code

One class template is all it takes to bridge `std::execution` senders into coroutine-native I/O. P4092R0 presents `await_sender`, a single-class-template adapter that consumes any `std::execution` sender from inside a coroutine, stores operation state inline, propagates stop tokens, separates `error_code` from `exception_ptr` at compile time, and posts the resumption back to the coroutine's originating executor. Unlike `execution::task`, the bridge requires no type erasure, no extra allocation beyond the coroutine frame, and no additional coroutine type. The complete implementation ships in Appendix A, compiled and demonstrated against `beman::execution` on MSVC 19.43.

### 3.11. P4093R0 - Producing Senders from Coroutine-Native Code

P4093R0 draws a hard line between coroutine-native I/O and `std::execution` by defining an "abstraction floor" that compound results must not cross. The paper presents `as_sender`, a bridge adapter that wraps any `IoAwaitable` as a sender while rejecting at compile time any awaitable whose result destructures into `(error_code, ...)` with additional elements. It introduces `split_ec`, a zero-allocation receiver adapter that routes a bare `error_code` through the sender three-channel model without exceptions, and contrasts this enforcement with `std::execution::task` from P3552R3, which permits compound results on the value channel at the cost of bypassing the composition algebra. A complete implementation against `beman::execution` and Capy is provided in the appendix.

### 3.12. P4094R0 - The Unification of Executors and P0443

A decade after SG1 directed the merger of three deployed executor models into one, P4094R0 audits the published record and finds almost no empirical evidence behind the rationale that justified unification. The paper catalogues every assertion that drove the design — shared thread pools, N x M explosion, teachability — and documents that the strongest code-level support in over 100 papers is a single hypothetical `parallel_for` snippet authored by the proposers themselves. It traces a previously uncharted terminology shift in which Kohlhoff's continuation-scheduling primitives (`dispatch`/`post`/`defer`) were progressively renamed, demoted, and erased across paper boundaries until the continuation framing disappeared from the API surface entirely. The analysis defines two competing framings of `execute(F&&)` — work submission versus continuation scheduling — and poses pointed questions about networking's twenty-one-year wait, the discarded property system, and the "one grand unified model" poll that never achieved consensus.

### 3.13. P4095R0 - The Basis Operation and P1525

P1525R0 diagnosed `execute(F&&)` as a poor basis operation and launched the sender/receiver model that became `std::execution`—but the diagnosis was conducted entirely under the work framing, not the continuation framing that the executor concept originally embodied. P4095R0 applies the two-framing distinction from P4094R0 to each of P1525R0's four deficiencies (error propagation, cancellation, zero-allocation scheduling, composition asymmetry), showing that three do not arise under the continuation framing and the fourth addresses a different question. The paper documents that no paper at the 2019 Cologne pivot analyzed whether the deficiencies were properties of the `execute` signature or properties of the work framing, and that the continuation-scheduling primitives `dispatch`/`post`/`defer`, the universal async model (N3747), and the networking use case were absent from the record. It concludes with a concrete comparison table scoring the coroutine executor concept (`dispatch(coroutine_handle<>)`) against P1525R0's four criteria, demonstrating that the continuation framing resolves each one without the sender/receiver machinery.

### 3.14. P4096R0 - Coroutine Executors and P2464R0

P4096R0 reopens the analytical record behind the most consequential executor decision of the last decade. The paper re-examines P2464R0's three deficiencies in P0443R14's `execute(F&&)` — no error channel, no lifecycle, no generic composition — and demonstrates that all three are artifacts of the work framing, not inherent properties of executor-based async; under the continuation framing, where the callable is a resumption handle rather than a unit of work, none of the deficiencies arise. It introduces the coroutine executor concept from P4003R0, whose `dispatch(coroutine_handle<>)` and `post(coroutine_handle<>)` enforce the continuation framing through the type system, and places it alongside P2300R10's sender/receiver model as a second published answer to whether the executor abstraction is adequate for async programming. The paper asks for nothing but leaves a pointed observation: the committee acted on a single-framing analysis in 2021, set aside the Networking TS, and five years later no sender-based networking has shipped.

### 3.15. P4097R0 - The Networking Claim and P2453R0

In October 2021, LEWG voted that sender/receiver is "a good basis" for networking — but the published record behind that word is almost entirely empty. P4097R0 conducts a systematic search of WG21 papers, poll outcomes, and mailing-list archives from the date of the vote through 2026, finding zero sender-based networking deployments, zero prototypes, and one hypothetical code example using a placeholder namespace. The paper reproduces the voter comments from P2453R0, several of which explicitly state that the commenter could not evaluate the networking claim yet still voted in favor. Twenty-one years after N1925 and five years after the poll, no sender-based networking implementation has shipped, and the partial-success error-channel concern first raised by Kohlhoff in P2430R0 (2021) persists in the literature as late as P2762R2 (2023).

### 3.16. P4098R0 - Async Claims and Evidence

A decade of committee decisions on executors, networking, and async programming rested on published claims — this paper asks what published evidence actually supported them. P4098R0 constructs a structured table of verbatim claims drawn from the causal chain of executor and networking papers (P0443, P1525, P2464, P2300, P2469, and others), paired against the published evidence found for each. The survey spans six thematic sections — unification, basis operations, networking dependency, the P2464 diagnosis, P2300 deployment scope, and Networking TS readiness — and applies a deliberately low evidence bar: a code snippet, a prototype, or a small user survey suffices. Where deployment data exists (notably Facebook and NVIDIA for GPU dispatch and infrastructure), the paper documents it; where the published record is empty, the cell is left blank. The result is a reference artifact that lets readers evaluate which decisions were grounded in published evidence and which were grounded in unpublished judgment.

### 3.17. P4099R0 - The Twenty-One Year Networking Arc

Four locally reasonable decisions, each under-evidenced, produced a decade without networking in the C++ standard — and P4099R0 lays the full causal chain on the table. The paper stitches together five companion retrospectives (P4094R0 through P4098R0) covering the 2014 executor unification, the 2019 basis-operation pivot, the 2021 P2464R0 diagnosis, and the 2021 poll claiming sender/receiver as a networking foundation, documenting what evidence existed at each decision point and what did not. It introduces the two-framing distinction (work framing vs. continuation framing), identifies a rationale-loss mechanism inherent in multi-author standardization, and catalogs the tools now available — C++20 coroutines, the coroutine executor concept (P4003R0), and interop bridges — that did not exist when those decisions were made. The paper asks for nothing; it assembles the published record and presents the design fork between awaitable-based and sender-based networking for the committee to evaluate on the evidence.

### 3.18. P4100R0 - Coroutine-Native I/O for C++29 (The Network Endeavor)

After two decades of false starts, a thirteen-paper series backed by two published libraries lays out a concrete path to standard networking in C++29. P4100R0 presents a two-stage plan: Stage One delivers pure C++20 abstractions (coroutine task, buffer concepts, stream concepts, combinators) with no platform dependency; Stage Two adds sockets, DNS, TLS, and the rest of the platform I/O stack. Three independent Boost libraries (MySQL, Redis, Postgres) are already building on the underlying Capy and Corosio libraries, and a production derivatives exchange has evaluated the design under real load. The paper positions coroutine-native I/O as complementary to `std::execution`, argues that shipping the abstractions first de-risks the timeline, and provides a quarter-by-quarter schedule targeting full LEWG review by end of 2028.

### 3.19. P4125R0 - Coroutine-Native I/O at a Derivatives Exchange

A derivatives exchange operator is porting its production infrastructure from Boost.Asio callbacks to a coroutine-only networking library, and the early returns are in. P4125R0 reports qualitative findings from three structured interviews with the engineering team after two to three weeks of integration, covering callback-to-coroutine migration patterns, an incremental "springboard function" adoption strategy, and error-handling friction around exception-vs-error-code boundaries. The engineers found the port less disruptive than anticipated and assessed the library as a viable production replacement, though no performance benchmarks have been completed and only TCP socket operations are covered. The paper is transparent about its limitations — small sample, author affiliation, incomplete feature coverage — and positions itself as early field evidence for the committee rather than a conclusive result.

### 3.20. P4126R0 - A Universal Continuation Model

Senders currently pay a coroutine frame allocation for every I/O operation they consume through the awaitable protocol, and P4126R0 argues they should not have to. The paper traces the history of frame-erased versus frame-visible coroutine designs from N4453 through P1063R0 to P3203R0, then proposes a "callback handle" — a 24-byte, user-owned struct whose two-pointer prefix matches the de facto coroutine frame ABI all three major compilers already share — that gives sender pipelines zero-allocation access to any IoAwaitable without modifying a single awaitable implementation. It presents working code for a `callback_frame` that senders embed in their operation state, demonstrates a `read_op_state` that invokes `await_suspend` without ever touching the heap, and identifies the standardization prerequisite: mandating the two-pointer-prefix layout so `coroutine_handle<>::from_address` on user-provided storage is well-defined. The paper names frame-visible stackless coroutines as the deeper long-term solution but positions the callback handle as the pragmatic path that unifies the sender and awaitable ecosystems under one I/O implementation today.

### 3.21. P4137R0 - Profile Analysis and Verification Evidence (PAVE)

The type-safety profile defines rules, but nobody has measured how much real code those rules actually cover. P4137R0 introduces PAVE, a three-phase methodology that classifies every function in a codebase against the profile using Clang AST predicates, then uses LLM-assisted triage to separate true positives from false positives, and finally infers annotations like `[[not_invalidating]]` to expand the verifiable subset. The paper identifies an "annotation dividend" metric that quantifies the practical value of richer annotation vocabularies versus revising the profile rules themselves. All three phases run on existing tooling today, and the results—whether the verifiable subset is large or vanishingly small—give the committee empirical ground truth before standardizing a safety guarantee whose scope is currently unknown.

### 3.22. P4172R0 - IoAwaitable for Coroutine-Native Byte-Oriented I/O

P4172R0 delivers the complete design audit trail behind the IoAwaitable protocol proposed in P4003R1. The paper partitions the async I/O problem across three audiences — application developers, framework authors, and I/O library authors — and justifies every protocol facility (two-argument `await_suspend`, type-erased `executor_ref`, out-of-band frame allocator propagation, `io_env`, `continuation`) against that audience model. It documents trade-offs for each decision with explicit revisit conditions, presents benchmark evidence showing a recycling frame allocator outperforming both `std::allocator` and mimalloc, and specifies bridge points (`await_sender`, `as_sender`) that position IoAwaitable and `std::execution` as complements rather than competitors. Appendices supply a complete `any_read_stream` type-erasure listing and the `io_awaitable_promise_base` mixin that reduces framework-author boilerplate to policy choices.

### 3.23. P4182R0 - A Citable Inventory of Platforms, Operating Systems, and Compiler Toolchains

P4182R0 delivers a single citeable reference that every future WG21 proposal can point to instead of re-explaining what coroutines, TLS, PMR, exceptions, and heap allocation look like across seven platform tiers. The paper catalogs desktop, mobile, console, full RTOS, lightweight RTOS, bare-metal, and GPU environments in a unified schema and pairs each row with a matching compiler-family table covering GCC, Clang, MSVC, Arm GNU, NVIDIA nvcc, and EDG. It extends the capability survey from P4127R0 with SG14-oriented columns for scheduling class, allocation style, and TLS access pattern. The document is explicitly a living reference: later revisions will add rows and schema columns as evidence accumulates.

---

## 4. Conclusion

This reading guide covers 23 papers from the April 2026 mailing. The author hopes it helps the reader find the papers most relevant to their work and interests.

---

## References

[1] P2583R3 - "Symmetric Transfer and Sender Composition" (Vinnie Falco, 2026).

[2] P4003R2 - "A Minimal Coroutine Execution Model" (Vinnie Falco, 2026).

[3] P4007R2 - "Open Issues in `std::execution::task`" (Vinnie Falco, 2026).

[4] P4014R1 - "The Sender Sub-Language For Beginners" (Vinnie Falco, 2026).

[5] P4035R0 - "The Need for Escape Hatches" (Vinnie Falco, 2026).

[6] P4088R0 - "What C++20 Coroutines Already Buy The Standard" (Vinnie Falco, 2026).

[7] P4089R0 - "On the Diversity of Coroutine Task Types" (Vinnie Falco, 2026).

[8] P4090R0 - "Sender I/O: A Constructed Comparison" (Vinnie Falco, 2026).

[9] P4091R0 - "Error Models of Regular C++ and the Sender Sub-Language" (Vinnie Falco, 2026).

[10] P4092R0 - "Consuming Senders from Coroutine-Native Code" (Vinnie Falco, 2026).

[11] P4093R0 - "Producing Senders from Coroutine-Native Code" (Vinnie Falco, 2026).

[12] P4094R0 - "The Unification of Executors and P0443" (Vinnie Falco, 2026).

[13] P4095R0 - "The Basis Operation and P1525" (Vinnie Falco, 2026).

[14] P4096R0 - "Coroutine Executors and P2464R0" (Vinnie Falco, 2026).

[15] P4097R0 - "The Networking Claim and P2453R0" (Vinnie Falco, 2026).

[16] P4098R0 - "Async Claims and Evidence" (Vinnie Falco, 2026).

[17] P4099R0 - "The Twenty-One Year Networking Arc" (Vinnie Falco, 2026).

[18] P4100R0 - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, 2026).

[19] P4125R0 - "Coroutine-Native I/O at a Derivatives Exchange" (Vinnie Falco, 2026).

[20] P4126R0 - "A Universal Continuation Model" (Vinnie Falco, 2026).

[21] P4137R0 - "Profile Analysis and Verification Evidence (PAVE)" (Vinnie Falco, 2026).

[22] P4172R0 - "IoAwaitable for Coroutine-Native Byte-Oriented I/O" (Vinnie Falco, 2026).

[23] P4182R0 - "A Citable Inventory of Platforms, Operating Systems, and Compiler Toolchains" (Mungo Gill, 2026).

