---
title: "A Reader's Guide to My May 2026 Papers"
document: D4194R0
date: 2026-05-31
intent: info
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

Fifteen papers dissect the async design space against its own specification, ship five open-source AI tools for committee self-audit, and deliver the production pipeline to break a twenty-one-year C++ networking deadlock.

This paper summarizes 15 papers by the author published in the
May 2026 mailing. It is a reading guide: an executive summary
that identifies the logical series within the collection, describes
what each series delivers, and provides individual summaries of every
paper. It asks for nothing.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the
committee.

This paper asks for nothing.

---

## 2. Executive Summary

Seven papers construct a single auditable argument that C++20 coroutines and `std::execution` senders serve fundamentally different domains - and that binding networking to the sender model imposes costs the specification itself cannot eliminate. The series opens with the historical pattern: every universal model that endured in computing was narrow, emergent, and battle-tested before standardization; every committee-designed one failed (P4034R0). From there, evidence accumulates paper by paper - twenty-four post-adoption changes to senders against zero to coroutines (P4041R0), a spec-mandated performance gap where a minimal HTTP request-response pays fifteen unnecessary state constructions (P4123R0), a `when_all` combinator provably blind to I/O errors because they arrive on the value channel (P4124R0), an allocator design space exhaustively shown to admit exactly two mechanisms and no more (P4127R0), a frame-visibility proposal that would close the mandatory heap allocation gap between the two models (P4166R0), and paired passages from P2300R10 where the specification appears to cite its own text against itself (P4178R0). Any single paper delivers an independent technical finding; the compound effect of reading the series is a structural portrait of the async design space that is difficult to dismiss on any one point without engaging the others.

Five papers ship open-source, AI-powered tools that propose to transform committee work from memory-dependent craft into auditable process - and every tool is turned on its own creator first. SAGE (P4046R0) interviews veteran committee members and distills their tacit judgment into corroborated principles, yielding eleven that survived cross-validation across five interviews. CRYSTAL BALL (P4047R0) tracks twenty-seven dated, falsifiable predictions about `std::execution` and grades each against the public record - eighteen confirmed, five wrong - producing a concrete measure of which prediction classes the committee can trust as C++29 planning begins. The Advocatus Diaboli (P4170R0) delivers five-phase adversarial paper review for under a dollar in API tokens and fifteen minutes of wall-clock time. "Is This C++?" (P4183R0) distills Stroustrup's *Design and Evolution* into a twenty-one-question litmus test executable by any frontier language model. Read individually, each tool solves a narrow problem; read together, they outline a methodology in which institutional knowledge, predictive accuracy, and design-principle fidelity are all measured, versioned, and made publicly auditable under CC0 licensing.

Two papers convert the async architecture argument from analysis into a staffed, version-controlled production line. P4036R0 demonstrates - through five escalating failure modes - why `span<byte>` breaks at every asynchronous boundary, and proposes the minimal buffer abstractions that twenty years of Boost.Asio field deployment have validated. P4048R0 lays out the organizational machinery to deliver C++29 networking: a six-team continuous pipeline, eleven companion papers feeding it, two shipping libraries with three independent adopters already in the field, and a two-stage delivery plan ensuring that partial delivery of standalone C++20 abstractions is still delivery even if the full networking stack slips. Where the async series establishes what the I/O architecture should look like, these two papers establish how it gets built and when it ships.

P4045R0 stands alone as a systematic point-by-point rebuttal of the case for deferring Contracts out of C++26. The paper documents the specific polls, telecons, and meeting outcomes that already disposed of every argument in the deferral proposal, revealing that seven of its fifteen cited papers address a single NB comment that generated extensive discussion but produced zero design changes to the adopted wording. The structural paradox at the center of the rebuttal - that the deployment experience demanded as a precondition is precisely what deferral prevents, as the Concepts TS demonstrated when it was withdrawn without producing the field data it was supposed to gather - reframes the deferral debate from a question of readiness to a question of institutional learning.

P4184R0 applies the "Is This C++?" litmus test to P3874R1 - the proposal to make C++ a memory-safe language - and scores it seven out of twenty-one, with every verdict traceable to a specific quoted passage in the evaluated paper. The analysis finds failures on zero-overhead, on preferring compile-time checking, and on current usefulness, among twelve other counts. The paper demonstrates what the tools cluster makes possible at scale: design-principle evaluation that is reproducible, auditable, and independent of the evaluator.

Taken as a whole, the fifteen papers present three things the committee has not had before in a single mailing contribution: a comprehensive technical decomposition of the async design space grounded in the specification's own normative text, a suite of open-source tools that make committee knowledge and predictive accuracy measurable, and an organizational pipeline with shipping code aimed at C++29 networking. The async series and the tools series reinforce each other - the tools audit the async argument, and the async argument demonstrates why auditable methodology matters. A reader who engages only a single paper gains a specific finding or a usable tool; a reader who follows a cluster gains a compound understanding no single paper achieves; a reader who crosses all three clusters encounters a qualitatively different picture of how the committee's technical decisions, institutional memory, and delivery capacity interact.

Three entry points serve different reader profiles. Committee members focused on the C++29 async direction should start with P4123R0 ("The Cost of Senders for Coroutine I/O"), which delivers the most concentrated technical finding - a spec-mandated performance gap demonstrated through line-by-line normative analysis - and naturally pulls the reader into the surrounding series. Readers interested in AI-assisted methodology for standards work should start with P4170R0 ("Prosecute Your Paper To Improve It"), the most immediately actionable paper in the collection: a structured prompt that any author can run against any paper today. Readers seeking the broadest view of the C++29 networking delivery plan should start with P4048R0 ("Networking for C++29: A Call to Action"), which provides the organizational context that makes the companion papers legible as a coordinated program rather than isolated contributions.

---

## 3. Individual Papers

### 3.1. P4034R0 - On Universal Models

Every universal model that endured in computing - TCP/IP, IEEE 754, STL iterators, REST - was narrow, emergent, and battle-tested before standardization; every committee-designed universal model - OSI, CORBA - failed. P4034R0 lays out the historical scorecard in a six-row table and then asks where `std::execution` falls on it. The paper argues that C++20 coroutines already contain a universal async protocol hiding in plain sight - three operations, zero coordination required, cross-library interop demonstrated today across cppcoro, Folly, Asio, and TooManyCooks - mirroring the Internet hourglass architecture. A side-by-side comparison maps `std::execution` onto CORBA across seven structural axes, from bundled-concern count to deferred primary use case, while noting that the 2021 SG1 poll on whether a grand unified async model was even needed returned no consensus.

### 3.2. P4036R0 - Why Span Is Not Enough

Six I/O ecosystems - POSIX, Windows, Asio, libuv, Go, and .NET - all independently converged on bespoke buffer types instead of reusing their language's generic byte view, and P4036R0 explains why the committee should take the hint. The paper walks through five escalating attempts to represent I/O buffers with `span<byte>`, showing how each one breaks: a single span cannot describe scatter/gather operations, a span of spans dangles the moment it crosses an asynchronous boundary, and a range of spans offers no way to consume 26 bytes from a 100-byte chunk without destroying the rest. It then invokes the committee's own precedent - P0298R3 added `std::byte` even though `unsigned char` had the right size and alignment - to argue that `span<byte>` deserves the same treatment one abstraction level higher. The proposed replacement is a minimal `mutable_buffer` / `const_buffer` pair exposing only `data()` and `size()`, with room for a diagnostic callback that `span<byte>` can never carry, drawn directly from the Networking TS buffer model that has been shipping in Boost.Asio for twenty years.

### 3.3. P4041R0 - Is `std::execution` a Universal Async Model?

Twenty-four post-adoption changes have landed on the sender sub-language since St. Louis - and zero have touched coroutines. P4041R0 assembles the public record on whether `std::execution` subsumes C++20 coroutines or whether the two serve fundamentally different domains, cataloguing every post-adoption paper, LWG defect, and NB ballot comment in a single table. The evidence is striking: six independent coroutine libraries converged on `coroutine_handle<>`-returning `await_suspend` for symmetric transfer, while the standard bridges use `void`; the reference implementation has 1,300 GitHub stars, but the I/O ecosystem built on it has 21. The paper surfaces structural friction - error channel routing, frame allocator timing, reversed `co_yield` semantics - not as design defects but as tradeoffs that compile-time work graphs impose on I/O code, and asks whether those tradeoffs should bind networking going forward.

### 3.4. P4045R0 - Response to P4043R0

P4045R0 takes every argument for deferring C++ Contracts out of C++26, lines them up against the committee record, and shows that not one of them is new. The paper walks through all 15 papers cited by P4043R0 - the design-churn claim, the outstanding NB comments, the TS alternative, the White Paper alternative - and documents the specific polls, telecons, and meeting outcomes that already disposed of each. Seven of those 15 papers turn out to address a single Romanian NB comment (RO 2-056) that generated extensive discussion but produced zero design changes to the adopted P2900R14. The paper also surfaces a structural paradox in the deferral argument: the deployment experience P4043R0 demands as a precondition is precisely what deferral prevents, as the Concepts TS demonstrated when it was withdrawn without producing the field data it was supposed to gather.

### 3.5. P4046R0 - SAGE: Saving All Gathered Expertise

WG21's most valuable knowledge has never been written down - it lives in the judgment of veteran participants who can spot a doomed proposal on sight but have never been asked to explain how. P4046R0 presents a three-stage agentic pipeline that conducts structured interviews with experienced committee members, feeds the transcripts through AI-assisted synthesis, and distills the results into corroborated principles backed by multiple independent sources. Five interviews - with Howard Hinnant, Matheus Izvekov, Dave Abrahams, Sean Parent, and Doug Gregor - yielded 11 principles that survived cross-validation, from which the pipeline generated a general-purpose paper-scoring rubric with concrete pass/fail indicators at each level. The authors then turned the rubric on their own paper first, surfacing five specific weaknesses - a demonstration that the methodology bites its creator before anyone else.

### 3.6. P4047R0 - CRYSTAL BALL: Checking Predictions Against the Record

Of the 27 dated, public, falsifiable predictions about `std::execution` that P4047 tracks, 18 were confirmed by the record and only 5 were flatly wrong. The paper collects every checkable claim it can find - from proponents and critics alike - covering timelines, safety concerns, customization mechanism stability, universality promises, networking readiness, and implementation maturity, then grades each against committee minutes, published papers, and conference talks. Safety and correctness warnings proved highly predictive; universality claims and the customization mechanism design did not. The scorecard is symmetric: domain viability predictions from proponents scored a perfect 3-for-3, while critics missed on the Networking TS timeline. What emerges is a concrete, auditable record of which classes of prediction the committee can trust - and which it should discount - as C++29 planning begins.

### 3.7. P4048R0 - Networking for C++29: A Call to Action

After twenty-one years without sockets, DNS, or TLS in the C++ standard, P4048R0 lays out the organizational machinery designed to finally break the deadlock. The paper proposes a six-team continuous production pipeline - Implementation, Design, Wording, Testing, plus two cross-cutting review teams - fed by eleven companion papers and two shipping libraries (Capy and Corosio) with three independent adopters already in the field. Work flows paper-by-paper through the pipeline, with multiple papers occupying different stages simultaneously; every handoff produces a visible, version-controlled artifact in a public GitHub repository. A two-stage delivery plan lets the committee ship pure C++20 abstractions (coroutine execution protocol, buffer concepts, stream concepts) as standalone value even if the full networking stack slips past C++29, ensuring that partial delivery is still delivery.

### 3.8. P4123R0 - The Cost of Senders for Coroutine I/O

Even after granting every proposed engineering fix to `std::execution::task` and comparing against the best possible conforming implementation, a spec-mandated performance gap remains for coroutine I/O users. P4123R0 walks through the normative text of [exec.task] line by line and identifies operations - `state<Rcvr>` construction, scheduler extraction, `affine_on` wrapping - that no conforming implementation can eliminate and that the coroutine-native model simply does not perform. Under the committee's stated direction that networking should use senders, every socket read, every write, every timer wait, and every DNS lookup pays this overhead: a minimal HTTP request-response accumulates 15 `state<Rcvr>` constructions, 15 scheduler extractions, and 10 `affine_on` wrappings where the coroutine-native path stores 10 pointers and is done. The paper invokes Stroustrup's zero-overhead principle and Sutter's two-part definition, presents two cases (I/O as awaitables, I/O as senders), and asks the committee to decide whether the gap justifies a separate task type for I/O.

### 3.9. P4124R0 - Combinators and Compound Results from I/O

`std::execution::when_all` cannot see I/O errors - they arrive on the value channel, and the combinator dispatches only on channel tags. P4124R0 traces the `when_all` completion handler through the P2300R10 specification and systematically shows that all three strategies for routing compound I/O results through the three-channel model fail: the value-channel strategy leaves `when_all` blind to errors, the error-channel strategy corrupts downstream composition with misplaced byte counts inside error tuples, and the predicate strategy repeats domain logic at every call site. The paper proposes domain-aware combinators - a single `when_all` that dispatches at compile time via concepts, selecting an IoAwaitable overload that inspects results directly with zero adapter overhead or delegating to `std::execution::when_all` for senders. The result is flat destructuring, correct error-driven cancellation, and no per-call-site boilerplate - two implementations behind one name, selected by the type system.

### 3.10. P4127R0 - The Coroutine Frame Allocator Timing Problem

P4127R0 proves that the design space for delivering a frame allocator to a C++20 coroutine is closed - exactly two mechanisms exist, and no future customization point can open a third. The paper exhaustively enumerates every coroutine customization point in the language, places each one on a timeline relative to `promise_type::operator new`, and shows that every mechanism either reduces to passing the allocator in the parameter list (`allocator_arg_t`), reduces to ambient state such as thread-local storage, or fires after the frame already exists. A side-by-side comparison across a three-deep coroutine call chain makes the ergonomic stakes concrete: Path A pollutes every signature and every call site with allocator plumbing, while Path B keeps signatures as pure domain logic at the cost of a single `fs:`-relative TLS load. The paper then presents a hybrid `operator new` overload set - shipping in the same promise type - that lets each call site choose its own path, and closes with a structured rebuttal of six common TLS objections, including a platform survey showing the intersection of "has `<memory_resource>`" and "lacks `thread_local`" is empty.

### 3.11. P4166R0 - Benefits of Frame-Visible Coroutines for Senders

Two of the three performance properties that `std::execution` senders hold over coroutines trace to a single C++20 design choice: the coroutine frame is opaque. P4166R0 revisits the Known-Layout Type model documented in P1492R0 (2019) and shows that adding frame-visible coroutines - where `sizeof(frame)` is `constexpr` - would eliminate `std::execution::task`'s mandatory heap allocation and give coroutine-based sender algorithms full optimizer visibility. The paper constructs a formal forward-and-reverse mapping between awaitable return types and the sender three-channel completion model, surfacing a structural constraint: compound I/O results (an error code and a byte count produced by the same operation) cannot round-trip through three mutually exclusive channels. A side-by-side property table makes the case that frame-visible coroutines close the gap between both async models while leaving compile-time work graphs - the type-level encoding of dependency topology - as the sender model's irreducible, unique contribution.

### 3.12. P4170R0 - Prosecute Your Paper To Improve It

For less than a dollar in API tokens and fifteen minutes of wall-clock time, every paper in the mailing can now know its own weaknesses before the committee does. P4170R0 introduces the Advocatus Diaboli, an open-source structured prompt that turns any frontier language model into a five-phase adversarial examiner for WG21 papers - complete with an internal counter-examiner that kills bad findings through six named challenges before they reach the record. The case study applies the tool to P2900R14 ("Contracts for C++," 256KB, 4,348 lines plus its 419KB rationale paper), producing five sections certified as battle-hardened, five formal objections surviving from nine candidates after cross-examination, and sixteen falsifiable predictions with explicit timelines. The tool ships in three cultural translations - a Latin ecclesiastical tribunal, a German engineering inspection, and a Chinese imperial court examination - all implementing identical methodology under CC0 public domain dedication, ready to copy into any frontier model today.

### 3.13. P4178R0 - Trade-offs in Asynchronous Abstraction Design

P2300R10 cites its own text against itself - and the results are more interesting than any outside critique could be. P4178R0 extracts paired passages from the `std::execution` specification where two sections of the same document appear to be in tension, organizing them into four recurring rhetorical patterns: claims walked back within a single section, inconsistent evidentiary standards applied to competing abstractions, prior art dismissed then quietly adopted, and stated priorities contradicted by the final design. A seven-line coroutine `retry` is placed beside the 125-line sender implementation of the same algorithm, letting the specification's own code make the argument. Where a charitable reading resolves the tension, the paper says so - making the unresolved cases all the harder to dismiss.

### 3.14. P4183R0 - Is This C++?

P4183R0 offers a 21-question litmus test - distilled entirely from Bjarne Stroustrup's *The Design and Evolution of C++* - that can be pointed at any proposal, feature, library, or blog post to measure how faithfully it embodies the language's founding principles. Each question maps to a specific Stroustrup quote (zero-overhead, static types, deterministic destruction, multi-paradigm composability, and more), plus one from Howard Hinnant on making the safe thing easy and the unsafe thing possible. The paper ships as a structured prompt designed to be executed by a large language model: a subagent extracts tagged evidence from the subject document, a verification phase confirms or overturns each tag, and a strict decision rule collapses 21 binary answers into a single verdict ranging from "This is C++" down to "This is another matter entirely." The entire paper is dedicated to the public domain under CC0, inviting anyone to reuse, fork, or embed the checklist in tutorials, linters, or review tooling without restriction.

### 3.15. P4184R0 - Is P3874R1 C++?

P3874R1 - the proposal to make C++ a memory-safe language - scores 7 out of 21 on a checklist of C++ design principles distilled from Stroustrup's own book, and the verdict is "not even close to C++." This paper applies the twenty-one criteria from P4183 "Tool: Is This C++?" to P3874R1, quoting directly from the evaluated paper at every step and rating each claim as supports-yes, supports-no, or overturned. The analysis finds that P3874R1 fails on zero-overhead ("bounds safety entails a performance cost"), on preferring compile-time checking (runtime enforcement is treated as coequal), on current usefulness (the paper itself concedes a new standard library is needed before the safe subset is practical), and on twelve other counts. Every verdict is traceable to a specific passage in P3874R1, making the evaluation independently auditable without requiring access to the AI model that produced it.

---

## 4. Conclusion

This reading guide covers 15 papers from the May 2026 mailing.
The author hopes it helps the reader find the papers most relevant to
their work and interests.

---

## References


[1] P4034R0 - "On Universal Models" (Vinnie Falco, 2026).
[2] P4036R0 - "Why Span Is Not Enough" (Vinnie Falco, 2026).
[3] P4041R0 - "Is `std::execution` a Universal Async Model?" (Vinnie Falco, 2026).
[4] P4045R0 - "Response to P4043R0" (Vinnie Falco, 2026).
[5] P4046R0 - "SAGE: Saving All Gathered Expertise" (Vinnie Falco, 2026).
[6] P4047R0 - "CRYSTAL BALL: Checking Predictions Against the Record" (Vinnie Falco, 2026).
[7] P4048R0 - "Networking for C++29: A Call to Action" (Vinnie Falco, 2026).
[8] P4123R0 - "The Cost of Senders for Coroutine I/O" (Vinnie Falco, 2026).
[9] P4124R0 - "Combinators and Compound Results from I/O" (Vinnie Falco, 2026).
[10] P4127R0 - "The Coroutine Frame Allocator Timing Problem" (Vinnie Falco, 2026).
[11] P4166R0 - "Benefits of Frame-Visible Coroutines for Senders" (Vinnie Falco, 2026).
[12] P4170R0 - "Prosecute Your Paper To Improve It" (Vinnie Falco, 2026).
[13] P4178R0 - "Trade-offs in Asynchronous Abstraction Design" (Vinnie Falco, 2026).
[14] P4183R0 - "Is This C++?" (Vinnie Falco, 2026).
[15] P4184R0 - "Is P3874R1 C++?" (Vinnie Falco, 2026).
