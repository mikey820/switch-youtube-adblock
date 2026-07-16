## Please star the repo if you find the project useful! :)

# Nintendo Switch YouTube ad-block patch

A small, build-specific Atmosphère IPS patch for the official YouTube app on Nintendo Switch. It suppresses video ad placements and removes TV masthead/ad-slot renderers while leaving ordinary player and browse data alone.

The repository contains no Nintendo or YouTube executable—only the original 653-byte IPS32 patch and its source.

## Supported build

| Item | Value |
| --- | --- |
| YouTube version | v4 |
| Title ID | `01003A400C3DA000` |
| Build ID | `825C18BBF5008500091842636FC2D8DE` |
| Original NSO SHA-256 | `33f71d01f6d581cd6148ceb97b2829e211460b69d61db03ede050c1045eda2e2` |
| IPS32 SHA-256 | `1e646449489b3b59475481fcc4f8db84a521458c250f810bf7519a6914ff2bcf` |

## Install

1. Download the Atmosphère ZIP from the [latest release](https://github.com/mikey820/switch-youtube-adblock/releases/latest).
2. Extract the ZIP to the root of your Switch SD card.
3. Boot Atmosphère and launch YouTube.

The installed patch should be at:

```text
SD:/atmosphere/exefs_patches/YouTubeAdBlock/825C18BBF5008500091842636FC2D8DE.ips
```

## Updates

I will do my very best to keep this patch up to date as YouTube releases new builds. If ad-free YouTube is especially important to you, consider setting **System Settings → System → Auto-Update Software** to **Off** and updating YouTube manually if you want after a compatible patch is released.

The Switch may still offer an update when you launch YouTube while connected to the internet. Do not accept that update or the patch will not work

## How it works

The patch adds a narrow hook to Cobalt's browser load path and runs a short script before YouTube handles API responses. The script wraps `JSON.parse`, removes `adPlacements`, `adSlots`, and `playerAds`, then filters `adSlotRenderer` and `tvMastheadRenderer` entries from supported TV browse layouts. The hook and script fit in the original NSO's page-alignment gaps, allowing Atmosphère to apply them directly without redistributing or replacing the executable.
