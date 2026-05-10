# Add Docker image validation inside adapter layer

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Validate the configured Docker image once when creating the Docker sandbox handle, inside the Docker adapter layer.

## Acceptance criteria

- [ ] DockerSandboxProvider checks the configured image once when the handle is created.
- [ ] The default image is ai-code-ralph-test-runtime:latest.
- [ ] The image name is configurable through setup_config.py.
- [ ] AI Code does not auto-build the image.
- [ ] Tests cover image check success and failure.

## Blocked by

- Blocked by `issues/028-add-docker-sandbox-mode-selection.md`

## User stories addressed

- User story 5

## Assumptions

- None

## Open questions

- None

## Notes

- None
