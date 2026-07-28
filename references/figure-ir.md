# Semantic Figure IR

Use the IR to describe scientific meaning, not coordinates or colors. Keep IDs stable across revisions.

## Top-level fields

- `title`: required figure title.
- `subtitle`: optional short explanatory line.
- `figure_type`: normally `methodology_diagram`.
- `reading_direction`: `left_to_right` or `top_to_bottom`.
- `canvas`: width, height, background, and margin.
- `groups`: semantic stages or modules.
- `nodes`: scientific components.
- `edges`: directed relationships.
- `annotations`: explanatory notes that are part of the figure.
- `metadata`: locked terms and project-specific information.

## Node fields

Required:

```json
{"id": "encoder", "label": "Document Encoder"}
```

Useful optional fields:

```json
{
  "type": "encoder",
  "group": "representation",
  "role": "representation",
  "details": ["context encoding", "mention pooling"],
  "dimension": "H ∈ R^{L×d}",
  "note": "shared weights",
  "locked": true,
  "metadata": {"symbol": "H"}
}
```

Supported visual node types include:

```text
process, module, encoder, decoder, classifier, input, data, document,
tensor, vector, matrix, attention, mask, graph, probability, loss,
operator, add, multiply, gate, output, prediction, static
```

Use `role` for semantic color mapping:

```text
input, data, representation, process, fusion, graph, training, loss,
output, static
```

## Edge fields

```json
{
  "source": "encoder",
  "target": "classifier",
  "type": "data_flow",
  "label": "H",
  "locked": false
}
```

Supported types:

- `data_flow`: primary feature or data transfer.
- `control_flow`: primary algorithmic sequence.
- `residual`: residual correction or merge path.
- `skip`: skip connection.
- `feedback`: iterative feedback loop.
- `training_only`: supervision used only in training.
- `reference`: explanatory mapping to a detail panel.
- `gradient`: optimization signal.

## Content discipline

Use concise labels. Move secondary details into `details`. Use `dimension` only when dimensional notation is important. Represent addition, multiplication, concatenation, gating, or Top-K selection as explicit operator nodes when they are scientifically meaningful.

Do not create an edge merely because two nodes are visually close. Every edge must be supported by the method description.
