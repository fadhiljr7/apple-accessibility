# Apple Accessibility Nutrition Labels: Evaluation Criteria (condensed)

Source: App Store Connect Help → *Manage app accessibility* (developer.apple.com/help/app-store-connect/manage-app-accessibility/). This file condenses Apple's guidance. When something is ambiguous, re-read the source page for that label.

## Contents
- [Ground rules](#ground-rules)
- [Availability per device](#availability-per-device)
- [VoiceOver](#voiceover)
- [Voice Control](#voice-control)
- [Larger Text](#larger-text)
- [Dark Interface](#dark-interface)
- [Differentiate Without Color Alone](#differentiate-without-color-alone)
- [Sufficient Contrast](#sufficient-contrast)
- [Reduced Motion](#reduced-motion)
- [Captions](#captions)
- [Audio Descriptions](#audio-descriptions)

---

## Ground rules

- **Claim rule:** "users must be able to complete **all of the common tasks** of your app using that feature."
- **Common tasks:** the app's primary functionality, plus first launch experience, login, purchase, and settings. Tasks that are uncommon in your app don't need to be considered.
- **Third-party and user-generated content** is out of scope unless those views are part of common tasks.
- **Accuracy:** follow App Review Guideline 2.3 (accurate metadata). App Review can contact the developer about misleading labels. Developers must keep labels up to date and **re-evaluate with every update**.
- **Per device:** support is declared separately for each device (iPhone, iPad, Mac, …). A device with nothing declared shows "not indicated yet" on the product page.
- **In-app settings** count if they match the system setting's functionality or offer finer control. **System features like Zoom or Hover Text don't count.** Users already have them regardless of your app.
- **Apple frameworks are optional.** Any technology can pass if the user experience meets the criteria.
- Labels show on iOS/iPadOS/macOS/tvOS/visionOS/watchOS 26 or later. They are voluntary for now; Apple says they will become required for submissions over time.

## Availability per device

| Feature | iPhone | iPad | Mac | Apple Watch | Apple TV | Vision Pro |
|---|---|---|---|---|---|---|
| VoiceOver | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Voice Control | ✓ | ✓ | ✓ | – | – | ✓ |
| Larger Text | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| Dark Interface | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Differentiate Without Color Alone | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Sufficient Contrast | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reduced Motion | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Captions | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Audio Descriptions | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

(Voice Control: iOS, macOS, and visionOS only. Larger Text: not on Mac.)

---

## VoiceOver

**Goal:** a blind user can do every common task with VoiceOver alone. Anything that can be tapped, clicked, or dragged must also work with VoiceOver. Start the accessibility evaluation here; the same work also helps Voice Control, Switch Control, and Hover Text.

**Pass requires all of:**
1. **Labels.** Every control, icon, and meaningful image has a concise, accurate label that makes sense out of context ("New Message", not "Press to compose…"; not "Click here"). Repeated actions name their target ("Delete Blue Shirt"). Labels contain **no** control type or state ("checkbox", "checked"); express those with traits. Decorative images are hidden. Text fields have a label in addition to their value. Charts expose data through Audio Graphs / chart accessibility or a reasonable text alternative. If users can upload media, they can describe it.
2. **Type, state, and value are conveyed and kept current** through traits (button, selected, adjustable, header…). After toggling, the new state is announced.
3. **All visible text is speakable.** Custom keyboards and PIN pads are operable. Transient banners and alerts are announced (`AccessibilityNotification` / `UIAccessibility.post`) without disrupting the user.
4. **Navigation is complete and logical.** Every element is reachable forward and backward, with no skipping, looping, or traps. Grouped items are reachable individually, or their actions are exposed as custom actions. Background refreshes don't move the cursor. Screen changes and modals move focus into the new content. Hidden, offscreen, or background content is unreachable.
5. **Interactive elements are operable.** Double-tap / VO+Space does what a tap does. Long-press menus and swipe actions are available as **custom actions**. Modals trap focus and dismiss with the escape gesture (`accessibilityPerformEscape`). Drag-and-drop and multi-touch gestures have alternatives. Custom controls (sliders, tab bars, steppers) behave like the native ones (e.g. adjustable with swipe up/down).

**Fail if:** any common-task control is unlabeled or mislabeled, a gesture has no alternative, focus gets lost or lands on hidden content, or a custom control can't be operated.

**Practical note:** claiming VoiceOver needs a real **end-to-end walkthrough of every common task with VoiceOver on**. Adding labels in code alone isn't enough. If you can't do or witness that walkthrough, implement the improvements but mark the label *not yet claimed* and give the user a walkthrough checklist.

## Voice Control

**Goal:** a user with limited mobility can do every common task by voice ("Tap Compose", "Scroll down", "Show numbers").

**Pass requires:**
1. **Every tappable element can be activated.** "Show numbers" puts a number on every interactive element. "Show names" shows a name for each, and "Tap <name>" works.
2. **Names match visible text.** If a button reads "End call", its label must not be "Leave call". A mismatch counts as a failure. Add alternatives with `accessibilityInputLabels` (SwiftUI) / `accessibilityUserInputLabels` (UIKit).
3. **Complex interactions are reachable by voice.** Swipe-revealed or hover-revealed controls and long presses are exposed as custom actions ("Show actions for 4"). Scrolling, panning, and zooming work through commands. Recording can be started and stopped by voice.
4. **Text entry.** "Type …", "Select …", and "Delete that" work in every text field. Standard fields work automatically; custom ones need work.

**Recommended:** let users extend or cancel timers and auto-hide; consider App Intents / Siri. Do VoiceOver first.

## Larger Text

**Goal:** users can read and complete common tasks with large text, without Zoom or Hover Text.

**Pass requires:**
- Text can grow to **at least 200%** of the default size, or to the system maximum. On iOS, Dynamic Type passes 200% at **AX3** and goes past 300% for body text at **AX5**. Capping at AX3 or higher is acceptable. Capping lower fails.
- Text **and meaningful icons** in the primary views grow **without overlapping and without severe truncation**.
- Controls that can't reasonably scale stay perceivable another way. For example, tab bars and toolbars use the **Large Content Viewer**.
- Dynamic Type **or** an in-app text-size control that reaches equivalent sizes. Web views used in common tasks need a font-size control, or must let Safari handle the content.

**Layout guidance:** scale primary content first; navigation chrome (Back, Edit) can scale less. Make primary buttons full-width. Stack side-by-side items vertically. Wrap to two or more lines rather than truncate. If you must truncate, the full text must be available elsewhere (e.g. a detail view). Test small, medium, large, and extra-large accessibility sizes, longer languages, RTL, and scripts with tall ascenders and descenders.

**watchOS:** the maximum is about 140%. Support Dynamic Type or an equivalent size. **tvOS:** keep the hierarchy, and support the largest size or an equivalent.

**Fail if:** fixed font sizes in common tasks, overlapping text, text truncated to unreadable ("This is…", "…"), a page that can't scroll so content is cut off, or a cap below AX3.

## Dark Interface

**Goal:** light-sensitive users can keep the interface **dark throughout** common tasks. Even brief bright flashes count against it.

**Pass if** one of:
1. The app is **dark by default** in every common task (excluding third-party or UGC content), **or**
2. Users can turn on a dark mode that keeps it dark. In order of preference: the system **Dark Mode**, then a **custom dark scheme**, then, as a last resort, **Smart Invert** (images and media must not invert, and colours must not change meaning, e.g. a red Delete must not turn green).

**Check:** large white or bright areas (banners, artwork, web content, launch screen, sheets, alerts, onboarding, paywall), white flashes during transitions or loading, and contrast in dark mode (grey on black is a common mistake). Test **Dark + Increase Contrast** together. Translucency over the background is acceptable if the UI itself is dark; reduce translucency under Increase Contrast or Reduce Transparency.

**Fail if:** `UIUserInterfaceStyle = Light` or forced `.light` with no dark alternative, hard-coded white surfaces in common tasks, or a bright flash on launch or navigation.

## Differentiate Without Color Alone

**Goal:** colour is never the **only** carrier of meaning. Keep the colour, and add another cue.

**Pass if** common tasks never rely on colour alone. Status, selection, validity, value, and categories also use **text, icons, shapes, patterns, position, or order**. Example: a green ✓ in a circle vs. a red ✕ in an octagon. Charts keep legend order and label elements directly. If colour truly must be the only differentiator (e.g. colour-coded charts), users must be able to **customize colours or choose another scheme**.

**Test:** turn on the **Grayscale** colour filter (Settings → Accessibility → Display & Text Size → Color Filters). If the app is hard to use in grayscale, it fails. Respond to `accessibilityDifferentiateWithoutColor` for extra cues where useful. A colour setting is a stop-gap, not the main solution.

**Common failures:** red/green success/error states, online/offline dots, selected tab or chip shown only by tint, form errors shown only by a red border, heat maps or calendars with no labels.

## Sufficient Contrast

**Goal:** low-vision users (and anyone in bright sun) can read text and see controls.

**Thresholds** (WCAG formula): **text ≥ 4.5:1**, **non-text (controls, state indicators such as checked/selected/enabled) ≥ 3:1**. Apple gives no separate large-text threshold.

**Pass if** common-task UI meets these **by default**. **Or**, when the default doesn't meet them: with Apple UI frameworks, the **Increase Contrast** setting must bring it to sufficient contrast; with custom UI frameworks, users must be able to choose a colour scheme that meets the minimums.

**Test with** Bold Text + Increase Contrast + Reduce Transparency on, in light **and** dark, then Increase Contrast on with Reduce Transparency off. Include text over materials, blur, gradients, and images. Check checked vs. unchecked and selected vs. unselected states. Measure with Accessibility Inspector or `scripts/contrast.py`.

**Fail if:** secondary or placeholder text, disabled-looking active controls, or brand tints are below threshold, text sits over translucent or photo backgrounds with no scrim, or states differ only by subtle tint.

## Reduced Motion

**Goal:** people with motion sensitivity can do every common task without triggering motion.

**When Reduce Motion is on, these must be disabled or changed:** depth simulation (parallax, animated blur, depth-of-field), multi-axis motion, multi-speed motion, spinning, vortex effects, and generally **scaling and zooming** and large peripheral or full-screen movement. **Auto-advancing carousels and other ongoing motion** should stop, or have a control to stop them.

**For each remaining animation:**
- **Purely decorative** (floating, drifting backgrounds, particles, pulsing): stop it.
- **Conveys meaning** (status change, hierarchy, "added to cart"): **don't remove it**. Replace it with a dissolve, cross-fade, highlight fade, or colour shift.
- Small, user-initiated press feedback is generally fine.

**Don't over-correct.** Removing all animation hurts comprehension.

**Fail if:** zoom or scale transitions, springs with large travel, spinning loaders that could be static, auto-playing carousels, or parallax remain with the setting on, or meaningful transitions are removed with no replacement.

## Captions

**Applies only if** the app has video, spoken audio, game interstitials or cut scenes with dialogue, or audio-only spoken content.

**Pass if:**
- Captions are **on by default when the system captions setting is on** (Settings → Accessibility → Subtitles & Captioning → Closed Captions + SDH). An in-app setting must match or exceed it.
- Video (including interstitials and cut scenes outside a standard player) has captions or subtitles. Dialogue subtitles are enough; CC/SDH with non-speech sounds ("[doorbell rings]") is preferred.
- Audio-only speech (podcasts, lyrics) has transcripts. These don't need to be time-synced.
- For third-party media, users can see which items are captioned (a CC/SDH badge, a language list).

**Fail if:** the caption feature exists but little or no content is captioned, or users can't tell what is captioned.
**Not applicable:** no video and no spoken audio. Pure music or ambient sound with no lyrics or speech = N/A.

## Audio Descriptions

**Applies only if** the app has video or time-based visual content: movies, TV, opening sequences, cut scenes, or visual-only tips.

**Pass if:**
- An audio description track is **selected by default when the system Audio Descriptions setting is on**. An in-app setting must match or exceed it.
- Video, interstitials, cut scenes, and visual-only hints have narrated descriptions.
- For third-party media, users can see which items are described (an AD badge).

**Fail if:** AD selection exists but little or no described content is available.
**Not applicable:** no video or time-based visual content.
