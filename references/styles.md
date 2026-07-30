# Six fixed reference-derived scientific styles

Each style is a locked combination of layout, palette, visual hierarchy, grouping, edge treatment, and scientific glyph usage. All six styles render the same semantic Figure IR and must not alter scientific meaning.

## S1 Botanical Sage Modular Style

ID: `s1-compact-modular`

Use a white canvas, soft dashed macro regions, a compact top-level overview, and lower module-detail panels. The core palette is `#EBF5E7`, `#DAEBD0`, `#BDDEAA`, `#9BCD7C`, `#BDCEEB`, and `#FFF1CC`, with `#4672C4` as the primary flow accent. Map inputs to muted blue, representations and outputs to layered sage greens, fusion to warm cream, and training-only elements to restrained peach. Keep large containers close to white.

## S2 Balanced Pastel Multi-Panel Style

ID: `s2-multi-panel`

Use an overview workflow plus labeled detail panels such as `(a)`, `(b)`, `(c)`, and `(d)`. The core palette is `#E49CA3`, `#ACD5EB`, `#B3D5AA`, `#BEAECF`, `#FCE0C4`, and `#F8B168`. Assign blue to inputs, sage to representations, pink to processing, lavender to fusion, orange to training, and peach to outputs. Preserve mappings between the overview and detailed subpanels.

## S3 High-Contrast Engineering Style

ID: `s3-dense-engineering`

Use a stage-based, very high-density engineering layout with compact modules, explicit dimensions, tensor annotations, small gaps, and strong implementation detail. The anchor palette is `#4472C7`, `#F0B906`, `#EC7A2D`, `#EAF3E4`, `#A5C88E`, and `#FFF0C4`, supported by pale blue and lavender. Use cobalt blue for data and residual structure, yellow for fusion, orange for training, green for outputs, and lavender for graph modules. Keep primary arrows dark and sufficiently thick.

## S4 Multiview Planning Panel Style

ID: `s4-macro-partition`

Use a left-side model flow and right-side explanatory panels. The core palette is `#E7DFEC`, `#DFECC0`, `#F8DAB9`, `#54B5E3`, `#FFF1CC`, and `#D9E7FB`. Map inputs to cream, backbone stages to soft green, process panels to pale blue, fusion and graph reasoning to lavender, training to peach, and outputs to cyan-accented blue. Use clear panel borders and generous whitespace.

## S5 Alignment-Gating Accent Style

ID: `s5-rigorous-graph`

Use a structured alignment and gating container with a prominent horizontal blue module, aligned lower green branches, red training modules, and a yellow-orange output region. The core palette is `#4472C7`, `#E2F0D9`, `#A5C88E`, `#FDE1E1`, `#C00000`, and `#FFC411`, with `#EC7A2D` and `#F2DCE9` as supporting accents. Keep primary logical arrows dark; reserve strong blue for residual or alignment links and strong red for training-only links.

## S6 Clinical Pastel Narrative Style

ID: `s6-paperbanana-soft`

Use two large narrative containers, typically an upper reasoning region and a lower representation or refinement region. The core palette is `#DDE5F6`, `#C4ECDA`, `#D6AEEC`, `#EEBBD3`, `#F4B183`, and `#809ED7`, with teal `#398D94` as a graph accent. Map inputs and processes to clinical blue, representations to mint, fusion to lavender, training to pink, outputs to peach, and graph modules to teal-mint. Keep arrows dark and direct while retaining intentional whitespace.

## Shared rendering requirement

- Fixed colors must remain visibly distinct in both individual PNG previews and the contact sheet.
- Use light publication fills, medium-dark borders, dark text, and stronger accents only for key functional roles.
- Borders, arrows, formulas, and labels must retain contrast after downsampling.
- PNG previews use high-resolution SVG rasterization, and the contact sheet uses Lanczos resampling.
- All styles preserve one semantic Figure IR and must not alter node labels, node count, equations, scientific relations, edge directions, inputs, outputs, losses, or training/inference meaning.
