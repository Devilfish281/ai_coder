import { run, codex } from "@ai-hero/sandcastle";
import { docker } from "@ai-hero/sandcastle/sandboxes/docker";

// Simple loop: an agent that picks open GitHub issues one by one and closes them.
// Run this with: npx tsx .sandcastle/main.mts
// Or add to package.json scripts: "sandcastle": "npx tsx .sandcastle/main.mts"

await run({
  // A name for this run, shown as a prefix in log output.
  name: "worker",

  // Docker sandbox.
  // Put BOTH keys here so setup hooks and shell commands inside Docker can use them.
  // Do not also put these keys in codex(..., { env }) or Sandcastle will throw
  // an overlapping env keys error.
  sandbox: docker({
    env: {
      OPENAI_KEY: process.env.OPENAI_KEY ?? process.env.OPENAI_API_KEY ?? "",
      GH_TOKEN: process.env.GH_TOKEN ?? "",
    },
  }),

  // The agent provider.
  // Direct Codex may work on Windows because it can use your saved Codex login.
  // Sandcastle runs Codex inside Docker, so we pass OPENAI_API_KEY into the agent.
  // Codex agent.
  // Do not pass OPENAI_API_KEY here because it is already in the Docker sandbox env.
  agent: codex("gpt-5.4-mini"),

  // Path to the prompt file. Shell expressions inside are evaluated inside the
  // sandbox at the start of each iteration, so the agent always sees fresh data.
  promptFile: "./.sandcastle/prompt.md",

  // Maximum number of iterations (agent invocations) to run in a session.
  // Each iteration works on a single issue. Increase this to process more issues
  // per run, or set it to 1 for a single-shot mode.
  maxIterations: 3,

  // Branch strategy — merge-to-head creates a temporary branch for the agent
  // to work on, then merges the result back to HEAD when the run completes.
  // This is required when using copyToWorktree, since head mode bind-mounts
  // the host directory directly (no worktree to copy into).
  branchStrategy: { type: "merge-to-head" },

  // Copy node_modules from the host into the worktree before the sandbox
  // starts. This avoids a full npm install from scratch on every iteration.
  // The onSandboxReady hook still runs npm install as a safety net to handle
  // platform-specific binaries and any packages added since the last copy.
  copyToWorktree: [],

  // Lifecycle hooks — commands grouped by where they run (host or sandbox).
  hooks: {
    sandbox: {
      onSandboxReady: [
        { command: "npm install" },
        { command: "/home/agent/.local/bin/poetry install --no-interaction" },
        {
          command:
            'export OPENAI_API_KEY="$OPENAI_KEY" && printf "%s" "$OPENAI_API_KEY" | codex login --with-api-key',
        },
      ],
    },
  },
});
