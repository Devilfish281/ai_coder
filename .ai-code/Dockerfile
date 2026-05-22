# AI Code RALPH Docker runtime template

# Expected image tag:
# ai-code-ralph-test-runtime:latest
#
# Manual build command:
# docker build -f .ai-code/Dockerfile -t ai-code-ralph-test-runtime:latest .
#
# This starter image is for the AI Code Docker bind-mount runtime.
# RALPH should run project commands with the repository mounted at /workspace.
# Do not put real secrets in this Dockerfile.

FROM python:3.12-slim

LABEL org.opencontainers.image.title="AI Code RALPH runtime"
LABEL org.opencontainers.image.description="Starter runtime image for AI Code scaffold workflows"
LABEL ai-code.image.tag="ai-code-ralph-test-runtime:latest"

ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

CMD ["python", "--version"]
