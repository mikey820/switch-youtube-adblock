# Nintendo Switch YouTube ad-block patch

A small, build-specific Atmosphère IPS patch for the official YouTube app on Nintendo Switch. It suppresses video ad placements and removes TV masthead/ad-slot renderers while leaving ordinary player and browse data alone.

The repository contains no Nintendo or YouTube executable—only the original 653-byte IPS32 patch and an optional patch-your-own-NSO tool.

## Supported build

| Item | Value |
| --- | --- |
| YouTube version | v4 |
| Title ID | `01003A400C3DA000` |
| Build ID | `825C18BBF5008500091842636FC2D8DE` |
| Original NSO SHA-256 | `33f71d01f6d581cd6148ceb97b2829e211460b69d61db03ede050c1045eda2e2` |
| Patched NSO SHA-256 | `2f4a7aa4962bcda0131607d799b651fbff570496823de42bd48d13e4c0a640cd` |
| IPS32 SHA-256 | `1e646449489b3b59475481fcc4f8db84a521458c250f810bf7519a6914ff2bcf` |

The optional NSO patcher checks the complete input hash and fails safely on any other build.

## Recommended: install the IPS patch

1. Download `switch-youtube-adblock-atmosphere-v1.1.0.zip` from the [latest release](https://github.com/mikey820/switch-youtube-adblock/releases/latest).
2. Fully close YouTube with **HOME → X → Close**.
3. Extract the ZIP to the root of your Switch SD card.
4. If you previously installed a full `main` override, rename `SD:/atmosphere/contents/01003A400C3DA000/exefs` to `exefs.disabled`.
5. Boot Atmosphère and launch YouTube.

The installed patch should be at:

```text
SD:/atmosphere/exefs_patches/YouTubeAdBlock/825C18BBF5008500091842636FC2D8DE.ips
```

Atmosphère selects the patch by Build ID, so it will not be applied to a different YouTube build.

## Alternative: patch your own NSO

Install Python 3, then run on macOS or Linux:

```sh
git clone https://github.com/mikey820/switch-youtube-adblock.git
cd switch-youtube-adblock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python patch_youtube.py /path/to/your/main.original -o main
```

On Windows, use:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python patch_youtube.py C:\path\to\main.original -o main
```

Your original file is never modified. The output must report the patched SHA-256 shown above.

### Install the generated NSO with Atmosphère

1. Fully close YouTube with **HOME → X → Close**.
2. Keep a backup of any existing override.
3. Put the generated file at:

   ```text
   SD:/atmosphere/contents/01003A400C3DA000/exefs/main
   ```

4. Boot Atmosphère and launch YouTube.
5. Try several monetized videos, including a longer video that normally has mid-roll ads. Also check the home screen for masthead ads.

Ad inventory varies, so one ad-free video alone is not a useful test.

## Roll back

Close YouTube and rename `SD:/atmosphere/exefs_patches/YouTubeAdBlock` to `YouTubeAdBlock.disabled`. If using the generated-NSO method, disable the title's `exefs` folder instead. No NAND files are changed.

## How it works

The patch adds a narrow hook to Cobalt's browser load path and runs a short script before YouTube handles API responses. The script wraps `JSON.parse`, removes `adPlacements`, `adSlots`, and `playerAds`, then filters `adSlotRenderer` and `tvMastheadRenderer` entries from supported TV browse layouts. The hook and script fit in the original NSO's page-alignment gaps, allowing Atmosphère to apply them directly without redistributing or replacing the executable.

The implementation is tied to the supported build's addresses and C++ object layout. A YouTube update or remote UI change may require a new patch. This is an ad-rendering patch, not a network privacy filter.

## Status and credits

The payload was tested successfully on real Nintendo Switch hardware with YouTube v4 under Atmosphère. The IPS32 package was also verified to produce the exact same mapped process image as the working full-NSO replacement.

Created by [mikey820](https://github.com/mikey820), with reverse-engineering and implementation assistance from OpenAI Codex. Not affiliated with Nintendo, Google, YouTube, or the Atmosphère project.

## License

The original code and patch payload in this repository are available under the MIT License. Third-party software and trademarks belong to their respective owners.
