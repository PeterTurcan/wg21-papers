# Senders, Receivers, std::execution — Community Research

Compiled: 2026-04-28
Sources: Reddit (r/cpp, r/wg21), Hacker News, developer blogs, WG21 papers, GitHub issues, Stack Overflow, mailing lists.

Every entry: exact verbatim quote, author/username, hyperlink.

---

## PRO P2300 / Senders+Receivers

> "The way to escape this trap is for the C++ standard to endorse one async abstraction. Then all the libraries that expose asynchrony can map their abstractions to the standard one, and we'll all be able to talk to each other. Babel solved. So that is why the C++ Standardization Committee is interested in this problem. Practically speaking, it's a problem that can only be solved by the standard."

- **Eric Niebler** - [What are Senders Good For, Anyway?](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) - Feb 4, 2024

> "You want to use senders because then you can stitch your async operations together with other operations from other libraries using generic algorithms from still other libraries. And so you can co_await your async operations in coroutines without having to write an additional line of code."

- **Eric Niebler** - [What are Senders Good For, Anyway?](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) - Feb 4, 2024

> "Why do we need senders when C++ has coroutines? I hope you realize by now that this isn't an either/or. Senders are part of the coroutine story. If your library exposes asynchrony, then returning a sender is a great choice: your users can await the sender in a coroutine if they like, or they can avoid the coroutine frame allocation and use the sender with a generic algorithm like then() or when_all(). The lack of allocations makes senders an especially good choice for embedded developers."

- **Eric Niebler** - [What are Senders Good For, Anyway?](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) - Feb 4, 2024

> "I'll grant that implementing senders is more involved than using ordinary C-style callbacks. But consuming senders is as easy as typing co_await, or as simple as passing one to an algorithm like sync_wait(). Opting in to senders is opting into an ecosystem of reusable code that will grow over time."

- **Eric Niebler** - [What are Senders Good For, Anyway?](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) - Feb 4, 2024

> "Separating the launch of the work from the construction of the operation state lets us aggregate lots of operation states into one that contains all the data needed by the entire task graph, swiveling everything into place before any work gets started. That means we can launch lots of async work with complex dependencies with only a single dynamic allocation or, in some cases, no allocations at all."

- **Eric Niebler** - [What are Senders Good For, Anyway?](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) - Feb 4, 2024

> "P2300 aims to support both concurrency and parallelism... One of the big reasons to love std::execution is that it works well with coroutines, and is the biggest usability improvement yet to use the coroutine support we already have."

- **Herb Sutter** - [Trip report: Summer ISO C++ standards meeting (St Louis, MO, USA)](https://herbsutter.com/2024/07/02/trip-report-summer-iso-c-standards-meeting-st-louis-mo-usa/) - July 2, 2024

> "Cross-platform means across different parallel programming models, using both distributed-memory and shared-memory, and across different computer architectures... The NVIDIA coauthors of P2300 report that parallel performance is on par with CUDA code."

- **Herb Sutter** (citing NVIDIA authors) - [Trip report: Summer ISO C++ standards meeting (St Louis)](https://herbsutter.com/2024/07/02/trip-report-summer-iso-c-standards-meeting-st-louis-mo-usa/) - July 2, 2024

> "Senders/receivers represent one of the major additions to C++, as they provide an underlying model for expressing computations, adding support for concurrency, parallelism, and asynchrony. By using senders/receivers, one can write programs that heavily and efficiently exploit concurrency, all while maintaining thread safety (no deadlocks, race conditions, etc.)."

- **Lucian Radu Teodorescu** - [Senders/Receivers: An Introduction](https://isocpp.org/blog/2025/01/senders-receivers-an-introduction-lucian-radu-teodorescu) - January 2025 (ACCU Overload 184)

> "Transitioning from classical multi-threaded programming with threads and locks to a structured concurrency model is akin to moving from programming based on goto statements to structured programming with clear code abstractions."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "Senders/receivers is not just a framework for specific types of problems; it's a global solution to concurrency. Every problem that can be solved with threads and locks can also be addressed using senders/receivers."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "I foresee a near future where describing concurrency in terms of senders/receivers is much easier to teach than concurrency with threads and locks."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "I think that senders/receivers is one of the most important features that C++ will have, standing very close to iterators. It will open a whole new world of programming in C++."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "A good concurrency model... may require major paradigm changes that C++ may not be ready to adopt... even if we decide to use new concurrency frameworks, senders/receivers are probably compatible with those; to my knowledge, every major concurrency paradigm can be (with some effort) mapped to senders/receivers. So, it may not be the ideal concurrency model, but it's probably the best foundation for general C++ concurrency. At least for now."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "P2300 has amazing promise, taking inspiration from Stepanov with the ambitious goal of generically abstracting asynchronous programming with the goal of zero runtime abstraction overhead. The promise is that this will allow us to write code that works equally well for describing asynchronous algorithms on a microcontroller (without allocation or exceptions) as it does for distributing the processing of terabytes of data across a cluster of GPUs or other supercomputers. It's a lofty goal, but as far as I can tell the goal is being met!"

- **Ben FrantzDale** - [Sender Intuition: Senders Don't Send](https://benfrantzdale.github.io/blog/2024/10/01/sender-intuition-senders-dont-send.html) - Oct 1, 2024

> "I believe S/R is a correct low-level foundation for general async programming based on function and sender composition. The core has been in use and studied literally for decades, just not in C++."

- **u/Steve_Downey** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "It would be a real disservice for users to have to wait until C++29 before they have an async coroutine task type out of the box that worked with the new async model proposed in P2300."

- **Lewis Baker, Eric Niebler, Kirk Shoop, Lucian Radu Teodorescu** - [P3109R0: A Plan for std::execution for C++26](https://open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3109r0.html) - 2024-02-12

> "Shipping std::execution without a system execution context would severely limit the out-of-box experience for users of the facility, requiring them to pull in third-party libraries to be able to do useful work."

- **Lewis Baker, Eric Niebler, Kirk Shoop, Lucian Radu Teodorescu** - [P3109R0: A Plan for std::execution for C++26](https://open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3109r0.html) - 2024-02-12

> "std::execution has earned its place. Herb Sutter reported that Citadel Securities uses it in production: 'We already use C++26's std::execution in production for an entire asset class, and as the foundation of our new messaging infrastructure.' Senders work well in their domain: compile-time work graph construction, GPU dispatch, high-frequency trading pipelines."

- **Vinnie Falco, Mungo Gill** (reporting Citadel testimony) - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "The three channels enable compile-time routing: upon_error attaches to the error path at the type level, let_value chains successes, and algorithms like when_all cancel siblings when a child completes through the error or stopped channel - all without runtime inspection of the payload."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "The finding is not that std::execution failed. It is that its scope is specific, not universal. Narrowing the scope is not admitting failure - it is recognizing success where it exists and clearing the path where it does not."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "The three-channel model is a property of the sender model, not a bug. When the best people in the field iterate for five years on a well-understood problem and every solution trades one cost for another, the evidence points toward a structural constraint rather than a missing insight."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "The essence of the sender/receiver proposal is essentially this: [sync function → async with continuation → curried → curried with operation state]. The model does work very well with coroutines and can avoid or defer a lot of the expected memory allocations of async operations."

- **u/gpderetta** - [Hacker News: Trying Out C++26 Executors](https://news.ycombinator.com/item?id=46072323) - 2025

> "It is a foundational library for C++ developers to experience the upcoming C++26 Senders/Receivers model today using C++20. Several modern networking and concurrency libraries (e.g., uring_exec) are starting to depend on stdexec."

- **@hollykbuck** - [conan-center-index: add stdexec package](https://github.com/conan-io/conan-center-index/pull/30060) - April 2026

> "The transition to structured concurrency can't come soon enough for me."

- **u/eric_niebler** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

---

## AGAINST P2300 / Senders+Receivers

### Complexity and Cognitive Load

> "The P2300 crew have collectively done a terrible job of making this work accessible. At the heart of P2300 is a simple, elegant (IMHO) core that brings many benefits, but it's hard to see that forest for all the trees."

- **Eric Niebler** - [What are Senders Good For, Anyway?](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) - Feb 4, 2024

> "After reading all that, my only thought is: 'Now let's see you debug that.' IMHO the more abstract and complex a system is, the more chances that something will go wrong. When one has to figure out what's actually happening among a huge mess of overly-abstracted code, simple and straightforward always wins. Perhaps it's some kind of job security."

- **u/userbinator** - [Hacker News: What are senders good for, anyway?](https://news.ycombinator.com/item?id=39261268) - Feb 2024

> "When reading the blog, I saw these really long, complex bits of code and was thinking to myself, '_this_ is simpler?!' It turns out those long complex pieces of code are not something the consumer, the program writer, me and you, will ever need to see. If the author reads this, I apologise for saying so, but IMO the blog post aims well but misfires: it needs to communicate to C++ developers what code _they_, ie _us_ normal folk, will see and write. Otherwise we'll get scared off."

- **anonymous** - [Hacker News: What are senders good for, anyway?](https://news.ycombinator.com/item?id=39261268) - Feb 2024

> "Is it just me or are the code examples of the executors absolutely unreadable/comprehensible without reading it 5 times? Even with different formatters I'd much prefer the tbb variant."

- **anonymous** - [Hacker News: Trying Out C++26 Executors](https://news.ycombinator.com/item?id=46072323) - 2025

> "I've been keeping an eye on the P2300 'Senders' proposal for generic asynchrony for many years, but felt like I never quite 'got' it. I know I'm not the only one who has found it challenging to grok... if you step into implementations, you quickly find yourself in a sea of underscores, namespaces, and customization-point objects. There are good reasons for all of these things, but they hindered my understanding."

- **Ben FrantzDale** - [Sender Intuition: Senders Don't Send](https://benfrantzdale.github.io/blog/2024/10/01/sender-intuition-senders-dont-send.html) - Oct 1, 2024

> "Reading the paper you linked. I have absolutely no idea what's going on in the P2300 examples. That's not c++. It's brainfuck with English words mixed in."

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "I seriously investigated [libunifex] for roughly 2 work-days. I didn't like it, and couldn't use it to do what I wanted. That doesn't mean that libunifex couldn't - it means that I couldn't. The cognitive load was too high."

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "I still have my concerns, as I think the heavily templating will come at a cost of clarity, but I haven't tried them on a large application yet."

- **anonymous** - [Hacker News: What are senders good for, anyway?](https://news.ycombinator.com/item?id=39261268) - Feb 2024

> "I used to live and breathe C++ early 2000s, but haven't touched it since. I can't make sense of modern C++."

- **anonymous** - [Hacker News: Trying Out C++26 Executors](https://news.ycombinator.com/item?id=46072323) - 2025

> "C++ has two ways of naming things: `std::incomprehensible_long_name` and `|`."

- **anonymous** - [Hacker News: Trying Out C++26 Executors](https://news.ycombinator.com/item?id=46072323) - 2025

> "Probably the worst part about senders/receivers is its ergonomics. It may not be that easy to use, especially when compared to other frameworks (coroutines, async/await, etc.). But this is not because there is something inherently broken in the model of senders/receivers. Most of the problem comes from the complexity of C++ and the way people are using the language."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "Using senders/receivers requires the programmer to spend some time wrapping their head around the concepts, and even after that, it's not the easiest framework to work with. This is true. Coroutines provide a much friendlier approach to concurrency."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "It is a brilliant design. It's just that the details involve a lot of complexity. Being a typical C++ proposal, it aims to be a 100% solution for every use case. This requires a whole bunch of customization mechanisms to adopt algorithms for specific execution contexts, a whole lot of metaprogramming to compute the completion signature, and many new concepts and utility functions. If an end user wants to compose existing senders, that is simple enough by using the | operator or writing a coroutine and co_awaiting a sender, but the implementation below is complex and writing your own sender is non-trivial. Similar to std::ranges, this could lead to higher compile times, more work for the optimizer to eliminate all those abstractions, and unreadable error messages if you do something wrong."

- **Jonathan Müller** - [Trip Report: Summer ISO C++ Meeting in St. Louis, USA](https://www.think-cell.com/en/career/devblog/trip-report-summer-iso-cpp-meeting-in-st-louis-usa) - July 2024

> "One particular complexity I don't like is the idea of environments. A sender can have an associated environment, which is essentially a compile-time key-value-store in the form of a named tuple of properties... This error is only detected when we compose them in main. If we compose two senders from different libraries in a third library using the environment from a fourth place, it can require a lot of digging around to figure out what exactly went wrong."

- **Jonathan Müller** - [Trip Report: Summer ISO C++ Meeting in St. Louis, USA](https://www.think-cell.com/en/career/devblog/trip-report-summer-iso-cpp-meeting-in-st-louis-usa) - July 2024

> "Concerns were raised that maybe it wasn't reviewed properly, as committee members were not able to fully understand the intricate design details, and instead just trusted the authors that they did a good enough job."

- **Jonathan Müller** - [Trip Report: Summer ISO C++ Meeting in St. Louis, USA](https://www.think-cell.com/en/career/devblog/trip-report-summer-iso-cpp-meeting-in-st-louis-usa) - July 2024

> "P2300 was adopted in the plenary vote and is now a part of the working draft which will become the C++26 standard, it was a very narrow vote with 1/3 voting against adoption. I expect some controversy to continue into the next meetings."

- **Jonathan Müller** - [Trip Report: Summer ISO C++ Meeting in St. Louis, USA](https://www.think-cell.com/en/career/devblog/trip-report-summer-iso-cpp-meeting-in-st-louis-usa) - July 2024

### Compiler Diagnostics and Error Messages

> "You can expose this in clang, just swap the order of the move_constructible constraint... Then compile test/exec/test_any_sender.cpp. Clang produces an error message so long (5500 lines) that it ICEs itself."

- **@seanbaxter** (Circle compiler author) - [NVIDIA/stdexec issue #856: sender concept has side effects, is order-dependent](https://github.com/NVIDIA/stdexec/issues/856) - March 2023

> "Can we just make recursive concept definitions ill-formed?"

- **@seanbaxter** - [NVIDIA/stdexec issue #856](https://github.com/NVIDIA/stdexec/issues/856#issuecomment-1487355184) - March 2023

> "I happily admit that those recursions gave me headaches."

- **@maikel** (stdexec collaborator) - [NVIDIA/stdexec issue #856](https://github.com/NVIDIA/stdexec/issues/856#issuecomment-1487236447) - March 2023

> "There's so much manual vtable work that I don't understand."

- **@seanbaxter** - [NVIDIA/stdexec issue #860: Help in locating circle codegen issue](https://github.com/NVIDIA/stdexec/issues/860) - March 2023

> "Internally the machinery seems to be confusing the derived type with the base type... Full compilation output attached." [attached was 60+ lines of template noise for a simple receiver-by-derivation usage]

- **@RobertLeahy** - [NVIDIA/stdexec issue #1408: Compile Error When Wrapping Receiver by Derivation](https://github.com/NVIDIA/stdexec/issues/1408) - August 2024

### API Confusion and Usability Surprises

> "I am trying to understand whether this is correct. What is the purpose of the set_error condition after the try/catch block if no exception was thrown? Wouldn't moving from r here twice cause undefined behavior since after the first move the object could be in an undefined state?"

- **@jtsylve** - [brycelelbach/wg21_p2300_execution issue #51: connect-awaitable correctness](https://github.com/brycelelbach/wg21_p2300_execution/issues/51) - October 2023

> "Looks like I am getting very weird compilation when trying to use let_error. I cannot specify type of the lambda to be either the actual error type nor std::exception_ptr. When I try to specify one of them, the compiler will complain it is not a well formed sender. I wonder whether this is intended and whether there are some recommended pattern for doing this?"

- **@taooceros** - [NVIDIA/stdexec issue #1564: type issue of let_error](https://github.com/NVIDIA/stdexec/issues/1564) - July 2025

> "the error message is not implying that, which makes me hard to understand."

- **@taooceros** - [NVIDIA/stdexec issue #1564](https://github.com/NVIDIA/stdexec/issues/1564#issuecomment-3050367813) - July 2025

> "The obvious solution was just use let_error([](int) .... But it's not working because of 'This is the design of stdexec'. [...] Is it fundamentally impossible? May let_* senders be implemented that way in future?"

- **@BartolomeyKant** - [NVIDIA/stdexec issue #1564](https://github.com/NVIDIA/stdexec/issues/1564#issuecomment-4090442036) - March 2026

> "This more user facing [chained let_error]. This more library internals [if constexpr overload dispatch pattern]." [arguing the recommended workaround is for library authors, not users]

- **@BartolomeyKant** - [NVIDIA/stdexec issue #1564](https://github.com/NVIDIA/stdexec/issues/1564#issuecomment-4089786873) - March 2026

> "it's counterintuitive and extremely limiting to omit the completion signatures. Without advertising completion signatures, any sender using repeat_effect essentially cannot be composed with any further senders."

- **@justend29** - [NVIDIA/stdexec issue #1782: repeat_* sender completion signature oddities](https://github.com/NVIDIA/stdexec/issues/1782) - January 2026

> "we observed in the field that it caught many programmers by surprise that a coroutine could thread-hop at co_awaits, leading to bugs."

- **@ericniebler** (P2300 author, documenting a known usability hazard) - [cplusplus/sender-receiver issue #358: with_awaitable_senders should use affine in its await_transform](https://github.com/cplusplus/sender-receiver/issues/358) - April 2026

> "Some are unclear how they would implement sender algorithms. 'If I'm writing a scheduler, what else will I have to implement at the same time?'"

- **@brycelelbach** (recording committee uncertainty) - [cplusplus/papers issue #1054: P2300 R10 std::execution](https://github.com/cplusplus/papers/issues/1054#issuecomment-887149527) - July 2021

> "3 sender channels vs 1 sender channel. What is set_error actually for? Expected errors? Unexpected errors?"

- **@brycelelbach** (recording UK delegation questions at WG21 telecon) - [cplusplus/papers issue #1054](https://github.com/cplusplus/papers/issues/1054#issuecomment-887148684) - July 2021

### Coroutine Impedance Mismatches (P4007 Gaps)

> "Every published sender implementation of I/O that the authors could find loses partial results on the error path."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "A server handling thousands of connections sees ECONNRESET constantly - clients disconnect, networks flap, load balancers probe, mobile users lose signal. Under this model, every routine disconnection that transfers zero bytes on the final call becomes an exception with stack unwinding. This contradicts twenty-five years of established I/O practice."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "For senders, no cost. For coroutines, everything." [on the asymmetric cost of the allocator propagation gap]

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "Senders get the allocator they do not need. Coroutines need the frame allocator they do not get."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "Chris Kohlhoff identified this tension in 2021 in P2430R0: 'Due to the limitations of the set_error channel (which has a single error argument) and set_done channel (which takes no arguments), partial results must be communicated down the set_value channel.' Five years and ten revisions later, the tension Kohlhoff identified remains unresolved."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "Shipping task is the risky choice, not the safe one. Four structural gaps locked in by ABI. A language change proposed to fix co_yield with_error for a channel I/O never uses. Frame allocator propagation still unsolved six months after adoption. Symmetric transfer structurally unreachable through the sender pipeline."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "A language rule that has served every coroutine library for a decade, and whose removal the committee previously declined, must now be reconsidered because one library requires it. The rule is not the problem."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "Mandating that standard networking be built on the sender model would force coroutine I/O users to pay these costs. A coroutine-native I/O research report (P4003R0) made the gaps visible by showing that partial results, error returns, cancellation, and frame allocator propagation emerge naturally when I/O is designed for coroutines."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

### Allocation and Performance Claims Disputed

> "Is this true in realistic use cases or only in minimal demos? From what I've seen, as soon as your code is complex enough that you need two compilation units, you need some higher level async abstraction, like coroutines. And as soon as you have coroutines, you need to type-erase both the senders and the scheduler, so you have at least couple of allocations per continuation."

- **u/gpderetta** - [Hacker News: Trying Out C++26 Executors](https://news.ycombinator.com/item?id=46072323) - 2025

> "I can't comment on this particular implementation but few years back I played around with a similar idea... my conclusion derived from the experiments was the same - it is allocation-heavy."

- **anonymous** - [Hacker News: Trying Out C++26 Executors](https://news.ycombinator.com/item?id=46072323) - 2025

### Immaturity / Missing Pieces

> "The implementation status of the library is not good enough. Therefore, I decided to continue with concurrency and std::execution. I will present the remaining C++26 features if a compiler implements them."

- **Rainer Grimm** - [std::execution - MC++ BLOG](https://www.modernescpp.com/index.php/stdexecution/) - Nov 18, 2024

> "Currently, no standard library provider ships senders/receivers; however, the reader can use the reference implementation of the feature [stdexec]."

- **Lucian Radu Teodorescu** - [Senders/Receivers: An Introduction](https://isocpp.org/blog/2025/01/senders-receivers-an-introduction-lucian-radu-teodorescu) - January 2025

> "Although the proposal has many advantages, there are still people who see the addition of this feature to the C++ standard at this point as a mistake. Some of the cited reasons are the complexity of the feature, compilation times, immaturity, and teachability."

- **Lucian Radu Teodorescu** - [Senders/Receivers: An Introduction](https://isocpp.org/blog/2025/01/senders-receivers-an-introduction-lucian-radu-teodorescu) - January 2025

> "P2300, by contrast, ships without a thread pool, without a coroutine task type, and with a 'paltry set' of algorithms. As P3109 acknowledges, users 'will need to go to third party libraries for thread-pools, or write their own.' The irony is acute: the proposal justified by avoiding third-party dependencies requires third-party dependencies to be useful."

- **Vinnie Falco** - [Against std::execution: A Case for Standard Networking and Third-Party Parallelism](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 17, 2025

> "Three of the four algorithms in the motivating example for std::execution are not part of C++26." [referring to stop_when, timeout, and first_successful]

- **Vinnie Falco, Mungo Gill** - [P4014R0: The Sender Sub-Language](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4014r0.pdf) - 2026-02-22

> "Partial implementation: P2300 assumes the existence of many algorithms which are clearly labeled as 'Not yet implemented' in the libunifex repository."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0: Response to P2464](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "There was a significant argument before the vote that senders/receivers are not teachable... There was also an argument that the diagnostics of the library implementing senders/receivers are quite poor."

- **Lucian Radu Teodorescu** - [Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 12, 2024

> "I don't think it's fair to consider standardizing S&R until there are at least a thousand codebases that use S&R. The probability of missing an important use-case, or an important gotcha is very very high if the actual quantity of 'Junior engineer + intern' experience in the field is low."

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

### Design Critique: P2300 is Not a Complete Async Model

> "P2300 does not propose an asynchronous model, it proposes a DSL for composing asynchronous operations which assumes an asynchronous model."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0: Response to P2464](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "This shows that P2300 is not a complete asynchronous model, but rather a DSL for composing and creating graphs of operations. It does not specify everything that is required for correct, safe-by-default use of asynchronicity, and relies on the user to take care when structuring their code around other senders."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "As specified in P2300, sender operations such as async_read_some are permitted to complete with a reentrant call to the receiver. Assuming an always-ready pipe, the only thing that stops this from causing stack overflow is the use of the typed_via algorithm. If we remove the typed_via, an always-ready pipe results in unbounded recursion. This puts the onus on the user to insert a typed_via, or equivalent, between asynchronous operations, to break the asynchronous loop... This is user-hostile as default behaviour."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "What is set_error for? Nominally set_error's purpose is to send an 'error signal' to a receiver but it's unclear what the exact intention is for 'error signals'... If the latter then the channel seems doomed to be misused. Users almost certainly won't interpret 'error' so narrowly."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "Absent from P2300 and libunifex is visible experience with adapting the model to different continuation styles... There is no visible analysis of P2300 covering allocation strategies, no user experience regarding optimized allocation strategies."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "The proposed solution in P2300 forces a single composition mechanism, one for which we have limited field experience, on every user."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

### std::execution::task Concerns

> "I have strong concerns about its [ex::task] design and urge the committee to reconsider."

- **Jonathan Müller** - [P3801R0: Concerns about the design of std::execution::task](https://isocpp.org/files/papers/P3801R0.html) - 2025

> "Having iterative code that is actually recursive is a potential security vulnerability."

- **Jonathan Müller** - [P3801R0: Concerns about the design of std::execution::task](https://isocpp.org/files/papers/P3801R0.html) - 2025

> "This is surprising behavior that can lead to unnecessary memory consumption and potentially hard to figure out bugs. It fundamentally breaks the promises of RAII where destruction is strictly tied to the end of a scope."

- **Jonathan Müller** - [P3801R0: Concerns about the design of std::execution::task](https://isocpp.org/files/papers/P3801R0.html) - 2025

> "As a standardization committee, we are drafting a standard that should outlive us. We are not working on some open-source library, we are designing the foundation for an entire ecosystem. If something has issues, and we know that it has issues, we should not have allowed a vote to approve it."

- **Jonathan Müller** - [P3801R0: Concerns about the design of std::execution::task](https://isocpp.org/files/papers/P3801R0.html) - 2025

> "The chain of events seems to be: [...] Destroying the spawn state destroys the task operation, which destroys the currently executing task coroutine frame, including the sender awaiter whose await_suspend() has not returned yet." [report of production crash]

- **@mika-fischer** - [NVIDIA/stdexec issue #2047: Another crash with stdexec::task (again probably premature coro destruction)](https://github.com/NVIDIA/stdexec/issues/2047) - April 2026

### Algorithm Customization is Broken

> "Early customization is irreparably broken and must be removed... The end result of all of this is that a default (which is effectively a CPU) implementation will be used to evaluate the then algorithm on the GPU. That is a bad state of affairs."

- **Eric Niebler** - [P3826R1: Fix or Remove Sender Algorithm Customization](https://isocpp.org/files/papers/P3826R1.html) - 2026

> "While the sender/receiver concepts and the algorithms themselves have been stable for several years now, the customization mechanism has seen a fair bit of recent churn."

- **Eric Niebler** - [P3826R1: Fix or Remove Sender Algorithm Customization](https://isocpp.org/files/papers/P3826R1.html) - 2026

### Committee Process Criticism

> "By standardizing P2300 before it has achieved Boost.Asio-level adoption, WG21 is attempting to confer borrowed power on a design that has not earned owned power. The risk is that the standard enshrines an inferior or premature design, crowding out potentially superior alternatives."

- **Vinnie Falco** - [Against std::execution: A Case for Standard Networking and Third-Party Parallelism](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 17, 2025

> "The standardization of P2300 over the Networking TS represents a strategic error driven by corporate capture (NVIDIA/Meta's parallel computing interests trumping universal networking needs), cultural dysfunction (the assumption that dependencies are unacceptable), and institutional sclerosis (the inability to ship stable, complete facilities in reasonable timeframes)."

- **Vinnie Falco** - [Against std::execution: A Case for Standard Networking and Third-Party Parallelism](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 17, 2025

> "WG21 no longer has the social technology to advance the standard in a manner that represents the best interests of the wider C++ community."

- **u/VinnieFalco** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "The committee process's priorities seem to have gone awry in recent times - favouring standardisation of new, minimally used ideas over well established practice... lately we seem to prefer favouring the elusive type of perfection that is only achievable with ideas and not actual implementations, where reality bites and bites hard."

- **Christopher Kohlhoff, Jamie Allsop, Vinnie Falco, Richard Hodges, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "These people do what they want, with their own agenda, and they don't care whose toes they step on. In my opinion WG21 is no longer capable of representing the needs of ordinary C++ users. I do not participate in WG21 anymore."

- **u/VinnieFalco** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "Standardizing P2300 is bad for everyone, because it lends even more argument fodder from the policies of idiots that using something that isn't standardized is bad. 'Can't use Asio because we have P2300, now stop asking and get back to your brainfuck++ code.'"

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "LEWG was given a false choice between the NetTS and sender/receiver. They chose, and now C++23 will lack networking. Pointless."

- **u/eric_niebler** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "I don't want to end up in a situation where some of senders/receivers are in, but crucial modifications (such as the diagnostic improvements) missed the C++26 deadline and cannot be applied later on when breaking changes are no longer possible."

- **Jonathan Müller** - [Trip Report: Summer ISO C++ Meeting in St. Louis, USA](https://www.think-cell.com/en/career/devblog/trip-report-summer-iso-cpp-meeting-in-st-louis-usa) - July 2024

---

## PRO Asio / Networking TS

> "The asynchronous model of Asio/Net.TS has evolved to support new use cases while also being careful not to leave existing use cases behind, and the strength of the composition model is testament to that. The model is the result of growth and adaptation from use in the real world, and is one reason it is so widely deployed."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "Asio/Net.TS is exactly the foundational, scalable asynchronous model upon which the higher level abstractions proposed in P2300 can and should be layered. Put simply, the DSL proposed by P2300 does not enable any missing functionality, and could be added in the future, after evolution to address support for a wider variety of use cases."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "The asynchronous model in the Asio/Net.TS offers a superset of the functionality exposed through P2300."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "Apart from being a proven, resilient, and much needed addition to the C++ Standard, the Networking TS also meets all the requirements listed in the Chair-Theory guidelines: Implementation experience: more than 18 years. Usage experience: many companies and open source projects, across many domains. Deployment experience: more than 18 years, both standalone and in Boost."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "Currently 'The C++ Standard can't access the Internet.' This is embarrassing and long overdue. We should continue with the standardisation of the Networking TS for C++23, with its universal asynchronous model built on extensible completion tokens."

- **Jamie Allsop, Vinnie Falco, Richard Hodges, Christopher Kohlhoff, Klemens Morgenstern** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "We can see the same or similar customisation points, with an equivalent executor-as-policy-object, in other successful asynchronous models, including: Grand Central Dispatch as 'DispatchQueue', Swift structured concurrency as 'Executor', Java Netty library as 'EventExecutor', .NET as 'SynchronizationContext'. While they differ in the details, this convergent evolution is indicative of the underlying requirement driving the design of asynchronous models."

- **Christopher Kohlhoff et al.** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "Asio/Net.TS has been proven as the foundation of multiple second order libraries, such as the widely used Boost.Beast, which in turn have enabled the development of a third order library ecosystem."

- **Christopher Kohlhoff et al.** - [P2469R0](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Oct 4, 2021

> "There is no one-size-fits-all approach to composition. This paper presents a high-level overview of the asynchronous model at the core of the Asio library. This model enshrines asynchronous operations as the fundamental building block of asynchronous composition, but in a way that decouples them from the composition mechanism. The asynchronous operations in Asio support callbacks, futures (both eager and lazy), fibers, coroutines, and approaches yet to be imagined."

- **Christopher Kohlhoff** - [P2444R0: The Asio Asynchronous Model](https://isocpp.org/files/papers/P2444R0.pdf) - 2021-09-15

> "An asynchronous agent's associated executor represents a policy of how, where, and when the agent should run, specified as a cross-cutting concern to the code that makes up the agent."

- **Christopher Kohlhoff** - [P2444R0: The Asio Asynchronous Model](https://isocpp.org/files/papers/P2444R0.pdf) - 2021-09-15

> "Kohlhoff designed Boost.Asio with error codes precisely because I/O errors are not exceptional - they are the normal texture of network programming. The C++ I/O ecosystem is built on if (ec)."

- **Vinnie Falco, Mungo Gill** - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

> "Networking is infrastructure. Every web server, every database client, every distributed system, every IoT device, every cloud application requires network I/O. The Networking TS, derived from Boost.Asio, represents over two decades of production deployment across thousands of applications. Chris Kohlhoff's design has been battle-tested in contexts ranging from high-frequency trading to embedded systems."

- **Vinnie Falco** - [Against std::execution: A Case for Standard Networking and Third-Party Parallelism](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 17, 2025

> "Boost.Asio's async model has remained largely stable since its introduction. Applications written against it fifteen years ago continue to function. This stability reflects design maturity - the problem space is well-understood, the abstraction boundaries are clear, and the failure modes are documented."

- **Vinnie Falco** - [Against std::execution: A Case for Standard Networking and Third-Party Parallelism](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 17, 2025

> "Arguments that the Networking TS's executor model was 'inadequate for heterogeneous computing' are true but irrelevant. Networking doesn't need heterogeneous computing. A TCP server does not run on GPUs. The demand that networking wait for a unified async model that also serves CUDA was a category error that cost the C++ community a decade."

- **Vinnie Falco** - [Against std::execution: A Case for Standard Networking and Third-Party Parallelism](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 17, 2025

> "The Networking TS ships as a complete, usable facility. A developer can write a TCP server using only the TS's abstractions."

- **Vinnie Falco** - [Against std::execution: A Case for Standard Networking and Third-Party Parallelism](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 17, 2025

> "Chris went out of his way to accommodate sender/receiver, even going so far as incorporating it into Asio to provide implementation experience. He also hosted video calls with networking domain experts already familiar with Asio in order to educate and solicit feedback - in his own time. The result of those sessions... was that there was no perceived use case for sender/receiver and absolutely no appetite for the domain-specific language which P2300 is proposing."

- **u/madmongo38** (Richard Hodges) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "On a positive note, the process has been healthy for Asio (if not for Chris, who spent his own personal time rebutting claims made with the benefit of corporate sponsorship)."

- **u/madmongo38** (Richard Hodges) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "My opinion on this decision is that it's the best thing to happen to Asio since, well, at least five years. The only regret is that the committee should have done this sooner, before wasting tons of Chris's (and occasionally his users') time for approximately zero benefit to anyone." [commenting on the Networking TS being freed from LEWG process]

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "I've used Boost.Asio in at least 3 different codebases for three different companies. I've never once had a reason or desire to use libunifex and other than Facebook, have not heard of anyone using it either."

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "Asio is a foundational library. If you see how general it is and what it has achieved to do (futures, coroutines, callbacks, cancellation, deferred, UDP, TCP, serial ports, unix sockets...) there is no doubt that it does way more and better than anything out there, at least in C++."

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "I continue to think that ASIO has a proven track record, and would have no qualms recommending it for someone looking for a networking library in C++."

- **u/Steve_Downey** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "The end-goal of p2300 is an abstract DSL that serves the perceived needs of one company."

- **u/madmongo38** (Richard Hodges) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

---

## AGAINST Asio / Networking TS

> "LEWG won't be pursuing P2444 as a general async model." [Poll 1 result: Weak Consensus Against - 5 SF / 10 WF / 6 N / 14 WA / 18 SA]

- **Bryce Adelstein Lelbach** (LEWG Vice Chair) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Nov 2021

> "LEWG no longer has consensus to standardize the Networking TS."

- **Bryce Adelstein Lelbach** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Nov 2021

> "Let me be honest though - Asio hasn't really won the hearts and minds of C++ programmers. The fact that there needed to be another complex and complicated library on top of Asio to simply make it useful isn't really proof that this is the right direction."

- **anonymous** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "Much is made of how old and stable ASIO is. The truth is that since sender/receiver turned up, ASIO has changed significantly, and not always been able to do so cleanly."

- **u/eric_niebler** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "The thing that breaks my heart is that we had to compete instead of collaborate. Judging from how much sender/receiver functionality has since landed in ASIO, Chris certainly saw some value in the work. Why waste time arguing and reinventing everything? We could be so much farther along now!"

- **u/eric_niebler** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "It is still not clear to me what happened. One issue is that there was no big company behind asio and some companies were looking for a more general framework. Still for what I have seen, sender/receiver only deal with composing async operations, the proposal so far still lack an actual network executor, so it is far from being ready. This is a shame I think, because while asio might not have been perfect it means that in 2024 C++ still lacks a network library."

- **anonymous** - [Hacker News: What are senders good for, anyway?](https://news.ycombinator.com/item?id=39261268) - Feb 2024

> "It's not like C++ devs have much choice but to deal with this stuff since Asio was effectively kicked out of standardisation."

- **anonymous** - [Hacker News: What are senders good for, anyway?](https://news.ycombinator.com/item?id=39261268) - Feb 2024

> "I don't believe [ASIO] is the best fit for all async work, even if it can be made to function."

- **u/Steve_Downey** - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "Some of us still care about compile times and being able to apply the Pimpl idiom. This is not possible when our libraries are forced to be header-only because of Asio."

- **@ecorm** - [chriskohlhoff/asio issue #1100: Feature request: Type-erased handler wrapper](https://github.com/chriskohlhoff/asio/issues/1100) - July 2022

> "It became clear during our discussion that the Networking TS has an async model distinct from senders/receivers. This was true with P0443 and P2300, so this is not a regression in the new proposal." [framing the Networking TS as fundamentally incompatible]

- **@brycelelbach** - [cplusplus/papers issue #1054](https://github.com/cplusplus/papers/issues/1054#issuecomment-887149527) - July 2021

> "SG4 polled at Kona (November 2023) on P2762R2 ('Sender/Receiver Interface For Networking'): 'Networking should support only a sender/receiver model for asynchronous operations; the Networking TS's executor model should be removed' - SF:5 F:5 N:1 A:0 SA:1. Consensus."

- **Vinnie Falco, Mungo Gill** (citing the SG4 committee poll result) - [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - 2026-02-22

---

## Committee Dynamics & Process

### Formal Poll Results (2021 LEWG Electronic Ballot)

Source: [Bryce Adelstein Lelbach, r/cpp](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Nov 3, 2021

| Poll | SF | WF | N | WA | SA | Result |
|---|---|---|---|---|---|---|
| Poll 1: NetTS/Asio is good basis for most async use cases | 5 | 10 | 6 | 14 | 18 | **Weak Consensus Against** |
| Poll 2: S&R (P2300) is good basis for most async use cases | 24 | 16 | 3 | 6 | 3 | **Consensus In Favor** |
| Poll 3: Stop pursuing Networking TS | 13 | 13 | 8 | 6 | 10 | **No Consensus** |
| Poll 4: Networking should be based on P2300 | 17 | 11 | 10 | 4 | 6 | **Weak Consensus In Favor** |

### Plenary Vote: P2300 into C++26 (June 2024, St. Louis)

> "P2300 was adopted in the plenary vote and is now a part of the working draft which will become the C++26 standard, it was a very narrow vote with 1/3 voting against adoption."

- **Jonathan Müller** - [Trip Report: Summer ISO C++ Meeting in St. Louis, USA](https://www.think-cell.com/en/career/devblog/trip-report-summer-iso-cpp-meeting-in-st-louis-usa) - July 2024

### One Committee Member's Personal Vote (Posted Publicly)

> "POLL 1: The Networking TS/Asio async model is a good basis for most asynchronous use cases, including networking, parallelism, and GPUs. 1-Strong For. Comments: Asio/Net.TS is proven in multiple disciplines, many corporations. POLL 2: The senders/receivers model is a good basis for most asynchronous use cases, including networking, parallelism, and GPUs. 5-Strong Against. Comments: Senders/Receivers is not foundational, it is high level. The DSL it aims to enable is certainly interesting and useful, but as a higher level abstraction it can and should be layered on top of the more foundational Net.TS/Asio. POLL 3: Stop pursuing the Networking TS design as the C++ Standard Library's answer for networking. 5-Strong Against. Comments: Its been 6 years since Net.TS was published and 18 years of Asio. Inventing something new and pushing it through ahead of the Net.TS to replace it, is quite frankly disrespectful. Not only does it disrespect the author of the TS who is more of a subject matter expert than anyone else in the committee, but it disrespects everyone who wrote papers on top of it expecting a high likelihood of acceptance. The message it sends to the C++ community is terrible: don't bother participating in WG21 or taking time to write papers, as your work can be discarded on a whim based on shifting political winds."

- **u/VinnieFalco** (Vinnie Falco) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Nov 2021

### On Corporate Influence

> "Yes, we are invested in having a standard abstraction that works for both CPUs and GPUs, I don't know how that's in the least surprising :)"

- **u/Griwes** (Michał Dominiak, NVIDIA, P2300 author) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

> "The committee operates by having technical discussions on technical merits, and that is what is going to be happening now that we've found a direction we want to pursue."

- **u/Griwes** (Michał Dominiak, NVIDIA) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

### On Access and Participation

> "There are members of WG21 who fund their attendance 100% out of their vacation time and their own money because their employer won't support them, and they live somewhere where there are no employers who would support them."

- **u/niallouglas** (Niall Douglas) - [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct 2021

---

## Sources Index

- [r/cpp: C++ committee polling results for asynchronous programming](https://old.reddit.com/r/cpp/comments/q6tgod/c_committee_polling_results_for_asynchronous/) - Oct/Nov 2021
- [r/wg21: P4007R0 - Senders and Coroutines](https://cppalliance.org/r/wg21/p4007r0-reddit.html) - Feb 2026
- [Hacker News: What are senders good for, anyway?](https://news.ycombinator.com/item?id=39261268) - Feb 2024
- [Hacker News: Std: Execution, Sender/Receiver, and the Continuation Monad](https://news.ycombinator.com/item?id=28894851) - Sep 2021
- [Hacker News: Show HN: Coros - A Modern C++ Library for Task Parallelism](https://news.ycombinator.com/item?id=41647025) - Sep 2024
- [Hacker News: Trying Out C++26 Executors](https://news.ycombinator.com/item?id=46072323) - 2025
- [Eric Niebler: What are Senders Good For, Anyway?](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/) - Feb 2024
- [Herb Sutter: Trip report: Summer ISO C++ standards meeting (St Louis)](https://herbsutter.com/2024/07/02/trip-report-summer-iso-c-standards-meeting-st-louis-mo-usa/) - July 2024
- [Jonathan Müller: Trip Report: Summer ISO C++ Meeting in St. Louis, USA](https://www.think-cell.com/en/career/devblog/trip-report-summer-iso-cpp-meeting-in-st-louis-usa) - July 2024
- [Lucian Radu Teodorescu: Senders/receivers in C++](http://lucteo.ro/2024/08/12/senders-receivers-in-cxx/) - Aug 2024
- [Lucian Radu Teodorescu: Senders/Receivers: An Introduction (ACCU Overload 184)](https://isocpp.org/blog/2025/01/senders-receivers-an-introduction-lucian-radu-teodorescu) - Jan 2025
- [Lucian Radu Teodorescu: Using Senders/Receivers](https://isocpp.org/blog/2025/04/using-senders-receivers-lucian-radu-teodorescu) - Apr 2025
- [Ben FrantzDale: Sender Intuition: Senders Don't Send](https://benfrantzdale.github.io/blog/2024/10/01/sender-intuition-senders-dont-send.html) - Oct 2024
- [Vinnie Falco: Against std::execution](https://www.vinniefalco.com/p/against-stdexecution-a-case-for-standard) - Dec 2025
- [Rainer Grimm: std::execution - MC++ BLOG](https://www.modernescpp.com/index.php/stdexecution/) - Nov 2024
- [P2469R0: Response to P2464](https://open-std.org/jtc1/sc22/wg21/docs/papers/2021/p2469r0.pdf) - Allsop, Falco, Hodges, Kohlhoff, Morgenstern - Oct 2021
- [P2444R0: The Asio Asynchronous Model](https://isocpp.org/files/papers/P2444R0.pdf) - Christopher Kohlhoff - Sep 2021
- [P3109R0: A Plan for std::execution for C++26](https://open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3109r0.html) - Baker, Niebler, Shoop, Teodorescu - Feb 2024
- [P4007R0: Senders and Coroutines](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - Falco, Gill - Feb 2026
- [P4014R0: The Sender Sub-Language](https://open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4014r0.pdf) - Falco, Gill - Feb 2026
- [P3826R1: Fix or Remove Sender Algorithm Customization](https://isocpp.org/files/papers/P3826R1.html) - Eric Niebler - 2026
- [P3801R0: Concerns about the design of std::execution::task](https://isocpp.org/files/papers/P3801R0.html) - Jonathan Müller - 2025
- [NVIDIA/stdexec issue #856: sender concept has side effects, is order-dependent](https://github.com/NVIDIA/stdexec/issues/856) - seanbaxter - Mar 2023
- [NVIDIA/stdexec issue #860: Help in locating circle codegen issue](https://github.com/NVIDIA/stdexec/issues/860) - seanbaxter - Mar 2023
- [NVIDIA/stdexec issue #1408: Compile Error When Wrapping Receiver by Derivation](https://github.com/NVIDIA/stdexec/issues/1408) - RobertLeahy - Aug 2024
- [NVIDIA/stdexec issue #1564: type issue of let_error](https://github.com/NVIDIA/stdexec/issues/1564) - taooceros, BartolomeyKant - Jul 2025 / Mar 2026
- [NVIDIA/stdexec issue #1782: repeat_* sender completion signature oddities](https://github.com/NVIDIA/stdexec/issues/1782) - justend29 - Jan 2026
- [NVIDIA/stdexec issue #2047: crash with stdexec::task](https://github.com/NVIDIA/stdexec/issues/2047) - mika-fischer - Apr 2026
- [cplusplus/sender-receiver issue #358: with_awaitable_senders should use affine](https://github.com/cplusplus/sender-receiver/issues/358) - ericniebler - Apr 2026
- [cplusplus/papers issue #1054: P2300 R10 std::execution](https://github.com/cplusplus/papers/issues/1054) - brycelelbach - Jul 2021
- [chriskohlhoff/asio issue #1100: Feature request: Type-erased handler wrapper](https://github.com/chriskohlhoff/asio/issues/1100) - ecorm - Jul 2022
- [brycelelbach/wg21_p2300_execution issue #51: connect-awaitable correctness](https://github.com/brycelelbach/wg21_p2300_execution/issues/51) - jtsylve - Oct 2023
