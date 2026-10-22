#!/usr/bin/env bash
# Toggle iOS Simulator accessibility settings for Accessibility Nutrition Label checks.
#
#   sim_a11y.sh stress [device]          AX3 text + Dark + Increase Contrast
#   sim_a11y.sh reset  [device]          default text size, Light, contrast off
#   sim_a11y.sh size <ax1..ax5|default|xs|s|m|l|xl|xxl|xxxl> [device]
#   sim_a11y.sh dark|light [device]
#   sim_a11y.sh contrast on|off [device]
#   sim_a11y.sh shot <name> [device]     screenshot to ./a11y-shots/<name>.png
#   sim_a11y.sh status [device]
#
# device defaults to "booted". Reduce Motion, Reduce Transparency, Bold Text,
# Grayscale and VoiceOver have no simctl switch: use the simulator's
# Settings → Accessibility, or Accessibility Inspector → Settings.
set -euo pipefail

cmd="${1:-help}"

size_name() {
  case "$1" in
    ax1) echo accessibility-medium ;;
    ax2) echo accessibility-large ;;
    ax3) echo accessibility-extra-large ;;
    ax4) echo accessibility-extra-extra-large ;;
    ax5) echo accessibility-extra-extra-extra-large ;;
    xs) echo extra-small ;; s) echo small ;; m) echo medium ;;
    l|default) echo large ;;
    xl) echo extra-large ;; xxl) echo extra-extra-large ;; xxxl) echo extra-extra-extra-large ;;
    *) echo "$1" ;;
  esac
}

case "$cmd" in
  stress)
    dev="${2:-booted}"
    xcrun simctl ui "$dev" content_size accessibility-extra-large
    xcrun simctl ui "$dev" appearance dark
    xcrun simctl ui "$dev" increase_contrast enabled
    echo "AX3 + Dark + Increase Contrast on ($dev). Relaunch the app to be safe." ;;
  reset)
    dev="${2:-booted}"
    xcrun simctl ui "$dev" content_size large
    xcrun simctl ui "$dev" appearance light
    xcrun simctl ui "$dev" increase_contrast disabled
    echo "Defaults restored ($dev)." ;;
  size)
    xcrun simctl ui "${3:-booted}" content_size "$(size_name "${2:?size required}")" ;;
  dark|light)
    xcrun simctl ui "${2:-booted}" appearance "$cmd" ;;
  contrast)
    case "${2:?on|off required}" in
      on) state=enabled ;; off) state=disabled ;; *) state="$2" ;;
    esac
    xcrun simctl ui "${3:-booted}" increase_contrast "$state" ;;
  shot)
    mkdir -p a11y-shots
    out="a11y-shots/${2:?name required}.png"
    xcrun simctl io "${3:-booted}" screenshot "$out" >/dev/null
    echo "$out" ;;
  status)
    dev="${2:-booted}"
    echo "content_size:      $(xcrun simctl ui "$dev" content_size)"
    echo "appearance:        $(xcrun simctl ui "$dev" appearance)"
    echo "increase_contrast: $(xcrun simctl ui "$dev" increase_contrast)" ;;
  *)
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//' ;;
esac
