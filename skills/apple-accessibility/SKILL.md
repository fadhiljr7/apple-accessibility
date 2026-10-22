---
name: apple-accessibility
description: Audit any Apple-platform app (SwiftUI, UIKit, AppKit, React Native, Expo, Flutter, Unity, Capacitor, .NET MAUI) against Apple's Accessibility Nutrition Labels criteria (VoiceOver, Voice Control, Larger Text, Dark Interface, Differentiate Without Color Alone, Sufficient Contrast, Reduced Motion, Captions, Audio Descriptions), let the user pick which labels to implement, implement and verify them, and hand back exactly what to declare in App Store Connect → App Accessibility. Use whenever the user mentions accessibility nutrition labels, App Store accessibility, Dynamic Type, Dark Mode support, Reduce Motion, VoiceOver, contrast, or making an iOS/iPadOS/macOS/watchOS/tvOS/visionOS app accessible — including when it is just one skill in a list for building a new app. In that case it runs LAST, after every other task is finished, because it audits the finished app.
---

# Apple Accessibility

Turn any app headed for the App Store into one that can **honestly** claim Apple's Accessibility Nutrition Labels. Then tell the user exactly what to tick in App Store Connect.

The labels are a public promise on the product page. Apple's rule: *a label may be claimed only if users can complete **all common tasks** of the app with that feature on.* App Review can ask developers to correct misleading labels (Guideline 2.3). Every recommendation in this skill follows from that rule. Claim less and be right, rather than claim more and be wrong.

**Common tasks** = the app's primary functionality, plus the basics every app has: **first launch / onboarding, login, purchase, and settings**. Rare flows don't count. Third-party or user-generated content is out of scope unless a common task depends on it.

---

## 1. When to run: always last

This skill audits a *finished* app. If the user asks for it together with other work (e.g. *"build me a heart-rate app using apple-accessibility, skill X and skill Y"*):

1. Acknowledge it right away ("Accessibility pass will run once the app is built").
2. If there is a task list (update_plan / TodoWrite / similar), add **"Apple Accessibility pass"** as the **final** item.
3. Do all other work first: features, design, other skills, bug fixes.
4. Start Phase 2 below only when that work is done and the app builds.

Why last: an audit of a half-built app goes stale as soon as the next screen lands. Fixes made early also get overwritten by later feature work, and you would end up auditing twice.

If the skill is invoked on its own against an existing app, start immediately.

Talk to the user in **their** language (the examples here are in English; translate them).

---

## 2. Understand the app

Run the static scanner first. It is fast, and it orients you before you read code:

```bash
python3 <skill-dir>/scripts/scan_app.py <project-root>          # markdown report
python3 <skill-dir>/scripts/scan_app.py <project-root> --json   # machine-readable
```

It reports the framework, target devices, forced light mode, fixed font sizes, animation hotspots, media and web views, and existing accessibility APIs, with `file:line` samples. Treat it as **triage, not a verdict**. Confirm every finding by reading the code it points to.

Then establish:

- **Framework & UI layer.** Read `references/apple-native.md` for SwiftUI/UIKit/AppKit, or `references/cross-platform.md` for React Native, Expo, Flutter, Unity, Capacitor/Cordova, .NET MAUI, or web views.
- **Devices.** iPhone, iPad, Mac, Apple Watch, Apple TV, Vision Pro. Labels are declared **per device**, and some labels don't exist on some devices (see `references/criteria.md` § Availability). Only test devices the app ships on. If the app is iPhone-only, don't audit iPad.
- **Common tasks.** Write the list down explicitly (e.g. *Onboarding → Log a reading → View history → Settings → Paywall*). Every later judgement is "does this task pass?".
- **Media.** Is there video, spoken audio, cut scenes, or podcasts? If not, Captions and Audio Descriptions are **Not applicable**.

---

## 3. Audit all nine features

Read `references/criteria.md`. It holds Apple's criteria for each label, condensed, with pass/fail conditions. For each feature, decide one status:

| Status | Meaning |
|---|---|
| ✅ **Ready** | Already passes for every common task; only needs verification |
| 🟢 **Achievable** | Can pass after concrete work. Estimate the effort: Small / Medium / Large |
| 🟠 **Not recommended now** | Possible in principle, but the effort or risk is out of proportion (e.g. a full VoiceOver walkthrough of a gesture-heavy canvas app), or it can't be verified in this environment well enough to claim |
| ⚪ **Not applicable** | Doesn't apply to this app or device (e.g. Captions without any media) |

Back each status with evidence: specific screens, files, and what fails. Where you can, run the app in the simulator under stress settings (AX5 text, Dark Mode, Increase Contrast). Screenshots catch layout problems the code hides. See `references/verification.md`.

**Recommended** = every feature that is ✅ Ready or 🟢 Achievable.

**The two best** = the two Recommended features with the best ratio of *users helped* to *risk of not genuinely passing*. Rank them like this:

1. Highest confidence that it will truly pass in every common task after the work.
2. Smallest effort.
3. Widest reach, as a tie-breaker. Larger Text and Dark Interface help the most people. Reduced Motion and Sufficient Contrast are next.

Explain each pick in one line.

---

## 4. Show the summary, then let the user choose

First print a compact readiness summary so the choice is informed:

```
## Accessibility readiness: <App> (<devices>)

| Feature | Status | Work | Why |
|---|---|---|---|
| Dark Interface | ✅ Ready | verify | Semantic colours everywhere; onboarding checked dark |
| Reduced Motion | 🟢 Achievable | Small | 3 zoom/scale transitions need fade fallbacks |
| Larger Text | 🟢 Achievable | Medium | Onboarding and paywall clip at AX3; fixed 54pt buttons |
| Sufficient Contrast | 🟠 Not recommended | Large | Brand grey #93A4B8 is 2.5:1 on white across 30 screens |
| Captions | ⚪ N/A | – | No video or spoken audio |
...
**Recommended:** Dark Interface, Reduced Motion, Larger Text
**Best two:** Dark Interface (already passes) + Reduced Motion (small, low-risk)
```

Then ask with the **AskUserQuestion** tool. The user moves with the arrow keys, presses Enter, and the session carries straight on:

- **question:** "Which accessibility features should I implement? Choose Other to type your own selection."
- **header:** `A11y labels`
- **options** (in this order):
  1. **label** `All recommended (N)`. **description**: the Recommended feature names plus the total effort, e.g. "Dark Interface, Reduced Motion, Larger Text — about a medium amount of work".
  2. **label** `Best two`. **description**: the two names and why, e.g. "Dark Interface + Reduced Motion: fastest to genuinely pass".
- The tool adds an **Other** field automatically. That is the **custom** option, where the user types their own choice.

Edge cases:
- **The user already named features in their request** (e.g. "…with Larger Text and Dark Mode"): treat that as a custom choice. Still show the summary, validate their picks as below, and only ask if a pick needs a fallback or a clearly better option exists.
- **Only one** feature is Recommended: offer `Implement <feature>` and `Skip for now`.
- **None** are Recommended: say so plainly and offer best-effort improvements that won't be claimed (see §5).
- **No AskUserQuestion tool** (e.g. Claude.ai or a non-interactive run): print the same three choices as a numbered list and ask the user to reply with 1, 2, or their own selection.

### Handling a custom choice

Map what the user typed to the nine label names, in any language or phrasing ("dark mode" → Dark Interface, "dynamic type" / "font besar" → Larger Text, "screen reader" → VoiceOver). Then handle each requested feature:

- **It's in Recommended** → accept it.
- **It's 🟠 Not recommended** → explain the cost and risk in one or two sentences, then offer a **fallback**:
  - *Best-effort, unclaimed*: implement the clear wins (e.g. labels on icon-only buttons, decorative images hidden) but **don't** declare the label until a full audit passes.
  - *Swap*: replace it with the closest Recommended feature.
  - *Full effort*: do it anyway, if it's genuinely feasible here and the user accepts the larger scope.
- **It's ⚪ Not applicable** → it can't be claimed honestly. The fallback is to leave it unclaimed (or answer "No" for that device) and to say what would make it applicable later, e.g. "add captions when you add video".
- **It's not one of the nine labels** (e.g. Switch Control, haptics, Bold Text) → explain that it isn't a nutrition label. If it's cheap, offer to do it as an unclaimed bonus, or map it to the related label (Bold Text → part of Sufficient Contrast testing).

If any requested item needs a fallback, confirm the final set with one more AskUserQuestion (`Proceed with <final set>` / `Recommended only`), so the user never gets something they didn't agree to.

---

## 5. Implement

Work through the chosen features in this order. Small, contained work comes first, and later features build on earlier helpers:

**Reduced Motion → Dark Interface → Sufficient Contrast → Differentiate Without Color Alone → Larger Text → VoiceOver → Voice Control → Captions → Audio Descriptions**

Apple advises doing VoiceOver before Voice Control, because the labels and actions you add for VoiceOver also drive Voice Control.

Principles that made this work in real apps:

- **Build shared helpers before touching screens.** For example: one `withMotion` / motion-aware transition, one adaptive stack that becomes a column at accessibility sizes, one "scroll if needed" container, one contrast-aware palette. Then every screen adapts the same way instead of improvising. Before writing a new helper, check whether the project already has one (e.g. an existing `FlowLayout`).
- **Leave the default experience untouched.** At default text size, light mode, and no accessibility settings, the app should look exactly as designed. Adapt only when the setting is on. Check that with a regression screenshot at the end.
- **Replace meaningful motion, don't delete it.** A mood or state change becomes a cross-fade. Decorative loops stop. Small, user-triggered press feedback may stay.
- **Prefer wrapping to truncating.** Rows become columns, chips flow onto new lines, fixed heights become minimum heights, and fixed-height pages scroll. Content that truly can't scale (an exported image, a data grid, a tab bar) needs another way to be perceived, such as the Large Content Viewer or a detail view. Document those exceptions honestly.
- **Calculate contrast; don't eyeball it.** Use `scripts/contrast.py` with the worst-case backgrounds (darkest light background, lightest dark card). Aim a little above 4.5:1 for text and 3:1 for non-text state.
- **Respect the project's style.** Match its naming, file layout, comment density, and architecture.

Framework-specific code: `references/apple-native.md` or `references/cross-platform.md`.

---

## 6. Verify, and be honest about what wasn't verified

Follow `references/verification.md`:

1. Build Debug and Release with no new warnings.
2. Walk every common task on every shipped device under the relevant settings: AX3 and AX5 text, Dark + Increase Contrast, Reduce Transparency, Grayscale, and Reduce Motion. Take screenshots where visuals matter.
3. Run `performAccessibilityAudit()` in a UI test when the project has a UI test target (or can reasonably get one).
4. Take a regression screenshot at default settings.

Some things can't be seen in a simulator screenshot: motion, VoiceOver speech, Voice Control commands, captions timing. For those, say they were **verified in code only** and give the user a 1-minute on-device check. Never report a feature as verified when it wasn't.

---

## 7. Finish: summary and App Store Connect reminder

End with this structure, in the user's language:

```
## Accessibility: done

**Implemented & verified**
- Larger Text: <what changed, key helpers, the cap (≥ AX3), deliberate exceptions>
- Reduced Motion: <…> (verified in code; please check on device: Settings → Accessibility → Motion → Reduce Motion)

**Not claimed (and why)**
- VoiceOver: labels added to icon buttons, but no full walkthrough yet
- Captions / Audio Descriptions: not applicable, no media

### What to declare in App Store Connect
| Feature | iPhone | iPad |
|---|---|---|
| Larger Text | ✅ Yes | ✅ Yes |
| Dark Interface | ✅ Yes | ✅ Yes |
| VoiceOver | ⬜ Not yet | ⬜ Not yet |
| Captions | ⚪ N/A | ⚪ N/A |
…
Accessibility URL (optional): <suggestion, or "none yet">
```

Also:
- Add or update an **Accessibility** section in the project README: the table above, where each label is implemented, and the re-check commands. Future releases must re-verify, because Apple expects labels to stay accurate with every update.
- If the project has a website, **offer** to create an `/accessibility` page to use as the Accessibility URL (template in `references/app-store-connect.md`).

Then **always** close with the reminder from `references/app-store-connect.md` § Reminder. The user needs to save and publish the implemented features in **App Store Connect → Apps → (app) → App Accessibility** when uploading the app. Nothing in the code tells the App Store about them, so the labels only appear once the user declares them there.

---

## Reference files

| File | Read when |
|---|---|
| `references/criteria.md` | Phase 3, always. Apple's criteria per label, availability per device, pass/fail |
| `references/apple-native.md` | Implementing in SwiftUI / UIKit / AppKit |
| `references/cross-platform.md` | React Native, Expo, Flutter, Unity, Capacitor/Cordova, .NET MAUI, web views |
| `references/verification.md` | Phase 6. Simulator commands, test matrix, UI-test audit, honest reporting |
| `references/app-store-connect.md` | Phase 7. Declaring labels, Accessibility URL, the closing reminder |

| Script | Use |
|---|---|
| `scripts/scan_app.py <root> [--json]` | Static triage of any project |
| `scripts/contrast.py FG BG [...]` | WCAG contrast ratio, pass/fail, and a suggested passing colour |
| `scripts/sim_a11y.sh <cmd>` | Toggle simulator text size, appearance, and contrast; take screenshots |
