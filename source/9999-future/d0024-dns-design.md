---
title: "DNS: Design Rationale"
document: D0024R0
date: 2026-05-15
intent: info
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

Every networked application resolves hostnames. None of them should block a thread to do it.

The C++ standard library has `<netdb.h>` by way of POSIX and `getaddrinfo` by way of convention. Neither is async. Neither is portable at the interface level. Neither returns endpoints in the vocabulary the rest of the I/O stack consumes. This paper documents the resolver that ships in [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup> today - the same shape [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html)<sup>[2]</sup> deployed for over twenty years, the same shape six independent ecosystems converged on without coordinating.

This paper is Paper 12 in the series defined by [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[3]</sup>. It depends on Paper 1 (IoAwaitable Protocol, [P4003R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r3.pdf)<sup>[4]</sup>) and Paper 11 (TCP, for `endpoint`, `ipv4_address`, and `ipv6_address`). Proposed wording for the vocabulary in this paper lives in the companion ask paper *DNS*<sup>[5]</sup>.

---

## Revision History

### R0: May 2026 (post-Brno mailing)

* Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author maintains [Boost.Beast](https://github.com/boostorg/beast)<sup>[6]</sup>, a published HTTP and WebSocket library built on Asio's resolver model, and develops [Capy](https://github.com/cppalliance/capy)<sup>[7]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup>, plus three further Boost libraries built on them: Boost.Http, Boost.Beast2, and Boost.Burl. Each consumes DNS resolution. The body of work creates a bias toward a dedicated resolver type.

This paper documents the resolver that ships in Corosio. The resolver is consumed by every application in Corosio that connects by hostname. Appendix B lists each header.

The [Networking TS](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[8]</sup> defined `ip::tcp::resolver`. The shape in this paper is the same shape. This paper recovers it on a parallel track to the Network Endeavor.

The companion paper is *DNS*<sup>[5]</sup> (the proposal-only ask paper for the resolver in this paper). [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[3]</sup> is the umbrella paper that places this work in series.

The author asks for nothing.

---

## 2. Why DNS Matters

A TCP socket connects to an endpoint - an IP address and a port. An endpoint is a number. Humans do not memorize numbers. They memorize names.

DNS is the translation layer between what humans write (`example.com:443`) and what sockets consume (`93.184.216.34:443`). Without it, every `connect()` call in every networked application requires a hardcoded IP address. Hardcoded addresses break when infrastructure changes, when services migrate, when CDNs rotate, when IPv6 is deployed alongside IPv4.

**The resolver is the first function call in every client application that connects to something by name.** It precedes `connect()`. It precedes TLS handshake. It precedes the first byte of protocol data. Every HTTP client, every database driver, every mail client, every chat application, every game client calls a resolver before it does anything else.

The C standard library provides `getaddrinfo`. It blocks. In a coroutine-native model, blocking a thread to resolve a hostname defeats the purpose of coroutines. An async resolver is not optional - it is the entry point to async networking.

**DNS is not a feature. It is a precondition.**

---

## 3. The `resolver` Design

### 3.1 Why a Class, Not Free Functions

The resolver is a class rather than a pair of free functions for three reasons.

**Execution context ownership.** The resolver holds a reference to the `execution_context` that drives its I/O. A free function would need the context passed to every call. The class captures it once at construction, the same pattern as `timer`, `tcp_socket`, and every other I/O object in the series.

**Cancellation scope.** `cancel()` cancels all outstanding operations on this resolver instance. A free function has no instance - cancellation would require a separate token or a global registry. The class provides a natural cancellation boundary.

**Resource management.** Platform resolver implementations may hold handles, thread pool references, or cached state. A class with move semantics and a destructor manages those resources through RAII. A free function would leak the management to the caller.

```cpp
std::io::resolver res(ctx);            // capture context once
auto r1 = co_await res.resolve(h1, s); // no context argument
auto r2 = co_await res.resolve(h2, s); // same context
res.cancel();                          // cancel scope
```

### 3.2 Execution Context Ownership

The resolver holds a non-owning reference to the `execution_context`. The context must outlive the resolver. This is the same lifetime model as `timer`, `tcp_socket`, `signal_set`, and every other I/O object in the series.

The alternative - owning a shared pointer to the context - was not selected. Shared ownership obscures lifetime relationships. The I/O objects in this series are explicit about who owns what. The resolver follows the pattern.

### 3.3 Result Caching

The resolver in this paper does not cache results. Each `resolve()` call performs a fresh lookup.

DNS caching is the responsibility of the platform's DNS resolver infrastructure - the stub resolver, the recursive resolver, `nscd`, `systemd-resolved`, or the OS-level DNS cache. These components are configured by the system administrator, respect TTL records, handle cache invalidation, and integrate with DNSSEC validation. Duplicating that caching inside a standard library resolver would create a second source of truth that conflicts with the platform's own cache management.

The resolver delegates to the platform. The platform caches.

---

## 4. Results Type

### 4.1 Why a Range of Endpoints

`getaddrinfo` returns a linked list of `addrinfo` structures. Each structure contains a `sockaddr` - the address and port. A single hostname may resolve to multiple addresses:

- **Dual-stack:** one IPv4 address and one IPv6 address.
- **Load balancing:** multiple addresses for the same service, rotated by the DNS server.
- **Redundancy:** primary and backup addresses.

Returning a single address would force the caller to retry the entire resolution when the first address fails. Returning the full range lets the caller iterate and try each endpoint until one succeeds. The iterate-and-connect pattern is the standard algorithm for robust client connections.

### 4.2 `getaddrinfo` Semantics

The resolver's forward resolution maps directly to `getaddrinfo`. The arguments are the same: a hostname (or numeric address string) and a service name (or numeric port string). The result is the same: a sequence of resolved endpoints.

The resolver's reverse resolution maps to `getnameinfo`. The argument is an endpoint (address and port). The result is a hostname and service name.

The standard library resolver is a coroutine-native wrapper around these POSIX functions. It does not redefine their semantics. It makes them async, cancellable, and type-safe.

### 4.3 Result Ownership

`results_type` owns its data. The resolved endpoints, hostnames, and service names are copied into the results object before the awaitable completes. The caller may store, move, or iterate the results after the resolver has been destroyed.

The alternative - returning a view into resolver-internal state - was not selected. A view would create a lifetime dependency between the results and the resolver. The results outlive the query. Ownership is the natural model.

---

## 5. Platform Implementation

### 5.1 Linux: `getaddrinfo_a`

Linux provides `getaddrinfo_a`, an asynchronous variant of `getaddrinfo` defined in `<netdb.h>`. It submits resolution requests and signals completion through a `sigevent` - either a signal, a thread callback, or polling. The resolver integrates `getaddrinfo_a` with the event loop through the platform's notification mechanism.

`getaddrinfo_a` supports batch resolution - multiple requests submitted in a single call. The resolver does not expose batching in the public API. Each `resolve()` call is independent.

### 5.2 Windows: `GetAddrInfoEx`

Windows provides `GetAddrInfoEx`, an asynchronous variant of `getaddrinfo` that completes through an OVERLAPPED structure or a completion callback. The resolver integrates `GetAddrInfoEx` with IOCP through the same completion port that drives TCP and timer operations.

`GetAddrInfoExCancel` cancels an outstanding `GetAddrInfoEx` request. The resolver's `cancel()` maps directly to this function.

### 5.3 Fallback: Thread Pool

On platforms that provide neither `getaddrinfo_a` nor `GetAddrInfoEx`, the resolver posts `getaddrinfo` to a thread pool and delivers the result through the event loop. The blocking call happens on a pool thread. The coroutine never blocks.

This is the same strategy Asio<sup>[2]</sup> and libuv<sup>[9]</sup> use. The thread pool is the universal fallback for platforms that did not invest in async DNS.

### 5.4 macOS/BSD: `getaddrinfo` on Thread Pool

macOS and FreeBSD do not provide a native async `getaddrinfo` variant. The resolver uses the thread pool fallback on these platforms. The Corosio implementation has shipped this configuration since the initial release.

---

## 6. Convergence

Six I/O ecosystems, designed independently, all arrived at the same shape for name resolution.

| Ecosystem       | Resolver API                                                    | Async model            | Result shape           |
| --------------- | --------------------------------------------------------------- | ---------------------- | ---------------------- |
| Asio (2003)     | `ip::tcp::resolver::async_resolve`<sup>[2]</sup>               | Completion token       | `results_type` range   |
| Go (2012)       | `net.Resolver.LookupHost`<sup>[10]</sup>                       | Goroutine + context    | `[]string`             |
| Rust (2020)     | `tokio::net::lookup_host`<sup>[11]</sup>                       | `async`/`.await`       | `impl Iterator<Item=SocketAddr>` |
| .NET (2000)     | `Dns.GetHostAddressesAsync`<sup>[12]</sup>                     | `Task<IPAddress[]>`    | Array of addresses     |
| Python (2014)   | `asyncio.getaddrinfo`<sup>[13]</sup>                           | `await`                | List of tuples         |
| libuv (2012)    | `uv_getaddrinfo`<sup>[9]</sup>                                 | Callback               | `addrinfo` list        |
| C++ standard    | (none)                                                          | (none)                 | (none)                 |

The first six rows are platforms or libraries. The seventh row is the standard.

Every ecosystem wraps the platform's `getaddrinfo` in its async model and returns a sequence of resolved addresses. The differences are syntactic. The shape is the same.

**Six ecosystems. Same shape. The C++ row is empty.**

---

## 7. Anticipated Objections

### 7.1 "But `getaddrinfo` Is Blocking and Works Fine"

`getaddrinfo` blocks the calling thread. In a thread-per-connection server, blocking one thread is acceptable. In a coroutine-native server handling thousands of connections on a small thread pool, blocking a thread to resolve a hostname stalls every coroutine sharing that thread.

The standard already acknowledged this problem. `getaddrinfo_a` exists on Linux. `GetAddrInfoEx` exists on Windows. Both are async variants of `getaddrinfo` that the platform vendors created because the blocking version does not scale.

The resolver in this paper wraps the async variants where available and falls back to a thread pool where they are not. The coroutine never blocks.

### 7.2 "But DNS-over-HTTPS Changes the Model"

DNS-over-HTTPS (DoH) and DNS-over-TLS (DoT) encrypt DNS queries to prevent eavesdropping and tampering. They change the transport, not the interface. The resolver still accepts a hostname and a service. It still returns a range of endpoints. Whether the query travels over UDP port 53, HTTPS port 443, or TLS port 853 is an implementation detail below the resolver's public API.

Modern operating systems increasingly handle DoH at the system level - Windows 11, macOS Ventura, iOS 14, and Android 9 all support system-wide encrypted DNS. The resolver delegates to the platform. The platform decides the transport.

### 7.3 "But the Resolver Should Support All Record Types"

DNS has dozens of record types: A, AAAA, MX, CNAME, SRV, TXT, PTR, SOA, NS, and more. A general-purpose DNS client would query any of them.

The resolver in this paper resolves hostnames to endpoints (A and AAAA records via forward resolution) and endpoints to hostnames (PTR records via reverse resolution). These are the two operations that every networked application needs. MX records are for mail servers. SRV records are for service discovery. TXT records are for SPF, DKIM, and domain verification. Each is a specialised use case.

A general-purpose DNS record query API is a possible future addition. It does not block the resolver that every client application calls before its first `connect()`.

### 7.4 "But Caching Should Be Standardised"

DNS caching is a system-level concern. The stub resolver caches. The recursive resolver caches. `nscd` caches. `systemd-resolved` caches. The Windows DNS Client service caches. Each layer respects TTL records, handles negative caching, and integrates with DNSSEC validation.

A standard library cache would duplicate this infrastructure, create conflicts with the platform's cache management, ignore TTL records the platform already tracks, and introduce stale-entry bugs that the platform resolvers have already solved.

The resolver delegates to the platform. The platform caches. Section 3.3 records this decision.

---

## 8. Deferrals

Five deferrals. Each is named so the scope is unambiguous.

### 8.1 DNS Record Types Beyond A/AAAA

MX, SRV, TXT, CNAME, SOA, NS, and other record types are not part of the resolver's public API. A general-purpose DNS record query API is a possible future paper. The resolver in this paper resolves hostnames to endpoints and endpoints to hostnames. Those are the operations the transport layer needs.

### 8.2 mDNS/Bonjour

Multicast DNS (mDNS) and DNS-SD (service discovery) operate on the local network without a DNS server. They are used by Bonjour (Apple), Avahi (Linux), and similar zero-configuration networking systems. The resolver in this paper delegates to the platform's DNS infrastructure; on platforms where mDNS is integrated into the system resolver (macOS, Windows 10+), mDNS names resolve transparently. Explicit mDNS APIs are outside the scope of this paper.

### 8.3 DNS-over-HTTPS/TLS

Encrypted DNS transports (DoH, DoT) change how queries reach the recursive resolver. They do not change the resolver's public API. The platform handles encrypted DNS transparently on modern operating systems. Exposing DoH/DoT configuration knobs - custom resolvers, certificate pinning, fallback policies - is outside the scope of this paper.

### 8.4 Custom DNS Servers

The resolver uses the system-configured DNS servers. Specifying custom DNS server addresses - for split-horizon DNS, for testing, for privacy-focused resolvers - is outside the scope of this paper. Applications that need custom DNS servers use platform-specific APIs or third-party DNS libraries.

### 8.5 Connection-Racing (Happy Eyeballs)

RFC 8305 ("Happy Eyeballs Version 2") defines an algorithm that races IPv6 and IPv4 connection attempts with a staggered start to minimize connection latency on dual-stack hosts. The algorithm combines resolution and connection into a single operation. The resolver in this paper returns endpoints; the caller iterates them. A `connect_by_name` algorithm that implements Happy Eyeballs is a possible future addition that builds on top of the resolver.

---

## 9. Why Now

The committee has had a resolver in front of it before.

| Year | Paper                                                                                         | Outcome                                                        |
| ---- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 2005 | [N1925](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2005/n1925.pdf)<sup>[14]</sup>    | First networking proposal for TR2 (included resolver)          |
| 2018 | [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[8]</sup>     | Networking TS draft with `ip::tcp::resolver`                   |
| 2026 | [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[3]</sup> | Network Endeavor frames the resolver as Paper 12               |

The resolver shape has been deployed for over twenty years in [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html)<sup>[2]</sup>. It is in the Networking TS<sup>[8]</sup>. It is in [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup> today.

The standard library is the place that does not have it.

**Twenty years of deployment. Six ecosystems in agreement. The standard library has no async resolver.**

---

## 10. Closing

We built this. It works. We are reporting what we found. Proposed wording for the resolver documented here lives in *DNS*<sup>[5]</sup>.

---

## Appendix A. `<std::io>` Synopsis (Informative)

Resolver-only synopsis. The `endpoint`, `ipv4_address`, and `ipv6_address` types come from Paper 11 (TCP).

```cpp
namespace std::io {

  class resolver {
  public:
    class results_type {
    public:
      class iterator;
      using const_iterator = iterator;

      iterator begin() const;
      iterator end() const;
      bool empty() const;
      std::size_t size() const;

      std::string_view host_name() const;
      std::string_view service_name() const;
    };

    explicit resolver(execution_context& ctx);

    resolver(resolver const&) = delete;
    resolver& operator=(resolver const&) = delete;
    resolver(resolver&&) noexcept;
    resolver& operator=(resolver&&) noexcept;

    ~resolver();

    IoAwaitable auto resolve(
        std::string_view host,
        std::string_view service);

    IoAwaitable auto resolve(endpoint const& ep);

    void cancel();
  };

}
```

---

## Appendix B. Corosio Header Inventory

The resolver in this paper ships in the following headers in [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup>. The list is a pointer to the implementation for the reader who wants to inspect it.

| Header                                            | Provides                                      |
| ------------------------------------------------- | --------------------------------------------- |
| `boost/corosio/ip/resolver.hpp`                   | `resolver`, `resolver::results_type`          |
| `boost/corosio/ip/tcp.hpp`                        | `endpoint`, `ipv4_address`, `ipv6_address`    |

---

## Acknowledgments

Christopher Kohlhoff designed the Asio `ip::tcp::resolver` that this proposal recovers for the standard. Twenty years of production deployment in Asio<sup>[2]</sup> is the foundation this work builds on.

The Networking TS authors codified the resolver semantics in [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[8]</sup>. The shape in this paper is the shape they specified.

Mohammad Nejati implemented the Corosio resolver on three platforms.

---

## References

[1] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[2] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - Asio resolver and networking services (Christopher Kohlhoff, 2003-2026).

[3] [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[4] [P4003R3](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4003r3.pdf) - "The IoAwaitable Protocol" (Vinnie Falco, 2026).

[5] *DNS* (Vinnie Falco, 2026). Companion ask paper. D0023R0.

[6] [Boost.Beast](https://github.com/boostorg/beast) - HTTP and WebSocket built on Boost.Asio (Vinnie Falco, 2017-2026).

[7] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[8] [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf) - "Working Draft, C++ Extensions for Networking" (Jonathan Wakely, 2018).

[9] [libuv](https://docs.libuv.org/en/v1.x/) - `uv_getaddrinfo` async DNS resolution (libuv contributors, 2012-2026).

[10] [Go standard library: `net.Resolver`](https://pkg.go.dev/net#Resolver) - DNS resolution with context and timeout (The Go Authors, 2012-2026).

[11] [Tokio: `tokio::net::lookup_host`](https://docs.rs/tokio/latest/tokio/net/fn.lookup_host.html) - Async DNS resolution (Tokio Contributors, 2020-2026).

[12] [.NET API: `Dns.GetHostAddressesAsync`](https://learn.microsoft.com/en-us/dotnet/api/system.net.dns.gethostaddressesasync) - Async DNS resolution (Microsoft, 2000-2026).

[13] [Python `asyncio.getaddrinfo`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.getaddrinfo) - Async DNS resolution (Python Software Foundation, 2014-2026).

[14] [N1925](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2005/n1925.pdf) - "Networking proposal for TR2 (rev. 1)" (Gerhard Wesp, 2005).
