---
title: "Timers"
document: D0015R0
date: 2026-05-15
intent: ask
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

This paper asks the committee to advance a timer type for coroutine-native I/O.

The timer is the simplest kernel interaction in the [Network Endeavor](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[1]</sup>. It proves the IoAwaitable protocol ([P4003R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r3.pdf)<sup>[2]</sup>) works end-to-end with a real operating system. One type, five member functions, one clock. The proposal is `std::io::timer` - an awaitable deadline that the kernel enforces. It is the first paper in Stage Two: Platform I/O.

The companion paper *Timers: Design Rationale*<sup>[3]</sup> provides the platform mapping, the convergence record across six ecosystems, anticipated objections, and the implementation inventory. Read this paper for the proposal; read the companion when you need the audit trail.

This paper is Paper 8 in the series defined by [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[1]</sup>. It depends on Paper 1 (IoAwaitable Protocol, [P4003R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r3.pdf)<sup>[2]</sup>).

---

## Revision History

### R0: May 2026 (post-Brno mailing)

* Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author maintains [Boost.Beast](https://github.com/boostorg/beast)<sup>[4]</sup> and develops [Capy](https://github.com/cppalliance/capy)<sup>[5]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[6]</sup>, plus three further Boost libraries built on them. Corosio ships a timer type on three platforms. The body of work creates a bias toward a dedicated timer type in the standard.

---

## 2. What This Paper Asks

The committee is asked to advance the following type for the standard library:

```cpp
namespace std::io {

  class timer {
  public:
    explicit timer(execution_context& ctx);
    timer(execution_context& ctx,
        std::chrono::steady_clock::time_point expiry);
    timer(execution_context& ctx,
        std::chrono::steady_clock::duration after);

    timer(timer const&) = delete;
    timer& operator=(timer const&) = delete;
    timer(timer&&) noexcept;
    timer& operator=(timer&&) noexcept;

    ~timer();

    IoAwaitable auto wait();

    void expires_at(
        std::chrono::steady_clock::time_point t);
    void expires_after(
        std::chrono::steady_clock::duration d);
    std::chrono::steady_clock::time_point expiry() const;

    std::size_t cancel();
    std::size_t cancel_one();
  };

}
```

One type. Three constructors. One awaitable operation. Two deadline setters. One deadline getter. Two cancellation functions.

---

## 3. The Timer Type

### 3.1 Construction

A timer is constructed with a reference to an `execution_context` - the event loop that will deliver the completion. Three constructors are provided:

```cpp
std::io::execution_context ctx;

// No initial deadline - caller must set one before waiting.
std::io::timer t1(ctx);

// Absolute deadline.
std::io::timer t2(ctx,
    std::chrono::steady_clock::now() + 5s);

// Relative deadline (equivalent to the above).
std::io::timer t3(ctx, 5s);
```

The timer holds a non-owning reference to the execution context. The execution context must outlive the timer.

### 3.2 `wait()`

```cpp
IoAwaitable auto wait();
```

Returns an awaitable that completes when the deadline expires or the operation is cancelled. The awaitable satisfies the IoAwaitable protocol defined in [P4003R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r3.pdf)<sup>[2]</sup>. On success, the result is `void`. On cancellation, the result carries `std::errc::operation_canceled`.

Multiple coroutines may await the same timer concurrently. Each receives its own completion.

```cpp
std::io::timer deadline(ctx, 30s);
auto result = co_await deadline.wait();
if (result.has_error())
    // cancelled or context stopped
```

### 3.3 Deadline Setters

```cpp
void expires_at(std::chrono::steady_clock::time_point t);
void expires_after(std::chrono::steady_clock::duration d);
```

Setting a new deadline cancels all outstanding `wait()` operations on this timer. Each cancelled operation completes with `std::errc::operation_canceled`. This is the same behaviour as Asio's `steady_timer`<sup>[7]</sup>: resetting the deadline implies cancellation of pending waiters.

`expires_after(d)` is equivalent to `expires_at(std::chrono::steady_clock::now() + d)`.

### 3.4 Deadline Getter

```cpp
std::chrono::steady_clock::time_point expiry() const;
```

Returns the currently set deadline. If no deadline has been set, returns `std::chrono::steady_clock::time_point{}` (the epoch).

---

## 4. Clock Requirements

The timer uses `std::chrono::steady_clock`. Steady clocks are monotonic - they are not affected by system clock adjustments, NTP synchronisation, or daylight saving transitions. A timeout of five seconds always takes five seconds.

Wall-clock time (`std::chrono::system_clock`) is inappropriate for timeouts. A backward adjustment can cause a timeout to fire late - or never. A forward adjustment can cause a timeout to fire immediately. These are real bugs that occur in production deployments when NTP corrects clock drift.

The standard library already provides the necessary clock type. The timer merely requires that the user express deadlines in terms of it. The conversion from `system_clock` to `steady_clock` is the caller's responsibility and should be explicit, not hidden inside the timer implementation.

---

## 5. Cancellation

### 5.1 `cancel()`

```cpp
std::size_t cancel();
```

Cancels all outstanding `wait()` operations on this timer. Each cancelled operation completes with `std::errc::operation_canceled`. Returns the number of operations cancelled.

### 5.2 `cancel_one()`

```cpp
std::size_t cancel_one();
```

Cancels at most one outstanding `wait()` operation on this timer. The cancelled operation completes with `std::errc::operation_canceled`. Returns 0 or 1. When multiple waiters exist, the implementation cancels the one that was initiated first (FIFO order).

### 5.3 Cancellation Semantics

Cancellation is cooperative. A cancelled operation does not complete synchronously inside `cancel()`. It completes asynchronously through the normal completion path with an error code. The coroutine awaiting the timer resumes and observes the error.

```cpp
std::io::timer t(ctx, 1h);

// Start a wait in a separate coroutine.
auto waiter = [&]() -> task<> {
    auto r = co_await t.wait();
    assert(r.has_error());
    assert(r.error() == std::errc::operation_canceled);
};

// Cancel from outside.
std::size_t n = t.cancel();  // n == 1
```

The return value of `cancel()` and `cancel_one()` is the count of operations that were actually cancelled. If the timer has already expired and the completion is pending dispatch, `cancel()` returns 0 - the operation completed, it was not cancelled.

---

## 6. Example Usage

### 6.1 Simple Timeout

```cpp
#include <std/io/timer.hpp>

task<> delayed_greeting(std::io::execution_context& ctx)
{
    std::io::timer t(ctx, 2s);
    co_await t.wait();
    std::println("Hello after two seconds");
}
```

### 6.2 Timeout on a Read Operation

```cpp
task<> read_with_timeout(
    std::io::execution_context& ctx,
    std::io::any_stream& stream,
    mutable_buffer buf)
{
    std::io::timer deadline(ctx, 30s);

    auto result = co_await when_any(
        stream.read_some(buf),
        deadline.wait());

    if (result.index() == 1)
        throw std::system_error(
            std::make_error_code(std::errc::timed_out));
}
```

### 6.3 Periodic Work

```cpp
task<> heartbeat(std::io::execution_context& ctx)
{
    std::io::timer t(ctx);
    for (;;)
    {
        t.expires_after(10s);
        co_await t.wait();
        send_heartbeat();
    }
}
```

### 6.4 Debounce

```cpp
task<> debounced_save(
    std::io::execution_context& ctx,
    document& doc)
{
    std::io::timer t(ctx);
    for (;;)
    {
        co_await doc.changed();
        t.expires_after(500ms);
        auto r = co_await t.wait();
        if (!r.has_error())
            co_await doc.save();
    }
}
```

---

## Suggested Straw Poll

> LEWG agrees that the timer type `std::io::timer` documented in this paper and its companion *Timers: Design Rationale* should be advanced as standard library vocabulary for coroutine-native I/O.

---

## Acknowledgments

Christopher Kohlhoff designed the Asio `steady_timer` that this proposal recovers for the standard. The Asio timer interface has been stable since 2007 and has been deployed in every Asio-based application since.

Mohammad Nejati implemented the Corosio timer on three platforms (IOCP, epoll, kqueue).

---

## References

[1] [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[2] [P4003R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r3.pdf) - "The IoAwaitable Protocol" (Vinnie Falco, 2026).

[3] *Timers: Design Rationale* (Vinnie Falco, 2026). Companion design paper. D0016R0.

[4] [Boost.Beast](https://github.com/boostorg/beast) - HTTP and WebSocket built on Boost.Asio (Vinnie Falco, 2017-2026).

[5] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[6] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[7] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - Asio steady_timer and timer services (Christopher Kohlhoff, 2003-2026).
