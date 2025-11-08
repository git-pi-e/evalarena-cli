## Contributing

### Repo Layout
- Go CLI lives in `go/` (module `evalarena-cli`)
- Legacy Python code is in `evalarena_py/`
- Docs live in `docs/`

### Build Go CLI
```bash
go build -o bin/evalarena ./src/cmd/evalarena
```

### Coding Guidelines
- Prefer clear, explicit names; avoid abbreviations
- Keep functions short and composable
- Handle errors explicitly; avoid swallowing network errors
- Avoid deep nesting; use early returns

### PR Tips
- Include a brief description and screenshots for UX changes
- Update `docs/` when adding commands or flags
- Keep changes scoped and reviewable


