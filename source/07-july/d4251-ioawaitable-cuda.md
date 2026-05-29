---
title: "CUDA Work-Graphs Using IoAwaitables: Our Findings"
document: P4251R0
date: 2026-07-01
intent: info
audience: SG1, LEWG
reply-to:
  - "Vinnie Falco <vinnie.falco@gmail.com>"
---

## Abstract

We used AI to design coroutine awaitables for CUDA and then asked whether the results were any good.

This paper documents an AI-generated research exercise: designing IoAwaitable adapters for CUDA streams, memory transfers, and graph launches, then comparing the resulting coroutine pipelines against equivalent `std::execution` sender compositions. CERN's coroutine-based GPU event processing project independently references the IoAwaitable protocol as a candidate for CUDA async composition.<sup>[43]</sup> The authors are not GPU domain experts. The findings are presented as questions, not assertions, and correction from practitioners is invited throughout.

---

## Revision History

### R0: July 2026 (post-Brno mailing)

- Initial revision.

---

## 1. Disclosure

The author provides information and serves at the pleasure of the committee.

The author developed and maintains [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> and [Corosio](https://github.com/cppalliance/corosio)<sup>[2]</sup>, coroutine-native I/O libraries under the C++ Alliance.

This paper is AI-generated from end to end. The research, CUDA code examples, and analysis were produced by AI. The authors are not domain experts in GPU programming. The findings are presented as a research exercise, not as expert testimony. Every technical claim may contain errors, and the questions posed throughout are genuine requests for correction from practitioners who work with these systems daily.

This paper explores how C++20 coroutines might integrate with CUDA's async completion model and places the findings in the record for evaluation by domain experts.

Capy's IoAwaitable protocol complements `std::execution`'s sender/receiver model for async composition. The author has a stake in the coroutine model's adoption.

A coroutine-only design cannot express compile-time work graphs. Each coroutine suspension potentially allocates a frame. The IoAwaitable protocol is not standardized. The authors' lack of GPU domain expertise means the code examples and performance assumptions may not reflect production practice.

This paper asks for nothing.

## 2. What std::execution Provides

Before examining coroutine alternatives, we acknowledge what `std::execution` achieves. These are specific, genuine properties.

**Zero-allocation composition.** Sender pipelines collapse into a single `operation_state` at compile time. No heap allocation, no virtual dispatch, no reference counting. This is a real property that coroutines do not match for multi-stage pipelines.<sup>[3]</sup>

**Domain customization.** A scheduler's `transform_sender` can replace `bulk` with a GPU kernel launch transparently. This enables writing algorithm code once and retargeting to CPU or GPU by swapping the scheduler.<sup>[4]</sup>

**Structured concurrency.** `counting_scope` tracks dynamically spawned work and prevents scope destruction until all work completes. Coroutines provide lexical-scope safety via `when_all`, but dynamic fan-out to an unknown number of tasks needs explicit library support.

**Scheduler-agnostic portability.** The Maxwell FDTD benchmark in the [stdexec](https://github.com/NVIDIA/stdexec)<sup>[5]</sup> repository demonstrates the same algorithm achieving parity with raw CUDA on GPU and running correctly on a CPU thread pool.

These are real. They stand without qualification.

## 3. The Bridge: `cudaLaunchHostFunc`

CUDA streams are in-order queues where operations execute sequentially.<sup>[6]</sup> When GPU work completes, the host needs notification. Three mechanisms exist:

- **Polling**: `cudaEventQuery` checks whether an event has completed.<sup>[7]</sup> Burns CPU cycles.
- **Blocking**: `cudaStreamSynchronize` blocks the calling thread.<sup>[8]</sup> Wastes a thread.
- **Callback**: `cudaLaunchHostFunc` enqueues a host function into the stream.<sup>[9]</sup> Zero busy-wait.

`cudaLaunchHostFunc` is the recommended replacement for the deprecated `cudaStreamAddCallback`.<sup>[6]</sup> The host function fires on a dedicated internal CPU thread created by the CUDA driver, not the application thread.<sup>[10]</sup><sup>[11]</sup> It cannot call CUDA APIs and must not create transitive dependencies on outstanding CUDA work.

This is the same structural pattern as epoll, IOCP, or io_uring completions arriving on arbitrary threads. In all cases, an async operation completes on a thread that is not the application's, and the application must dispatch the result to the correct execution context. This is the exact problem that Capy's executor-affinity dispatch was designed to solve.

For comparison, nvexec takes a different approach: device-side queuing into a task hub with a host-side poller thread.<sup>[12]</sup> Both approaches address the same underlying problem.

**Question for the reader:** Is `cudaLaunchHostFunc` the standard mechanism for non-blocking GPU completion notification in production CUDA code? Are there constraints on its use in high-throughput scenarios that we have not accounted for?

## 4. Hand-Rolled Awaitables

The simplest integration writes a minimal awaitable that resumes the coroutine from the CUDA callback:

```cpp
struct cuda_stream_awaiter
{
    cudaStream_t stream;

    bool await_ready() const noexcept
    {
        return false;
    }

    void await_suspend(std::coroutine_handle<> h)
    {
        cudaLaunchHostFunc(stream,
            [](void* data) {
                std::coroutine_handle<>::from_address(
                    data).resume();
            },
            h.address());
    }

    void await_resume() noexcept {}
};
```

This works. But `resume()` executes on the CUDA driver callback thread. There is no executor affinity, no cancellation support, and no frame allocation control. The coroutine's continuation runs on whatever thread the CUDA driver chose, which may not be safe for application logic that touches shared state.

**Question for the reader:** Is it safe to resume a C++ coroutine directly from the CUDA driver callback thread, or does production code typically need to dispatch the resumption to a specific application thread?

## 5. The IoAwaitable Protocol

The IoAwaitable protocol from [Capy](https://github.com/cppalliance/capy)<sup>[1]</sup> extends the standard awaitable with an execution environment:

```cpp
template<typename A>
concept IoAwaitable =
    requires(A a, std::coroutine_handle<> h,
             io_env const* env) {
        a.await_suspend(h, env);
    };
```

The `io_env`<sup>[13]</sup> bundles three properties:

```cpp
struct io_env
{
    executor_ref executor;
    std::stop_token stop_token;
    std::pmr::memory_resource* frame_allocator
        = nullptr;
};
```

The `executor_ref`<sup>[14]</sup> is a type-erased executor with `dispatch(continuation&)` returning `coroutine_handle<>` for symmetric transfer<sup>[15]</sup>, and `post(continuation&)` for deferred execution. The `continuation`<sup>[16]</sup> type is a simple intrusive-list node:

```cpp
struct continuation
{
    std::coroutine_handle<> h;
    continuation* next = nullptr;
};
```

The `io_env` flows forward through `co_await` chains via `task`'s<sup>[17]</sup> `await_transform`, which wraps each child awaitable and passes the environment into its `await_suspend`. The critical difference from the hand-rolled version: the awaitable knows which executor to resume on, carries a cancellation token, and has access to the frame allocator.

**Question for the reader:** Does this forward-propagation model - where the execution environment flows into each awaitable via `await_suspend` - address the concerns that GPU schedulers have about coroutine integration? Are there additional properties a GPU-aware awaitable would need?

## 6. CUDA Operations as IoAwaitables

### Kernel launch

Submit the kernel, then enqueue `cudaLaunchHostFunc`. The callback dispatches the continuation to the correct executor:

```cpp
class cuda_kernel_awaitable
{
    cudaStream_t stream_;
    continuation cont_;

    struct resume_ctx
    {
        executor_ref ex;
        continuation* cont;
    };

    static void CUDART_CB
    resume_on_executor(void* arg)
    {
        auto* ctx =
            static_cast<resume_ctx*>(arg);
        ctx->ex.post(*ctx->cont);
        delete ctx;
    }

public:
    // kernel launched before co_await
    explicit cuda_kernel_awaitable(
        cudaStream_t s) noexcept
        : stream_(s) {}

    bool await_ready() const noexcept
    {
        return false;
    }

    std::coroutine_handle<>
    await_suspend(std::coroutine_handle<> h,
                  io_env const* env)
    {
        cont_.h = h;
        auto* ctx = new resume_ctx{
            env->executor, &cont_};
        cudaLaunchHostFunc(stream_,
            &resume_on_executor, ctx);
        return std::noop_coroutine();
    }

    void await_resume() noexcept {}
};
```

### Memory transfer

The same pattern wraps `cudaMemcpyAsync`.<sup>[18]</sup> One caveat: `cudaMemcpyAsync` is only truly asynchronous with pinned (page-locked) memory.<sup>[19]</sup> With pageable memory allocated via `malloc` or `new`, the call blocks the host thread despite the `Async` suffix.<sup>[20]</sup> For multi-gigabyte model weight transfers that can take seconds, this distinction matters.

### CUDA Graph launch

`cudaGraphLaunch`<sup>[21]</sup> replays a captured kernel DAG. The same IoAwaitable pattern applies: launch the graph, enqueue the host callback, dispatch to the executor.

### Stream synchronization

A pure wait-for-completion awaitable using only `cudaLaunchHostFunc` on the target stream.

**Question for the reader:** Are these the right CUDA operations to wrap as awaitables? Are there GPU operations we have missed that would not fit this pattern?

## 7. Composition

Sequential stages are the order of `co_await` statements. Fan-out and fan-in use Capy's `when_all`<sup>[22]</sup> with `std::stop_token`<sup>[23]</sup> propagation. Conditionals use `if/else`. Loops use `for/while` with `break`. Error handling uses `try/catch`. These are standard C++ control flow constructs.

A training loop with data-dependent control flow:

```cpp
capy::task<> train(gpu_context& gpu,
                   dataset& data,
                   cudaStream_t stream)
{
    for (auto& batch : data)
    {
        co_await cuda_memcpy(stream,
            d_batch, batch.data(), batch.size(),
            cudaMemcpyHostToDevice);

        co_await cuda_launch(stream, g, b,
            forward_kernel, d_batch, d_act, N);

        float loss;
        co_await cuda_memcpy(stream,
            &loss, d_act, sizeof(float),
            cudaMemcpyDeviceToHost);

        if (loss < threshold)
            break;

        co_await cuda_launch(stream, g, b,
            backward_kernel, d_act, d_grad, N);

        co_await cuda_launch(stream, g, b,
            update_kernel, d_weights, d_grad,
            lr, N);
    }
}
```

A `for` loop with a conditional `break` in the middle, reading an intermediate result back from the GPU to decide whether to continue. The control flow is ordinary C++.

**Question for the reader:** Does this training loop reflect how real GPU pipelines handle data-dependent decisions mid-computation? Are there patterns in production GPU code that would not compose this way?

## 8. The std::execution Comparison

The concessions from Section 2 stand. What follows are structural observations, placed adjacent for the reader's evaluation.

**Compiler constraints.** The nvexec GPU path requires `nvc++` 25.9+ with `-stdpar=gpu`.<sup>[5]</sup><sup>[24]</sup> It does not work with nvcc, gcc, clang, or MSVC. The coroutine approach works with any C++20 compiler plus the CUDA toolkit.

**Operation state placement.** stdexec issue #953<sup>[25]</sup> documents that GPU sender operation states residing on the host stack cause invalid memory access in bulk kernels. The fix requires pinned host memory allocation, adding overhead absent from ordinary CUDA programming.

**Control flow in sender pipelines.** Several sources document the sender pipeline's relationship with non-linear control flow:

[P4014R1](https://isocpp.org/files/papers/P4014R1.pdf)<sup>[26]</sup> maps every C++ control flow construct to its sender equivalent: `if/else` becomes `let_value` returning `variant_sender`; loops become recursive `let_value` or `repeat_effect_until`. It takes an entire WG21 paper to explain how to express basic control flow in senders.

[P4007R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf)<sup>[27]</sup> analyzes the structural difference: "zero-allocation sender composition and coroutine constant-stack cannot both be satisfied."

Teodorescu writes in ACCU Overload 185<sup>[28]</sup>: "non-linear control flow like loops and branches is more cumbersome via sender composition than via coroutine co_await."

Meta's internal guidance for libunifex (GitHub issue #586<sup>[29]</sup>, December 2023): "Our experience at Meta has been that coroutines are easier to read, write, debug, and just generally maintain than composition-of-sender algorithms-style code. The advice we give to internal teams adopting Unifex is that they should prefer coroutines until they know that the overheads are unacceptable."

The stdexec [retry.hpp](https://github.com/NVIDIA/stdexec/blob/main/examples/algorithms/retry.hpp)<sup>[30]</sup> example shows what retry looks like in senders: a custom `_retry_receiver` intercepts `set_error`, destroys the current child operation via `optional::emplace`, reconnects the multi-shot sender, and restarts.

SG14's formal recommendation ([P4029R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4029r0.pdf))<sup>[31]</sup>: "Networking (SG4) should not be built on top of P2300."

**Question for the reader:** Is this a fair characterization of the tradeoffs? Are there sender pipeline capabilities in the GPU domain that we have not accounted for?

## 9. Independent Validation

We are not the first to explore this pattern. Several independent projects have arrived at the same design: `cudaLaunchHostFunc` (or its driver-level equivalent `cuLaunchHostFunc`) as the bridge between GPU completion and coroutine resumption.

**CERN wp1.7-coroutine-tests.**<sup>[43]</sup> The ATLAS and LHCb experiments at CERN developed a coroutine-based scheduler for GPU event processing. Their pattern uses `cudaLaunchHostFunc` to notify the scheduler when a GPU slot completes, and the coroutine suspends via `co_yield` until resumption. The project's documentation references Capy as a candidate for composing async CUDA operations.

**cuda-oxide (NVIDIA Labs, Rust).**<sup>[44]</sup> NVIDIA's own research lab implemented the same mechanism in Rust. Their `DeviceFuture` submits GPU work, enqueues a `cuLaunchHostFunc` callback that sets an `AtomicBool` and wakes a Tokio `Waker`, and the async runtime resumes the task on the next poll. Zero busy-wait. The three-state machine (Idle, Executing, Complete) is structurally identical to a network socket future.

**Taro (University of Wisconsin-Madison).**<sup>[45]</sup> A C++20 coroutine task-graph system for CPU-GPU workloads. GPU tasks suspend the CPU thread via coroutines when waiting for GPU completion, allowing other tasks to run. Uses `cudaLaunchHostFunc` for the callback. Published at Euro-Par 2024 and presented at CppCon 2023. Reported 40-80% speedup over blocking approaches.

**async-cuda (Oddity AI, Rust, production).**<sup>[46]</sup> A production library whose authors state: "Since the GPU is just another I/O device (from the point of view of your program), the async model actually fits surprisingly well."

**Schr&ouml;dinger Desmond (production, GTC 2024).**<sup>[47]</sup> The Desmond molecular dynamics engine uses C++ coroutines to overlap multiple GPU simulations. Coroutines suspend when a simulation hits a serial bottleneck, allowing another simulation to use the GPU. Presented at NVIDIA's GTC 2024 by NVIDIA's own DevTech team. Achieved up to 2.02x speedup in FEP+ drug discovery workloads. Coroutines were chosen because they could "retrofit into existing CUDA code without complex code restructuring."

**TTG/PaRSEC (DOE Exascale Computing Project).**<sup>[48]</sup> A template task graph framework where `co_await ttg::device::select(...)` and `co_await ttg::device::wait(...)` are the primary mechanism for GPU task dispatch. Supports CUDA, HIP/ROCm, and Intel Level Zero. The project states that "the use of coroutines is the primary reason why TTG requires C++20 support."

**RDMA coroutine libraries.** Three independent projects wrap RDMA verbs as coroutine awaitables: RDMA++ (rdmapp)<sup>[49]</sup> wraps libibverbs with C++20 coroutines using `ibv_comp_channel` fd; Loom<sup>[50]</sup> provides C++23 typed bindings over libfabric with `co_await ep.async_receive(buf, asio::use_awaitable)`; and FORD<sup>[51]</sup> (USENIX FAST 2022) implements coroutine-enabled distributed transactions over one-sided RDMA, spawning multiple follow-on systems (Motor, CREST at ASPLOS 2026).

**Question for the reader:** Are we reading this landscape correctly? Are there significant projects using the `cudaLaunchHostFunc`-to-coroutine pattern that we have missed?

## 10. Large-Scale Data Transfers

GPU programming is not just kernel launches. For large models, the dominant async operations are data transfers, and these are fundamentally I/O:

- **NCCL AllReduce** for a 600B-parameter model: milliseconds to seconds per collective. Completion via CUDA stream callback.
- **PCIe/NVLink `cudaMemcpyAsync`**: seconds for multi-gigabyte weight transfers. Completion via `cudaLaunchHostFunc`.
- **RDMA verbs** (`ibv_post_send`): completion via `ibv_comp_channel.fd` - a plain file descriptor that works with epoll, io_uring, or kqueue. The same reactor pattern as TCP sockets.
- **UCX** (`ucp_tag_send_nbx`): completion via callback with `void* user_data`, or `ucp_worker_get_efd()` for reactor integration.

These completion models - streams, file descriptors, callbacks - map directly to the IoAwaitable/reactor pattern:

```cpp
capy::task<> allreduce(
    nccl_comm& comm, cudaStream_t stream,
    float* sendbuf, float* recvbuf,
    size_t count)
{
    ncclAllReduce(sendbuf, recvbuf, count,
        ncclFloat, ncclSum,
        comm.handle(), stream);
    co_await cuda_stream_awaiter{stream};
}
```

The RDMA completion channel exposes an fd. [Corosio](https://github.com/cppalliance/corosio)<sup>[2]</sup>'s reactor watches it with epoll. The completion returns `(wr_id, status, byte_len)` - the same compound result pattern as TCP. The `wr_id` stores the coroutine handle for dispatch.

Five HPC networking libraries (NCCL, UCX, libibverbs, libfabric, NVSHMEM) run every LLM training cluster on earth. None use compile-time work graphs.

**Question for the reader:** Is the structural alignment between RDMA completion channels and the coroutine reactor pattern a coincidence, or does it reflect something fundamental about how GPU-to-GPU data movement works? Are there HPC networking workloads where compile-time visibility of the transfer operations would enable optimizations we have not considered?

## 11. CUDA Graphs and the Static Graph Question

Sender pipelines provide compile-time `operation_state` fusion. [P3425R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3425r1.html)<sup>[32]</sup> documents 8 bytes saved per nesting level via constant pointer offsets. This is real.

CUDA Graphs<sup>[33]</sup> capture kernel DAGs via stream capture<sup>[8]</sup>:

```c
cudaStreamBeginCapture(stream,
    cudaStreamCaptureModeGlobal);
kernel_A<<<grid, block, 0, stream>>>(args);
kernel_B<<<grid, block, 0, stream>>>(args);
cudaStreamEndCapture(stream, &graph);

cudaGraphInstantiate(&instance, graph, 0);
cudaGraphLaunch(instance, stream);
```

The quantitative picture:

- Graph replay: approximately 2.5 us for the entire graph on CUDA 12.6+.<sup>[34]</sup>
- For 100 sequential kernels: stream launch approximately 400 us vs graph launch approximately 2.5 us - a 160x reduction.<sup>[34]</sup>
- In DALLE2 inference (740 kernels, 3.4ms GPU time), 75% of end-to-end latency is CPU launch delays.<sup>[35]</sup>

The driver sees SM count, memory bandwidth, occupancy, and hardware topology. Sender compile-time fusion operates on host-side pointer arithmetic. CUDA Graphs operate on GPU hardware scheduling.

A CUDA Graph launch composes naturally as an IoAwaitable. The coroutine is the outer loop with data-dependent control flow; the graph is the inner optimized hotpath:

```cpp
capy::task<> train(gpu_context& gpu,
                   dataset& data,
                   cudaGraphExec_t graph,
                   cudaStream_t stream)
{
    for (auto& batch : data)
    {
        co_await cuda_memcpy(stream,
            d_in, batch.data(), batch.size(),
            cudaMemcpyHostToDevice);

        // replay the optimized graph
        cudaGraphLaunch(graph, stream);
        co_await cuda_stream_awaiter{stream};

        float loss;
        co_await cuda_memcpy(stream,
            &loss, d_act, sizeof(float),
            cudaMemcpyDeviceToHost);

        if (loss < threshold)
            break;
    }
}
```

**Question for the reader:** Does CUDA Graph stream capture already provide the work-graph optimization that compile-time sender fusion aims to deliver? Or does sender fusion provide something above what CUDA Graphs offer at the driver level?

## 12. The Frame Allocation Question

Each coroutine suspension potentially allocates a frame. Sender `operation_state` is a single compile-time allocation. This is a real structural difference.

### HALO

Heap Allocation eLision Optimization<sup>[36]</sup> allows the compiler to place the coroutine frame in the caller's frame when the lifetime is provably bounded. Capy's `task` is annotated with `[[clang::coro_await_elidable]]`<sup>[37]</sup> to enable this.

HALO is fragile in practice:

- The attribute was introduced<sup>[38]</sup> because "real-world Task types are rarely simple enough for CoroElide's SSA analysis."
- Confirmed regression: patterns working in Clang 17-18 broke in Clang 19-20. `when_all`-style patterns cannot leverage HALO even in principle.<sup>[39]</sup>
- Correctness bug: HALO combined with `suspend_never` causes a bad-free of stack memory.<sup>[40]</sup>
- Parentheses around a `co_await` operand silently break elision. Fixed in Clang 22; backport to 21 declined.<sup>[41]</sup>
- Clang-only. Not GCC, not MSVC.

HALO is nice when it fires. It is not something to rely on.

### Does it matter?

Capy's `io_env` carries a `std::pmr::memory_resource*`.<sup>[42]</sup> Thread-local recycling pools amortize allocation cost to near zero. This is reliable, portable, and works regardless of compiler optimization.

| Operation | Time |
|---|---|
| Coroutine frame alloc (PMR pool) | 2-5 ns |
| Coroutine frame alloc (malloc) | 30-60 ns |
| CUDA kernel launch (C++) | 1,000-5,000 ns |
| `cudaMemcpy` (4 bytes) | 10,000 ns |
| CUDA Graph replay (entire graph) | 2,500 ns |
| Conv2d forward (A100, BS=1) | 24,000 ns |
| NCCL AllReduce (600B model) | 1,000,000,000+ ns |

A coroutine frame allocation with a PMR pool is 200x-100,000x cheaper than the GPU operations it orchestrates. For a 900B-parameter model's AllReduce that takes seconds, the 5 ns frame allocation is nine orders of magnitude smaller.

**Question for the reader:** Is our assumption about the relative cost of frame allocation accurate at GPU workload scale? Are there scenarios in high-frequency kernel dispatch where coroutine frame allocation becomes a measurable bottleneck?

## 13. The Expressiveness Test

A single scenario in both styles.

**Scenario.** Multi-stage GPU inference pipeline with batch iteration, conditional preprocessing, multi-stream parallel execution, device-to-host readback for data-dependent branching, timeout per batch, retry on transient GPU allocation failure, and early termination on fatal error.

### Coroutine version (Capy IoAwaitable)

```cpp
capy::task<> process_one_batch(
    gpu_context& gpu,
    corosio::io_context& ioc,
    batch& batch)
{
    auto stream = gpu.make_stream();

    // retry allocation
    float* d_input = nullptr;
    for (int i = 0; i < 3; ++i)
    {
        auto err = cudaMallocAsync(
            &d_input, batch.bytes(),
            stream);
        if (err == cudaSuccess)
            break;
        if (i == 2)
            throw cuda_error(err);
        corosio::timer t(ioc, 100ms);
        co_await t.wait();
    }

    co_await cuda_memcpy(stream,
        d_input, batch.data(),
        batch.bytes(),
        cudaMemcpyHostToDevice);

    // conditional preprocess
    if (batch.size() > MAX_SIZE)
        co_await cuda_launch(
            stream, g, b,
            resize_kernel,
            d_input, MAX_SIZE);
    else
        co_await cuda_launch(
            stream, g, b,
            pad_kernel,
            d_input, MAX_SIZE);

    // parallel model stages
    float *d_a, *d_b;
    cudaMallocAsync(
        &d_a, OUT_BYTES, stream);
    cudaMallocAsync(
        &d_b, OUT_BYTES, stream);

    co_await capy::when_all(
        cuda_launch(
            gpu.make_stream(),
            g, b, stage_a,
            d_input, d_a, N),
        cuda_launch(
            gpu.make_stream(),
            g, b, stage_b,
            d_input, d_b, N));

    // readback for decision
    float score;
    co_await cuda_memcpy(stream,
        &score, d_a,
        sizeof(float),
        cudaMemcpyDeviceToHost);

    if (score > THRESHOLD)
        co_await cuda_launch(
            stream, g, b,
            postprocess,
            d_a, d_b, N);

    co_await cuda_memcpy(stream,
        batch.result(), d_a,
        OUT_BYTES,
        cudaMemcpyDeviceToHost);

    cudaFreeAsync(d_input, stream);
    cudaFreeAsync(d_a, stream);
    cudaFreeAsync(d_b, stream);
}

capy::task<> inference_pipeline(
    gpu_context& gpu,
    corosio::io_context& ioc,
    std::span<batch> batches,
    std::chrono::seconds timeout_dur)
{
    for (auto& batch : batches)
    {
        try
        {
            auto [ec] = co_await
                capy::timeout(
                    process_one_batch(
                        gpu, ioc, batch),
                    timeout_dur);
            if (ec == capy::cond::timeout)
            {
                log("batch timed out");
                continue;
            }
            if (ec)
                break;
        }
        catch (cuda_error const& e)
        {
            log("cuda error: {}",
                e.what());
            break;
        }
    }
}
```

### Sender pipeline version (stdexec)

Verified against stdexec source. Uses `exec::repeat_until` (not the deprecated `repeat_effect_until`), `exec::when_any` for timeout racing, `exec::any_sender_of<>` for conditional branch unification, and mutable captured state for iteration. `exec::schedule_after` requires a `timed_scheduler`-conforming scheduler.

```cpp
auto inference_pipeline(
    gpu_context& gpu,
    std::span<batch> batches,
    std::chrono::seconds timeout_dur)
{
    std::size_t idx = 0;
    auto const n = batches.size();
    auto gpu_sched =
        gpu.get_scheduler();
    auto timer_sched =
        gpu.get_timer_scheduler();

    if (n == 0)
        return stdexec::just();

    return stdexec::just()
    | stdexec::let_value([&]()
        -> exec::any_sender_of<bool>
    {
        auto& batch = batches[idx];

        // retry allocation
        int attempt = 0;
        auto alloc_with_retry =
            stdexec::just()
            | stdexec::let_value([&]()
                -> exec::any_sender_of<
                    bool>
            {
                auto err =
                    cudaMallocAsync(
                        &batch.d_input,
                        batch.bytes(),
                        batch.stream);
                if (err == cudaSuccess)
                    return stdexec::just(
                        true);
                if (++attempt >= 3)
                    throw cuda_error(err);
                return
                    exec::schedule_after(
                        timer_sched, 100ms)
                    | stdexec::then([] {
                        return false;
                    });
            })
            | exec::repeat_until();

        // upload
        auto upload =
            stdexec::then([&] {
            cudaMemcpyAsync(
                batch.d_input,
                batch.data(),
                batch.bytes(),
                cudaMemcpyHostToDevice,
                batch.stream);
        });

        // conditional preprocess
        auto preprocess =
            stdexec::then([&] {
            if (batch.size() > MAX_SIZE)
                resize_kernel
                    <<<g, b, 0,
                       batch.stream>>>(
                    batch.d_input,
                    MAX_SIZE);
            else
                pad_kernel
                    <<<g, b, 0,
                       batch.stream>>>(
                    batch.d_input,
                    MAX_SIZE);
        });

        // parallel stages
        auto parallel_stages =
            stdexec::when_all(
            exec::on(gpu_sched,
                stdexec::then([&] {
                stage_a
                    <<<g, b, 0,
                       batch.stream_a>>>(
                    batch.d_input,
                    batch.d_a, N);
            })),
            exec::on(gpu_sched,
                stdexec::then([&] {
                stage_b
                    <<<g, b, 0,
                       batch.stream_b>>>(
                    batch.d_input,
                    batch.d_b, N);
            }))
        );

        // readback + conditional
        auto readback_and_post =
            stdexec::then([&] {
                cudaMemcpyAsync(
                    &batch.score,
                    batch.d_a,
                    sizeof(float),
                    cudaMemcpyDeviceToHost,
                    batch.stream);
                cudaStreamSynchronize(
                    batch.stream);
                return batch.score;
            })
            | stdexec::let_value(
                [&](float score)
                -> exec::any_sender_of<>
            {
                if (score > THRESHOLD)
                    return exec::on(
                        gpu_sched,
                        stdexec::then([&] {
                        postprocess
                            <<<g, b, 0,
                               batch
                               .stream>>>(
                            batch.d_a,
                            batch.d_b, N);
                    }));
                else
                    return
                        stdexec::just();
            });

        // download
        auto download =
            stdexec::then([&] {
            cudaMemcpyAsync(
                batch.result(),
                batch.d_a, OUT_BYTES,
                cudaMemcpyDeviceToHost,
                batch.stream);
        });

        // cleanup
        auto cleanup =
            stdexec::then([&] {
            cudaFreeAsync(
                batch.d_input,
                batch.stream);
            cudaFreeAsync(
                batch.d_a, batch.stream);
            cudaFreeAsync(
                batch.d_b, batch.stream);
        });

        // compose one batch
        auto one_batch =
            alloc_with_retry
            | upload
            | preprocess
            | parallel_stages
            | readback_and_post
            | download
            | cleanup;

        // timeout: when_any races
        // batch vs timer
        auto timed_batch =
            exec::when_any(
            std::move(one_batch)
                | stdexec::then([&]()
                    -> std::optional<
                        bool> {
                    return false;
                }),
            exec::schedule_after(
                timer_sched, timeout_dur)
                | stdexec::then([]()
                    -> std::optional<
                        bool> {
                    return std::nullopt;
                })
        )
        | stdexec::then(
            [&](std::optional<bool>
                result)
            -> bool
        {
            if (!result) {
                log("batch timed out");
                return false;
            }
            return *result;
        })
        | stdexec::upon_error(
            [&](std::exception_ptr
                eptr) -> bool
        {
            try {
                std::rethrow_exception(
                    eptr);
            } catch (
                cuda_error const& e) {
                log("cuda error: {}",
                    e.what());
                return true;
            } catch (...) {
                return true;
            }
        });

        return timed_batch;
    })
    | exec::repeat_until();
}
```

**Question for the reader:** Is this a representative scenario for GPU inference pipelines? Would a production system encounter all of these control flow patterns in a single pipeline? And for the sender version: would a sender practitioner write this differently?

## 14. Conclusion

C++20 coroutines have been in the language since 2020.

The IoAwaitable protocol provides executor affinity, cancellation, and frame allocation - the same concerns that `std::execution` addresses through a different mechanism. CUDA's own infrastructure - streams, events, graphs, `cudaLaunchHostFunc` - provides the completion hooks that IoAwaitables consume. CUDA Graphs provide GPU-side optimization at the driver level, operating on hardware topology that no host-side compiler can see.

Every HPC networking library's completion model - streams, file descriptors, callbacks, completion queues - maps to the coroutine reactor pattern. None use compile-time work graphs.

The frame allocation cost is real. It is nanoseconds against microsecond-to-millisecond GPU operations.

Coroutines and senders interoperate via bridge functions (`await_sender`, `as_sender`). This is not a zero-sum choice.

**The GPU already has a work-graph engine. Now it has two voices.**

## Acknowledgements

Eric Niebler, Micha&lstrok; Dominiak, Lewis Baker, Lucian Radu Teodorescu, Lee Howes, Kirk Shoop, Michael Garland, Bryce Adelstein Lelbach, Dietmar K&uuml;hl, and Jens Maurer, whose work on `std::execution` (P2300R10) this paper examines and builds upon.

Richard Smith and Gor Nishanov for P0981R0 (HALO analysis). Chuanqi Xu for the `[[clang::coro_await_elidable]]` attribute and P2477R3 (coroutine allocation elision). Dietmar K&uuml;hl and Maikel Nadolski for P3552R3 (`std::execution::task`). Lewis Baker for cppcoro, the operator `co_await` and symmetric transfer blog posts, and P3425R1 (operation-state sizes). Michael Wong for P4029R0 (SG14 priority list). Lucian Radu Teodorescu for the sender tutorial in ACCU Overload 185.

Michael Garland and the NVIDIA stdexec team for the nvexec GPU schedulers and the Maxwell FDTD benchmark. The CERN wp1.7 team for their coroutine-based GPU event processing work. Dian-Lun Lin (University of Wisconsin-Madison) for Taro and its CppCon 2023 presentation. The NVIDIA Labs team for cuda-oxide. Jiqun Tu (NVIDIA) and Ellery Russell (Schr&ouml;dinger) for the Desmond coroutine integration presented at GTC 2024. The TTG/PaRSEC team for demonstrating coroutine-based heterogeneous GPU dispatch at DOE Exascale scale.

This paper was generated with AI assistance (Claude, via Cursor).

## References

[1] [Capy](https://github.com/cppalliance/capy) (C++ Alliance).

[2] [Corosio](https://github.com/cppalliance/corosio) (C++ Alliance).

[3] [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) - "`std::execution`" (Eric Niebler, Micha&lstrok; Dominiak, Lewis Baker, Lucian Radu Teodorescu, Lee Howes, Kirk Shoop, Michael Garland, Bryce Adelstein Lelbach, 2024).

[4] [nvexec stream_context.cuh](https://github.com/NVIDIA/stdexec/blob/main/include/nvexec/stream_context.cuh) - NVIDIA stdexec GPU scheduler.

[5] [NVIDIA/stdexec](https://github.com/NVIDIA/stdexec) - Reference implementation of `std::execution`.

[6] [CUDA Programming Guide: Asynchronous Concurrent Execution](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/asynchronous-execution.html) (NVIDIA, 2024).

[7] [CUDA Runtime API: Event Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EVENT.html) (NVIDIA, 2024).

[8] [CUDA Runtime API: Stream Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__STREAM.html) (NVIDIA, 2024).

[9] [CUDA Runtime API: Execution Control](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EXECUTION.html) (NVIDIA, 2024).

[10] [CUDA Handbook: Stream Callbacks](https://www.cudahandbook.com/2012/09/stream-callbacks/) (Nicholas Wilt, 2012).

[11] [Stack Overflow: Exception Handling in cudaLaunchHostFunc Callbacks](https://stackoverflow.com/questions/75145603/catching-an-exception-thrown-from-a-callback-in-cudalaunchhostfunc) (2023).

[12] [DeepWiki: nvexec GPU Execution](https://deepwiki.com/NVIDIA/stdexec/6-gpu-execution-with-nvexec).

[13] [Capy io_env](https://github.com/cppalliance/capy/blob/master/include/boost/capy/ex/io_env.hpp) (C++ Alliance).

[14] [Capy executor_ref](https://github.com/cppalliance/capy/blob/master/include/boost/capy/ex/executor_ref.hpp) (C++ Alliance).

[15] [Understanding Symmetric Transfer](https://lewissbaker.github.io/2020/05/11/understanding_symmetric_transfer) (Lewis Baker, 2020).

[16] [Capy continuation](https://github.com/cppalliance/capy/blob/master/include/boost/capy/continuation.hpp) (C++ Alliance).

[17] [Capy task](https://github.com/cppalliance/capy/blob/master/include/boost/capy/task.hpp) (C++ Alliance).

[18] [CUDA Runtime API: Memory Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__MEMORY.html) (NVIDIA, 2024).

[19] [CUDA Programming Guide: Page-Locked Host Memory](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html) (NVIDIA, 2024).

[20] [CUDA Runtime API: API Synchronization Behavior](https://docs.nvidia.com/cuda/cuda-runtime-api/api-sync-behavior.html) (NVIDIA, 2024).

[21] [CUDA Runtime API: Graph Management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__GRAPH.html) (NVIDIA, 2024).

[22] [Capy when_all](https://github.com/cppalliance/capy/blob/master/include/boost/capy/when_all.hpp) (C++ Alliance).

[23] [std::stop_token](https://en.cppreference.com/w/cpp/thread/stop_token) (cppreference).

[24] [NVIDIA HPC SDK Compilers Reference Guide](https://docs.nvidia.com/hpc-sdk/compilers/hpc-compilers-ref-guide/) (NVIDIA, 2024).

[25] [stdexec Issue #953: Bulk kernel memory-access bug](https://github.com/NVIDIA/stdexec/issues/953).

[26] [P4014R1](https://isocpp.org/files/papers/P4014R1.pdf) - "The Sender Sub-Language For Beginners" (Vinnie Falco, Steve Bergino, Mungo Gill, 2026).

[27] [P4007R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4007r0.pdf) - "Senders and Coroutines" (2026).

[28] [Using Senders/Receivers](https://accu.org/journals/overload/33/185/teodorescu/) - ACCU Overload 185 (Lucian Radu Teodorescu, 2025).

[29] [libunifex Issue #586](https://github.com/facebook/libunifex/issues/586) - Meta internal guidance on senders vs coroutines (2023).

[30] [stdexec retry.hpp](https://github.com/NVIDIA/stdexec/blob/main/examples/algorithms/retry.hpp) - Retry algorithm example.

[31] [P4029R0](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4029r0.pdf) - "The SG14 Priority List for C++29/32" (Michael Wong, 2026).

[32] [P3425R1](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3425r1.html) - "Reducing operation-state sizes for subobject child operations" (Lewis Baker, 2025).

[33] [CUDA Programming Guide: CUDA Graphs](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html) (NVIDIA, 2024).

[34] [NVIDIA CUDA Graph Best Practices: Quantitative Benefits](https://docs.nvidia.com/dl-cuda-graph/cuda-graph-basics/cuda-graph.html) (NVIDIA, 2024).

[35] [PyGraph: Robust Compiler Support for CUDA Graphs in PyTorch](https://arxiv.org/html/2503.19779v3) (2025).

[36] [P0981R0](https://www.open-std.org/JTC1/SC22/WG21/docs/papers/2018/p0981r0.html) - "Halo: coroutine Heap Allocation eLision Optimization: the joint response" (Richard Smith, Gor Nishanov, 2018).

[37] [Clang Attribute Reference: coro_await_elidable](https://clang.llvm.org/docs/AttributeReference.html#coro-await-elidable) (LLVM).

[38] [LLVM PR #99282: Introduce coro_await_elidable](https://github.com/llvm/llvm-project/pull/99282) (Chuanqi Xu, 2024).

[39] [LLVM Issue #64586: CoroElide failures and regressions](https://github.com/llvm/llvm-project/issues/64586).

[40] [LLVM Issue #188230: HALO + suspend_never bad-free](https://github.com/llvm/llvm-project/issues/188230).

[41] [LLVM Issue #178256: Parentheses break coro_await_elidable](https://github.com/llvm/llvm-project/issues/178256).

[42] [std::pmr::memory_resource](https://en.cppreference.com/w/cpp/memory/memory_resource) (cppreference).

[43] [cern-nextgen/wp1.7-coroutine-tests](https://github.com/cern-nextgen/wp1.7-coroutine-tests) - CERN coroutine-based GPU event processing scheduler (2026).

[44] [cuda-oxide: The DeviceOperation Model](https://nvlabs.github.io/cuda-oxide/async-programming/the-device-operation-model.html) - NVIDIA Labs async GPU programming in Rust (2026).

[45] [Taro](https://github.com/dian-lun-lin/taro) - C++20 coroutine task-graph system for CPU-GPU workloads (Dian-Lun Lin, University of Wisconsin-Madison, 2024).

[46] [async-cuda](https://github.com/oddity-ai/async-cuda) - Async CUDA for Rust (Oddity AI, 2024).

[47] [Optimizing Drug Discovery with CUDA Graphs, Coroutines, and GPU Workflows](https://developer.nvidia.com/blog/optimizing-drug-discovery-with-cuda-graphs-coroutines-and-gpu-workflows/) - NVIDIA Developer Blog (Jiqun Tu, Ellery Russell, 2024).

[48] [TTG (Template Task Graph)](https://github.com/TESSEorg/ttg) - C++20 coroutine-based heterogeneous task graph on PaRSEC (2024).

[49] [rdmapp](https://github.com/howardlau1999/rdmapp) - C++20 coroutine wrapper for libibverbs (2024).

[50] [Loom](https://github.com/sielicki/loom) - C++23 typed interface over libfabric with Asio coroutine integration.

[51] [FORD](https://github.com/minghust/ford) - Coroutine-enabled distributed transactions over one-sided RDMA (USENIX FAST 2022).
