# Problem 4 — Bounded Worker Pool (Go, hard)

Write a single Go file named `pool.go`, with `package main`, that implements:

```go
// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error)
```

(The grader supplies its own `func main`; your file must NOT define `main`.
Declare exactly these two identifiers at package level, plus any unexported
helpers you need.)

## Required semantics

1. **Ordering** — on success, `results[i]` is the value returned by
   `tasks[i]`, for every `i`. Return `([]any, nil)` with
   `len(results) == len(tasks)`.
2. **Bounded concurrency** — at any instant, at most `workers` tasks are
   executing. Tasks must actually run concurrently up to that bound (a serial
   implementation is wrong and will fail the timing checks).
3. **Validation** — if `workers < 1`, return a non-nil error immediately
   without running any task. If `len(tasks) == 0`, return an empty (or nil)
   slice and nil error.
4. **Fail fast** — if any task returns a non-nil error:
   - `Run` returns `(nil, err)` where `err` is (or wraps) the **first error
     that occurred**;
   - tasks that have not yet **started** must never start;
   - the `ctx` passed to still-running tasks must be cancelled, so
     cooperative tasks can abort early;
   - `Run` must still wait for already-started tasks to finish before
     returning (no goroutine leaks).
5. **Context cancellation** — if the parent `ctx` is cancelled (or times
   out) while `Run` is in flight: stop starting new tasks, cancel the
   task context, wait for started tasks, and return `(nil, ctx.Err())`
   (or an error wrapping it).
6. **Panic safety is not required** — tasks are trusted not to panic.

## Constraints

- Standard library only.
- No busy-waiting (`for {}` polling loops with `time.Sleep` are not
  acceptable for the core synchronization; use channels / sync primitives).
- Must compile with Go 1.22+ and be race-free (`go run -race` clean).

**Deliverable: exactly one file, `pool.go` (`package main`, no `func main`).**
