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
		return nil, context.Canceled // or a custom error; spec says non-nil error
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Create a cancellable context that is cancelled when the first error occurs
	// or when the parent context is cancelled.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	var firstErr error
	var errOnce sync.Once
	var wg sync.WaitGroup

	// Use a semaphore channel to limit concurrency
	sem := make(chan struct{}, workers)

	// We need to track which tasks have been started so we can stop starting new ones
	// on error or context cancellation.

	// We'll use a dispatch pattern: a dispatcher goroutine sends task indices to workers.
	// But we need to ensure that once an error occurs, no new tasks start.

	// Approach:
	// - Create a channel for task indices to dispatch.
	// - Workers pull from this channel.
	// - A dispatcher sends indices 0..len(tasks)-1, but stops if ctx is done or firstErr is set.
	// - When a task completes with an error, set firstErr (once) and cancel taskCtx.
	// - Workers check if taskCtx is done before starting a task; if so, they don't run it.
	//   Actually, we need to be careful: if a task is already dispatched but not yet started,
	//   and an error occurs, we should not start it.

	// Let's use a different approach:
	// - We have `workers` goroutines.
	// - Each worker loops: acquire sem, get next task index from a shared counter (with mutex),
	//   check if we should stop (ctx done or firstErr set), if so release sem and break.
	//   Otherwise, run the task.

	// Actually, let's use a simpler pattern with a channel for task indices.

	taskCh := make(chan int)
	var dispatchWg sync.WaitGroup

	// Dispatcher: sends task indices to taskCh
	dispatchWg.Add(1)
	go func() {
		defer dispatchWg.Done()
		defer close(taskCh)
		for i := 0; i < len(tasks); i++ {
			select {
			case <-taskCtx.Done():
				return
			case taskCh <- i:
			}
		}
	}()

	// Workers
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-taskCtx.Done():
					return
				case idx, ok := <-taskCh:
					if !ok {
						return
					}
					// Check again if we should stop
					select {
					case <-taskCtx.Done():
						return
					default:
					}
					// Run the task
					result, err := tasks[idx](taskCtx)
					if err != nil {
						errOnce.Do(func() {
							firstErr = err
							cancel()
						})
					} else {
						results[idx] = result
					}
				}
			}
		}()
	}

	// Wait for all workers to finish
	wg.Wait()
	dispatchWg.Wait()

	// Check if the parent context was cancelled
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
