# Free-form input protocol

SciFigure must accept the user's input exactly as provided. It must not require a form, fixed section names, a particular file name, or a predefined prompt structure.

## Accepted input

The user may provide any combination of:

- one sentence describing the desired figure;
- a long natural-language model description;
- abstract, introduction, related-work, methodology, or experiment text;
- equations, symbol definitions, pseudocode, or algorithm steps;
- source code, repository files, or code-analysis conclusions;
- PDF, DOCX, Markdown, TXT, CSV, JSON, spreadsheets, images, or sketches;
- an existing figure that should be revised;
- reference figures used only for layout, palette, density, or visual language;
- explicit drawing requirements or informal feedback;
- terminology that must remain exact;
- content that must be omitted.

A file named `method.md` is optional and never required.

## Internal interpretation

Without asking the user to reformat the request, infer:

### Scientific structure

- research task;
- inputs and outputs;
- sequential stages;
- parallel branches;
- shared modules;
- feature, tensor, graph, or representation transformations;
- loss functions and training-only signals;
- inference and decoding flow;
- feedback, residual, skip, or iterative relations;
- formulas and symbols that need visual representation.

### Drawing intent

- overview figure;
- detailed module figure;
- multi-panel explanation;
- training/inference comparison;
- data-construction workflow;
- system architecture;
- graph-reasoning diagram;
- compact engineering architecture;
- conceptual macro-partition figure.

### Constraints

- locked labels and formulas;
- required modules and relations;
- prohibited modules or details;
- language of figure text;
- layout direction and aspect ratio;
- information density;
- whether formulas are shown or omitted;
- whether reference images affect layout, palette, or both.

## Evidence priority

When information conflicts, use:

1. current explicit user instructions;
2. locked terminology and structure;
3. detailed methods and equations;
4. verified source-code execution flow;
5. abstract and introduction;
6. sketches;
7. visual reference images;
8. automatic inference.

Do not let a visual reference override the user's scientific content.

## Clarification policy

Proceed directly when a faithful figure can be created from the available information.

Ask one focused clarification only when a missing fact would change scientific correctness, such as an unknown arrow direction, an ambiguous training/inference distinction, or two contradictory definitions of the same module. Do not ask the user to reorganize all content into a template.

## Internal artifacts

Create these internally as needed:

- `source_summary.json`;
- `figure_ir.json`;
- semantic validation report;
- resolved style layouts;
- working SVG files;
- PNG previews.

Do not require the user to prepare these artifacts, and do not expose them during the preview stage unless the user explicitly requests diagnostics.

## Examples of valid user requests

```text
使用 $scifigure，把下面的模型说明画成科研方法图，先生成六种风格预览：……
```

```text
使用 $scifigure，分析我上传的论文和草图。正文决定模型结构，草图只参考排版和配色。
```

```text
使用 $scifigure，分析当前仓库中的模型和损失代码，绘制训练与推理流程。训练专用连接使用虚线。
```

```text
使用 $scifigure。输入是多模态序列，经过三个编码器和一个共享融合模块，最终输出两个预测头。两个损失放在主流程下方。图中文字用英文。
```
