package main

import (
	"context"
	"errors"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}

	n := len(tasks)
	if n == 0 {
		return nil, nil
	}

	// Create a derived context that we can cancel if a task fails or the parent context is cancelled.
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, n)
	
	// We use a channel to feed task indices to workers.
	taskIdxChan := make(chan int)
	
	// We use a channel to collect results/errors.
	// Since we need to return the first error and wait for all started tasks,
	// we'll use a struct to pass results back.
	type result struct {
		idx int
		val any
		err error
	}
	resChan := make(chan result, n)

	var wg sync.WaitGroup
	
	// Start workers.
	numWorkers := workers
	if numWorkers > n {
		numWorkers = n
	}

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range taskIdxChan {
				// Check if we should even start this task.
				// The select ensures we don't start a task if the context is already done.
				select {
				case <-runCtx.Done():
					return
				default:
				}

				val, err := tasks[idx](runCtx)
				
				// Send result back.
				// Note: even if runCtx is cancelled, we must send the result to ensure
				// the collector knows this task finished.
				resChan <- result{idx: idx, val: val, err: err}
			}
		}()
	}

	// Producer goroutine: feeds indices to workers.
	go func() {
		defer close(taskIdxChan)
		for i := 0; i < n; i++ {
			select {
			case <-runCtx.Done():
				return
			case taskIdxChan <- i:
			}
		}
	}()

	// Collector logic.
	// We need to wait for all workers to finish to ensure no leaks.
	// We also need to capture the first error.
	
	var firstErr error
	var errOnce sync.Once

	// We'll use a separate goroutine to close resChan once all workers are done.
	go func() {
		wg.Wait()
		close(resChan)
	}()

	// Process results as they come in.
	// We need to keep track of how many tasks have completed to know when we are done.
	// However, if an error occurs, we stop processing and return.
	// But we MUST wait for all workers to finish (wg.Wait) before returning to avoid leaks.
	
	// To satisfy "wait for already-started tasks to finish", we can't just return immediately.
	// We'll collect results in a loop.
	
	completedCount := 0
	for res := range resChan {
		if res.err != nil {
			errOnce.Do(func() {
				firstErr = res.err
				cancel() // Stop other tasks and prevent new ones from starting.
			})
		} else {
			// Only store result if we haven't encountered an error yet.
			// Actually, we can store them all, but if firstErr is set, we return nil.
			results[res.idx] = res.val
		}
		completedCount++
		
		// If we hit an error, we don't break the loop immediately because we need 
		// to drain resChan or wait for wg.Wait to ensure no leaks.
		// The loop `for res := range resChan` will naturally terminate when wg.Wait() 
		// finishes and resChan is closed.
	}

	// If the parent context was cancelled, return its error.
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	if firstErr != nil {
		return nil, firstErr
	}

	return results, nil
}
