package main

import (
	"context"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errInvalidWorkers
	}
	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}

	// Task context: cancelled as soon as any task fails or the parent is done.
	taskCtx, cancelTasks := context.WithCancel(ctx)
	defer cancelTasks()

	results := make([]any, n)

	// jobs is an unbuffered channel of indices. Dispatcher sends; workers pick up.
	jobs := make(chan int)

	// firstErr captures the first error encountered, along with its index.
	var (
		errOnce    sync.Once
		firstErr   error
		errIndex   int
		parentDone = ctx.Done()
	)

	// stopInitiated is closed once we want to stop dispatching new work.
	stopInitiated := make(chan struct{})
	var stopOnce sync.Once
	signalStop := func() { stopOnce.Do(func() { close(stopInitiated) }) }

	// Watch parent context: on cancel, initiate stop.
	go func() {
		select {
		case <-parentDone:
			signalStop()
			// Also cancel task ctx so running tasks observe cancellation.
			cancelTasks()
		case <-stopInitiated:
		}
	}()

	var wg sync.WaitGroup
	wg.Add(workers)

	for w := 0; w < workers; w++ {
		go func() {
			defer wg.Done()
			for i := range jobs {
				v, err := tasks[i](taskCtx)
				if err != nil {
					// Record first error.
					errOnce.Do(func() {
						firstErr = err
						errIndex = i
						// Cancel task ctx to abort other running tasks.
						cancelTasks()
						// Stop dispatching new work.
						signalStop()
					})
					// Task errored: don't store its result.
					return
				}
				results[i] = v
			}
		}()
	}

	// Dispatcher: sends task indices up to (but not past) first error.
	dispatchDone := make(chan struct{})
	go func() {
		defer close(dispatchDone)
		defer close(jobs)
		for i := 0; i < n; i++ {
			select {
			case <-stopInitiated:
				return
			case jobs <- i:
			}
		}
	}()

	wg.Wait()
	<-dispatchDone

	// Determine outcome. Prefer explicit task error if any.
	select {
	case <-stopInitiated:
		// Something stopped us. Was it a task error or parent cancellation?
		if firstErr != nil {
			return nil, firstErr
		}
		// Parent context must have been cancelled.
		if err := ctx.Err(); err != nil {
			return nil, err
		}
		return nil, context.Canceled
	default:
	}

	if firstErr != nil {
		return nil, firstErr
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	_ = errIndex
	return results, nil
}

type poolError string

func (e poolError) Error() string { return string(e) }

const errInvalidWorkers = poolError("pool: workers must be >= 1")
