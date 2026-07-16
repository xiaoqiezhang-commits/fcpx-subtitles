# FCPX Subtitles

[English](README.md)

一个面向专业剪辑师商业交付的 Final Cut Pro 中英双语字幕 Codex Skill。

`fcpx-subtitles` 不只是把文字转换成 XML。它把单行断句、中英时间同步、无标点规范、字体版式检查和重复内容检测等商业交付要求，固化为一套可重复、可验证的 FCPXML 工作流。

## 为什么适合剪辑师

- 分别生成中文和英文 FCPXML 交付文件
- 每张字幕卡严格保持视觉单行
- 中英文逐卡对应，开始时间和持续时间完全一致
- 按语义、呼吸、停顿、说话转折、列举或强调自然断句
- 执行无标点交付规范，同时保留英文撇号和词内连字符
- 检查分辨率、帧率、字体、字号、位置、时长、重叠和空字幕
- 检测相邻字幕的意外重复和内容残留
- 以实际录音为准，参考稿只用于核对事实性内容
- 使用无第三方依赖的 Python 脚本确定性生成并验证 XML

## 为商业交付而设计

粗剪中看似正常的字幕，到了交付阶段仍可能出错：字幕意外换成两行、英文轨和中文轨时间不一致、标点规则不统一，或者上一张字幕被错误地重复到下一张。

这个 Skill 会在生成前明确这些规则，并在生成后自动检查 XML。过长字幕只会被标记出来交由剪辑师判断，不会按照字数机械切分，因此能够保护品牌名、车型名、技术术语和自然语义单元。

## 使用条件

- 安装 Final Cut Pro 的 macOS
- 支持本地 Skill 的 Codex
- Python 3.9 或更高版本
- 剪辑电脑已经安装 XML 中使用的字体

这套工作流基于 Final Cut Pro 12.3 开发，生成使用 Basic Title 的 FCPXML 1.10。更换 Final Cut Pro 版本或标题模板后，应先在实际交付环境中测试 XML。

## 安装

```bash
git clone https://github.com/xiaoqiezhang-commits/fcpx-subtitles.git ~/.codex/skills/fcpx-subtitles
```

如果新安装的 Skill 没有立即出现，请重新启动 Codex。

## 在 Codex 中调用

```text
$fcpx-subtitles 请为这段采访音频分别制作中文和英文 FCPXML 字幕
```

生成前，Skill 会询问不能擅自猜测的项目变量：

- 字体和字重
- 字号
- 画面尺寸
- 帧率
- 输出中文、英文或两者
- 中英文各自的位置
- 是否有参考稿或逐字稿

如果没有指定字体，它会建议使用 macOS 常见且支持中英文的 `PingFang SC Regular`，但这只是建议，不是写死的默认值。

## 字幕编辑规范

1. 先根据实际音频转写，录音内容是最终依据。
2. 参考稿只用于核对人名、品牌、车型、技术术语、数字和关键措辞。
3. 先稳定原语言逐字稿，再进行翻译。
4. 长句按照自然语义和说话节奏拆分。
5. 每张字幕卡只能显示一行；过长时增加下一张字幕卡，不能在卡内换行。
6. 中英文逐卡对应，并保持完全相同的开始时间和持续时间。
7. 句中标点替换成一个空格，句末标点直接删除。
8. 保留 `don't` 一类英文撇号和 `production-ready` 一类词内连字符。
9. 删除相邻字幕之间无意产生的重复内容。

## 确定性命令行工具

Skill 使用 UTF-8 编码、以 `|` 分隔的字幕表：

```text
start|end|en|zh
00:00:00.000|00:00:02.000|We listen before we design|我们先倾听 再开始设计
```

分别生成中英文 XML：

```bash
python3 scripts/build_fcpxml.py \
  --input examples/segments.tsv \
  --output-dir output \
  --name Interview \
  --width 1920 --height 1080 --fps 25 \
  --font-family "PingFang SC" --font-face Regular --font-size 54 \
  --languages zh,en \
  --position-zh "0 -360" --position-en "0 -410"
```

检查中英文文件：

```bash
python3 scripts/validate_fcpxml.py \
  --zh output/Interview-中文.fcpxml \
  --en output/Interview-English.fcpxml \
  --width 1920 --height 1080 --fps 25 \
  --font-family "PingFang SC" --font-face Regular --font-size 54 \
  --position-zh "0 -360" --position-en "0 -410"
```

更多细节请查看[字幕规范](references/subtitle-standard.md)和[示例说明](examples/README.md)。

## 自动检查范围

- XML 是否可以解析以及是否具备必要的 FCPXML 工程结构
- 分辨率和精确帧时长
- 字体、字重、字号、位置和可选位移参数
- 每张字幕卡是否严格单行
- 标点与空格规范
- 空字幕和零时长
- 时间线重叠
- 相邻字幕重复
- 中英文卡片数量和时间是否一致
- 对过长单行字幕给出人工复核提醒

## 它不会替代什么

- 它不是独立的语音识别引擎；需要由 Codex 或其他转写步骤提供经过核对的文字和时间码。
- 它不能替代剪辑师对语义、表演、阅读速度和客户术语的判断。
- 它不负责多机位剪辑、效果或动态包装。
- 它不能保证兼容所有自定义标题模板或未来的 FCPXML 版本。

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```

## 开源许可

[MIT](LICENSE)

Final Cut Pro 是 Apple Inc. 的商标。本项目为独立项目，与 Apple 无隶属或官方认可关系。

