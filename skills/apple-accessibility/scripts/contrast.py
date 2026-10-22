#!/usr/bin/env python3
"""
WCAG contrast checker for the Sufficient Contrast label.

    python3 contrast.py FG BG [FG BG ...] [--target 4.5] [--nontext]
    python3 contrast.py --file pairs.txt          # lines: FG BG [label]; "//" comments

Colours: #RGB, #RRGGBB, #RRGGBBAA (alpha is composited over BG), 0xRRGGBB.
Thresholds: text 4.5:1, non-text (controls, state indicators) 3:1.
For failing pairs it suggests the nearest passing foreground, mixing toward
black or white in 1% steps, whichever direction reaches the target first.
"""

import sys


def parse(value: str):
    v = value.strip().lstrip("#")
    if v.lower().startswith("0x"):
        v = v[2:]
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) not in (6, 8):
        raise ValueError(f"bad colour: {value}")
    rgb = [int(v[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    alpha = int(v[6:8], 16) / 255 if len(v) == 8 else 1.0
    return rgb, alpha


def composite(fg, alpha, bg):
    return [f * alpha + b * (1 - alpha) for f, b in zip(fg, bg)]


def luminance(rgb):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def to_hex(rgb):
    return "#" + "".join(f"{round(c * 255):02X}" for c in rgb)


def suggest(fg, bg, target):
    best = None
    for goal in (0.0, 1.0):
        for step in range(1, 101):
            t = step / 100
            cand = [c + (goal - c) * t for c in fg]
            if ratio(cand, bg) >= target:
                if best is None or step < best[0]:
                    best = (step, cand)
                break
    return (to_hex(best[1]), best[0]) if best else (None, None)


def check(fg_s, bg_s, target, label=""):
    bg, _ = parse(bg_s)
    fg_raw, alpha = parse(fg_s)
    fg = composite(fg_raw, alpha, bg)
    r = ratio(fg, bg)
    ok = r >= target
    line = f"{'PASS' if ok else 'FAIL'}  {r:5.2f}:1  {fg_s} on {bg_s}  (target {target}:1)"
    if label:
        line += f"  [{label}]"
    if not ok:
        hex_, step = suggest(fg, bg, target)
        line += f"  → try {hex_} ({step}% mix)" if hex_ else "  → no foreground reaches target on this background"
    print(line)
    return ok


def main(argv):
    args = argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print(__doc__)
        return 0 if args else 2
    target = 4.5
    if "--nontext" in args:
        target = 3.0
        args.remove("--nontext")
    if "--target" in args:
        i = args.index("--target")
        target = float(args[i + 1])
        del args[i:i + 2]
    pairs = []
    if "--file" in args:
        i = args.index("--file")
        with open(args[i + 1]) as fh:
            for raw in fh:
                # "#" starts a colour, so comments use "//".
                if raw.lstrip().startswith("//"):
                    continue
                parts = raw.strip().split(None, 2)
                if len(parts) >= 2:
                    pairs.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
        del args[i:i + 2]
    if len(args) % 2:
        print("Give colours in FG BG pairs.", file=sys.stderr)
        return 2
    pairs += [(args[i], args[i + 1], "") for i in range(0, len(args), 2)]
    results = [check(fg, bg, target, label) for fg, bg, label in pairs]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
