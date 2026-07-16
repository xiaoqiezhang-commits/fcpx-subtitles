---
name: fcpx-subtitles
description: Use when creating or checking interview subtitles for Final Cut Pro, especially separate Chinese and English FCPXML files that require single-line cards, matched bilingual timing, configurable project typography, and strict subtitle QA.
---

# FCPX Subtitles

Create separate, validated Chinese and English subtitle timelines for Final Cut Pro.

## Preflight

Before transcribing or generating XML, confirm these project variables with the user:

1. font family and font face or weight
2. font size
3. frame size in pixels
4. frame rate
5. requested output: Chinese, English, or both
6. language-specific subtitle positions if they differ
7. whether a reference script or transcript exists

Do not silently reuse settings from an earlier project. If the user has no font preference, suggest the macOS bilingual option `PingFang SC Regular` and wait for confirmation. Keep all variables editable.

## Editorial workflow

1. Transcribe from the actual audio. Treat the spoken recording as the source of truth.
2. Use a reference script only to verify names, brands, models, technical terms, numbers, and key phrasing. Do not replace the actual speech with prompting copy.
3. Translate after the source-language transcript is stable.
4. Segment by meaning, breath, pause, turn, list item, or emphasis. Never split mechanically by character count and never split a proper name, brand, model, or technical term.
5. Keep every subtitle card on exactly one line. If a card is visually too long, create additional sequential cards; never insert a line break.
6. Make Chinese and English cards correspond one-to-one with identical start times and durations.
7. Deliver separate Chinese and English FCPXML files, never two language tracks in one file unless the user explicitly requests that exception.

## Text rules

- Remove punctuation in both languages.
- Replace punctuation inside a sentence with exactly one space.
- Remove punctuation at the end of a sentence without leaving a trailing space.
- Preserve apostrophes inside words such as `don't` and in-word hyphens such as `production-ready`.
- Collapse repeated spaces and remove leading or trailing spaces.
- Check adjacent repetition. A previous card must not reappear as the prefix, suffix, or full text of the next card unless the user explicitly requests a repeated effect.

## Build and validate

Prepare a UTF-8 pipe-delimited file with this header:

```text
start|end|en|zh
00:00:00.000|00:00:02.000|English card|中文字幕
```

Read [subtitle-standard.md](references/subtitle-standard.md) for the input contract, supported frame rates, and command examples.

Run `scripts/build_fcpxml.py` with the confirmed project variables. Then always run `scripts/validate_fcpxml.py` on the generated files. Do not deliver files if validation reports errors. Review warnings about unusually long cards manually; they are prompts for editorial judgment, not automatic split instructions.

## Final QA

- Import or parse succeeds and required FCPXML structure exists.
- Resolution, frame rate, font, size, and per-language position match the confirmed settings.
- Every card is one line with nonzero duration and no overlap.
- Punctuation and whitespace follow the text rules.
- Chinese and English counts and timings match exactly.
- No adjacent repetition or accidental carry-over remains.
- Long cards have been reviewed without breaking protected terms.
