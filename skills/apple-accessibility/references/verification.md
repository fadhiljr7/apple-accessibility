# Verification

The goal is evidence, not optimism. For every claimed label, every common task, on every shipped device: did you **see** it pass, or only **reason** that it should? Report which one honestly.

## Contents
- [Test matrix](#test-matrix)
- [Simulator settings](#simulator-settings)
- [Screens to capture](#screens-to-capture)
- [Automated audit in UI tests](#automated-audit-in-ui-tests)
- [What can't be verified in a simulator](#what-cant-be-verified-in-a-simulator)
- [Re-check commands for the README](#re-check-commands-for-the-readme)

---

## Test matrix

| Label | Settings to turn on | What to look for |
|---|---|---|
| Larger Text | text size **AX3** (`accessibility-extra-large`) and **AX5** (`accessibility-extra-extra-extra-large`) | no clipping, no overlap, no "…" in key text, everything reachable by scrolling, icons scale |
| Dark Interface | Dark appearance (+ Increase Contrast) | no white or bright surfaces, no flash on launch, sheets, web views, or loading |
| Sufficient Contrast | Increase Contrast, Reduce Transparency, Bold Text, in light **and** dark | text ≥ 4.5:1, state indicators ≥ 3:1, opaque cards where needed |
| Differentiate | Color Filters → **Grayscale** | every status or selection still distinguishable |
| Reduced Motion | Reduce Motion | no zoom, scale, spin, parallax, or auto-carousel; meaningful changes still visible as fades |
| VoiceOver | VoiceOver | full walkthrough of each common task forwards and backwards; labels, traits, actions, focus |
| Voice Control | Voice Control | "Show numbers", "Show names", "Tap <name>" on each control; "Type …" in fields |
| Captions | Closed Captions + SDH | captions visible by default on all media in common tasks |
| Audio Descriptions | Audio Descriptions | AD track selected by default |

Finish with a **regression pass at default settings**. The design must look unchanged.

## Simulator settings

`scripts/sim_a11y.sh` wraps these (`stress`, `reset`, `size`, `dark`, `light`, `contrast`, `shot`):

```bash
xcrun simctl ui booted content_size accessibility-extra-large             # AX3
xcrun simctl ui booted content_size accessibility-extra-extra-extra-large # AX5
xcrun simctl ui booted appearance dark
xcrun simctl ui booted increase_contrast enabled
xcrun simctl io booted screenshot shot.png
```

- **Reduce Motion, Reduce Transparency, Bold Text, Grayscale, VoiceOver** have no `simctl ui` switch. Toggle them in the simulator's **Settings → Accessibility** app (drive it with the iOS Simulator tool if available), or with Xcode → Open Developer Tool → **Accessibility Inspector** → Settings while it targets the simulator.
- **Per-app text size without changing the device:** launch with `-UIPreferredContentSizeCategoryName UICTContentSizeCategoryAccessibilityXL` (AX3) or `…AccessibilityXXXL` (AX5). This is handy in UI tests and `simctl launch`.
- **Reaching deep screens:** if the app has debug launch arguments or deep links (e.g. an onboarding-step flag), use them to capture each screen quickly. Read the code for the exact name before relying on one.
- If the app is iPhone-only, don't test iPad, and vice versa. Labels are per device.
- Build first: `xcodebuild -scheme <Scheme> -destination 'platform=iOS Simulator,name=<Device>' build`. Then install and launch with `xcrun simctl install booted <App.app>` and `xcrun simctl launch booted <bundle id>`. Use the project's existing build tooling if it has one.

## Screens to capture

At minimum, for each shipped device, capture each common task screen under its relevant setting:

1. First launch / onboarding (every page)
2. Main screen(s) of the primary task, scrolled to the bottom
3. Create/edit flows and their sheets
4. Login / sign-up (if any)
5. Paywall / purchase (if any)
6. Settings
7. Alerts, empty states, error states

Read each screenshot. Don't assume a build that compiles looks right.

## Automated audit in UI tests

On iOS 17+, `XCUIApplication.performAccessibilityAudit()` catches missing labels, clipped text, low contrast, small hit regions, and Dynamic Type problems on the current screen:

```swift
func testAccessibilityAudit() throws {
    let app = XCUIApplication()
    app.launchArguments += ["-UIPreferredContentSizeCategoryName",
                            "UICTContentSizeCategoryAccessibilityXL"]
    app.launch()
    try app.performAccessibilityAudit()                       // all audit types
    // Navigate to each common-task screen and audit again.
    // Narrow with: try app.performAccessibilityAudit(for: [.dynamicType, .contrast, .textClipped])
}
```

Audit types: `.contrast`, `.elementDetection`, `.hitRegion`, `.sufficientElementDescription`, `.dynamicType`, `.textClipped`, `.trait`, `.action`, `.parentChild`. A failing audit is a lead to investigate; some issues are false positives (e.g. intentional decorative contrast). Passing the audit is **not** the same as passing Apple's criteria. A human walkthrough is still the bar for VoiceOver and Voice Control.

Add a UI test target only if the project already has one or the user agrees. Don't restructure their project uninvited.

## What can't be verified in a simulator

Be explicit in the summary about anything only verified in code:

- **Motion.** Screenshots don't show animation. Verify in code, then give the user a 1-minute device check: *Settings → Accessibility → Motion → Reduce Motion on → open <screens>; nothing should zoom, spin, or slide*.
- **VoiceOver / Voice Control.** Speech and voice commands need a real walkthrough. If nobody has walked every common task, the label stays *not yet claimed*.
- **Captions and AD timing.** Play the media with the system settings on.
- **Real-device-only features** (Live Activities, widgets, HealthKit data, camera): note any common task that depends on them.

## Re-check commands for the README

Write a short block like this into the app's README Accessibility section, so the next release can re-verify:

```bash
xcrun simctl ui booted content_size accessibility-extra-large
xcrun simctl ui booted appearance dark
xcrun simctl ui booted increase_contrast enabled
# then: Settings → Accessibility → Motion → Reduce Motion, and Display → Color Filters → Grayscale
```
