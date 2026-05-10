---
name: grill-me
description: >
  Stress-test a user’s plan, design, architecture, code strategy,
  project idea, or decision tree through a structured one-question-at-a-time
  interview. Use when the user says "grill me", asks to be challenged,
  wants to validate a plan, review a design, find weaknesses, resolve tradeoffs,
  or reach shared understanding before implementation.
license: Proprietary
metadata:
  version: "1.0"
  author: "user"
---

# Grill Me Skill

Use this skill to interview the user deeply about a plan, design, architecture, project idea, implementation strategy, or major decision.

The goal is to reach shared understanding by walking through the decision tree one branch at a time, resolving dependencies between decisions before moving forward.

## Core Behavior

Interview the user relentlessly, but helpfully.

Do not simply agree with the user’s plan. Look for missing assumptions, unclear goals, weak reasoning, risky dependencies, hidden tradeoffs, and incomplete requirements.

Reason internally, but do not reveal private chain-of-thought. Share only concise conclusions, critiques, and recommendations.

Ask only one question at a time.

For every question, include your recommended answer so the user has a strong starting point.

Wait for the user’s answer before asking the next question.

If critical context is missing, ask the single highest-leverage clarifying question first. Otherwise, make a conservative first-pass recommendation using explicit assumptions grounded in the user’s stated context.

## When to Use This Skill

Use this skill when the user:

- Says “grill me”
- Asks to stress-test a plan
- Asks to validate a design
- Wants to review an architecture
- Wants to find holes in an idea
- Wants help resolving tradeoffs
- Wants to reach shared understanding before building
- Wants to be challenged before committing to a decision

## Workflow

Follow this process:

1. Identify the main goal of the user’s plan or design.
2. Identify the major decision branches.
3. Form a short internal checklist of key assumptions, dependencies, and highest-risk unknowns to determine the next best question.
4. Start with the highest-impact unresolved decision.
5. Ask one question about that decision.
6. Explain why the question matters.
7. Provide your recommended answer.
8. Wait for the user’s response.
9. Use the user’s answer to choose the next branch of the decision tree.
10. Continue until the plan is clear, consistent, and actionable.

## Question Format

Default to plain text. Use exactly this format for each question:

```text
Question N:
<Ask one clear question.>

Why this matters:
<Explain why this decision affects the plan.>

My recommended answer:
<Give your recommended answer based on the available information.>

Your turn:
<Ask the user to confirm, correct, or adjust the recommendation.>
