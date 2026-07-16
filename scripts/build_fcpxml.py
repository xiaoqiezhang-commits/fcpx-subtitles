#!/usr/bin/env python3
import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path


FPS = {
    "23.976": Fraction(1001, 24000),
    "24": Fraction(1, 24),
    "25": Fraction(1, 25),
    "29.97": Fraction(1001, 30000),
    "30": Fraction(1, 30),
    "50": Fraction(1, 50),
    "59.94": Fraction(1001, 60000),
    "60": Fraction(1, 60),
}
FORBIDDEN = re.compile(r"[，。！？；：、,.!?;:\"“”‘’（）()【】\[\]《》<>…—]")
TITLE_EFFECT = "~/Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"


def fail(message):
    raise ValueError(message)


def parse_time(value):
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2})\.(\d{3})", value)
    if not match:
        fail(f"invalid timestamp: {value}")
    hours, minutes, seconds, millis = map(int, match.groups())
    if minutes > 59 or seconds > 59:
        fail(f"invalid timestamp: {value}")
    return Fraction(((hours * 60 + minutes) * 60 + seconds) * 1000 + millis, 1000)


def snap(value, frame_duration):
    frames = int(value / frame_duration + Fraction(1, 2))
    return frames * frame_duration


def fcptime(value):
    return f"{value.numerator}/{value.denominator}s" if value.denominator != 1 else f"{value.numerator}s"


def read_rows(path, frame_duration, languages):
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="|")
        if reader.fieldnames != ["start", "end", "en", "zh"]:
            fail("input header must be start|end|en|zh")
        for line_no, row in enumerate(reader, 2):
            start = snap(parse_time(row["start"]), frame_duration)
            end = snap(parse_time(row["end"]), frame_duration)
            if end <= start:
                fail(f"line {line_no}: subtitle duration must be greater than zero")
            if rows and start < rows[-1]["end"]:
                fail(f"line {line_no}: subtitle overlaps the previous card")
            for language in languages:
                value = row[language]
                if not value.strip():
                    fail(f"line {line_no}: {language} text is empty")
                if "\n" in value or "\r" in value or "\\n" in value or "\\r" in value:
                    fail(f"line {line_no}: every subtitle card must stay on one line")
                if value != value.strip() or "  " in value:
                    fail(f"line {line_no}: {language} has invalid surrounding or repeated spaces")
                if FORBIDDEN.search(value):
                    fail(f"line {line_no}: {language} contains forbidden punctuation")
            rows.append({"start": start, "end": end, "en": row["en"], "zh": row["zh"]})
    if not rows:
        fail("input has no subtitle rows")
    return rows


def make_document(rows, language, args, frame_duration):
    root = ET.Element("fcpxml", version="1.10")
    resources = ET.SubElement(root, "resources")
    ET.SubElement(
        resources, "format", id="r1", name=f"FFVideoFormat{args.height}p{args.fps}",
        frameDuration=fcptime(frame_duration), width=str(args.width), height=str(args.height),
        colorSpace="1-1-1 (Rec. 709)",
    )
    ET.SubElement(resources, "effect", id="r2", name="Basic Title", uid=TITLE_EFFECT)
    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", name=args.name)
    project = ET.SubElement(event, "project", name=f"{args.name}-{'中文' if language == 'zh' else 'English'}")
    sequence = ET.SubElement(
        project, "sequence", format="r1", duration=fcptime(rows[-1]["end"]),
        tcStart="0s", tcFormat="NDF", audioLayout="stereo", audioRate="48k",
    )
    spine = ET.SubElement(sequence, "spine")
    gap = ET.SubElement(spine, "gap", name="Subtitles", offset="0s", start="0s", duration=fcptime(rows[-1]["end"]))
    position = args.position_zh if language == "zh" else args.position_en
    adjust = args.adjust_zh if language == "zh" else args.adjust_en
    for index, row in enumerate(rows, 1):
        title = ET.SubElement(
            gap, "title", name=f"Card {index:03d}", lane="1", offset=fcptime(row["start"]),
            ref="r2", start="0s", duration=fcptime(row["end"] - row["start"]),
        )
        if adjust:
            ET.SubElement(title, "adjust-transform", position=adjust)
        text = ET.SubElement(title, "text")
        style = ET.SubElement(text, "text-style", ref="ts1")
        style.text = row[language]
        ET.SubElement(
            title, "text-style-def", id="ts1"
        ).append(ET.Element(
            "text-style", font=args.font_family, fontFace=args.font_face,
            fontSize=str(args.font_size), fontColor="1 1 1 1", alignment="center",
        ))
        ET.SubElement(title, "param", name="Position", key="9999/999166631/999166633/1/100/101", value=position)
    ET.indent(root, space="  ")
    return ET.ElementTree(root)


def parser():
    p = argparse.ArgumentParser(description="Build separate Final Cut Pro subtitle XML files")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--width", type=int, required=True)
    p.add_argument("--height", type=int, required=True)
    p.add_argument("--fps", choices=FPS, required=True)
    p.add_argument("--font-family", required=True)
    p.add_argument("--font-face", required=True)
    p.add_argument("--font-size", type=float, required=True)
    p.add_argument("--languages", default="zh,en")
    p.add_argument("--position-zh", default="0 -410")
    p.add_argument("--position-en", default="0 -410")
    p.add_argument("--adjust-zh")
    p.add_argument("--adjust-en")
    return p


def main():
    args = parser().parse_args()
    try:
        languages = [item.strip() for item in args.languages.split(",") if item.strip()]
        if not languages or any(item not in {"zh", "en"} for item in languages):
            fail("languages must contain zh, en, or both")
        if args.width <= 0 or args.height <= 0 or args.font_size <= 0:
            fail("width, height, and font size must be positive")
        rows = read_rows(args.input, FPS[args.fps], languages)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        names = {"zh": f"{args.name}-中文.fcpxml", "en": f"{args.name}-English.fcpxml"}
        for language in languages:
            path = args.output_dir / names[language]
            make_document(rows, language, args, FPS[args.fps]).write(path, encoding="utf-8", xml_declaration=True)
            print(path)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
