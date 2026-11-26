# Third-party components

The [NGCD ODE license](LICENSE.md) covers only what Rodrigo Tadeu "CyberRep" wrote. The parts below were made by other people and keep their own terms.

## NGCD firmware — based on NeoCDSDLoader

The NGCD firmware (the `.WAD`: the BIOS patch that runs on the console, the MCU program and the CPLD) is a modified version of the **[NeoCDSDLoader](https://github.com/furrtek/NeoCDSDLoader)** project: the SD Loader board, the MCU firmware, the CPLD and the original loader.

NeoCDSDLoader is licensed under the **GNU General Public License v3.0** ([license](https://github.com/furrtek/NeoCDSDLoader/blob/main/LICENSE)). As that license requires, the NGCD firmware is distributed under the same GPL-3.0 terms, and the complete source code of our modifications (the loader patch and the MCU program NGCD 00.12) is included in the `NGCD_firmware_source_0012.zip` file attached to each release of this repository. The CPLD is used unchanged.

What we changed:

- **Loader**: loads the NGCD menu from the `.boot` folder at power-on, safe mode (hold A, B, C or D), the warning screen with update from the root `.WAD`, quiet card reads, LED off option.
- **MCU (NGCD 00.12)**: file commands for the menu (open, read with seek, write, list, make folder, delete, rename) and SD card free space.

## Menu (`BOOT.ISO`)

- **NeoGeo Development Wiki** — documentation of the hardware, the BIOS calls and the memory card format used by the save manager.
- Tested on **NeoCD-Libretro**, the emulator that served as the base for testing the loader.

## Generator, conversion tools and web page

- They use, without including them: **Python**, **FFmpeg**, **Pillow**, **NumPy**, **chdman** (MAME) and **py7zr**, each under its own license.

## Media and game data

- Part of the covers and screenshots comes from **libretro-thumbnails** — https://github.com/libretro-thumbnails/SNK_-_Neo_Geo_CD
- Covers, screenshots, videos and game names belong to their respective owners.
- Neo Geo and Neo Geo CD are trademarks of their owner; this project is not affiliated with or endorsed by it.

---

## Português

A [licença do NGCD ODE](LICENSE.md) cobre só o que Rodrigo Tadeu "CyberRep" escreveu. As partes abaixo foram feitas por outras pessoas e mantêm os termos delas.

**Firmware NGCD — baseado no NeoCDSDLoader.** O firmware NGCD (o `.WAD`: o remendo da BIOS que roda no console, o programa do MCU e o CPLD) é uma versão modificada do projeto **[NeoCDSDLoader](https://github.com/furrtek/NeoCDSDLoader)**: a placa do SD Loader, o firmware do MCU, o CPLD e o loader original. O NeoCDSDLoader é licenciado sob a **GNU General Public License v3.0** ([licença](https://github.com/furrtek/NeoCDSDLoader/blob/main/LICENSE)). Como essa licença pede, o firmware NGCD é distribuído sob a mesma GPL-3.0, e o código-fonte completo das nossas alterações (o patch do loader e o programa do MCU NGCD 00.12) está no arquivo `NGCD_firmware_source_0012.zip` de cada versão (Releases) deste repositório. O CPLD é usado sem mudança.

O que mudamos: no **loader**, carregar o menu NGCD da pasta `.boot` ao ligar, o modo de segurança (segurar A, B, C ou D), a tela de aviso com a atualização pelo `.WAD` da raiz, a leitura silenciosa do cartão e o LED desligado; no **MCU (NGCD 00.12)**, os comandos de arquivo para o menu (abrir, ler com *seek*, gravar, listar, criar pasta, apagar, renomear) e o espaço livre do cartão SD.

**Menu.** **NeoGeo Development Wiki** (documentação do hardware, das rotinas da BIOS e do formato do cartão de memória usado pelo gerenciador de saves). Testado no **NeoCD-Libretro**, o emulador que serviu de base para testar o loader.

**Gerador, ferramentas e página.** Usam, sem incluí-los: **Python**, **FFmpeg**, **Pillow**, **NumPy**, **chdman** (MAME) e **py7zr**, cada um com a sua licença.

**Mídias e dados dos jogos.** Parte das capas e telas vem do **libretro-thumbnails** (https://github.com/libretro-thumbnails/SNK_-_Neo_Geo_CD). Capas, telas, vídeos e nomes de jogos pertencem aos seus donos. Neo Geo e Neo Geo CD são marcas do seu titular; este projeto não é ligado a ele nem endossado por ele.
