---
name: game-ui-reference-to-engine
description: Use when extracting, redrawing, cleaning, importing, and assembling production game UI from reference screenshots or UI concept images. Especially useful for Cocos Creator / Unity workflows where reference UI must become reusable image assets plus independent dynamic labels, icons, bars, states, and hit areas.
---

# UI 制作 Skill：参考图素提取与引擎拼装

这个 skill 用于把 UI 效果图或参考截图，转化为游戏引擎中可维护、可替换、可动态变化的真实 UI。

核心目标不是把整张参考图贴进游戏，而是：

1. 从参考图中拆出可复用图素。
2. 用 image2 / gpt-image-2 清理或重绘为正式资产。
3. 导入 Cocos / Unity 等引擎。
4. 用 Sprite、Label、Bar、Icon、State Overlay、Hit Area 重新拼装。
5. 通过截图和分块对比验证接近参考图。

## 核心原则

参考图只能作为视觉来源，不能作为运行时整屏 UI。

运行时 UI 必须由以下部分组成：

- 可复用固定图素：背景、面板、按钮底、边框、角花、分割线、槽位、进度条底。
- 动态文本：资源数值、气血、修为、任务描述、按钮文字、日志、状态名。
- 可替换图片：角色头像、怪物图、物品 icon、奖励 icon、地图缩略图、技能 icon。
- 状态覆盖：选中、高亮、禁用、锁定、完成、推荐、受击、风险、奖励、按下态。
- 独立交互层：按钮 hit area、拖拽区、hover/pressed 反馈。

任何会变化、会替换、会本地化、会被数值驱动的内容，都不应该烘焙在图素里。

## 工作流

### 1. 读取参考图

先确认：

- 参考图尺寸。
- 游戏设计分辨率。
- 当前引擎画布实际缩放。
- 参考图中哪些部分是固定装饰，哪些是动态内容。

如果参考图很大，先按 2x2、3x3 或 4x4 切块观察，不要只看整图。

### 2. 建立拆分清单

对每个界面列出资产表：

| 类型 | 示例 | 处理方式 |
| --- | --- | --- |
| 固定图素 | 宣纸面板、玉牌按钮、金边框 | 提取/重绘为透明 PNG |
| 动态文本 | 灵石 2、气血 48/48、按钮文字 | 引擎 Label |
| 可替换 icon | 灵草、灵石、护符、丹药 | 独立 Sprite |
| 数值条 | 气血条、修为条 | track + fill 分离 |
| 状态 | 推荐、锁定、已完成、危险 | 独立 overlay |
| 交互 | 按钮点击区域 | 独立 Hit Area |

拆分前先问：这个元素将来是否可能替换、变化、复用、动画化？

只要答案是“是”，就必须独立。

### 3. 初始裁剪

从参考图裁剪目标元素时：

- 裁剪只作为 image2 的输入或临时对位参考。
- 不要把粗糙截图裁剪直接当最终资产。
- 图素有效部分周围只保留均匀 3-5px 透明边缘。
- 有发光或阴影时可以保留必要溢出，但要记录原因。

### 4. 使用 image2 / gpt-image-2 清理或重绘

适合 image2 的任务：

- 去掉文字、数字、头像、奖励数量。
- 补全被 UI 遮挡的背景。
- 重绘边缘不干净的按钮、面板、角花。
- 生成 textless 面板、按钮底、奖励槽、资源格。
- 去除黑边、白边、背景残留、文字残影。

不要接受以下结果：

- 画布比例变化。
- 图标位置漂移。
- 线条变粗或变细。
- 材质变成另一种风格。
- 残留旧文字阴影。
- 出现模糊块、涂抹感、AI 新增花纹。
- 边框不直、角花变形。

### 5. image2 Prompt 模板

```text
Use case: game-ui-asset
Asset type: reusable UI sprite
Input image role: reference crop from a Chinese xianxia game UI

Task:
Redraw / clean this UI element into a production-ready reusable game asset.

Output:
Transparent PNG.
Preserve the original canvas ratio unless explicitly asked to trim.
No source screenshot background.
No baked variable text, numbers, portraits, rewards, or state labels.

Remove:
All dynamic text, numbers, resource values, HP values, cultivation values,
button captions, portraits, item icons, enemy art, reward quantities,
and gameplay-specific state labels.

Preserve:
The same Chinese xianxia visual language,
parchment / jade / gold-line materials,
border thickness,
corner ornaments,
lighting direction,
pixel density,
shadow style,
and original geometry.

Edge quality:
Clean alpha,
no black matte,
no white fringe,
no jagged crop edge,
no old text ghosting,
no blurred or warped borders.

Canvas bounds:
Keep the visible asset centered.
Leave only an even 3-5 px transparent margin unless glow or shadow needs more.

Avoid:
Changing layout,
inventing new decoration,
overpainting noise,
smudged inpainting,
new icons,
new text,
or style drift.
```

### 6. 本地图像工具的注意事项

如果使用 Codex 内置 `image_gen`：

- 本地图像需要先用 `view_image` 让模型看到。
- 当前内置调用通常只有 `prompt` 参数。
- 生成图默认保存在 `D:\CodeX\.codex\generated_images\...`。
- 项目要使用时，再复制到工程资源目录。
- 不要直接覆盖原始参考图，除非用户明确要求。

如果生成结果不符合参考，不要接入工程。保留为实验图即可。

### 7. 引擎导入规则

以 Cocos Creator 为例：

- 固定图素用 Sprite 节点。
- 文字、数字、说明、按钮文案用 Label 节点。
- 头像、怪物、奖励、物品 icon 用独立 Sprite。
- 血条、修为条拆成 track 和 fill。
- 选中、禁用、推荐、风险、受击闪光用独立 Overlay。
- 点击区域用独立 hit node，不依赖图片透明区域。
- 按钮按下效果作用于按钮本体，不要额外加黑色遮罩。
- 动态节点命名要稳定，例如 `StatusStoneValue`、`PrepHpFill`、`ResultRewardGrassIcon`。

### 8. Cocos 拼装建议

推荐结构：

```text
ScreenRoot
  Background
  FixedArtLayer
    PanelSprites
    ButtonSprites
    SlotSprites
  DynamicArtLayer
    PortraitSprites
    ItemIcons
    RewardIcons
    BarFills
    StateOverlays
  TextLayer
    Labels
    Values
    Logs
  HitLayer
    ButtonHitAreas
```

注意：

- 固定图素层不要包含会变化的文字。
- `HitLayer` 可以透明，但必须尺寸稳定。
- 所有 UI 元素要有明确宽高，避免文本变化导致布局跳动。
- Web 预览要检查是否拉伸，设计分辨率与 canvas 适配策略必须一致。

### 9. 验证流程

每次接入图素后都要验证：

1. 刷新资源。
2. 重建或刷新场景节点。
3. 保存场景。
4. 打开预览。
5. 截图当前界面。
6. 与参考图做整图对比。
7. 再做 2x2 / 3x3 / 4x4 分块对比。
8. 检查动态数值是否真的变化。
9. 检查按钮 hover / pressed / disabled 状态。
10. 检查不同分辨率下是否拉伸、重叠、出框。

如果发现以下问题，必须回滚或重做资产：

- 参考图素和程序图素混用导致风格割裂。
- 文本重复或 icon 重复。
- 动态值被旧图素烘焙值覆盖。
- 面板边缘残破、模糊、变形。
- 按钮按下出现黑框或遮罩。
- 图素周围残留背景。
- 空白图素有文字残影。

### 10. 允许的临时策略

如果 textless 资产还没达到质量标准，可以短期使用参考切片作为视觉兜底，但必须满足：

- 不使用整屏截图。
- 只使用独立面板、按钮、顶栏等切片。
- 文档中标记这是 fallback。
- 后续必须用 image2 重绘 textless 版本。
- 不把低质量本地 inpaint / 模糊 / 平铺清理图接入运行版本。

这个策略只能用于保持视觉接近参考，不能作为最终上线结构。

### 11. 命名规范

推荐路径：

```text
assets/resources/<module>/ui_sources/
assets/resources/<module>/ui_extracted/
assets/resources/<module>/ui_parts/
```

推荐命名：

```text
common_panel_paper_blank.png
common_button_primary_blank.png
topbar_resource_cell_blank.png
prep_task_panel_textless.png
prep_disciple_panel_textless.png
prep_items_panel_textless.png
prep_reward_slot_blank.png
battle_unit_slot_empty.png
result_reward_tile_blank.png
```

### 12. 交付标准

一个 UI 图素可进入游戏，必须同时满足：

- alpha 正确。
- 边缘干净。
- 无背景残留。
- 无旧文字残影。
- 无动态数值烘焙。
- 无不均匀透明边距。
- 放回 UI 后风格匹配参考图。
- 动态内容由引擎节点控制。
- 截图对比无明显偏移、拉伸、重叠。
- 交互状态可独立控制。

最终目标：游戏 UI 看起来与参考效果图一致，但内部结构是可维护、可复用、可动态变化的真实引擎 UI。
