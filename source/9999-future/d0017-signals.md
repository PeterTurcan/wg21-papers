---
title: "Signals"
document: D0017R0
date: 2026-05-15
intent: ask
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

This paper asks the committee to advance an async signal handling facility - `signal_set` with registration, waiting, and cancellation - as standard library vocabulary for I/O.

`<csignal>` is from 1989. Its `signal()` function installs a handler that runs in signal context, where almost nothing is safe to call. Modern C++ servers need to wait for `SIGINT` or `SIGTERM` the same way they wait for a timer or a socket: with `co_await`. The facility proposed here makes that possible. It ships today in [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup>.

The companion paper *Signals: Design Rationale*<sup>[7]</sup> provides the design rationale, the convergence record across six ecosystems, anticipated objections, and the implementation inventory. Read this paper for the proposal; read the companion when you need the audit trail.

This paper is Paper 9 in the series defined by [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[2]</sup>. It depends on Paper 1 (IoAwaitable Protocol, [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf)<sup>[3]</sup>). It is a Stage Two paper.

---

## Revision History

### R0: May 2026 (post-Brno mailing)

* Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author develops and maintains [Capy](https://github.com/cppalliance/capy)<sup>[4]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup>, which implement the `signal_set` type proposed here. The body of work creates a bias toward coroutine-native signal handling.

This paper is the proposal-only ask paper for the signal handling vocabulary. The design rationale lives in the companion *Signals: Design Rationale*<sup>[7]</sup>.

---

## 2. What This Paper Asks

The committee is asked to advance the following vocabulary for the standard library:

```cpp
namespace std::io {

  class signal_set {
  public:
    using flags_t = /* implementation-defined */;

    explicit signal_set(execution_context& ctx);

    void add(int signal_number);
    void add(int signal_number, flags_t flags);
    void remove(int signal_number);
    void clear();

    IoAwaitable auto wait();
    void cancel();
  };

}
```

One type. Six operations. One awaitable return.

---

## 3. The `signal_set` Type

### 3.1 Construction

```cpp
explicit signal_set(execution_context& ctx);
```

A `signal_set` is constructed with a reference to an `execution_context`. The context provides the reactor (epoll, kqueue, IOCP) that delivers signal notifications. The signal set starts empty.

### 3.2 Registration

```cpp
void add(int signal_number);
void add(int signal_number, flags_t flags);
void remove(int signal_number);
void clear();
```

`add()` registers a signal number with the set. The one-argument overload uses default flags. The two-argument overload accepts platform-specific flags (Section 4). Adding a signal number that is already in the set has no effect. `remove()` removes a single signal number. `clear()` removes all signal numbers.

Registration is a precondition for `wait()`. A `signal_set` that contains no signal numbers has nothing to wait for.

### 3.3 Waiting

```cpp
IoAwaitable auto wait();
```

Returns an `IoAwaitable` whose result is the signal number that was received. The awaitable suspends the calling coroutine until one of the registered signals is delivered. When multiple signals arrive before the coroutine resumes, the implementation delivers one per `wait()` call. The caller calls `wait()` again for the next.

```cpp
std::io::signal_set sigs(ctx);
sigs.add(SIGINT);
sigs.add(SIGTERM);

auto [ec, signo] = co_await sigs.wait();
if (!ec)
    std::println("received signal {}", signo);
```

The result type follows the IoAwaitable error convention: a structured binding of `error_code` and value. The value is the signal number as `int`.

### 3.4 Cancellation

```cpp
void cancel();
```

Cancels any outstanding `wait()` operation. The pending awaitable completes with `error::operation_aborted`. This is the same cancellation convention used by timers and sockets throughout the series.

---

## 4. Signal Numbers and Flags

### 4.1 Signal Numbers

Signal numbers are `int` values. The standard signal constants - `SIGINT`, `SIGTERM`, `SIGABRT`, `SIGHUP`, `SIGUSR1`, `SIGUSR2`, and others - are defined by `<csignal>` and by POSIX. This paper does not define new signal constants. It consumes the existing ones.

### 4.2 Flags

```cpp
using flags_t = /* implementation-defined */;
```

The `flags_t` type carries platform-specific signal disposition flags. On POSIX systems, these correspond to `sigaction` flags:

| Flag             | Effect                                              |
| ---------------- | --------------------------------------------------- |
| `SA_RESTART`     | Restart interrupted system calls                    |
| `SA_NOCLDSTOP`   | Do not generate `SIGCHLD` when children stop        |
| `SA_NOCLDWAIT`   | Do not create zombie processes                      |
| `SA_NODEFER`     | Do not block the signal during its own handler      |
| `SA_RESETHAND`   | Reset the signal handler to default after delivery  |

The flags parameter is optional. When omitted, the implementation uses platform-appropriate defaults. On Windows, where the POSIX signal disposition model does not apply, `flags_t` operations that have no platform equivalent are silently ignored. The companion *Signals: Design Rationale*<sup>[7]</sup> Section 5 documents the platform compatibility rationale.

---

## 5. Cancellation

Cancellation follows the IoAwaitable protocol. The `signal_set` respects stop tokens propagated through the coroutine environment. When the stop token is triggered, the pending `wait()` operation completes with `error::operation_aborted`.

The explicit `cancel()` member function provides a second cancellation path. Both paths produce the same result. `cancel()` exists because signal handling is often managed at the application level, where a stop token may not be the natural control mechanism.

```cpp
std::io::signal_set sigs(ctx);
sigs.add(SIGINT);

// Path 1: stop token cancels the wait.
auto [ec, signo] = co_await sigs.wait();

// Path 2: explicit cancel from another coroutine.
sigs.cancel();
```

---

## 6. Graceful Shutdown Pattern

The primary use case for async signal handling is graceful server shutdown. The pattern composes `signal_set::wait()` with an accept loop using `when_any`:

```cpp
std::io::task<> run_server(
    std::io::execution_context& ctx)
{
    std::io::tcp_acceptor acceptor(ctx, endpoint);
    std::io::signal_set sigs(ctx);
    sigs.add(SIGINT);
    sigs.add(SIGTERM);

    co_await when_any(
        accept_loop(acceptor),
        sigs.wait());
}
```

When `SIGINT` or `SIGTERM` is delivered, `when_any` cancels the accept loop and returns. The server shuts down. No global state. No signal handler. No `volatile sig_atomic_t`. One line of composition replaces the entire `<csignal>` ceremony.

The same pattern works for any lifecycle boundary. A health-check server, a background worker with graceful drain, a test harness with a timeout - any task that should stop on signal delivery composes the same way.

---

## 7. Suggested Straw Poll

> LEWG agrees that the async signal handling facility `signal_set` with `add`, `remove`, `clear`, `wait`, and `cancel` documented in this paper and its companion *Signals: Design Rationale* should be advanced as standard library vocabulary for I/O.

---

## Acknowledgments

Christopher Kohlhoff designed the original `signal_set` in Asio. The type, its API shape, and its integration with the reactor are his work. This paper recovers the shape for a coroutine-native model.

Mohammad Nejati implemented the Corosio signal handling backend across `signalfd`, `kqueue`, and Windows console events.

---

## References

[1] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[2] [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[3] [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf) - "A Minimal Coroutine Execution Model" (Vinnie Falco, Steve Gerbino, Mungo Gill, 2026).

[4] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[5] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - Signal set and reactor integration (Christopher Kohlhoff, 2003-2026).

[6] [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf) - "Working Draft, C++ Extensions for Networking" (Jonathan Wakely, 2018).

[7] *Signals: Design Rationale* (Vinnie Falco, 2026). Companion design paper. D0018R0.
