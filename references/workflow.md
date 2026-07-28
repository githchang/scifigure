# SciFigure output workflow

## Input stage: free-form request

Read the user's complete current message, relevant conversation context, and attachments. Do not require `method.md`, named sections, a fixed template, JSON, or any predefined fields.

Internally separate scientific content, drawing intent, constraints, locked terminology, exclusions, and visual preferences. Create one semantic `figure_ir.json` without asking the user to prepare it.

## Stage 1: six PNG previews

Validate the internal Figure IR, then render all six built-in styles. The preview command produces six public PNG files plus an optional PNG contact sheet. It also creates internal SVG, resolved-layout JSON, and validation reports under each style directory. Share only PNG previews with the user.

The six previews must express the same scientific content. Layout families can use overview panels, detail callouts, stage numbering, or macro containers, but they must not change the underlying method.

## Stage 2: selected-style revision

Once the user chooses a preview, preserve the selected style ID. Interpret subsequent free-form feedback directly. Modify the semantic IR for content corrections, or modify layout/style data for a visual correction. Re-render one selected PNG preview. Do not regenerate all styles unless the user asks to compare again.

Version selected previews with names such as:

```text
selected_preview_v1.png
selected_preview_v2.png
selected_preview_v3.png
```

## Stage 3: finalization

Finalize only after explicit approval. Generate final PNG, SVG, and VSDX from the same `ResolvedFigure` object. The VSDX must contain individual editable shapes and text. Keep the internal validation and manifest files, but share only the three final figure files unless the user asks for diagnostics.
