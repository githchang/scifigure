# SciFigure

SciFigure is a Codex Skill for creating general-purpose scientific figures without external model or image-generation APIs.

It accepts **completely free-form input** from the current conversation and attachments. Users do not need to create `method.md`, fill named fields, write JSON, or prepare Figure IR.

## Workflow

1. The user provides any scientific content and drawing requirements in their own format.
2. Codex extracts one internal semantic Figure IR.
3. SciFigure renders six PNG previews from the same Figure IR using six fixed built-in templates.
4. The user selects one style and provides free-form revision feedback.
5. After explicit approval, SciFigure exports the approved figure as PNG, SVG, and editable VSDX.

## Six fixed built-in styles

1. **S1** — CATDM-style top overview and lower detail panels, with bright blue, green, orange, teal, and purple local accents.
2. **S2** — cross-modal overview plus labeled multi-panel decomposition using vivid coordinated pink, blue, yellow, green, purple, and teal modules.
3. **S3** — TSPulse-style dense engineering stages with high-contrast tensor annotations and vivid blue, purple, cyan, peach, and green hierarchy.
4. **S4** — GTM/Fourier left model flow plus right explanatory panels with bright cream, green, blue, cyan, orange, and teal regions.
5. **S5** — adaptive-gating structure with a prominent blue alignment layer, green branches, red training links, and orange output emphasis.
6. **S6** — verbal-reasoning narrative containers using brighter dusty blue, pink, lavender, teal, and blue-gray modules.

All six styles preserve the same scientific modules, labels, edge directions, equations, and training/inference meaning.

## Rendering quality

- PNG previews are rasterized at a minimum internal scale of 2.75x.
- Contact sheets use Lanczos downsampling rather than nearest-neighbour resizing.
- Fixed palettes use stronger fill saturation, clearer borders, darker text, and higher-contrast arrows.

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
