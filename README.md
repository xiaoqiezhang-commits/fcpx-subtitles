# FCPX Subtitles

[中文说明](README.zh-CN.md)

A production-oriented Codex Skill for professional editors delivering bilingual interview subtitles in Final Cut Pro.

`fcpx-subtitles` does more than turn text into XML. It turns commercial subtitle delivery standards—single-line segmentation, synchronized Chinese–English timing, punctuation control, typography checks, and duplicate detection—into a repeatable, validated FCPXML workflow.

## Why editors use it

- Produces separate Chinese and English FCPXML deliverables
- Keeps every subtitle card on one visual line
- Aligns both languages card-for-card with identical timing
- Segments by meaning, breath, pause, turn, list item, or emphasis
- Enforces punctuation-free delivery while preserving apostrophes and in-word hyphens
- Checks resolution, frame rate, font, size, position, duration, overlap, and empty cards
- Detects accidental carry-over and adjacent repeated text
- Treats the recorded speech as the source of truth and reference scripts as factual checks only
- Uses deterministic, dependency-free Python scripts for generation and QA

## Designed for commercial delivery

Subtitles that look acceptable during a rough cut can still fail delivery: a line wraps unexpectedly, the English track drifts from the Chinese track, punctuation is inconsistent, or text from the previous card is repeated by mistake.

This Skill makes those rules explicit before export and verifies the generated XML afterward. Long cards are flagged for editorial review rather than split mechanically, so brand names, model names, technical terms, and natural speech units remain intact.

## Requirements

- macOS with Final Cut Pro
- Codex with local Skill support
- Python 3.9 or later for the deterministic scripts
- The fonts referenced by the XML installed on the editing system

The workflow was developed with Final Cut Pro 12.3 and generates FCPXML 1.10 using Basic Title. Test XML in your delivery environment before adopting it for a new Final Cut Pro version or title template.

## Install

```bash
git clone https://github.com/xiaoqiezhang-commits/fcpx-subtitles.git ~/.codex/skills/fcpx-subtitles
```

Restart Codex if the newly installed Skill does not appear immediately.

## Use with Codex

Invoke it explicitly:

```text
$fcpx-subtitles Create separate Chinese and English FCPXML subtitles for this interview audio
```

Before generation, the Skill asks for the variable settings that should never be guessed:

- font family and face or weight
- font size
- frame size
- frame rate
- Chinese, English, or both
- language-specific positions
- optional reference script or transcript

If no font is specified, it suggests `PingFang SC Regular`, a commonly available macOS option that supports Chinese and English. It remains a suggestion, not a fixed default.

## Editorial rules

1. Transcribe the actual audio first.
2. Use a reference script only to verify names, brands, models, technical terms, numbers, and key phrasing.
3. Stabilize the source-language transcript before translating.
4. Divide long speech at natural semantic and spoken boundaries.
5. Keep each subtitle card to one visual line—create another card instead of inserting a line break.
6. Match Chinese and English cards one-to-one with identical start times and durations.
7. Replace punctuation inside a sentence with one space and remove sentence-final punctuation.
8. Preserve apostrophes such as `don't` and in-word hyphens such as `production-ready`.
9. Remove accidental repetition between adjacent cards.

## Deterministic CLI

The Skill uses a UTF-8 pipe-delimited segment table:

```text
start|end|en|zh
00:00:00.000|00:00:02.000|We listen before we design|我们先倾听 再开始设计
```

Generate separate files:

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

Validate the pair:

```bash
python3 scripts/validate_fcpxml.py \
  --zh output/Interview-中文.fcpxml \
  --en output/Interview-English.fcpxml \
  --width 1920 --height 1080 --fps 25 \
  --font-family "PingFang SC" --font-face Regular --font-size 54 \
  --position-zh "0 -360" --position-en "0 -410"
```

See [the subtitle standard](references/subtitle-standard.md) and [the example guide](examples/README.md) for details.

## Validation coverage

The validator checks:

- parseable FCPXML and required project structure
- resolution and exact rational frame duration
- font family, face, size, position, and optional transform adjustment
- exactly one line per card
- punctuation and whitespace rules
- non-empty text and positive duration
- timeline overlap
- adjacent repetition
- bilingual card-count and timing parity
- warning-level long-card metrics for manual review

## What it does not do

- It is not a standalone speech-recognition engine; Codex or another transcription step supplies the reviewed text and timing.
- It does not replace an editor's judgment about meaning, performance, reading speed, or client terminology.
- It does not create multicam edits, effects, or styled motion graphics.
- It cannot guarantee compatibility with every custom title template or future FCPXML version.

## Run tests

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)

Final Cut Pro is a trademark of Apple Inc. This project is independent and is not affiliated with or endorsed by Apple.

