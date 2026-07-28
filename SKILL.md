---
name: scifigure
description: Create, compare, revise, and finalize general-purpose scientific figures from completely free-form user input without external model APIs. Use for research methodology diagrams, neural-network architectures, multi-panel module figures, graph-reasoning figures, experimental workflows, training/inference diagrams, and publication-ready editable PNG, SVG, and VSDX outputs. Infer scientific structure and drawing requirements from the current conversation and supplied attachments, generate six same-content PNG style previews first, continue revisions in the selected style, and produce final PNG/SVG/VSDX only after explicit user approval.
---

# SciFigure

SciFigure accepts completely free-form input. Never require `method.md`, a fixed prompt template, named sections, JSON, or predefined fields.

Use the current user message, relevant conversation context, and supplied attachments as the source input. The user may provide any combination of natural-language descriptions, abstracts, introductions, methodology text, equations, pseudocode, source code, tables, captions, PDFs, DOCX files, Markdown, TXT, CSV, sketches, reference images, layout requirements, style preferences, terminology locks, exclusions, or revision feedback.

Use the bundled deterministic renderer. Do not call external VLM, image-generation, or drawing APIs.

## Input interpretation

Read `references/custom-input.md` before interpreting a new drawing request.

Internally infer and separate:

1. scientific content: what the figure must represent;
2. drawing intent: the communication goal of the figure;
3. structural constraints: required modules, relationships, inputs, outputs, branches, losses, and training/inference distinctions;
4. locked terminology: labels, formulas, symbols, and names that must remain exact;
5. exclusions: content that must not appear;
6. layout preferences: direction, panels, density, callouts, grouping, and aspect ratio;
7. visual preferences: palette, typography, line style, and reference-image role.

Do not ask the user to create or supply Figure IR. Create and maintain Figure IR internally.

When sources conflict, use this priority:

1. explicit instructions in the current request;
2. explicitly locked terminology and structure;
3. detailed methodology and equations;
4. verified source-code execution flow;
5. abstract and introduction;
6. sketches;
7. visual reference images;
8. automatic layout inference.

Reference images control visual style only. Never import their scientific modules, labels, equations, or connections into the user's figure.

## Required workflow

1. Read the user's complete free-form request, relevant context, and attachments.
2. Read `references/custom-input.md` and `references/figure-ir.md`.
3. Extract the scientific structure and drawing constraints without forcing the input into a fixed form.
4. Preserve every user-approved or explicitly locked term exactly.
5. Create one internal semantic `figure_ir.json`. Keep scientific content separate from style and coordinates.
6. Run:

```bash
python scripts/scifigure.py validate-ir --ir figure_ir.json
python scripts/scifigure.py preview --ir figure_ir.json --output run/previews
```

7. Inspect all six PNG previews and their validation reports. Fix semantic errors in `figure_ir.json`; fix reusable rendering defects in the renderer rather than patching PNG pixels.
8. Return the six PNG previews to the user. Do not return candidate SVG, VSDX, resolved-layout JSON, Figure IR, or validation files during this first stage.
9. After the user selects a style, keep that style fixed. Apply revisions to `figure_ir.json` or the selected layout logic and run:

```bash
python scripts/scifigure.py render \
  --ir figure_ir.json \
  --style s6-paperbanana-soft \
  --output run/selected \
  --name selected_preview_v2
```

10. Return only the updated PNG preview while revision continues.
11. Finalize only after explicit approval such as “定稿”, “确认输出”, or “生成最终文件”:

```bash
python scripts/scifigure.py finalize \
  --ir figure_ir.json \
  --style s6-paperbanana-soft \
  --output run/finalized
```

12. Return exactly these final deliverables:
   - `figure_final.png`
   - `figure_final.svg`
   - `figure_final.vsdx`

## Non-negotiable rules

- Accept free-form input; never require named sections, a fixed file name, or a fixed input schema from the user.
- Keep one semantic Figure IR across all six initial style previews.
- Keep node labels, node count, scientific relations, edge directions, equations, dimensions, and training/inference meaning consistent across styles.
- Never invent modules, losses, inputs, outputs, metrics, or causal links.
- Treat visual duplication used for detail callouts as an alternate view of the same source node, not a new scientific component.
- Never edit the raster preview directly.
- Generate PNG by rasterizing the same SVG geometry used by the renderer.
- Generate VSDX as editable shapes, text, groups, and vector connector paths; never embed the PNG as the whole Visio page.
- Do not expose the final SVG or VSDX before explicit approval.
- Do not add PDF, PPTX, TikZ, JPEG, WebP, Studio, MCP, provider, authentication, billing, or API configuration features unless the user separately requests a future extension.

## Style selection

Read `references/styles.md` when selecting or explaining styles. The fixed built-in styles are:

- `s1-compact-modular`
- `s2-multi-panel`
- `s3-dense-engineering`
- `s4-macro-partition`
- `s5-rigorous-graph`
- `s6-paperbanana-soft`

## Validation

Read `references/design-rules.md` before changing renderer behavior. Before each preview, inspect:

- semantic completeness and terminology consistency;
- node overlap and canvas bounds;
- text-overflow risk;
- arrows crossing or passing through unrelated nodes;
- visual hierarchy, spacing, contrast, and main-flow clarity.

Before final delivery, verify the VSDX package report and confirm that final PNG, SVG, and VSDX come from the same resolved figure.

## Bundled resources

- `references/custom-input.md`: free-form input interpretation and evidence priority.
- `references/workflow.md`: preview, selection, revision, and finalization protocol.
- `references/figure-ir.md`: semantic IR fields, node/edge types, and examples.
- `references/styles.md`: detailed six-style specification.
- `references/design-rules.md`: shared scientific-figure design system.
- `references/vsdx.md`: Visio export behavior and editability requirements.
- `references/usage.md`: installation and command reference.
- `examples/demo_ir.json`: complete renderer test input; not a required user format.
- `schemas/figure_ir.schema.json`: internal JSON Schema reference.
