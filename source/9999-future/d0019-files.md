---
title: "Files"
document: D0019R0
date: 2026-05-15
intent: ask
audience: LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

This paper asks the committee to advance async file I/O - `stream_file` and `random_access_file` - as standard library vocabulary.

Every server writes logs. Every database writes pages. Every media pipeline writes frames. Today, C++ programs doing async I/O must drop to raw platform APIs for files while using library abstractions for sockets. `stream_file` and `random_access_file` close that gap. Both satisfy the same stream concepts as TCP sockets. The same generic algorithms work on files and network connections. The same buffer sequences. The same error model. The same cancellation. On Windows, IOCP with `FILE_FLAG_OVERLAPPED`. On Linux, `io_uring` is on the roadmap; POSIX file I/O is the current backend. Shipping in [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup>.

The companion paper *Files: Design Rationale*<sup>[9]</sup> provides the design rationale, the convergence record across six ecosystems, anticipated objections, and the implementation inventory. Read this paper for the proposal; read the companion when you need the audit trail.

This paper is Paper 10 in the series defined by [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf)<sup>[2]</sup>. It depends on Paper 1 (the IoAwaitable Protocol, [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf)<sup>[3]</sup> and [P4172R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4172r0.pdf)<sup>[4]</sup>) and Paper 6 (Stream Concepts, D0011/D0012). Stage Two paper.

---

## Revision History

### R0: May 2026 (post-Brno mailing)

* Initial version.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author develops and maintains [Capy](https://github.com/cppalliance/capy)<sup>[5]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[1]</sup>. File I/O ships in Corosio today on Windows (IOCP) and Linux (POSIX). The experience informs this proposal.

This paper is the proposal-only ask paper for `stream_file` and `random_access_file`. The design rationale lives in the companion *Files: Design Rationale*<sup>[9]</sup>.

---

## 2. What This Paper Asks

The committee is asked to advance the following vocabulary for the standard library:

```cpp
namespace std::io {

  enum class file_flags : unsigned {
    read       = 1,
    write      = 2,
    read_write = 3,
    create     = 4,
    truncate   = 8,
    append     = 16,
    exclusive  = 32
  };

  constexpr file_flags operator|(file_flags, file_flags);
  constexpr file_flags operator&(file_flags, file_flags);

  class stream_file;          // sequential file I/O
  class random_access_file;   // seekable file I/O

}
```

Two file types. One flag enumeration. The same buffer sequences and error model as sockets.

---

## 3. `stream_file`

### 3.1 Purpose

`stream_file` provides sequential async file I/O. It satisfies `Stream` (Paper 6). The same generic algorithms that work on `tcp_socket` work on `stream_file`. A function that accepts `any_stream&` handles both network and file I/O without change.

### 3.2 Interface

```cpp
class stream_file
{
public:
    explicit stream_file(execution_context& ctx);

    stream_file(stream_file&& other) noexcept;
    stream_file& operator=(stream_file&& other) noexcept;
    ~stream_file();

    stream_file(stream_file const&) = delete;
    stream_file& operator=(stream_file const&) = delete;

    IoAwaitable auto open(
        std::filesystem::path const& p,
        file_flags flags);

    void close();

    bool is_open() const noexcept;

    IoAwaitable auto read_some(
        MutableBufferSequence auto const& buffers);

    IoAwaitable auto write_some(
        ConstBufferSequence auto const& buffers);
};
```

### 3.3 Satisfies `Stream`

`stream_file` provides `read_some()` and `write_some()` with the same signatures as `tcp_socket`. It satisfies the `ReadStream`, `WriteStream`, and `Stream` concepts. This means:

```cpp
std::io::task<> copy_to_socket(
    std::io::stream_file& file,
    std::io::tcp_socket& sock)
{
    std::array<std::byte, 4096> buf;
    for (;;)
    {
        auto [ec, n] = co_await file.read_some(
            std::io::buffer(buf));
        if (ec) co_return;
        auto [ec2, _] = co_await sock.write_some(
            std::io::buffer(buf, n));
        if (ec2) co_return;
    }
}
```

The function does not know whether `file` is a local file, a network-mounted file, or any other `ReadStream`. The concept abstracts the source.

### 3.4 Sequential Access

`stream_file` maintains an internal file position. Each `read_some()` advances the position by the number of bytes read. Each `write_some()` advances the position by the number of bytes written. There is no `seek()` - for seekable access, use `random_access_file`.

### 3.5 `open()`

```cpp
IoAwaitable auto open(
    std::filesystem::path const& p,
    file_flags flags);
```

`open()` is an async operation. On Windows, it calls `CreateFileW` with `FILE_FLAG_OVERLAPPED`. On Linux, it opens the file descriptor. The returned awaitable completes with an `error_code` indicating success or failure.

```cpp
std::io::stream_file file(ctx);
auto [ec] = co_await file.open(
    "/var/log/app.log",
    file_flags::write | file_flags::create |
    file_flags::append);
if (ec) co_return ec;
```

### 3.6 `close()`

`close()` is synchronous. It releases the underlying file handle. Any pending async operations on the file are cancelled. After `close()`, `is_open()` returns `false`.

---

## 4. `random_access_file`

### 4.1 Purpose

`random_access_file` provides seekable async file I/O. Every read and write takes an explicit byte offset. There is no internal position state. This makes `random_access_file` safe for concurrent reads and writes to different regions of the same file - the caller controls positioning.

### 4.2 Interface

```cpp
class random_access_file
{
public:
    explicit random_access_file(execution_context& ctx);

    random_access_file(random_access_file&& other) noexcept;
    random_access_file& operator=(
        random_access_file&& other) noexcept;
    ~random_access_file();

    random_access_file(random_access_file const&) = delete;
    random_access_file& operator=(
        random_access_file const&) = delete;

    IoAwaitable auto open(
        std::filesystem::path const& p,
        file_flags flags);

    void close();

    bool is_open() const noexcept;

    IoAwaitable auto read_some_at(
        std::uint64_t offset,
        MutableBufferSequence auto const& buffers);

    IoAwaitable auto write_some_at(
        std::uint64_t offset,
        ConstBufferSequence auto const& buffers);

    std::uint64_t size() const;
};
```

### 4.3 Offset-Based Access

Every I/O operation takes an explicit `offset`:

```cpp
std::io::random_access_file db(ctx);
auto [ec] = co_await db.open(
    "pages.db",
    file_flags::read_write);
if (ec) co_return ec;

// Read page 42 (4 KiB pages)
constexpr std::uint64_t page_size = 4096;
std::array<std::byte, page_size> page;
auto [ec2, n] = co_await db.read_some_at(
    42 * page_size,
    std::io::buffer(page));
```

No internal cursor. No race between `seek()` and `read()`. The offset is part of the operation, not part of the file state.

### 4.4 Does Not Satisfy `Stream`

`random_access_file` does **not** satisfy the `Stream` concept. The `Stream` concept requires `read_some(buffers)` and `write_some(buffers)` - no offset parameter. `random_access_file` provides `read_some_at(offset, buffers)` and `write_some_at(offset, buffers)`. The signatures are intentionally different because the semantics are different: sequential vs. positional.

This is a deliberate design choice. Wrapping a seekable file in a sequential interface hides the offset and creates hidden mutable state. The two types serve different access patterns with different interfaces.

### 4.5 Concurrent Access

Because there is no internal position, multiple coroutines can read different regions of the same `random_access_file` concurrently without coordination:

```cpp
std::io::task<> parallel_read(
    std::io::random_access_file& f)
{
    co_await when_all(
        read_region(f, 0, 4096),
        read_region(f, 4096, 4096),
        read_region(f, 8192, 4096));
}
```

Each `read_some_at` is independent. No locks. No position contention.

---

## 5. Open Modes and Flags

### 5.1 `file_flags`

```cpp
enum class file_flags : unsigned {
    read       = 1,   // open for reading
    write      = 2,   // open for writing
    read_write = 3,   // open for reading and writing
    create     = 4,   // create if not exists
    truncate   = 8,   // truncate to zero length
    append     = 16,  // writes append to end
    exclusive  = 32   // fail if file already exists
};
```

Flags combine with bitwise OR:

```cpp
auto [ec] = co_await file.open(path,
    file_flags::write |
    file_flags::create |
    file_flags::truncate);
```

### 5.2 Mapping to Platform APIs

| `file_flags`       | POSIX `open()`            | Windows `CreateFileW`                 |
|--------------------|---------------------------|---------------------------------------|
| `read`             | `O_RDONLY`                | `GENERIC_READ`                        |
| `write`            | `O_WRONLY`                | `GENERIC_WRITE`                       |
| `read_write`       | `O_RDWR`                  | `GENERIC_READ \| GENERIC_WRITE`       |
| `create`           | `O_CREAT`                 | `CREATE_NEW` / `OPEN_ALWAYS`          |
| `truncate`         | `O_TRUNC`                 | `TRUNCATE_EXISTING` / `CREATE_ALWAYS` |
| `append`           | `O_APPEND`                | `FILE_APPEND_DATA`                    |
| `exclusive`        | `O_EXCL`                  | `CREATE_NEW`                          |

The mapping is direct. No abstraction penalty.

---

## 6. Relationship to `std::filesystem`

`std::filesystem` provides path manipulation, directory iteration, file status queries, and synchronous file operations. It does not provide async I/O.

`std::io::stream_file` and `std::io::random_access_file` provide async byte-level I/O. They accept `std::filesystem::path` as input. The two facilities are complementary:

```cpp
namespace fs = std::filesystem;

// std::filesystem: query, create directory
if (!fs::exists(log_dir))
    fs::create_directories(log_dir);

// std::io: async write
std::io::stream_file log(ctx);
auto [ec] = co_await log.open(
    log_dir / "app.log",
    file_flags::write | file_flags::create |
    file_flags::append);
```

`std::filesystem` manages the namespace. `std::io` moves the bytes.

---

## 7. Suggested Straw Poll

> LEWG agrees that the async file I/O vocabulary `stream_file` and `random_access_file` documented in this paper and its companion *Files: Design Rationale* should be advanced as standard library vocabulary for coroutine-native I/O.

---

## Acknowledgments

Christopher Kohlhoff designed Asio's `stream_file` and `random_access_file` - the production abstractions that this proposal builds on. Their deployment across two decades established both types as essential file I/O infrastructure.

The Networking TS authors ([N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf)<sup>[6]</sup>) codified the stream concepts that make file and socket I/O interchangeable.

---

## References

[1] [Corosio](https://github.com/cppalliance/corosio) - Coroutine-native I/O on epoll, kqueue, and IOCP (Vinnie Falco, 2024-2026).

[2] [P4100R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4100r1.pdf) - "Coroutine-Native I/O for C++29 (The Network Endeavor)" (Vinnie Falco, Steve Gerbino, Michael Vandeberg, Mungo Gill, Mohammad Nejati, 2026).

[3] [P4003R3](https://isocpp.org/files/papers/P4003R3.pdf) - "A Minimal Coroutine Execution Model" (Vinnie Falco, Steve Gerbino, Mungo Gill, 2026).

[4] [P4172R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4172r0.pdf) - "IoAwaitable for Coroutine-Native Byte-Oriented I/O" (Vinnie Falco, Steve Gerbino, Mungo Gill, 2026).

[5] [Capy](https://github.com/cppalliance/capy) - Coroutine-native I/O abstractions for C++20 (Vinnie Falco, 2023-2026).

[6] [N4771](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/n4771.pdf) - "Working Draft, C++ Extensions for Networking" (Jonathan Wakely, 2018).

[7] [Boost.Asio](https://www.boost.org/doc/libs/release/doc/html/boost_asio.html) - Async I/O including stream_file and random_access_file (Christopher Kohlhoff, 2003-2026).

[8] [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) - "`std::execution`" (Micha&lstrok; Dominiak, Georgy Evtushenko, Lewis Baker, Lucian Radu Teodorescu, Lee Howes, Kirk Shoop, Michael Garland, Eric Niebler, Bryce Adelstein Lelbach, 2024).

[9] *Files: Design Rationale* (Vinnie Falco, 2026). Companion design paper. D0020R0.
