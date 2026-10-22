# Declaring the labels in App Store Connect

Source: App Store Connect Help → *Manage Accessibility Nutrition Labels*.

## Who can do it
Account Holder, Admin, Finance, App Manager, or Marketing role.

## First-time setup
1. **App Store Connect → Apps →** select the app.
2. In the sidebar, click **App Accessibility**.
3. Click **Get Started**.
4. Confirm the devices. If the latest version is live (or the app supports only one device), devices are detected automatically. If a version is still editable (e.g. *Prepare for Submission*), select the devices, then **Save**.
5. Click **Add [Device] Support** for each device (iPhone, iPad, Mac, …).
6. Choose **Yes** (supports at least one feature) or **No** (supports none), then **Next**.
7. Tick the supported features, then **Next**.
8. Responses are saved as a **Draft**. Click **Publish**. If several devices are declared, select each device to publish, then **Publish** again.
   - You can only publish for devices that have a **live version** on the App Store. For a brand-new app, fill in the draft now and publish once the first version is live.
   - Changes publish immediately but can take up to 24 hours to show for everyone.

## Updating later
**Apps →** app **→ App Accessibility → Edit** (next to the device) **→ Save → Publish**. Do this whenever a release changes accessibility support. Apple expects labels to stay accurate.

## Accessibility URL (optional)
**App Accessibility → Accessibility URL → Add URL** (or **Edit**) **→ Publish**. It appears on the product page on all devices except Apple TV. If no version is live yet, it goes live with the first release.

The URL should be specific to this app. Good content:
- each supported feature and how to turn it on (system settings + any in-app settings)
- known limitations (e.g. "the exported share image keeps a fixed size")
- languages available for captions, if any
- a contact for accessibility feedback

### `/accessibility` page template
```
# Accessibility in <App>

<App> supports these accessibility features on <devices>:

## Larger Text
Text grows with your iPhone's text size up to <AX3 / the largest size>.
Turn it on: Settings → Accessibility → Display & Text Size → Larger Text.
Limitations: <honest list, or "none known">.

## Dark Interface
…

## Not yet supported
We're working on <VoiceOver …>. If something gets in your way, email <contact>.

Last reviewed: <date, version>
```

## API
Labels can also be managed programmatically through the App Store Connect API (*Accessibility declarations*).

---

## Reminder

Close every run with this reminder, translated into the user's language and filled in from the summary table:

> 📱 **Don't forget App Store Connect.** These features only appear on your App Store page after you declare them.
> When you upload this version, go to **App Store Connect → Apps → <App> → App Accessibility**, choose **Get Started** (or **Edit**), add support for **<devices>**, tick **<claimed features>**, then **Save** and **Publish**.
> Leave **<unclaimed features>** unticked until they fully pass. You can only publish for a device once a version is live, so if this is your first release, save the draft now and publish right after approval.
> Optional: add your Accessibility URL (<url or "e.g. https://yourdomain.com/accessibility">).
