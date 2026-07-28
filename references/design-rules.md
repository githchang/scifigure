# Shared scientific figure design rules

## Color

Use color to encode function, not decoration. Prefer low-saturation fills and medium-saturation borders. Reserve stronger colors for outputs, losses, warnings, or key innovations.

Default semantic meanings:

- blue: input, data, foundational representation;
- green: encoding, feature extraction, representation learning;
- purple: fusion, reasoning, core method;
- orange: scoring, optimization, training processes;
- red or rose: losses, errors, warnings;
- teal: output, prediction, result;
- grey: frozen, static, auxiliary, or reference content.

## Shapes

- Use rounded rectangles for trainable or procedural modules.
- Use stacks for tensors and embeddings.
- Use bars or dot sequences for vectors and probabilities.
- Use grids for matrices, masks, and attention maps.
- Use node-link glyphs for graphs.
- Use circles for addition, multiplication, gating, and merge operators.
- Use dashed containers for logical, optional, or training-only regions.

## Arrows

- Use solid dark arrows for primary data or process flow.
- Use thinner lines for skip and residual paths.
- Use dashed warm lines for training-only supervision.
- Use dashed grey lines for references and detail callouts.
- Keep arrowheads visible and unambiguous.
- Avoid routing through unrelated nodes or text.

## Layout

- Establish one obvious reading direction.
- Align nodes to a grid or shared baselines.
- Keep related modules closer than unrelated modules.
- Use whitespace between semantic phases.
- Keep repeated module types visually consistent.
- Prefer a clear main flow over decorative symmetry.
- Limit text inside modules; move detail into concise secondary lines.

## Validation priorities

1. Scientific correctness.
2. Logical flow and complete connections.
3. Legible text at publication scale.
4. No node overlap or canvas overflow.
5. Minimal edge crossings.
6. Consistent color, shape, and typography encoding.
