## Open scaffold questions

These questions are intentionally documented for future scaffold-generation issues. They are not answered by Issue 053.

1. Should the first scaffold generator overwrite existing `.ai-code/` files or skip them by default?
2. Should generated prompt templates include repository context placeholders immediately, or wait for the repository-context module to stabilize?
3. Should `.ai-code/.env.example` include Codex settings now, or wait until CodexProvider is fully stable?
4. Should Docker scaffold files be generated in the Docker phase or only in the full template-scaffolding phase?
5. Should the scaffold command create directories only, files only, or both?
6. Should scaffold generation be dry-run by default?
7. Should generated files include comments explaining every placeholder?

## Testing plan

This issue is documentation-only. Runtime behavior should not change.

Required verification:

```powershell
poetry run pytest
```
