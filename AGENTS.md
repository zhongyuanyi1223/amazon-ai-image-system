# Amazon AI Image System

This repository is a shared Amazon AI image production system. These are project
rules, subordinate to platform instructions and explicit user instructions.

## Mandatory entry point
All Amazon image creation, editing, planning, optimization, review, and image-set
requests enter through `amazon-image-director`. Internal Skills are not operator
entry points. Repository maintenance requests are not image-production jobs.

## Workflow and hard gates
Intake → analysis → validation → resolve conflicts → draft plan → operator
confirmation → product lock → execution planning → prompts → generation → QC
→ revision if needed → final delivery. Read `config/workflow-policy.md`.
Use `scripts/workflow.py` to persist transitions. Run the generation validator
and `begin` before EVERY initial or repair generation batch. Never generate if
generation.confirmed is not true, P0 facts are missing/inferred/conflicting,
confirmation is stale, or the generation capability is unavailable.

## Product lock and claims
Lock identity, structure, material, color, quantity, dimensions, accessories,
functional claims, immutable features and references after confirmation.
Changing locked facts, the image plan, requirements, model or references invalidates
confirmation. Never invent facts, certifications, safety/performance claims,
dimensions, materials, package quantity, accessories or functions.

## Operator experience
Ask only necessary business questions after reading supplied evidence. Operators
must not need to write prompts or understand Skill, Agent, JSON or model parameters.
Show a Chinese confirmation summary including facts, plan, protected features,
claims, requested model and any inability to verify the actual native image model.

## Agents and models
The Director may delegate analysis, planning, prompt engineering and QC to the
four configured specialists; only the Director writes the canonical Job state
and calls image tools. Delegate sequential dependent steps and wait for results.
Default reasoning model: gpt-5.6; effort: high. Image policy is maintained only in
`config/model-policy.md`. Do not silently substitute models or modify user config.

## QC and delivery
Inspect actual images against references. Every latest image must have a matching
PASS report before FINAL. FAIL → REVISION; at most three repairs per image, then
ask for a revised plan. Retain all versions. No external image providers in V1.
Scripts enforce local workflow gates; they do not sandbox Codex's native tools.
Do not claim an unexecuted native invocation or visual QC passed.
