package main

import (
    "context"
    "errors"
    "sync"
)

type Task func(ctx context.Context) (any, error)

var errInvalidWorkers = errors.New("pool: workers must be at least 1")

func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
    if workers < 1 {
        return nil, errInvalidWorkers
    }
    n := len(tasks)
    if n == 0 {
        return []any{}, nil
    }

    taskCtx, cancel := context.WithCancel(ctx)
    defer cancel()

    results := make([]any, n)
    idxCh := make(chan int)

    var mu sync.Mutex
    var firstErr error
    var stopped bool

    recordErr := func(e error) {
        mu.Lock()
        if !stopped {
            stopped = true
            firstErr = e
        }
        mu.Unlock()
        cancel()
    }

    stoppedNow := func() bool {
        mu.Lock()
        defer mu.Unlock()
        return stopped
    }

    numWorkers := workers
    if numWorkers > n {
        numWorkers = n
    }

    var wg sync.WaitGroup
    wg.Add(numWorkers)
    for w := 0; w < numWorkers; w++ {
        go func() {
            defer wg.Done()
            for i := range idxCh {
                v, err := tasks[i](taskCtx)
                if err != nil {
                    recordErr(err)
                    return
                }
                results[i] = v
            }
        }()
    }

dispatch:
    for i := 0; i < n; i++ {
        if stoppedNow() {
            break dispatch
        }
        select {
        case idxCh <- i:
        case <-taskCtx.Done():
            break dispatch
        }
    }
    close(idxCh)
    wg.Wait()

    mu.Lock()
    e := firstErr
    mu.Unlock()

    if e != nil {
        return nil, e
    }
    if err := ctx.Err(); err != nil {
        return nil, err
    }
    return results, nil
}
