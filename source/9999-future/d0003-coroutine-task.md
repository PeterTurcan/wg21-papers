---
title: "Coroutine Task"
document: D0003R0
date: 2026-05-15
intent: ask
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

This paper asks the committee to advance `task<T>` - a lazy coroutine task with one template parameter - as standard library vocabulary, together with the launch functions `run()` and `run_async()`, a `thread_pool` execution context, and a `system_context` process-wide singleton.

Every [Corosio](https://github.com/cppalliance/corosio)<sup>[2]</sup> example and test uses `task<T>` with `run()`. Every [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> consumer returns `task<T>`. The type has one template parameter because `coroutine_handle<>` erases the coroutine's type structurally. No allocator parameter. No executor parameter. No scheduler parameter. The IoAwaitable protocol propagates context through `await_suspend` - the task type stays simple.

The companion paper *Coroutine Task: Design Rationale*<sup>[8]</sup> provides the design rationale, the convergence record across five ecosystems, anticipated objections, and the implementation inventory. Read this paper for the proposal; read the companion when you need the audit trail.

This paper is Paper 2 in the series defined by [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[4]</sup>. It depends on Paper 1 (the IoAwaitable Protocol, [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf)<sup>[5]</sup> and [P4172R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4172r0.pdf)<sup>[6]</sup>). The [Networking TS](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[7]</sup> defined executor and completion token machinery; this paper recovers the task shape on a coroutine-native track.

---

## Revision History

### R0: May 2026 (post-Brno mailing)

* Initial Version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author maintains [Boost.Beast](https://github.com/boostorg/beast)<sup>[3]</sup> and develops [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[2]</sup>, plus three further Boost libraries built on them. Every asynchronous entry point in these libraries returns `task<T>`. [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html)<sup>[9]</sup> ships `awaitable<T>`, the predecessor shape. The body of work creates a bias toward a single coroutine task type.

This paper is the proposal-only ask paper for `task<T>`, the launch functions, and the execution contexts. The design rationale lives in the companion *Coroutine Task: Design Rationale*<sup>[8]</sup>. The IoAwaitable protocol that `task<T>` implements is defined in [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf)<sup>[5]</sup> and [P4172R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4172r0.pdf)<sup>[6]</sup>.

---

## 2. What This Paper Asks

The committee is asked to advance the following vocabulary for the standard library:

```cpp
namespace std::io {

  template<class T = void>
  class task;                       // lazy coroutine task

  template<class T>
  T run(task<T>);                   // block until complete

  template<class T>
  void run_async(task<T>);          // submit for execution

  class thread_pool;                // multi-threaded execution context
  class system_context;             // process-wide singleton

}
```

One task type. Two launch functions. Two execution contexts.

---

## 3. The Task

### 3.1 Shape

`task<T>` is a lazy, single-consumer coroutine return type. It satisfies `IoAwaitable`.

```cpp
template<class T = void>
class task
{
public:
    using value_type = T;

    struct promise_type;

    task(task&& other) noexcept;
    task& operator=(task&& other) noexcept;
    ~task();

    task(task const&) = delete;
    task& operator=(task const&) = delete;
};
```

`task<T>` is move-only. It is not copyable. It is not default-constructible. The coroutine does not start until the task is awaited or launched with `run()` or `run_async()`.

### 3.2 One Template Parameter

`task<T>` has one template parameter: the result type. There is no allocator parameter, no executor parameter, no scheduler parameter. The type-erasure that makes this possible is structural: `coroutine_handle<>` erases the coroutine's promise type, and the IoAwaitable protocol propagates the execution context through `await_suspend` at the point of co_await.

```cpp
std::io::task<response> handle_request(std::io::any_stream& stream)
{
    auto [ec, req] = co_await read_request(stream);
    if (!ec)
    {
        auto res = process_request(req);
        std::tie(ec) = co_await write_response(stream, res);
    }
    co_return {ec};
}
```

The function signature names `task<response>`. It does not name the executor that will run it, the allocator that will allocate its frame, or the stop token that will cancel it. Those are propagated by the IoAwaitable protocol at co_await time. The caller's execution context flows into the callee. The callee does not need to know.

### 3.3 Lazy, Not Eager

`task<T>` is lazy. The coroutine body does not execute until the task is awaited or launched. Lazy start has three consequences:

1. **No dangling.** The coroutine cannot run before the caller has bound the execution context.
2. **No wasted work.** A task that is never awaited never runs. A task that is cancelled before it starts never allocates I/O resources.
3. **Composability.** `when_all(task_a(), task_b())` constructs both tasks, then starts them together. The combinator controls the start order.

### 3.4 Promise Type

The promise type implements the IoAwaitable protocol. It holds the execution context, the stop token, and the frame allocator - all propagated from the parent coroutine through `await_suspend`.

```cpp
struct task<T>::promise_type
{
    std::suspend_always initial_suspend() noexcept;
    /* unspecified */ final_suspend() noexcept;

    task<T> get_return_object() noexcept;

    template<class U>
    void return_value(U&& value);   // when T is not void

    void return_void();              // when T is void

    void unhandled_exception();

    // IoAwaitable protocol hooks
    template<class Awaitable>
    decltype(auto) await_transform(Awaitable&& a);

    // Frame allocator support
    static void* operator new(std::size_t n);
    static void operator delete(void* p, std::size_t n);
};
```

`initial_suspend()` returns `std::suspend_always` - the coroutine is lazy. `final_suspend()` returns an awaiter that transfers control back to the parent via symmetric transfer. `await_transform` injects the IoAwaitable protocol into every co_await expression inside the coroutine.

### 3.5 co_await Behaviour

Awaiting a `task<T>` from within another coroutine does the following:

1. `await_ready()` returns `false`. The task has not started.
2. `await_suspend(parent_handle)` captures the parent's coroutine handle for symmetric transfer. The parent's execution context, stop token, and frame allocator are propagated to the child's promise.
3. The child coroutine begins execution.
4. When the child completes, `final_suspend` resumes the parent via symmetric transfer - no stack buildup, no intermediate dispatch.
5. `await_resume()` returns the child's result or rethrows its exception.

**One type. One parameter. The frame does the rest.**

---

## 4. Launch Functions

### 4.1 `run()`

```cpp
template<class T>
T run(task<T> t);
```

`run()` blocks the calling thread until the task completes. It creates a temporary execution context (or uses `system_context`), starts the task, and runs the event loop until the task's result is available.

```cpp
int main()
{
    auto result = std::io::run(do_work());
    std::cout << result << "\n";
}
```

`run()` is the bridge from synchronous `main()` to asynchronous coroutine code. It is the entry point. Every Corosio example begins with `run()`.

### 4.2 `run_async()`

```cpp
template<class T>
void run_async(task<T> t);
```

`run_async()` submits the task for execution on the current execution context without blocking. The task runs concurrently with other tasks on the same context. The caller does not wait for the result.

```cpp
std::io::task<> accept_loop(std::io::tcp_acceptor& acceptor)
{
    for (;;)
    {
        auto [ec, stream] = co_await acceptor.accept();
        if (ec) break;
        std::io::run_async(handle_client(std::move(stream)));
    }
}
```

`run_async()` is fire-and-forget at the coroutine level. The execution context keeps the task alive until it completes. The task inherits the caller's execution context through the IoAwaitable protocol.

---

## 5. Execution Contexts

### 5.1 `thread_pool`

```cpp
class thread_pool
{
public:
    explicit thread_pool(std::size_t thread_count);
    ~thread_pool();

    thread_pool(thread_pool const&) = delete;
    thread_pool& operator=(thread_pool const&) = delete;

    using executor_type = /* unspecified */;
    executor_type get_executor() noexcept;

    void join();
    void stop();
};
```

`thread_pool` is a multi-threaded execution context. It satisfies `execution_context`. Its executor satisfies `Executor` (defined in [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf)<sup>[5]</sup>). Coroutines dispatched to the pool run on any of the pool's threads.

```cpp
int main()
{
    std::io::thread_pool pool(4);
    std::io::run(pool, do_work());
    pool.join();
}
```

### 5.2 `system_context`

```cpp
class system_context
{
public:
    system_context(system_context const&) = delete;
    system_context& operator=(system_context const&) = delete;

    static system_context& instance() noexcept;

    using executor_type = /* unspecified */;
    executor_type get_executor() noexcept;

    void join();
    void stop();
};
```

`system_context` is a process-wide singleton. It is backed by a `thread_pool` whose thread count is implementation-defined (typically `std::thread::hardware_concurrency()`). It provides a default execution context for programs that do not need to manage their own pool.

```cpp
int main()
{
    auto result = std::io::run(do_work());
    return result;
}
```

When `run()` is called without an explicit execution context, it uses `system_context::instance()`.

---

## 6. Standalone Value

After Papers 1 and 2, Asio users get `task<T>` with frame allocator propagation as a drop-in replacement for `asio::awaitable<T>`.

```cpp
// Before: Asio-coupled
asio::awaitable<response>
handle_request(asio::ip::tcp::socket& sock);

// After: standard vocabulary, backend-agnostic
std::io::task<response>
handle_request(std::io::any_stream& stream);
```

Three gains:

1. **Physical insulation.** Business logic drops the Asio header dependency. The header declares `task<response>`. Consumers include neither Asio nor Corosio.
2. **Compilation improvement.** Fewer translation units include Asio headers. The heavy machinery is confined to the files that need it.
3. **Backend insulation.** Swap Asio for Corosio by recompiling one `.cpp` file. Consumers never recompile. Headers do not change.

**`task<T>` is the return type the ecosystem shares. `run()` is the entry point every program needs.**

---

## 7. Suggested Straw Poll

> LEWG agrees that the coroutine task vocabulary `task<T>`, `run()`, `run_async()`, `thread_pool`, and `system_context` documented in this paper and its companion *Coroutine Task: Design Rationale* should be advanced as standard library vocabulary for coroutine-native I/O.

---

## Acknowledgments

Gor Nishanov and Lewis Baker designed C++20 coroutines - the language mechanisms that make `task<T>` possible. `coroutine_handle<>`, `promise_type`, symmetric transfer, and stackless frames are their work. This paper builds on it.

Christopher Kohlhoff designed Asio's executor model and the stream architecture that `task<T>` integrates with through the IoAwaitable protocol.

The `std::execution` authors ([P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)<sup>[10]</sup>) - Eric Niebler, Kirk Shoop, Lewis Baker, and their collaborators - explored execution contexts and schedulers. `thread_pool` and `system_context` in this paper serve the same role for coroutine-native I/O that their schedulers serve for sender-based composition.

---

## References

[1] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[2] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[3] [Boost.Beast](https://github.com/boostorg/beast) - HTTP and WebSocket built on Boost.Asio (Vinnie Falco, 2017-2026).

[4] [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[5] [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf) - "A Minimal Coroutine Execution Model" (Vinnie Falco, Steve Gerbino, Mungo Gill, 2026).

[6] [P4172R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4172r0.pdf) - "IoAwaitable for Coroutine-Native Byte-Oriented I/O" (Vinnie Falco, Steve Gerbino, Mungo Gill, 2026).

[7] [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf) - "Working Draft, C++ Extensions for Networking" (Jonathan Wakely, 2018).

[8] *Coroutine Task: Design Rationale* (Vinnie Falco, 2026). Companion design paper. D0004R0.

[9] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - Executor model and completion tokens (Christopher Kohlhoff, 2003-2026).

[10] [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) - "`std::execution`" (Micha&lstrok; Dominiak, Georgy Evtushenko, Lewis Baker, Lucian Radu Teodorescu, Lee Howes, Kirk Shoop, Michael Garland, Eric Niebler, Bryce Adelstein Lelbach, 2024).
