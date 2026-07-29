# Six fixed reference-based scientific styles

Each style is a locked combination of layout, palette, visual hierarchy, grouping, edge treatment, and scientific glyph usage. All six styles render the same semantic Figure IR and must not alter scientific meaning.

## S1 CATDM Reference Scientific Style

ID: `s1-compact-modular`

Use a white canvas, gray dashed macro regions, a compact top-level overview, and lower module-detail panels. Keep macro containers white, but use lightly tinted modules with bright blue, green, orange, teal, and purple borders and glyphs. Maintain strong contrast after contact-sheet downsampling; do not allow the preview to become near-white or gray.

## S2 Cross-Modal Reconstruction Multi-Panel Style

ID: `s2-multi-panel`

Use an overview workflow plus labeled detail panels such as `(a)`, `(b)`, `(c)`, and `(d)`. Use coordinated vivid pink, blue, yellow, green, purple, and teal modules with readable panel backgrounds and clear border contrast. Preserve mappings between the overview and detailed subpanels.

## S3 TSPulse Dense Engineering Style

ID: `s3-dense-engineering`

Use a stage-based, very high-density engineering layout with compact modules, explicit dimensions, tensor/feature annotations, small gaps, and strong implementation detail. Use vivid blue, purple, cyan, peach, green, and yellow structures on white macro regions. Keep primary flow arrows dark and sufficiently thick.

## S4 GTM / Fourier Panel Style

ID: `s4-macro-partition`

Use a left-side model flow and right-side explanatory panels. Map inputs to bright cream/yellow blocks, backbone or representation stages to fresh green, attention/analysis panels to blue or cyan, optimization to orange, and outputs to teal. Use clear colored panel borders and generous whitespace.

## S5 Adaptive Gating Structured Style

ID: `s5-rigorous-graph`

Use a structured gating container with a prominent horizontal blue alignment layer, aligned lower green and cyan branches, red or pink training modules, and a right-side orange decoder/output region. Keep primary logical arrows dark; use vivid red and blue accents for cross-attention, gating, or residual links.

## S6 Verbal Reasoning Narrative Block Style

ID: `s6-paperbanana-soft`

Use two large narrative containers, typically an upper reasoning region and a lower latent-thinking region. Use bright dusty blue, dusty pink, lavender, teal, and blue-gray modules instead of nearly gray cards. Keep arrows dark and direct while retaining conceptual readability and intentional whitespace.

## Shared rendering requirement

- Fixed colors must remain visibly distinct in both individual PNG previews and the contact sheet.
- Borders, arrows, formulas, and labels must retain contrast after downsampling.
- PNG previews use high-resolution SVG rasterization, and the contact sheet uses Lanczos resampling.
- All styles preserve one semantic Figure IR and must not alter node labels, node count, equations, scientific relations, edge directions, inputs, outputs, losses, or training/inference meaning.
