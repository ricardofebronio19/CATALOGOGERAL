---
name: create-skill
description: "Create a reusable SKILL.md file for VS Code agent customization workflows."
user-invocable: true
---

# Create Skill

## Purpose

Use this skill when you want to capture a multi-step workflow or methodology from a conversation and turn it into a reusable `SKILL.md` definition for this repository.

## When to Use

- You have a repeatable project workflow, debugging approach, or review checklist that should be codified.
- The task requires packaging a series of steps, decisions, and completion checks into a single, reusable project skill.
- You want a workspace-scoped skill that others on the team can invoke.

## What This Skill Produces

This skill helps you create a `SKILL.md` file with:

- A clear `name` and `description` in YAML frontmatter.
- A concise purpose statement explaining the workflow.
- A step-by-step process for executing the workflow.
- Decision points and quality criteria for choosing the right customization primitive.
- Validation guidance to ensure the skill is in the right location and uses proper syntax.

## Workflow

1. Review the conversation and extract the workflow steps.
2. Identify decision points and branching logic.
3. Determine whether the skill should be workspace-specific or personal.
4. Draft the `SKILL.md` content following the project’s conventions.
5. Save the file in `.github/skills/<skill-name>/SKILL.md`.
6. Confirm the file is syntactically correct and the description is actionable.

## Quality Checklist

- The skill describes a clear, reusable workflow.
- It includes a summary of the expected output.
- It identifies when the skill should be used and when it should not.
- The YAML frontmatter is valid and includes `name` and `description`.
- The file is stored in `.github/skills/<skill-name>/SKILL.md` for workspace sharing.

## Example Prompt

`/create-skill Create a SKILL.md file for generating repository-specific release notes from changelog entries.`

## Related Customizations

- `copilot-instructions.md` for repository-wide agent behavior.
- `.github/skills/<name>/SKILL.md` for workspace-specific reusable workflows.
