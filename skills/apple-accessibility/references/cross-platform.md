# Implementing the labels in cross-platform and non-native stacks

The criteria are the same for every technology (`criteria.md`). Only the APIs differ. Whatever the stack, the iOS shell still matters: check `Info.plist` (`UIUserInterfaceStyle`), the launch screen, and any native screens.

## Contents
- [React Native / Expo](#react-native--expo)
- [Flutter](#flutter)
- [Unity](#unity)
- [Web views, Capacitor, Cordova, Ionic](#web-views-capacitor-cordova-ionic)
- [.NET MAUI](#net-maui)
- [Other (Compose Multiplatform, Godot, custom engines)](#other)

---

## React Native / Expo

| Label | How |
|---|---|
| Reduced Motion | `AccessibilityInfo.isReduceMotionEnabled()` + `addEventListener('reduceMotionChanged', …)`. Reanimated: `useReducedMotion()`, or `.reduceMotion(ReduceMotion.System)` on animations. Replace scale/slide `LayoutAnimation`s and `Animated` springs with an opacity fade; stop looping Lottie (`autoPlay={!reduceMotion}`). |
| Dark Interface | `useColorScheme()`; colours via `PlatformColor('systemBackground')` or `DynamicColorIOS({ light, dark })`. **Expo:** `app.json` → `"userInterfaceStyle": "automatic"`. Templates often ship `"light"`, which writes `UIUserInterfaceStyle = Light` and fails the label. Also set a dark splash (`expo-splash-screen` `dark` config) and navigation theme (`DarkTheme`). |
| Sufficient Contrast | `DynamicColorIOS({ light, dark, highContrastLight, highContrastDark })` responds to Increase Contrast. `AccessibilityInfo.isReduceTransparencyEnabled()` → replace `BlurView` with opaque fills. |
| Differentiate | Design cues (icons, text). `AccessibilityInfo.isGrayscaleEnabled()` exists but don't rely on it; build the cues in by default. |
| Larger Text | RN scales `fontSize` with Dynamic Type by default. Failures come from `allowFontScaling={false}`, `maxFontSizeMultiplier` below ~2 (AX3 is ≈2.35× body), fixed `height`s, and `numberOfLines={1}`. Use `useWindowDimensions().fontScale` (≥ 1.8 ≈ accessibility sizes) to switch `flexDirection: 'row'` → `'column'` and to wrap screens in `ScrollView`. |
| VoiceOver | `accessible`, `accessibilityLabel`, `accessibilityRole` (`button`, `header`, `adjustable`, …), `accessibilityState` (`{ selected, checked, disabled }`), `accessibilityValue`, `accessibilityActions` + `onAccessibilityAction` (custom and `increment`/`decrement`/`escape`/`magicTap`), `accessibilityElementsHidden` / `importantForAccessibility="no-hide-descendants"`, `accessibilityViewIsModal`, `AccessibilityInfo.announceForAccessibility()`, `AccessibilityInfo.setAccessibilityFocus()`. `Pressable` without a label is a common failure. |
| Voice Control | Labels must match visible text. Expose swipe-row actions via `accessibilityActions`. |
| Captions | `react-native-video`: `textTracks` + `selectedTextTrack={{ type: 'system' }}` follows the system caption preference. `expo-video`: provide subtitle tracks in the HLS/asset and verify they show with the system setting on. Transcripts for audio-only speech. |
| Audio Descriptions | Provide AD audio tracks in HLS (`CHARACTERISTICS="public.accessibility.describes-video"`). Native AVPlayer selection honours the system setting. |

## Flutter

| Label | How |
|---|---|
| Reduced Motion | `MediaQuery.disableAnimationsOf(context)` reflects iOS Reduce Motion. Swap `Hero`, scale/slide `PageRouteBuilder` transitions, and `AnimatedScale`/rotation for `FadeTransition`; stop `repeat()`ing controllers and Rive/Lottie loops. |
| Dark Interface | `MaterialApp(theme:, darkTheme:, themeMode: ThemeMode.system)`; Cupertino: `CupertinoDynamicColor`. Avoid literal `Colors.white` surfaces. Dark launch screen in `ios/Runner/Base.lproj/LaunchScreen.storyboard`, or an asset colour with a dark variant. |
| Sufficient Contrast | `MaterialApp(highContrastTheme:, highContrastDarkTheme:)` engages with Increase Contrast; `MediaQuery.highContrastOf(context)`. `CupertinoDynamicColor.withBrightnessAndContrast(…)`. |
| Differentiate | Design cues; charts (`fl_chart` etc.) need labels or markers per series. |
| Larger Text | Text scales via `MediaQuery.textScalerOf`. Failures: `TextScaler.noScaling`, `textScaleFactor: 1.0`, `MediaQuery.withClampedTextScaling(maxScaleFactor: < 2.0)`, fixed `SizedBox(height:)` around text, `maxLines: 1` + `overflow: ellipsis` on key text. Switch `Row` → `Column` when `textScaler.scale(16) / 16 >= 1.8`; wrap with `SingleChildScrollView`; use `Wrap` for chips. |
| VoiceOver | `Semantics(label:, button: true, header: true, value:, onTap:)`, `MergeSemantics`, `ExcludeSemantics` for decoration, `IconButton(tooltip:)` (the tooltip becomes the label), `Semantics(customSemanticsActions: {…})`, `SemanticsService.announce(...)`, `BlockSemantics` for modals. Custom-painted widgets (`CustomPaint`) are invisible to VoiceOver until wrapped in `Semantics`. |
| Voice Control | Same semantics labels; match the visible text. |
| Captions | `video_player`: `closedCaptionFile` / embedded captions. Read the system preference through a small platform channel (`UIAccessibility.isClosedCaptioningEnabled`) so captions are on by default. |
| Audio Descriptions | Native player track selection via a platform view or channel. |

## Unity

- Use Apple's open-source **Unity plug-ins** (`github.com/apple/unityplugins`), specifically the **Apple.Accessibility** package. It exposes accessibility elements (`AccessibilityNode`: label, traits, value, actions) to VoiceOver and Voice Control, and reads system settings (Reduce Motion, preferred text size, Increase Contrast, Differentiate Without Color, captions).
- Larger Text: scale UI text (TextMeshPro) from the preferred content size, or offer an in-game text-size setting that reaches ≥ 200%.
- Reduced Motion: disable camera shake, parallax, screen-space bloom pulses, and spinning UI; offer an in-game "Reduce motion" toggle that defaults to the system value.
- Captions/AD: cut scenes and dialogue need subtitles, on by default when the system captions setting is on; describe visual-only hints.
- Dark Interface: many games are dark by default. Check menus, the store, and loading screens for bright flashes.

## Web views, Capacitor, Cordova, Ionic

If common tasks render in a `WKWebView`, the **web content** must meet the criteria:

- Dynamic Type: set `html { font: -apple-system-body; }` and size everything in `rem`/`em`. WebKit then follows the iOS text size. Alternatively, provide an in-app font-size control.
- Dark: `@media (prefers-color-scheme: dark)` plus `<meta name="color-scheme" content="light dark">`; set the web view's background to dark (`isOpaque = false`) to avoid white flashes while loading.
- Contrast: `@media (prefers-contrast: more)`.
- Motion: `@media (prefers-reduced-motion: reduce)` disables transforms, parallax, smooth-scroll, and auto-carousels.
- VoiceOver/Voice Control: semantic HTML, `<button>` not `<div onclick>`, `aria-label`, `alt`, `aria-live` for status, focus management for modals (`inert`, `<dialog>`).
- Captions: `<track kind="captions" default>`; native fullscreen video uses the system caption style.

## .NET MAUI

- VoiceOver: `SemanticProperties.Description`, `.Hint`, `.HeadingLevel`; `AutomationProperties.IsInAccessibleTree="False"` for decoration; `SemanticScreenReader.Announce()`.
- Larger Text: `FontAutoScalingEnabled` (default true). Don't disable it on key text; avoid fixed `HeightRequest` on text containers.
- Dark: `AppThemeBinding` / `Application.Current.UserAppTheme = AppTheme.Unspecified`.
- Reduce Motion / Increase Contrast: read `UIKit.UIAccessibility.IsReduceMotionEnabled` / `DarkerSystemColorsEnabled` in iOS platform code and expose them to shared code.

## Other

Compose Multiplatform, Godot, Kotlin/Native UI, and custom engines: find how the framework maps to UIKit accessibility (`UIAccessibilityElement`) and to system settings. If it can't expose elements to VoiceOver or follow Dynamic Type, classify those labels as 🟠 Not recommended, and say why, rather than claiming them.
