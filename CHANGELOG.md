# 📝 Version history

[← Back to start](README.md) · **English** · [Português](CHANGELOG.pt.md) · [Español](CHANGELOG.es.md)

Everything that changed in the **menu** (`BOOT.ISO`), the **NGCD firmware** (loader + MCU) and the **tools** (web page and `generate_usb.py`), newest first.

- [Menu — 1.0](#-menu--10)
- [Menu — before 1.0 (0.x versions)](#-menu--before-10-0x-versions)
- [NGCD firmware](#-ngcd-firmware)
- [Tools (page, generate_usb.py)](#-tools-page-generate_usbpy)

---

## 🚀 Menu — 1.0

First public release. It brings together everything done in the development versions (0.x), described below, and adds:

- 📊 **Redesigned SD and NVRAM bars.** The name in the menu font with a shadow, a dark track with the used part in colour (blue for SD, yellow for NVRAM) and the free space right-aligned, with tighter letters.
- 🌙 **3DO-style screen saver**: our logo and each console, **one at a time**, moving across the dark screen; every 2 bounces off the edge the image changes. The menu texts and bars no longer show on top.
- 📜 **Long names scroll to the end**: with MCU NGCD 00.12 the menu reads the whole folder name (up to 63 letters; it used to stop at the 25th) and the whole gamelist title (it used to stop at the 31st).
- 💿 **Default cover with rounded corners**, like real covers.
- 🎞️ **Smoother Carousel FX**: covers are read ahead in the direction you are moving, 2 steps ahead.
- **CD drive**: the "Boot from the CD drive" option left the Options; the **CD** box on the main menu already does it.
- 🔧 **Fixes from the console test**: longer SD and NVRAM bars, with more spaced digits and the unit (G, M, K) a bit to the right; controller test with the standard footer (**B** button: hold to exit); serial number on one line like the other items; **CONSOLE** tab in the storage manager; screen saver no longer loses pieces while the menu was still loading covers or video.
- **About** shows **Menu 1.00**, the loader firmware, the MCU and the CPLD.

What 1.0 has, in short: 6 display modes (List, Covers, Carousel, Carousel FX, Showcase and Strip), video preview, packed covers and screenshots, favorites, recents and stats, genre and country filter, a sheet for each game in 3 languages, save manager, CD box for the CD drive, BIOS dump, firmware update from the console, 10 tracks, 10 backgrounds and a screen saver.

---

## 🧪 Menu — before 1.0 (0.x versions)

The development versions, newest first.

### 📦 0.70 — Packed covers and sliding Carousel FX

**Packed covers and screenshots**
- 📦 **All covers in a single file** (`.media/covers/cover.pak`, with the 5 sizes of each game) and the screenshots in another (`.media/screenshots/screenshots.pak`). The menu opens the pack once and goes straight to the image, instead of looking for each file in a folder with hundreds of them.
- An image outside the pack, or a card without packs: the menu uses the loose files.
- On the page, *Media → Card*: **Cover and screenshot format: PAK or Individual**. When you switch, the page converts what is already on the card.

**Carousel FX**
- 🎞️ **Covers slide when you move**: each one goes from its place to its neighbour's, turning and changing size.
- **Much faster**: the menu's multiply and divide now use the processor's own instructions (the whole menu got lighter), each cover only changes size and position each frame, and the neighbour's large cover is already in memory.
- The default cover (game without a cover) is turned toward the centre too, with a reflection.
- Fixed: a strip of another cover under the reflection (console only) and the top bar and footer cut on the right.

### 📦 0.63 — Fixes from the console test
- Carousel FX no longer freezes on entry without the 96 covers.
- Showcase and Strip without the stray dots in the description; Strip without half a cover over the default cover.
- Footer buttons closer together, to fit on the TV.

### 📦 0.62 — Carousel FX, Showcase and Strip
- 🖼️ **Three new display modes**: **Carousel FX** (side covers turned toward the centre, as trapezoids, with a floor reflection), **Showcase** (large cover, sheet and the whole description with scrolling) and **Strip** (screenshot and data on top, a row of covers below).
- **Carousel with bigger inner covers** (96, between the outer and the centre one), in a new 16-palette cover.
- Games footer with **C FAV**, **D INFO** and the **SELECT FILTER** button; SELECT or START open the filter.

### 📦 0.59 to 0.61 — Filter, BIOS dump and modular menu
- 🔎 **Filter** by genre and country, with `[ ]`/`[X]` boxes, how many games pass and the **A MARK**, **B OK**, **C CLEAR** buttons.
- 💾 **Dump ROM**: the console copies its own BIOS (512 KB) to `.roms/` (e.g. `frontload_japao.bin`), without duplicates.
- 🧩 **Modular menu**: Options, saves, CD drive, filter and the new modes are only read when they open. The menu's fixed memory gained ~68 KB free.
- The loader shortcuts (A+B+C+D with START/SELECT) no longer leave the menu by accident.
- List with Video: a game without video shows "No video".
- CD timing meter in the list info strip.
- The folder for installed firmwares became `.wad`.

### 📦 0.52 to 0.58 — Card in the ODE standard
- 🗂️ **Everything in the ODE standard**: the menu in `.boot`, media in `.media`, options, favorites, recents, stats and the game list in `.config` (`ngcd*.ode`, text, one option per line), saves in `.saves`.
- **Media outside `BOOT.ISO`**: the menu became small and covers are read straight from the card, by game name.
- **List video without stutter**: read bit by bit, it starts as soon as the first frame arrives.
- **Covers kept in memory** and the neighbours read while the controller is idle.
- **3DO-style top bar**: logo in the middle, SD and NVRAM bars, region flag.
- New options: SD bar, NVRAM bar and Flag (show/hide).
- Carousel with the frame outside the cover and stepped sizes (48, 64, 128).
- The firmware already installed is not rewritten at every power-on.

### 📦 0.31 to 0.45 — New game box and Carousel
- 🎠 **Carousel**: a large 128 × 128 cover in the centre and two on each side.
- **Game info**: over the media or below it; screenshot and video in 4:3.
- **No more lines when loading** cover, screenshot and video: colours are only written while the TV is not drawing.
- The previous image stays in the box until the new one is ready.
- **Screen saver** with both consoles and the logo; region flag at the top.
- Play count in the bottom bar.
- **SD card space** with MCU NGCD 00.12.

### 📦 0.21 to 0.30 — CD box, saves and quiet reading
- 💿 **CD box** on the main screen, with a spinning disc: boots the CD in the drive.
- 💾 **Storage manager**: console and SD card, copy, restore and delete saves; backup of the whole memory.
- 🤫 **Quiet reading**: the card is only read while the TV is not drawing (no snow on the picture).
- **No flicker**: each screen is built behind and shows up whole.
- **Official game names** (Title or Folder).
- Translucent bands on the cover (transparency 0 to 100%), last game thumbnail, About and Thanks.

### 📦 0.1 to 0.20 — The base
- **0.20** — Standard window for questions, progress and result; CD drive, developer mode, Debug DIPs and timing meter.
- **0.17** — 🎵 10 background tracks, with volume and Random; video starting faster.
- **0.15 and 0.16** — Covers mode (grid); accordion Options; Letters for the whole menu.
- **0.10 to 0.14** — 🎬 Video in the list; shiny covers; description with margins and game switching.
- **0.7 to 0.9** — Sounds, 9 screen backgrounds, year/country and star/genre bands; 3 languages and each game's data; 16 main screen layouts; star effect when favoriting.
- **0.4 to 0.6** — ⭐ Favorites, recents and stats; controller test, picture adjustment, accents; console and SD Loader info; covers and screenshots.
- **0.1 to 0.3** — The first version: main screen, game list and the ODE-standard font; the loader loads the menu by itself at power-on; options and saves on the card; loader region, logo and LEDs.

---

## 🧩 NGCD firmware

The firmware comes in a `.WAD` with three parts: the **loader** (the console BIOS patch), the **MCU** (the SD Loader microcontroller program) and the **CPLD**. See the explanation in the [README](README.md#-what-is-in-the-firmware-wad-loader-mcu-and-cpld).

### NGCD 00.12 (loader NGCD 12 · MCU NGCD 00.12 · CPLD 00.03)

**MCU NGCD 00.12**
- 📁 **File commands** for the menu: open, read at any point (*seek*), write, list folders, make folders, delete and rename.
- 📊 **SD card space** (total and free).
- It is what allows media in `.media`, cover packs, options in `.config`, the save manager, the BIOS dump and updates from the menu. Compatible with everything MCU 00.11 did.

**Loader NGCD 12**
- 🎮 **"Quit game" in the in-game menu goes back to the NGCD menu** (the `BOOT.ISO`), no longer to the SD Loader folder list. In safe mode it still stays in the SD Loader menu.
- The SD Loader screen shows the version as **NGCD 00.12**.
- 🚀 **Loads the NGCD menu by itself at power-on**, from the `.boot` folder (or `_BOOT`, on older cards).
- 🛟 **Safe mode**: holding A, B, C or D at power-on goes straight to the original SD Loader menu.
- **Warning screen** when the card has no menu: **A** = SD Loader menu, **C** = update from the root `.WAD`.
- **Quiet reading** on request from the menu (no snow while reading the card).
- LED with the **Off** option.
- Region, boot animation and LEDs chosen in the menu apply from the next game.

---

## 🛠️ Tools (page, generate_usb.py)

### 📅 November 2026 (menu 1.0)
- **Page**: the header shows the menu version (1.0) and the firmware version.
- **Page and `generate_usb.py`**: **Cover and screenshot format: PAK or Individual**, converting what is already on the card (`--individual` in the generator).

### 📅 November 2026 (menus 0.52 to 0.63)
- **`generate_usb.py` rebuilt on the page's layout** (`.boot`, `.media`, `.config`) and now **fixes the discs** for the SD Loader: `.chd` (chdman), `.nrg`, `.img` + `.ccd`, `.iso`/`.img`/`.bin` without `.cue`, `.iso` + mp3/ogg/flac (tracks become `.wav`), `.zip`/`.7z`, a game loose in the root and a `.cue` with TABs.
- The page **only copies** the menu and the firmware from the kit folder, and only when they changed; writing again does not rewrite what is already on the card.
- The page copies the menu to `.boot` and warns you when the console still has the old loader.
- 16-palette 96 covers for the Carousel, also created for the covers already on the card.

### 📅 November 2026 (menus 0.6 to 0.30)
- **Web page** that writes the whole card: Step by step, How to use, Manual, What's new, Rename folders, Find the game (for a game without a cover), warnings for names longer than 25 letters and for more than 200 games, listen to the menu music.
- **`generate_usb.py`**: covers, screenshots, videos and game texts, with a step-by-step wizard.
