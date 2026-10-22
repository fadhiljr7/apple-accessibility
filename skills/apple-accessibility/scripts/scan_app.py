#!/usr/bin/env python3
"""
Static accessibility triage for an Apple-platform app project.

Detects the framework and target devices, then counts code patterns that
matter for each Accessibility Nutrition Label (fixed font sizes, animations,
forced light mode, media, existing accessibility APIs, ...), with file:line
samples. It is a starting point for the audit, not a verdict: every finding
should be confirmed by reading the code.

Usage:
    python3 scan_app.py <project-root>          # markdown report
    python3 scan_app.py <project-root> --json   # JSON
    python3 scan_app.py <project-root> --skip web,Docs   # skip extra folder names

Marketing folders (website, docs, fastlane, screenshots, ...) are skipped by
default, and so is a top-level web/ when the app itself is native/Flutter/RN.
Standard library only.
"""

import json
import os
import plistlib
import re
import sys
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "Pods", "build", "Build", "DerivedData", ".build",
    "Carthage", ".dart_tool", ".gradle", "android", "Library", "Temp", "obj",
    "bin", ".expo", ".next", "dist", "vendor", ".swiftpm", "xcuserdata",
    "__pycache__", ".venv", "venv",
}
CODE_EXT = {".swift", ".m", ".mm", ".h", ".js", ".jsx", ".ts", ".tsx", ".dart",
            ".cs", ".kt", ".html", ".css", ".scss", ".vue", ".svelte", ".xaml"}
MEDIA_EXT = {".mp4", ".m4v", ".mov", ".m3u8", ".mp3", ".m4a", ".aac", ".wav", ".caf",
             ".flac", ".aif", ".aiff", ".ogg", ".opus"}
VIDEO_EXT = (".mp4", ".m4v", ".mov", ".m3u8")
# Folders that sit next to an app but aren't the app: marketing sites, launch
# videos, store screenshots, references. "web" is only skipped when the app
# itself is native/Flutter/RN (see is_app_shell_elsewhere).
NOT_APP_DIRS = {"brag-output", "marketing", "fastlane", "screenshots", "Screenshot",
                "Screenshots", "References", "docs", "website", "landing"}
WEB_DIRS = {"web", "site"}
CAPTION_EXT = {".vtt", ".srt", ".scc", ".ttml"}
MAX_FILE_BYTES = 1_500_000
SAMPLES = 5

# (feature, key, description, regex, kind) — kind: "risk" | "support" | "info"
RULES = [
    # Larger Text
    ("larger_text", "fixed_font_swiftui", "SwiftUI fixed-size system font (numeric literal)",
     r"\.system\(\s*size\s*:\s*\d", "risk"),
    ("larger_text", "fixed_font_custom", "Font.custom(fixedSize:) never scales",
     r"fixedSize\s*:", "risk"),
    ("larger_text", "fixed_font_uikit", "UIKit fixed font without UIFontMetrics",
     r"UIFont\.(systemFont|boldSystemFont|monospacedDigitSystemFont)\(\s*ofSize|UIFont\(\s*name:[^)]*size:", "risk"),
    ("larger_text", "low_type_cap", "dynamicTypeSize capped below AX3",
     r"dynamicTypeSize\(\s*\.\.\.\s*(DynamicTypeSize)?\.(xSmall|small|medium|large|xLarge|xxLarge|xxxLarge|accessibility1|accessibility2)\b", "risk"),
    ("larger_text", "fixed_type_size", "dynamicTypeSize pinned to one size",
     r"\.dynamicTypeSize\(\s*\.(xSmall|small|medium|large|xLarge|xxLarge|xxxLarge)\s*\)", "risk"),
    ("larger_text", "fixed_height", "Fixed frame height (check if it holds text)",
     r"\.frame\([^)]*\bheight\s*:\s*\d", "info"),
    ("larger_text", "line_limit_1", "lineLimit(1) / numberOfLines 1 / maxLines 1",
     r"\.lineLimit\(\s*1\s*\)|numberOfLines\s*=\s*1\b|numberOfLines=\{1\}|maxLines\s*:\s*1\b", "info"),
    ("larger_text", "shrink_to_fit", "minimumScaleFactor / adjustsFontSizeToFitWidth (text shrinks back)",
     r"minimumScaleFactor|adjustsFontSizeToFitWidth", "info"),
    ("larger_text", "rn_no_scaling", "React Native font scaling disabled or capped low",
     r"allowFontScaling\s*=\s*\{\s*false\s*\}|allowFontScaling\s*:\s*false|maxFontSizeMultiplier\s*[=:]\s*\{?\s*1(\.\d+)?\b", "risk"),
    ("larger_text", "flutter_no_scaling", "Flutter text scaling disabled or clamped low",
     r"TextScaler\.noScaling|textScaleFactor\s*:\s*1(\.0)?\b|TextScaler\.linear\(\s*1(\.0)?\s*\)|maxScaleFactor\s*:\s*1(\.\d+)?\b", "risk"),
    ("larger_text", "dynamic_type_support", "Dynamic Type APIs in use",
     r"\.font\(\s*\.(largeTitle|title|title2|title3|headline|subheadline|body|callout|footnote|caption|caption2)\b|UIFontMetrics|adjustsFontForContentSizeCategory|preferredFont\(forTextStyle|@ScaledMetric|isAccessibilitySize|isAccessibilityCategory|ViewThatFits|textScalerOf|fontScale", "support"),
    ("larger_text", "large_content_viewer", "Large Content Viewer",
     r"accessibilityShowsLargeContentViewer|UILargeContentViewerInteraction|showsLargeContentViewer", "support"),

    # Dark Interface
    ("dark_interface", "forced_light", "Light mode forced in code",
     r"preferredColorScheme\(\s*\.light\s*\)|overrideUserInterfaceStyle\s*=\s*\.light|ThemeMode\.light\b|userInterfaceStyle\"?\s*:\s*\"light\"", "risk"),
    ("dark_interface", "hardcoded_colors", "Hard-coded colour literals (check they adapt)",
     r"Color\(\s*red\s*:|UIColor\(\s*red\s*:|Color\(\s*hex|UIColor\(\s*hex|#[0-9A-Fa-f]{6}\b|Color\(0x[0-9A-Fa-f]{6,8}\)|Colors\.white\b", "info"),
    ("dark_interface", "white_surfaces", "Literal white backgrounds",
     r"\.background\(\s*(Color\.)?white\b|backgroundColor\s*=\s*\.white|backgroundColor\s*:\s*['\"](#fff|#ffffff|white)['\"]", "risk"),
    ("dark_interface", "dark_support", "Appearance-aware code",
     r"colorScheme|userInterfaceStyle|useColorScheme|Appearance\.getColorScheme|darkTheme\s*:|ThemeMode\.system|DynamicColorIOS|PlatformColor|systemBackground|prefers-color-scheme|AppThemeBinding", "support"),

    # Sufficient Contrast
    ("sufficient_contrast", "contrast_support", "Increase Contrast / Reduce Transparency handling",
     r"colorSchemeContrast|accessibilityContrast|isDarkerSystemColorsEnabled|accessibilityReduceTransparency|isReduceTransparencyEnabled|highContrast|prefers-contrast|DarkerSystemColorsEnabled", "support"),
    ("sufficient_contrast", "materials", "Translucent materials / blur (check text on top)",
     r"\.(ultraThin|thin|regular|thick|ultraThick)Material\b|UIBlurEffect|UIVisualEffectView|glassEffect|BlurView|BackdropFilter", "info"),
    ("sufficient_contrast", "faint_text", "Low-opacity foreground (possible low contrast)",
     r"\.(foregroundStyle|foregroundColor)\([^)]*opacity\(\s*0?\.[0-4]", "risk"),

    # Differentiate Without Color Alone
    ("differentiate_without_color", "differentiate_support", "Differentiate Without Color handling",
     r"accessibilityDifferentiateWithoutColor|shouldDifferentiateWithoutColor|accessibilityDisplayShouldDifferentiateWithoutColor", "support"),
    ("differentiate_without_color", "red_green", "Red/green colour usage (check it isn't the only cue)",
     r"\.(red|green)\b|systemRed|systemGreen|Colors\.(red|green)\b", "info"),
    ("differentiate_without_color", "charts", "Charts (need labels/symbols, legend order)",
     r"import Charts\b|\bChart\s*\{|foregroundStyle\(\s*by:|fl_chart|victory-native|react-native-chart|syncfusion_flutter_charts", "info"),

    # Reduced Motion
    ("reduced_motion", "animations", "Animations",
     r"withAnimation|\.animation\(|\.spring\(|\.bouncy|\.snappy|UIView\.animate|CABasicAnimation|CAKeyframeAnimation|Animated\.(timing|spring|loop)|LayoutAnimation|AnimationController|keyframeAnimator|phaseAnimator", "info"),
    ("reduced_motion", "motion_triggers", "Scale/rotate/3D/zoom/parallax/looping motion",
     r"scaleEffect|rotationEffect|rotation3DEffect|matchedGeometryEffect|navigationTransition\(\s*\.zoom|\.transition\(\s*\.(scale|slide|move|push)|repeatForever|UIInterpolatingMotionEffect|UIMotionEffect|parallax|symbolEffect|Hero\(|ScaleTransition|RotationTransition|LottieView|AnimationView|SKAction|withRepeat|\.repeat\(", "risk"),
    ("reduced_motion", "reduce_motion_support", "Reduce Motion handling",
     r"accessibilityReduceMotion|isReduceMotionEnabled|reduceMotionStatusDidChange|useReducedMotion|ReduceMotion\.|disableAnimations|prefers-reduced-motion|accessibilityDisplayShouldReduceMotion", "support"),
    ("reduced_motion", "carousel", "Auto-advancing timers (carousels?)",
     r"Timer\.publish|Timer\.scheduledTimer|autoplay|autoPlay|setInterval", "info"),

    # VoiceOver
    ("voiceover", "a11y_api", "Accessibility labels/traits/actions in use",
     r"accessibilityLabel|accessibilityHint|accessibilityValue|accessibilityElement\(|accessibilityAddTraits|accessibilityTraits|accessibilityAction|accessibilityHidden|accessibilityRepresentation|isAccessibilityElement|accessibilityAdjustableAction|AccessibilityNotification|UIAccessibility\.post|accessibilityRotor|Semantics\(|semanticsLabel|accessibilityRole|accessibilityState|aria-label|SemanticProperties", "support"),
    ("voiceover", "tap_gestures", "Tap/drag/long-press gestures on non-buttons (need labels/actions)",
     r"\.onTapGesture|\.onLongPressGesture|DragGesture|LongPressGesture|UITapGestureRecognizer|UIPanGestureRecognizer|GestureDetector\(|onLongPress", "risk"),
    ("voiceover", "decorative_hidden", "Decorative images hidden",
     r"Image\(\s*decorative|accessibilityHidden\(\s*true|ExcludeSemantics|importantForAccessibility=\"no|accessibilityElementsHidden", "support"),
    ("voiceover", "custom_canvas", "Custom drawing (invisible to VoiceOver unless exposed)",
     r"\bCanvas\s*\{|CustomPaint|drawRect|draw\(_\s*rect|SKView|SpriteView|MTKView|SceneView|RealityView|GLKView", "risk"),

    # Voice Control
    ("voice_control", "input_labels", "Voice Control input labels",
     r"accessibilityInputLabels|accessibilityUserInputLabels", "support"),
    ("voice_control", "text_fields", "Text input fields",
     r"\bTextField\b|SecureField|TextEditor|UITextField|UITextView|TextInput\b|TextFormField", "info"),

    # Media → Captions / Audio Descriptions
    ("media", "video", "Video playback",
     r"AVPlayer\b|AVPlayerViewController|VideoPlayer\(|AVPlayerLayer|react-native-video|expo-video|expo-av|video_player|chewie|better_player|<video", "info"),
    ("media", "audio", "Audio playback / speech",
     r"AVAudioPlayer|AVAudioEngine|AVQueuePlayer|AVSpeechSynthesizer|just_audio|audioplayers|expo-audio|react-native-track-player|<audio", "info"),
    ("media", "captions_support", "Caption / subtitle handling",
     r"isClosedCaptioningEnabled|MACaptionAppearance|\.legible\b|appliesMediaSelectionCriteriaAutomatically|textTracks|selectedTextTrack|closedCaptionFile|kind=\"captions\"|transcript", "support"),
    ("media", "ad_support", "Audio description handling",
     r"describesVideoForAccessibility|MAAudibleMediaCopyPreferredCharacteristics|describes-video", "support"),

    # Common-task hints
    ("common_tasks", "purchase", "Purchases / paywall",
     r"import StoreKit|Product\.products|SKPaymentQueue|RevenueCat|Purchases\.|SubscriptionStoreView|react-native-iap|in_app_purchase", "info"),
    ("common_tasks", "login", "Login / authentication",
     r"SignInWithAppleButton|ASAuthorization|FirebaseAuth|Auth\.auth\(\)|signIn\(|GoogleSignIn|supabase\.auth|Clerk|Auth0", "info"),
    ("common_tasks", "onboarding", "Onboarding / first launch",
     r"[Oo]nboarding|hasSeenIntro|firstLaunch|isFirstLaunch|Welcome(View|Screen)", "info"),
    ("common_tasks", "settings", "Settings screen",
     r"Settings(View|Screen|Page)\b|SettingsLink|openSettingsURLString", "info"),
    ("common_tasks", "web_views", "Web views (web content must meet criteria too)",
     r"WKWebView|WebView\(|SFSafariViewController|react-native-webview|webview_flutter|InAppWebView|Capacitor", "info"),
]
COMPILED = [(f, k, d, re.compile(rx), kind) for f, k, d, rx, kind in RULES]

DEVICE_FAMILY = {"1": "iPhone", "2": "iPad", "3": "Apple TV", "4": "Apple Watch", "7": "Apple Vision Pro"}


def has_app_shell(root: Path):
    """True if the app lives outside a top-level web/ folder (native, Flutter, RN)."""
    return (any(root.glob("*.xcodeproj")) or (root / "ios").is_dir()
            or (root / "pubspec.yaml").exists() or (root / "Package.swift").exists())


def walk(root: Path, extra_skip=()):
    skip_web = has_app_shell(root)
    for dirpath, dirnames, filenames in os.walk(root):
        top = Path(dirpath) == root
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and d not in NOT_APP_DIRS and d not in extra_skip
                       and not d.startswith(".") and not (top and skip_web and d in WEB_DIRS)]
        for name in filenames:
            yield Path(dirpath) / name


def read_text(path: Path):
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def detect_framework(root: Path, files):
    names = {p.name for p in files}
    frameworks = []
    pkg = root / "package.json"
    if pkg.exists():
        text = read_text(pkg) or ""
        if '"expo"' in text:
            frameworks.append("Expo (React Native)")
        elif '"react-native"' in text:
            frameworks.append("React Native")
        elif "@capacitor/core" in text:
            frameworks.append("Capacitor")
        elif "cordova" in text:
            frameworks.append("Cordova")
    if "pubspec.yaml" in names and "flutter" in (read_text(next(p for p in files if p.name == "pubspec.yaml")) or ""):
        frameworks.append("Flutter")
    if (root / "ProjectSettings" / "ProjectVersion.txt").exists() or any(p.suffix == ".unity" for p in files):
        frameworks.append("Unity")
    if any(p.suffix == ".csproj" and "UseMaui" in (read_text(p) or "") for p in files):
        frameworks.append(".NET MAUI")
    swift = [p for p in files if p.suffix == ".swift"]
    if swift:
        sample = "".join((read_text(p) or "")[:4000] for p in swift[:400])
        ui = [n for n, token in (("SwiftUI", "import SwiftUI"), ("UIKit", "import UIKit"), ("AppKit", "import AppKit")) if token in sample]
        frameworks.append("Native Swift (" + ", ".join(ui or ["no UI import found"]) + ")")
    elif any(p.suffix in {".m", ".mm"} for p in files):
        frameworks.append("Native Objective-C")
    return frameworks or ["Unknown"]


def detect_devices(files):
    devices, notes = set(), []
    for p in files:
        if p.name == "project.pbxproj":
            text = read_text(p) or ""
            for fam in re.findall(r'TARGETED_DEVICE_FAMILY = "?([\d,]+)"?;', text):
                devices.update(DEVICE_FAMILY.get(x, x) for x in fam.split(","))
            if re.search(r"SDKROOT = macosx", text) or "SUPPORTS_MACCATALYST = YES" in text:
                devices.add("Mac")
            if "SUPPORTS_MAC_DESIGNED_FOR_IPHONE_IPAD = YES" in text:
                notes.append("Runs on Mac as 'Designed for iPad' — Mac label may be declared separately")
            if "INFOPLIST_KEY_UIUserInterfaceStyle = Light" in text:
                notes.append(f"FORCED LIGHT MODE via build setting INFOPLIST_KEY_UIUserInterfaceStyle = Light ({p})")
    return sorted(devices), notes


def plist_findings(files, root):
    out = []
    for p in files:
        if p.suffix != ".plist" or p.name != "Info.plist":
            continue
        try:
            with open(p, "rb") as fh:
                data = plistlib.load(fh)
        except Exception:
            continue
        style = data.get("UIUserInterfaceStyle")
        if style == "Light":
            out.append(f"FORCED LIGHT MODE: UIUserInterfaceStyle = Light in {p.relative_to(root)}")
        elif style == "Dark":
            out.append(f"App is always dark: UIUserInterfaceStyle = Dark in {p.relative_to(root)}")
        if data.get("UIRequiresFullScreen"):
            out.append(f"UIRequiresFullScreen in {p.relative_to(root)}")
    return out


def colorset_findings(files):
    total = dark = high = 0
    for p in files:
        if p.name == "Contents.json" and p.parent.suffix == ".colorset":
            total += 1
            text = read_text(p) or ""
            if '"dark"' in text:
                dark += 1
            if '"high"' in text:
                high += 1
    return {"colorsets": total, "with_dark_variant": dark, "with_high_contrast_variant": high}


def scan(root: Path, extra_skip=()):
    files = list(walk(root, extra_skip))
    hits = defaultdict(lambda: {"count": 0, "samples": []})
    media_files, caption_files = [], []
    for path in files:
        ext = path.suffix.lower()
        if ext in MEDIA_EXT:
            media_files.append(str(path.relative_to(root)))
        if ext in CAPTION_EXT:
            caption_files.append(str(path.relative_to(root)))
        if ext not in CODE_EXT and path.name not in {"app.json", "app.config.js", "package.json", "pubspec.yaml"}:
            continue
        text = read_text(path)
        if not text:
            continue
        rel = str(path.relative_to(root))
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if len(line) > 600 or stripped.startswith(("//", "/*", "*")):
                continue
            for feature, key, _, rx, _ in COMPILED:
                if rx.search(line):
                    entry = hits[(feature, key)]
                    entry["count"] += 1
                    if len(entry["samples"]) < SAMPLES:
                        entry["samples"].append(f"{rel}:{lineno}: {line.strip()[:140]}")

    devices, device_notes = detect_devices(files)
    app_json = root / "app.json"
    if not devices and app_json.exists():
        # Expo managed apps have no Xcode project until prebuild.
        text = read_text(app_json) or ""
        devices = ["iPhone", "iPad"] if re.search(r'"supportsTablet"\s*:\s*true', text) else ["iPhone"]
        device_notes.append("Devices inferred from Expo app.json (ios.supportsTablet)")
    report = {
        "root": str(root),
        "scanned_files": len(files),
        "frameworks": detect_framework(root, files),
        "devices": devices or ["unknown (no Xcode project found)"],
        "notes": device_notes + plist_findings(files, root),
        "asset_colors": colorset_findings(files),
        "media_files": media_files[:20],
        "media_file_count": len(media_files),
        "caption_files": caption_files[:20],
        "features": {},
    }
    for feature, key, desc, _, kind in COMPILED:
        entry = hits.get((feature, key), {"count": 0, "samples": []})
        report["features"].setdefault(feature, []).append(
            {"key": key, "description": desc, "kind": kind, "count": entry["count"], "samples": entry["samples"]}
        )
    report["hints"] = hints(report)
    return report


def count(report, feature, key):
    return next(r["count"] for r in report["features"][feature] if r["key"] == key)


def hints(r):
    h = {}
    forced_light = any("FORCED LIGHT" in n for n in r["notes"]) or count(r, "dark_interface", "forced_light")
    h["dark_interface"] = (
        "Light mode is forced — fails unless a dark scheme is added." if forced_light
        else "No forced light mode found; check hard-coded white surfaces, launch screen, artwork, web views.")
    risks = sum(count(r, "larger_text", k) for k in ("fixed_font_swiftui", "fixed_font_custom", "fixed_font_uikit", "low_type_cap", "fixed_type_size", "rn_no_scaling", "flutter_no_scaling"))
    h["larger_text"] = (f"{risks} fixed/capped font sites — fix those, then test AX3/AX5." if risks
                        else "No fixed fonts found; still test AX3/AX5 for clipping and fixed heights.")
    triggers, guarded = count(r, "reduced_motion", "motion_triggers"), count(r, "reduced_motion", "reduce_motion_support")
    h["reduced_motion"] = (f"{triggers} motion-trigger sites, {guarded} Reduce Motion checks." if triggers
                           else "Few motion triggers found — likely Small effort.")
    has_video = count(r, "media", "video") > 0 or any(f.lower().endswith(VIDEO_EXT) for f in r["media_files"])
    has_audio = count(r, "media", "audio") > 0 or r["media_file_count"] > 0
    h["captions"] = ("Video found — Captions apply." if has_video
                     else "Audio found — Captions apply only if it contains speech/lyrics." if has_audio
                     else "No media found — likely Not applicable.")
    h["audio_descriptions"] = ("Video found — Audio Descriptions apply." if has_video
                               else "No video found — likely Not applicable.")
    h["voiceover"] = (f"{count(r, 'voiceover', 'a11y_api')} accessibility API uses, "
                      f"{count(r, 'voiceover', 'tap_gestures')} custom gestures, "
                      f"{count(r, 'voiceover', 'custom_canvas')} custom-drawn views. Claim only after a full walkthrough.")
    return h


def to_markdown(r):
    out = [f"# Accessibility scan: {r['root']}", "",
           f"**Framework:** {', '.join(r['frameworks'])}  ",
           f"**Files scanned:** {r['scanned_files']}  ",
           f"**Devices:** {', '.join(r['devices'])}  ",
           f"**Asset colours:** {r['asset_colors']['colorsets']} colorsets, "
           f"{r['asset_colors']['with_dark_variant']} with dark, "
           f"{r['asset_colors']['with_high_contrast_variant']} with high-contrast variants  ",
           f"**Media files:** {r['media_file_count']}  ",
           f"**Caption files:** {len(r['caption_files'])}", ""]
    if r["notes"]:
        out += ["## Notes"] + [f"- {n}" for n in r["notes"]] + [""]
    out += ["## Hints (triage — confirm in code)"] + [f"- **{k}**: {v}" for k, v in r["hints"].items()] + [""]
    icon = {"risk": "⚠️", "support": "✅", "info": "ℹ️"}
    for feature, rows in r["features"].items():
        out.append(f"## {feature}")
        for row in rows:
            out.append(f"- {icon[row['kind']]} {row['description']}: **{row['count']}**")
            out += [f"    - `{s}`" for s in row["samples"]]
        out.append("")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(__doc__)
        return 0 if len(argv) >= 2 else 2
    root = Path(argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2
    extra = ()
    if "--skip" in argv:
        extra = tuple(argv[argv.index("--skip") + 1].split(","))
    report = scan(root, extra)
    print(json.dumps(report, indent=2) if "--json" in argv else to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
