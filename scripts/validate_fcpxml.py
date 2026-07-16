#!/usr/bin/env python3
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path


FPS = {
    "23.976": Fraction(1001, 24000), "24": Fraction(1, 24), "25": Fraction(1, 25),
    "29.97": Fraction(1001, 30000), "30": Fraction(1, 30), "50": Fraction(1, 50),
    "59.94": Fraction(1001, 60000), "60": Fraction(1, 60),
}
FORBIDDEN = re.compile(r"[，。！？；：、,.!?;:\"“”‘’（）()【】\[\]《》<>…—]")


def time_value(value):
    if not value or not value.endswith("s"):
        raise ValueError(f"invalid FCP time {value!r}")
    raw = value[:-1]
    return Fraction(raw) if "/" in raw else Fraction(int(raw), 1)


def normalized(text):
    return " ".join(text.lower().split())


def repeated(a, b, language):
    a, b = normalized(a), normalized(b)
    if a == b or b.startswith(a + " ") or a.startswith(b + " "):
        return True
    if language == "zh":
        left, right = a.replace(" ", ""), b.replace(" ", "")
        if left == right or right.startswith(left) or left.startswith(right):
            return True
        limit = min(len(left), len(right))
        return any(left[-n:] == right[:n] for n in range(4, limit + 1))
    left, right = a.split(), b.split()
    limit = min(len(left), len(right))
    return any(left[-n:] == right[:n] for n in range(2, limit + 1))


def inspect(path, language, errors, warnings):
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        errors.append(f"{path}: XML parse failed: {exc}")
        return None, []
    if root.tag != "fcpxml" or root.find("./library/event/project/sequence/spine") is None:
        errors.append(f"{path}: missing required FCPXML project structure")
    titles = root.findall(".//title")
    cards = []
    previous_end = None
    previous_text = None
    for index, title in enumerate(titles, 1):
        text = title.findtext("text/text-style") or ""
        try:
            start = time_value(title.get("offset"))
            duration = time_value(title.get("duration"))
        except ValueError as exc:
            errors.append(f"{path} card {index}: {exc}")
            continue
        if duration <= 0:
            errors.append(f"{path} card {index}: duration must be greater than zero")
        if previous_end is not None and start < previous_end:
            errors.append(f"{path} card {index}: overlaps the previous card")
        if not text:
            errors.append(f"{path} card {index}: text is empty")
        if "\n" in text or "\r" in text or "\\n" in text or "\\r" in text:
            errors.append(f"{path} card {index}: subtitle must stay on one line")
        if text != text.strip() or "  " in text:
            errors.append(f"{path} card {index}: invalid surrounding or repeated spaces")
        if FORBIDDEN.search(text):
            errors.append(f"{path} card {index}: forbidden punctuation")
        if previous_text and repeated(previous_text, text, language):
            errors.append(f"{path} cards {index - 1}-{index}: adjacent repetition")
        metric = len(text.replace(" ", "")) if language == "zh" else len(text)
        if metric > (28 if language == "zh" else 70):
            warnings.append(f"{path} card {index}: review long one-line subtitle ({metric})")
        cards.append((start, duration, text, title))
        previous_end = start + duration
        previous_text = text
    if not titles:
        errors.append(f"{path}: no title cards found")
    return root, cards


def main():
    p = argparse.ArgumentParser(description="Validate Final Cut Pro subtitle XML")
    p.add_argument("--zh", type=Path)
    p.add_argument("--en", type=Path)
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--fps", choices=FPS)
    p.add_argument("--font-family")
    p.add_argument("--font-face")
    p.add_argument("--font-size", type=float)
    p.add_argument("--position-zh")
    p.add_argument("--position-en")
    p.add_argument("--adjust-zh")
    p.add_argument("--adjust-en")
    args = p.parse_args()
    if not args.zh and not args.en:
        p.error("provide --zh, --en, or both")
    errors, warnings, results = [], [], {}
    for language, path in (("zh", args.zh), ("en", args.en)):
        if not path:
            continue
        root, cards = inspect(path, language, errors, warnings)
        if root is None:
            continue
        results[language] = cards
        expected_position = args.position_zh if language == "zh" else args.position_en
        expected_adjust = args.adjust_zh if language == "zh" else args.adjust_en
        fmt = root.find("./resources/format")
        if fmt is None:
            errors.append(f"{path}: missing format resource")
        else:
            if args.width is not None and fmt.get("width") != str(args.width):
                errors.append(f"{path}: width does not match {args.width}")
            if args.height is not None and fmt.get("height") != str(args.height):
                errors.append(f"{path}: height does not match {args.height}")
            if args.fps and fmt.get("frameDuration") != (f"{FPS[args.fps].numerator}/{FPS[args.fps].denominator}s" if FPS[args.fps].denominator != 1 else f"{FPS[args.fps].numerator}s"):
                errors.append(f"{path}: frame rate does not match {args.fps}")
        for index, (_, _, _, title) in enumerate(cards, 1):
            style = title.find("text-style-def/text-style")
            if style is None:
                errors.append(f"{path} card {index}: missing text style")
                continue
            if args.font_family and style.get("font") != args.font_family:
                errors.append(f"{path} card {index}: font does not match {args.font_family}")
            if args.font_face and style.get("fontFace") != args.font_face:
                errors.append(f"{path} card {index}: font face does not match {args.font_face}")
            if args.font_size is not None and float(style.get("fontSize", "nan")) != args.font_size:
                errors.append(f"{path} card {index}: font size does not match {args.font_size:g}")
            position = title.find("param[@name='Position']")
            if expected_position and (position is None or position.get("value") != expected_position):
                errors.append(f"{path} card {index}: position does not match {expected_position}")
            adjust = title.find("adjust-transform")
            if expected_adjust and (adjust is None or adjust.get("position") != expected_adjust):
                errors.append(f"{path} card {index}: transform adjustment does not match {expected_adjust}")
    if "zh" in results and "en" in results:
        zh, en = results["zh"], results["en"]
        if len(zh) != len(en):
            errors.append(f"bilingual card count mismatch: zh={len(zh)} en={len(en)}")
        for index, (z, e) in enumerate(zip(zh, en), 1):
            if z[:2] != e[:2]:
                errors.append(f"bilingual timing mismatch at card {index}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(f"PASS: validated {sum(len(value) for value in results.values())} subtitle cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
