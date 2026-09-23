package main

import (
	"context"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most workers running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errInvalidWorkers
	}
	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	// Child context: cancelled either when a task fails or when the parent
	// context is cancelled.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, n)

	type outcome struct {
		idx int
		err error
	}

	// jobCh carries the index of the next task to start. It is closed by the
	// dispatcher goroutine when there is nothing left to do or when we should
	// stop starting new tasks.
	jobCh := make(chan int)

	var (
		firstErr   error
		firstErrMu sync.Mutex
	)

	// dispatch feeds indices to workers. We use an unbuffered channel so that
	// a task index is only handed out when a worker is ready to start it; when
	// we abort, the dispatcher stops handing out new indices, guaranteeing that
	// unstarted tasks never begin.
	dispatch := func() {
		defer close(jobCh)
		for i := 0; i < n; i++ {
			select {
			case jobCh <- i:
			case <-taskCtx.Done():
				return
			}
		}
	}

	var (
		wg       sync.WaitGroup
		stopOnce sync.Once
	)

	// stop records the first error seen and cancels the task context.
	stop := func(err error) {
		if err == nil {
			return
		}
		stopOnce.Do(func() {
			firstErrMu.Lock()
			firstErr = err
			firstErrMu.Unlock()
			cancel()
		})
	}

	actualWorkers := workers
	if actualWorkers > n {
		actualWorkers = n
	}

	go dispatch()

	for w := 0; w < actualWorkers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range jobCh {
				// The task's own context: it gets cancelled by taskCtx.
				v, err := tasks[idx](taskCtx)
				if err != nil {
					stop(err)
					return
				}
				results[idx] = v
			}
		}()
	}

	// Wait for all started tasks to finish.
	wg.Wait()

	firstErrMu.Lock()
	err := firstErr
	firstErrMu.Unlock()

	if err != nil {
		return nil, err
	}
	// If we stopped because the parent context was cancelled, report it.
	if cerr := ctx.Err(); cerr != nil {
		return nil, cerr
	}
	return results, nil
}

type poolError string

func (e poolError) Error() string { return string(e) }

const errInvalidWorkers = poolError("pool: workers must be >= 1")
