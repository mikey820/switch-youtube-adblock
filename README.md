# Nintendo Switch YouTube ad-block patcher

A small, build-specific patcher for the official YouTube app on an Atmosphère-modded Nintendo Switch. It suppresses video ad placements and removes TV masthead/ad-slot renderers while leaving ordinary player and browse data alone.

The repository contains no Nintendo or YouTube executable. You must provide your own legally obtained `main` NSO.

## Supported build

| Item | Value |
| --- | --- |
| YouTube version | v4 |
| Title ID | `01003A400C3DA000` |
| Build ID | `825C18BBF5008500091842636FC2D8DE` |
| Original NSO SHA-256 | `33f71d01f6d581cd6148ceb97b2829e211460b69d61db03ede050c1045eda2e2` |
| Patched NSO SHA-256 | `2f4a7aa4962bcda0131607d799b651fbff570496823de42bd48d13e4c0a640cd` |

The patcher checks the complete input hash and fails safely on any other build.

## Patch your file

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

## Install with Atmosphère

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

Close YouTube and rename the title's `exefs` folder to `exefs.disabled`, or restore your previous override. No NAND files are changed.

## How it works

The patch adds a narrow hook to Cobalt's browser load path and runs a short script before YouTube handles API responses. The script wraps `JSON.parse`, removes `adPlacements`, `adSlots`, and `playerAds`, then filters `adSlotRenderer` and `tvMastheadRenderer` entries from supported TV browse layouts.

The implementation is tied to the supported build's addresses and C++ object layout. A YouTube update or remote UI change may require a new patch. This is an ad-rendering patch, not a network privacy filter.

## Status and credits

Tested successfully on real Nintendo Switch hardware with YouTube v4 under Atmosphère.

Created by [mikey820](https://github.com/mikey820), with reverse-engineering and implementation assistance from OpenAI Codex. Not affiliated with Nintendo, Google, YouTube, or the Atmosphère project.

## License

The original code and patch payload in this repository are available under the MIT License. Third-party software and trademarks belong to their respective owners.
