# Implementing the labels in SwiftUI, UIKit and AppKit

Patterns that have shipped in real apps. Adapt names to the project; don't copy blindly. Check first whether the project already has an equivalent helper.

## Contents
- [Shared helpers file](#shared-helpers-file)
- [Reduced Motion](#reduced-motion)
- [Dark Interface](#dark-interface)
- [Sufficient Contrast](#sufficient-contrast)
- [Differentiate Without Color Alone](#differentiate-without-color-alone)
- [Larger Text](#larger-text)
- [VoiceOver](#voiceover)
- [Voice Control](#voice-control)
- [Captions & Audio Descriptions](#captions--audio-descriptions)
- [UIKit equivalents](#uikit-equivalents)
- [AppKit (Mac)](#appkit-mac)

---

## Shared helpers file

Put the cross-cutting helpers in one file, e.g. `Support/AccessibilityLayout.swift`, so every screen adapts the same way. A header comment explaining *why* the file exists helps the next developer.

## Reduced Motion

```swift
import SwiftUI
import UIKit

/// `withAnimation`, except springs and bounces become a short cross-fade
/// when Reduce Motion is on. Reads the system setting directly, so it also
/// works from view models.
@discardableResult
func withMotion<Result>(_ animation: Animation = .default,
                        _ body: () throws -> Result) rethrows -> Result {
    try withAnimation(UIAccessibility.isReduceMotionEnabled
                      ? .easeInOut(duration: 0.2) : animation, body)
}

extension Animation {
    static func motionAware(_ animation: Animation, reduceMotion: Bool) -> Animation {
        reduceMotion ? .easeInOut(duration: 0.2) : animation
    }
}

extension AnyTransition {
    /// The given transition normally; a plain fade under Reduce Motion.
    static func motionAware(_ transition: AnyTransition, reduceMotion: Bool) -> AnyTransition {
        reduceMotion ? .opacity : transition
    }
}

/// Full-screen zoom transitions are exactly the depth effect Reduce Motion
/// exists to remove, so fall back to the standard push/present.
struct ZoomUnlessReduced: ViewModifier {
    let sourceID: AnyHashable
    let namespace: Namespace.ID
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func body(content: Content) -> some View {
        if reduceMotion { content }
        else { content.navigationTransition(.zoom(sourceID: sourceID, in: namespace)) }
    }
}
```

Checklist. Grep for these and decide *stop*, *replace with fade*, or *keep* for each:
- `withAnimation(.spring…)`, `.animation(.spring…)` → `withMotion` / `.motionAware`
- `.transition(.scale / .slide / .move…)` → `.motionAware(…)`
- `.scaleEffect`, `.rotationEffect`, `.rotation3DEffect` driven by state or loops → hold still or fade
- `.repeatForever` (breathing, floating, pulsing, shimmer), particles, drifting gradients, `TimelineView` animations → stop (render a still frame)
- `matchedGeometryEffect`, `.navigationTransition(.zoom…)` → standard transition
- `.symbolEffect(.bounce / .pulse / .variableColor…)` → pass `isActive: !reduceMotion`, or drop it
- Auto-advancing carousels → stop auto-advance
- Parallax / `UIInterpolatingMotionEffect` → don't add under Reduce Motion
- Lottie / SpriteKit / SceneKit / RealityKit → pause, or show a static frame
- Meaningful state changes (mood, progress, selection) → cross-fade, never delete

## Dark Interface

- Use semantic colours (`Color(.systemBackground)`, `.primary`, `.secondary`, `Color(.secondarySystemBackground)`) or asset-catalog colours with **Any / Dark** appearances. Hard-coded `.white` surfaces, `Color(red:green:blue:)` and hex colours are the usual leaks.
- Remove `UIUserInterfaceStyle = Light` from Info.plist and `.preferredColorScheme(.light)` / `overrideUserInterfaceStyle = .light`, unless the app provides its own dark scheme.
- **Launch screen:** give the `UILaunchScreen` background colour a dark variant, or users get a white flash on every cold start.
- **Bright artwork/banners:** dim them in dark mode so a sunlit photo isn't the brightest thing on screen:

```swift
@Environment(\.colorScheme) private var colorScheme
// …
image.overlay(Color.black.opacity(colorScheme == .dark ? 0.25 : 0))
```

- Check sheets, alerts, onboarding, the paywall, web views (`WKWebView` needs `prefers-color-scheme` CSS in the page, and `isOpaque = false` + a dark `backgroundColor` to avoid a white flash), PDFs, and empty states.
- Test **Dark + Increase Contrast**. Grey-on-black text often fails.

## Sufficient Contrast

Approach used successfully: keep the brand palette by default, and push colours to ≥ 4.5:1 (text) and ≥ 3:1 (non-text) when **Increase Contrast** is on. Make cards opaque under Increase Contrast or Reduce Transparency.

```swift
@Environment(\.colorSchemeContrast) private var contrast          // .standard / .increased
@Environment(\.accessibilityReduceTransparency) private var reduceTransparency

var cardBackground: some ShapeStyle {
    (contrast == .increased || reduceTransparency)
        ? AnyShapeStyle(Color(.secondarySystemBackground))
        : AnyShapeStyle(.ultraThinMaterial)
}
```

- Asset catalog colours: tick **High Contrast** in the attributes inspector and give each colour a high-contrast variant (light and dark).
- For computed palettes, compute the adjusted colour instead of guessing. Mix toward white or black in 1% steps until the ratio clears the target against the **worst-case background** (the darkest light background and the lightest dark card the colour can appear on). `scripts/contrast.py FG BG --target 4.8` prints such a suggestion. Aim slightly above 4.5 for margin.
- Watch for: `.secondary` / `.opacity(0.4)` text on tinted cards, placeholder text, text on photos (add a scrim), white text on light brand colours, selected vs. unselected states that differ only by a faint tint.
- If the default palette already passes everywhere, no runtime switching is needed. Say so in the summary.

## Differentiate Without Color Alone

```swift
@Environment(\.accessibilityDifferentiateWithoutColor) private var differentiate

Label(isOnline ? "Online" : "Offline",
      systemImage: isOnline ? "checkmark.circle.fill" : "xmark.octagon.fill")
    .foregroundStyle(isOnline ? .green : .red)
```

- Every status or selection carries a **shape, icon, text, or position** cue. Example: a selected chip also gets a checkmark or bold weight, not only a tint.
- Form errors: an icon plus a message, not only a red border.
- Charts (Swift Charts): use `.symbol(by:)` / `.lineStyle(by:)` / direct annotations alongside `.foregroundStyle(by:)`; keep legend order equal to series order.
- Calendars and heat maps: add numbers, glyphs, or patterns when `differentiate` is true. Grayscale is the test.

## Larger Text

Foundation (from shipped apps):

```swift
/// Layouts are designed and verified up to AX3 (>200%, Apple's bar).
/// Cap here only if something truly can't go further; never below AX3.
extension View {
    func appTypeScale() -> some View { dynamicTypeSize(...DynamicTypeSize.accessibility3) }
}
// Apply at every scene root AND every .sheet / .fullScreenCover root:
// presented views take the system size directly.

/// Row normally, column at accessibility sizes.
struct AdaptiveStack<Content: View>: View {
    var horizontalAlignment: HorizontalAlignment = .leading
    var verticalAlignment: VerticalAlignment = .center
    var spacing: CGFloat?
    @ViewBuilder var content: () -> Content
    @Environment(\.dynamicTypeSize) private var typeSize

    var body: some View {
        let layout = typeSize.isAccessibilitySize
            ? AnyLayout(VStackLayout(alignment: horizontalAlignment, spacing: spacing))
            : AnyLayout(HStackLayout(alignment: verticalAlignment, spacing: spacing))
        layout(content)
    }
}

/// Exactly as designed when it fits; scrolls when larger text makes it too
/// tall (onboarding, paywalls, fixed-height pages).
struct ScrollIfNeeded<Content: View>: View {
    @ViewBuilder var content: () -> Content
    var body: some View {
        ViewThatFits(in: .vertical) {
            content()
            ScrollView { content().padding(.vertical, 8) }
                .scrollBounceBehavior(.basedOnSize)
        }
    }
}

/// Segmented controls don't grow; at accessibility sizes use a menu instead.
struct AdaptiveSegmentedPickerStyle: ViewModifier {
    @Environment(\.dynamicTypeSize) private var typeSize
    func body(content: Content) -> some View {
        if typeSize.isAccessibilitySize { content.pickerStyle(.menu) }
        else { content.pickerStyle(.segmented) }
    }
}
```

Also add a `FlowLayout: Layout` for chip rows that should wrap. It lays children out left to right and starts a new line when the next child doesn't fit.

Fix list. Grep for each:
- `.font(.system(size: N))` → a text style (`.body`, `.headline`, …). To keep a custom size, scale it: `@ScaledMetric(relativeTo: .body) var size: CGFloat = N` + `.font(.system(size: size))`. `Font.custom(name, size:)` already scales (relative to body; pass `relativeTo:` to pick a style). `Font.custom(name, fixedSize:)` never scales.
- `.frame(height: N)` on anything containing text → `minHeight:`; fixed `width:` on text → let it grow.
- `.lineLimit(1)` on important text → remove, or `lineLimit(1...3)`. `minimumScaleFactor` is not a fix; text shrinking back defeats the setting.
- Icons beside text: `@ScaledMetric(relativeTo: .body) var iconSize: CGFloat = 24`.
- Side-by-side label + value, or label + control → `AdaptiveStack`, or move the label above the control.
- Fixed-size grids of cards → `LazyVGrid(columns: [GridItem(.adaptive(minimum: scaledMin))])`; on iPad, drop to one column at accessibility sizes.
- Tab bars and toolbars don't scale: system tab bars get the Large Content Viewer for free. For custom bars, add `.accessibilityShowsLargeContentViewer()` with a label.
- Exported images, data grids, and other content that legitimately stays fixed: document it as an exception and make sure the information is available as text elsewhere.
- Truncation is acceptable only if the full text is reachable (e.g. a detail screen).

## VoiceOver

```swift
Button { delete(item) } label: { Image(systemName: "trash") }
    .accessibilityLabel("Delete \(item.name)")              // target named, no "button"

Image("hero-wave").accessibilityHidden(true)                // decorative
// or Image(decorative: "hero-wave")

HStack { Image(systemName: "flame"); Text("12"); Text("day streak") }
    .accessibilityElement(children: .combine)              // one stop: "12 day streak"

Text("Settings").accessibilityAddTraits(.isHeader)

// Custom control → behave like a native slider
Fader(value: $volume)
    .accessibilityRepresentation { Slider(value: $volume, in: 0...1) { Text("Rain volume") } }
// or
    .accessibilityValue("\(Int(volume * 100)) percent")
    .accessibilityAdjustableAction { dir in volume += (dir == .increment ? 0.1 : -0.1) }

// Swipe / long-press actions as custom actions
row.accessibilityAction(named: "Mark complete") { complete(item) }

// Transient status
AccessibilityNotification.Announcement("Saved").post()

// Charts
Chart(data) { … }.accessibilityChartDescriptor(self)   // or per-mark .accessibilityLabel/.accessibilityValue
```

- `.onTapGesture` on a non-Button view → make it a `Button`, or add `.accessibilityAddTraits(.isButton)` + a label.
- Drag-only interactions → add actions (`.accessibilityAction`) or an adjustable action.
- Modals and overlays: `.accessibilityAddTraits(.isModal)` on custom overlays; dismiss via `.accessibilityAction(.escape) { … }`.
- Reading order: `.accessibilitySortPriority`. Move focus on screen change with `@AccessibilityFocusState`.
- Don't label things with their type or state ("checkbox, checked"). Use traits (`.isSelected`, `.isToggle`).

## Voice Control

- Visible text is the command. Keep the accessibility label **matching or starting with** the visible text.
- Icon-only buttons need a short label users would say ("Add", "Share", "Filter").
- Add synonyms: `.accessibilityInputLabels(["End call", "Hang up"])` (the first one is shown by "Show names").
- Swipe-to-delete and long-press menus → custom actions (Voice Control shows them with a double chevron).
- Custom text inputs must accept dictation and select/delete. Standard `TextField` / `TextEditor` already do.
- Timers that auto-dismiss content should be extendable or cancellable.

## Captions & Audio Descriptions

- `AVPlayer` / `VideoPlayer` / `AVPlayerViewController` apply the user's caption and AD preferences automatically when `player.appliesMediaSelectionCriteriaAutomatically` is `true` (the default) and the asset contains legible tracks (WebVTT in HLS, CEA-608/708, or embedded tx3g) or AD audio tracks tagged `public.accessibility.describes-video`.
- Custom players: read `UIAccessibility.isClosedCaptioningEnabled` (and observe `closedCaptioningStatusDidChangeNotification`), or `MACaptionAppearanceGetDisplayType(.user)`. Select a legible option with `AVMediaSelectionGroup` + `.legible`. For AD, check `MAAudibleMediaCopyPreferredCharacteristics()` for `.describesVideoForAccessibility`.
- Game cut scenes and interstitials outside a player need their own subtitle rendering, on by default when the system setting is on.
- Audio-only speech (podcasts, guided meditations) → a transcript screen. It doesn't need to be time-synced.
- Third-party catalogues → show **CC** / **AD** badges and the available languages.

## UIKit equivalents

| Need | UIKit |
|---|---|
| Reduce Motion | `UIAccessibility.isReduceMotionEnabled`, `reduceMotionStatusDidChangeNotification` |
| Dynamic Type | `UIFont.preferredFont(forTextStyle:)` or `UIFontMetrics(forTextStyle:).scaledFont(for:)` + `adjustsFontForContentSizeCategory = true`; `numberOfLines = 0` |
| Accessibility size check | `traitCollection.preferredContentSizeCategory.isAccessibilityCategory` → switch `UIStackView.axis` to `.vertical` |
| Cap size | `view.maximumContentSizeCategory = .accessibilityExtraLarge` (AX3) |
| Large Content Viewer | `UILargeContentViewerInteraction`, `showsLargeContentViewer = true`, `largeContentTitle/Image` |
| Contrast | `UIColor { $0.accessibilityContrast == .high ? … : … }`, `UIAccessibility.isDarkerSystemColorsEnabled`, `isReduceTransparencyEnabled` |
| Colour cue | `UIAccessibility.shouldDifferentiateWithoutColor` |
| Labels/traits | `accessibilityLabel`, `accessibilityTraits`, `isAccessibilityElement`, `accessibilityElementsHidden`, `accessibilityViewIsModal` |
| Actions | `accessibilityCustomActions = [UIAccessibilityCustomAction(name:actionHandler:)]`, `accessibilityPerformEscape()` |
| Voice Control | `accessibilityUserInputLabels` |
| Announce | `UIAccessibility.post(notification: .announcement, argument: "Saved")`; `.screenChanged` / `.layoutChanged` to move focus |
| Dark | dynamic `UIColor`s / asset colours; `traitCollectionDidChange` or `registerForTraitChanges` for CGColor layers |

## AppKit (Mac)

- Larger Text **isn't a Mac label**. Skip it.
- Settings: `NSWorkspace.shared.accessibilityDisplayShouldReduceMotion`, `…ShouldIncreaseContrast`, `…ShouldDifferentiateWithoutColor`, `…ShouldReduceTransparency`. Observe `NSWorkspace.accessibilityDisplayOptionsDidChangeNotification`.
- Dark: semantic `NSColor` (`.windowBackgroundColor`, `.labelColor`); `NSAppearance` drives appearance.
- VoiceOver/Voice Control: `setAccessibilityLabel`, `setAccessibilityRole`; every action must also be reachable by keyboard (Tab, arrow keys) with VoiceOver on.
