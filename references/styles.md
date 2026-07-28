# Six fixed reference-based scientific styles

Each style is a locked combination of layout, palette, visual hierarchy, grouping, edge treatment, and scientific glyph usage. All six styles render the same semantic Figure IR and must not alter scientific meaning.

## S1 CATDM Reference Scientific Style

ID: `s1-compact-modular`

Use a white canvas, gray dashed macro regions, a compact top-level overview, and lower module-detail panels. Keep most containers white or near-white. Apply blue, green, orange, teal, and purple only as local accents in borders, feature blocks, small glyphs, and selected edges. Do not use large colored background regions.

## S2 Cross-Modal Reconstruction Multi-Panel Style

ID: `s2-multi-panel`

Use an overview workflow plus labeled detail panels such as `(a)`, `(b)`, `(c)`, and `(d)`. Use coordinated low-saturation pink, blue, yellow, green, and purple modules with light panel backgrounds and restrained borders. Preserve clear mappings between the overview and detailed subpanels.

## S3 TSPulse Dense Engineering Style

ID: `s3-dense-engineering`

Use a stage-based, very high-density engineering layout with compact modules, explicit dimensions, tensor/feature annotations, small gaps, and strong implementation detail. Use white or near-white macro regions with blue, purple, teal, peach, green, and muted yellow local structures. Keep primary flow arrows dark and engineering-oriented.

## S4 GTM / Fourier Panel Style

ID: `s4-macro-partition`

Use a left-side model flow and right-side explanatory panels. Map inputs to cream/yellow blocks, backbone or representation stages to soft green, attention/analysis panels to blue or cyan, and outputs to teal. Use panel borders and whitespace to separate embedding, attention, masking, and analysis details.

## S5 Adaptive Gating Structured Style

ID: `s5-rigorous-graph`

Use a structured gating container with a prominent horizontal alignment layer, aligned lower branches, and a right-side decoder/output region. Use pale blue, green, pink, and orange modules on a white or warm near-white canvas. Keep the primary logical arrows dark; use controlled red and blue accents for cross-attention, gating, or residual links.

## S6 Verbal Reasoning Narrative Block Style

ID: `s6-paperbanana-soft`

Use two large narrative containers, typically an upper reasoning region and a lower latent-thinking region. Use gray-white backgrounds with dusty blue, dusty pink, muted lavender, and soft blue-gray modules. Keep arrows dark and direct. Favor conceptual readability, generous whitespace, and low-saturation block hierarchy over engineering density.

## Shared non-negotiable requirement

All six styles must preserve one semantic Figure IR. Style changes may alter layout, grouping, density, shape treatment, typography hierarchy, palette mapping, and detail-callout placement. They must not alter node labels, node count, equations, scientific relations, edge directions, inputs, outputs, losses, or training/inference meaning.
