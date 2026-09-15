# 中秋图片着色提示词

2026-09-15，使用内置 image_gen 编辑原图，banner 输出替换项目中的同名素材；网页瓷碗着色版已按用户反馈撤回，恢复原图。

## README banner

路径：`docs/assets/readme-hero.png`

```text
Use case: style-transfer. Edit target: supplied README banner. Colorize this exact Chinese Mid-Autumn bobing banner, preserving panoramic 3:1 composition, all six dice, porcelain bowl, mountains, moon, and exact Chinese text 中秋博饼 and 六颗骰子，一碗好运. Rich festive yet refined full color, not monochrome or sepia: vermilion red main title, deep teal subtitle, blue-green Chinese landscape and pine, luminous soft golden moon and warm ivory paper sky, cobalt blue porcelain floral patterns with subtle jade accents, ivory dice with red one/four pips and dark other pips. Keep existing typography and scene geometry as closely as possible. No additional text or objects. Save edited banner image.
```

## 网页瓷碗图（已撤回，仅保留尝试记录）

路径：`site/src/assets/porcelain-bowl.png`

```text
Use case: style-transfer. Edit target: supplied porcelain bowl website illustration. Colorize the exact image while preserving shape, perspective, framing and exactly six dice and their visible pip counts. Make the porcelain bowl cobalt blue and jade teal floral and wave patterns on warm ivory glazed ceramic, subtle gold rim. Ivory dice have vermilion red pips on faces with one or four pips, dark navy pips on other faces. Elegant festive Chinese Mid-Autumn full color product illustration. Background solid warm ivory #fffaf2 with soft natural shadow. No text, no additional objects. Keep the whole bowl in frame.
```

生成图保留六颗骰子，但个别装饰骰面的点数与原图有变化；图片不作为判奖示例，网页数字骰面与规则文字仍由回归脚本核对源稿。banner 同样有此漂移（如右上那颗原为两点、成图读作一点）：构图与文字未变，但骰面本身不作判奖依据。
