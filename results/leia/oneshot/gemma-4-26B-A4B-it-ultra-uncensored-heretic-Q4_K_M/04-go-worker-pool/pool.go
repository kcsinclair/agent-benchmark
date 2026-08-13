package main

import (
	"context"
	"fmt"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// result wraps the output of a task to be passed through channels.
type result struct {
	index int
	val   any
	err   error
}

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, fmt.Errorf("workers must be at least 1")
	}

	if len(tasks) == 0 {
		return nil, nil
	}

	// Create a derived context that we can cancel internally to signal
	// all running tasks to stop if one fails or the parent context is cancelled.
	runCtx, cancelAll := context.WithCancel(ctx)
	defer cancelAll()

	// taskChan distributes indices of tasks to be processed.
	taskChan := make(chan int)
	// resultChan collects results from workers.
	resultChan := make(chan result)
	// wg tracks all goroutines (workers + the collector) to ensure no leaks.
	var wg sync.WaitGroup

	// We use a separate goroutine to feed tasks into the channel.
	// This allows us to stop feeding tasks immediately if an error occurs.
	go func() {
		defer close(taskChan)
		for i := range tasks {
			select {
			case <-runCtx.Done():
				return
			case taskChan <- i:
			}
		}
	}()

	// Start the worker pool.
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range taskChan {
				// Check if we should even start this task.
				// This handles the "tasks that have not yet started must never start" rule.
				select {
				case <-runCtx.Done():
					return
				default:
				}

				val, err := tasks[idx](runCtx)
				
				// Send result back. We don't use a select here because we 
				// must ensure the collector receives the result to avoid blocking.
				resultChan <- result{index: idx, val: val, err: err}
			}
		}()
	}

	// The collector goroutine manages the results and the error-fast-path.
	// It is responsible for calling cancelAll() if an error is encountered.
	finalResults := make([]any, len(tasks))
	var runErr error
	
	// We use a WaitGroup to ensure the collector finishes before we return.
	// This prevents goroutine leaks.
	collectorDone := make(chan struct{})
	go func() {
		defer close(collectorDone)
		for i := 0; i < len(tasks); i++ {
			select {
			case res := <-resultChan:
				if res.err != nil {
					runErr = res.err
					cancelAll() // Signal all other workers to stop/abort
					// We don't return immediately; we must wait for workers to finish.
				} else {
					finalResults[res.index] = res.val
				}
			case <-runCtx.Done():
				// If the parent context is cancelled, we stop waiting for results.
				// Note: if runErr was already set by a task error, that takes precedence.
				if runErr == nil {
					runErr = runCtx.Err()
				}
			}
			
			// If we hit an error, we stop processing the resultChan loop.
			if runErr != nil {
				return
			}
		}
	}()

	// Wait for all workers to finish (either naturally or via cancellation).
	wg.Wait()
	// Wait for the collector to finish processing or exit.
	<-collectorDone

	if runErr != nil {
		return nil, runErr
	}

	return finalResults, nil
}
