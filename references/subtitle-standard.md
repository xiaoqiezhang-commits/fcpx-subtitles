# Subtitle input and command reference

## Segment table

Use UTF-8 text with `|` separators and the exact header `start|end|en|zh`. Times use `HH:MM:SS.mmm`. Text must already follow the punctuation rule and must contain no literal or escaped line breaks.

When generating only one language, retain the full header; the unused text column may be empty.

## Supported frame rates

The generator accepts `23.976`, `24`, `25`, `29.97`, `30`, `50`, `59.94`, and `60`. It maps fractional rates to Final Cut's exact rational frame durations and snaps all boundaries to frames.

## Generate

```bash
python3 scripts/build_fcpxml.py \
  --input segments.tsv \
  --output-dir ./output \
  --name Interview \
  --width 1920 --height 1080 --fps 25 \
  --font-family "PingFang SC" --font-face Regular --font-size 54 \
  --languages zh,en \
  --position-zh "0 -410" --position-en "0 -410"
```

For a separate English vertical adjustment, add an illustrative value such as `--adjust-en "0 -8.5"`. Positions are project variables, not universal defaults.

Generated names are `<name>-中文.fcpxml` and `<name>-English.fcpxml`.

## Validate

```bash
python3 scripts/validate_fcpxml.py \
  --zh output/Interview-中文.fcpxml \
  --en output/Interview-English.fcpxml \
  --width 1920 --height 1080 --fps 25 \
  --font-family "PingFang SC" --font-face Regular --font-size 54 \
  --position-zh "0 -410" --position-en "0 -410"
```

Validation exits nonzero on structural or editorial errors. Long-card messages are warnings only and require human review.
