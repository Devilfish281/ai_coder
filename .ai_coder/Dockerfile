FROM python:3.12-bookworm

# Install system dependencies.
RUN apt-get update && apt-get install -y \
  git \
  curl \
  jq \
  ca-certificates \
  gnupg \
  pipx \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 and npm.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
  && apt-get update \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI.
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && apt-get update \
  && apt-get install -y gh \
  && rm -rf /var/lib/apt/lists/*

# Create the non-root agent user.
RUN useradd -m -u 1000 -s /bin/bash agent

# Install Codex CLI globally.
RUN npm install -g @openai/codex

# Switch to the non-root agent user.
USER agent

# Add pipx-installed tools, such as Poetry, to PATH.
ENV PIPX_HOME="/home/agent/.local/pipx"
ENV PIPX_BIN_DIR="/home/agent/.local/bin"
ENV PATH="/home/agent/.local/bin:${PATH}"

# Install Poetry.
RUN pipx install poetry

# Prove Python and Poetry are available during image build.
RUN python --version
RUN poetry --version

WORKDIR /home/agent

# Sandcastle bind-mounts the git worktree at /home/agent/workspace.
ENTRYPOINT ["sleep", "infinity"]
