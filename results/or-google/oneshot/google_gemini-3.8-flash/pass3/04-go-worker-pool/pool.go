if workers < 1 {
    return nil, errors.New("pool: workers must be at least 1")
}
if len(tasks) == 0 {
    return []any{}, nil
}
if ctx.Err() != nil {
    return nil, ctx.Err()
}
