# Skills (public Cursor Agent Skills)

Canonical packages for Markdown scientific papers → Word.

| Directory | Skill name | Purpose |
|-----------|------------|---------|
| [`manuscript_md/`](manuscript_md/SKILL.md) | `manuscript_md` | Writing conventions + docx / submission build |
| [`manuscript-reference/`](manuscript-reference/SKILL.md) | `manuscript-reference` | Bibliography + literature notes + checkme |
| [`word-docx-compare/`](word-docx-compare/SKILL.md) | `word-docx-compare` | macOS Word Compare + version tags |

Install: [`../docs/INSTALL.md`](../docs/INSTALL.md)

Build entrypoint remains the repo-root [`Taskfile.yml`](../Taskfile.yml)
(`lab-paper` CLI). Skills hold the scripts/filters/docs the agent should follow.

```text
skills/<name>/
  SKILL.md      # agent entry (required)
  scripts/      # executable tooling
  …             # filters, csl, templates as needed
```
