# Agents

Guidance for coding agents working in this repository. `CLAUDE.md` links here.

## Branches

Name a branch `<type>/<short-description>`, in lowercase words joined by hyphens:

| Type | For |
|---|---|
| `feature/` | New behaviour: an engine, a bot, a replay, a tool. |
| `fix/` | A bug fix. |
| `docs/` | Documentation only. |
| `refactor/` | A change of structure that keeps behaviour. |
| `test/` | Tests only. |
| `chore/` | Upkeep: dependencies, CI, tooling. |

For example `feature/lynx-engine`, `fix/morlock-replay-crash`, `docs/candidates-status`. Start
each branch from the latest `main`.

## Before pushing

```sh
python3 lib/botelo/registry.py check
uv run --with pytest --with chess==1.11.2 pytest -q
```

Both must pass. `README.md` describes the layout, the registry (`bots.toml`) and how to add a bot,
an engine or a replay.
