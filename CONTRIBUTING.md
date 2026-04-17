# Contributing

## Development setup

```bash
git clone https://github.com/brianpelow/platform-conductor
cd platform-conductor
uv sync
uv run pytest
```

## Standards

- All PRs require passing CI
- Test coverage must not decrease
- Update CHANGELOG.md for user-facing changes