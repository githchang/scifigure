# SciFigure

SciFigure is a Codex Skill for creating general-purpose scientific figures without external model or image-generation APIs.

It accepts **completely free-form input** from the current conversation and attachments. Users do not need to create `method.md`, fill named fields, write JSON, or prepare Figure IR.

## Workflow

1. The user provides any scientific content and drawing requirements in their own format.
2. Codex extracts one internal semantic Figure IR.
3. SciFigure renders six PNG previews from the same Figure IR using six fixed reference-based styles.
4. The user selects one style and provides free-form revision feedback.
5. After explicit approval, SciFigure exports the approved figure as PNG, SVG, and editable VSDX.

## Six fixed built-in styles

1. **S1 CATDM Reference Scientific Style** — top overview, lower detail panels, white canvas, gray dashed regions, local blue/green/orange/purple accents.
2. **S2 Cross-Modal Reconstruction Multi-Panel Style** — overview plus `(a)(b)(c)(d)` detail panels with coordinated pink, blue, yellow, green, and purple modules.
3. **S3 TSPulse Dense Engineering Style** — dense stage-based engineering layout, compact blocks, tensor annotations, blue/purple/teal/peach hierarchy.
4. **S4 GTM / Fourier Panel Style** — left model flow plus right explanatory panels, cream input blocks, green backbone, blue/cyan analysis areas.
5. **S5 Adaptive Gating Structured Style** — structured gating container, alignment layer, aligned branches, red/blue cross-links, orange decoder/output emphasis.
6. **S6 Verbal Reasoning Narrative Block Style** — two large narrative containers using gray-white, dusty blue, dusty pink, and muted lavender.

All six styles preserve the same scientific modules, labels, edge directions, equations, and training/inference meaning.

## Example request

```text
使用 $scifigure，把下面的内容画成科研方法图，先生成六种风格的 PNG 预览：

模型接收文本和图像两种输入，分别经过两个编码器。编码结果进入共享融合模块，
随后分成分类分支和生成分支。训练时使用分类损失、生成损失和一致性损失，
推理时只保留两个输出分支。主流程从左到右，训练专用损失放在下方，图中文字使用英文。
```

The request may instead reference uploaded papers, source code, figures, sketches, tables, or any other relevant files.

## Install as a Codex Skill

```text
$skill-installer install https://github.com/githchang/scifigure
```

Restart Codex after installation, then invoke:

```text
使用 $scifigure，……
```

## Final outputs

After explicit approval:

```text
figure_final.png
figure_final.svg
figure_final.vsdx
```

The three files are generated from the same resolved layout. The VSDX contains editable vector shapes and text rather than a page-sized embedded PNG.
