# bug-patterns

A living library of bug patterns distilled from real fixes — mostly Android/Kotlin/Xposed-module work, plus a few build, CI, and process lessons.

**Rule: 1 bug = 1 file.** Every pattern file follows the same shape:

> symptom → root cause → fix → runnable check (how to verify the fix, not just claim it)

The discipline that keeps this library alive is documented in [`AGENTS.md`](AGENTS.md) ("Bug patterns" section) and [`bug-patterns/RULES.md`](bug-patterns/RULES.md) — including the rule that every new session reads the patterns for its domain *before* writing code.

## Layout

| Path | What |
|---|---|
| `AGENTS.md` | Operating manual: working conventions, subagent orchestration, review discipline, and the lessons that produced this library |
| `bug-patterns/RULES.md` | How patterns are written, indexed, and maintained |
| `bug-patterns/INDEX.md` | Index of patterns |
| `bug-patterns/android/` | Android platform patterns (Xposed hooks, Compose, system APIs) |
| `bug-patterns/kotlin/` | Kotlin language patterns |
| `bug-patterns/build/` | Build / Gradle / CI patterns |
| `bug-patterns/process/` | Process patterns (docs drift, agent campaigns, false completion claims) |
| `bug-patterns/*.md` | Cross-domain patterns (spoofx-\*, preflight-edit, bulk operations…) |

Patterns reference real commits, CI runs, and device-verified evidence. Claims without evidence are called out, not published.

Some files are written in Vietnamese — that's the working language of the projects these lessons came from.
