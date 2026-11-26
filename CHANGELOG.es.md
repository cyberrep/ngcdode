# 📝 Historial de versiones

[← Volver al inicio](README.es.md) · [English](CHANGELOG.md) · [Português](CHANGELOG.pt.md) · **Español**

Todo lo que cambió en el **menú** (`BOOT.ISO`), en el **firmware NGCD** (loader + MCU) y en las **herramientas** (página web y `generate_usb.py`), de la versión más nueva a la más antigua.

- [Menú — 1.0](#-menú--10)
- [Menú — antes de la 1.0 (versiones 0.x)](#-menú--antes-de-la-10-versiones-0x)
- [Firmware NGCD](#-firmware-ngcd)
- [Herramientas (página, generate_usb.py)](#-herramientas-página-generate_usbpy)

---

## 🚀 Menú — 1.0

Primera versión pública. Reúne todo lo hecho en las versiones de desarrollo (0.x), descritas abajo, y añade:

- 📊 **Barras de la SD y de la NVRAM rediseñadas.** El nombre en la letra del menú con sombra, el carril oscuro con lo usado en color (azul en la SD, amarillo en la NVRAM) y el espacio libre alineado a la derecha, con las letras más juntas.
- 🌙 **Protector de pantalla como en 3DO**: nuestro logo y cada consola, **uno a la vez**, paseando por la pantalla oscura; cada 2 choques con el borde cambia de imagen. Los textos y las barras del menú ya no aparecen encima.
- 📜 **El nombre largo se desplaza hasta el final**: con el MCU NGCD 00.12 el menú lee el nombre entero de la carpeta (hasta 63 letras; antes paraba en la 25ª) y el título entero del gamelist (antes paraba en la 31ª).
- 💿 **Portada por defecto con las esquinas redondeadas**, como las portadas de verdad.
- 🎞️ **Carrusel FX más fluido**: lee antes las portadas hacia el lado al que avanzas, 2 pasos adelante.
- **Unidad de CD**: se quitó la opción "Iniciar desde el CD" de las Opciones; la caja **CD** del menú principal ya lo hace.
- **Acerca de** muestra **Menú 1.00**, el firmware del loader, el MCU y el CPLD.

Lo que tiene la 1.0, en resumen: 6 modos de vista (Lista, Portadas, Carrusel, Carrusel FX, Vitrina y Franja), vista previa en vídeo, portadas y pantallas en paquete, favoritos, recientes y estadísticas, filtro por género y país, ficha de cada juego en 3 idiomas, gestor de partidas, caja CD para la unidad de CD, extracción de la BIOS, actualización del firmware desde la consola, 10 músicas, 10 fondos y protector de pantalla.

---

## 🧪 Menú — antes de la 1.0 (versiones 0.x)

Las versiones de desarrollo, de la más nueva a la más antigua.

### 📦 0.70 — Portadas en paquete y Carrusel FX deslizante

**Portadas y pantallas en paquete**
- 📦 **Todas las portadas en un solo archivo** (`.media/covers/cover.pak`, con los 5 tamaños de cada juego) y las pantallas en otro (`.media/screenshots/screenshots.pak`). El menú abre el paquete una vez y va directo a la imagen, en vez de buscar cada archivo en una carpeta con cientos de ellos.
- Imagen fuera del paquete, o tarjeta sin paquete: el menú usa los archivos sueltos.
- En la página, *Medios → Tarjeta*: **Formato de portadas y pantallas: PAK o Individual**. Al cambiar de formato, la página convierte lo que ya está en la tarjeta.

**Carrusel FX**
- 🎞️ **Las portadas se deslizan al moverte**: cada una va de su posición a la de la vecina, girando y cambiando de tamaño.
- **Mucho más rápido**: las multiplicaciones y divisiones del menú pasaron a usar las instrucciones del propio procesador (todo el menú quedó más ligero), cada portada solo cambia de tamaño y posición en cada cuadro, y la portada grande de la vecina ya está en memoria.
- La portada por defecto (juego sin portada) también queda girada hacia el centro, con reflejo.
- Corregidos: una franja de otra portada bajo el reflejo (solo en la consola) y la barra de arriba y el pie cortados a la derecha.

### 📦 0.63 — Correcciones de la prueba en consola
- El Carrusel FX ya no se cuelga al entrar sin las portadas de 96.
- Vitrina y Franja sin los puntitos en la descripción; Franja sin media portada sobre la portada por defecto.
- Botones del pie más juntos, para caber en la TV.

### 📦 0.62 — Carrusel FX, Vitrina y Franja
- 🖼️ **Tres modos de vista nuevos**: **Carrusel FX** (portadas de los lados giradas hacia el centro, en trapecio, con reflejo en el suelo), **Vitrina** (portada grande, ficha y la descripción entera con desplazamiento) y **Franja** (pantalla y datos arriba, fila de portadas abajo).
- **Carrusel con las portadas de dentro más grandes** (96, entre la de fuera y la del centro), en una portada nueva de 16 paletas.
- Pie de Juegos con **C FAV**, **D INFO** y el botón **SELECT FILTRO**; SELECT o START abren el filtro.

### 📦 0.59 a 0.61 — Filtro, extracción de la BIOS y menú en módulos
- 🔎 **Filtro** por género y país, con casillas `[ ]`/`[X]`, cuántos juegos pasan y los botones **A MARCAR**, **B OK**, **C LIMPIAR**.
- 💾 **Extraer ROM**: la consola copia su propia BIOS (512 KB) a `.roms/` (ej. `frontload_japao.bin`), sin duplicar.
- 🧩 **Menú en módulos**: Opciones, partidas, unidad de CD, filtro y los modos nuevos solo se leen al abrirlos. La memoria fija del menú ganó ~68 KB libres.
- Los atajos del loader (A+B+C+D con START/SELECT) ya no sacan del menú sin querer.
- Lista con Vídeo: un juego sin vídeo muestra "Sin vídeo".
- Medidor de tiempo del CD en la banda de información de la lista.
- La carpeta de los firmwares instalados pasó a ser `.wad`.

### 📦 0.52 a 0.58 — Tarjeta con el estándar ODE
- 🗂️ **Todo con el estándar ODE**: el menú en `.boot`, los medios en `.media`, las opciones, favoritos, recientes, estadísticas y la lista de juegos en `.config` (`ngcd*.ode`, texto, una opción por línea), las partidas en `.saves`.
- **Medios fuera del `BOOT.ISO`**: el menú quedó pequeño y las portadas se leen directo de la tarjeta, por el nombre del juego.
- **Vídeo de la lista sin trabas**: leído poco a poco, empieza en cuanto llega el primer cuadro.
- **Portadas guardadas en memoria** y las vecinas leídas con el control quieto.
- **Parte de arriba como en 3DO**: logo en el medio, barras de la SD y de la NVRAM, bandera de la región.
- Opciones nuevas: Barra de la SD, Barra de la NVRAM y Bandera (mostrar/ocultar).
- Carrusel con el marco por fuera de la portada y tamaños escalonados (48, 64, 128).
- El firmware ya instalado no se regraba en cada encendido.

### 📦 0.31 a 0.45 — Caja del juego nueva y Carrusel
- 🎠 **Carrusel**: portada grande de 128 × 128 en el centro y dos a cada lado.
- **Info de los juegos**: sobre la imagen o debajo; pantalla y vídeo en 4:3.
- **Sin rayas al cargar** portada, pantalla y vídeo: los colores solo se graban mientras la TV no dibuja.
- La imagen anterior queda en la caja hasta que la nueva esté lista.
- **Protector de pantalla** con las dos consolas y el logo; bandera de la región arriba.
- Veces jugado en la barra de abajo.
- **Espacio de la tarjeta SD** con el MCU NGCD 00.12.

### 📦 0.21 a 0.30 — Caja CD, partidas y lectura silenciosa
- 💿 **Caja CD** en la pantalla principal, con el disco girando: arranca el CD que está en el lector.
- 💾 **Gestor de almacenamiento**: consola y tarjeta SD, copiar, restaurar y borrar partidas; copia de la memoria entera.
- 🤫 **Lectura silenciosa**: la tarjeta solo se lee mientras la TV no dibuja (sin lluvia en la imagen).
- **Sin parpadeos**: cada pantalla se monta por detrás y aparece entera.
- **Nombre oficial de los juegos** (Título o Carpeta).
- Bandas translúcidas en la portada (transparencia de 0 a 100%), miniatura del último juego, Acerca de y Agradecimientos.

### 📦 0.1 a 0.20 — La base
- **0.20** — Ventana estándar para preguntas, progreso y resultado; unidad de CD, modo desarrollador, Debug DIPs y medidor de tiempo.
- **0.17** — 🎵 10 músicas de fondo, con volumen y Aleatoria; vídeo que empieza más rápido.
- **0.15 y 0.16** — Modo Portadas (rejilla); Opciones en acordeón; Letras para todo el menú.
- **0.10 a 0.14** — 🎬 Vídeo en la lista; portadas con brillo; descripción con márgenes y cambio de juego.
- **0.7 a 0.9** — Sonidos, 9 fondos de pantalla, bandas de año/país y estrella/género; 3 idiomas y los datos de cada juego; 16 disposiciones de la pantalla principal; estrella con efecto al marcar favorito.
- **0.4 a 0.6** — ⭐ Favoritos, recientes y estadísticas; prueba de control, ajuste de imagen, acentos; información de la consola y del SD Loader; portadas y pantallas.
- **0.1 a 0.3** — La primera versión: pantalla principal, lista de juegos y la fuente del estándar ODE; el loader carga el menú solo al encender; opciones y partidas en la tarjeta; región, logo y LED del loader.

---

## 🧩 Firmware NGCD

El firmware viene en un `.WAD` con tres partes: el **loader** (el parche de la BIOS de la consola), el **MCU** (el programa del microcontrolador del SD Loader) y el **CPLD**. Mira la explicación en el [README](README.es.md#-qué-hay-en-el-firmware-wad-loader-mcu-y-cpld).

### NGCD 00.12 (loader NGCD 12 · MCU NGCD 00.12 · CPLD 00.03)

**MCU NGCD 00.12**
- 📁 **Comandos de archivo** para el menú: abrir, leer en cualquier punto (*seek*), grabar, listar carpetas, crear carpetas, borrar y renombrar.
- 📊 **Espacio de la tarjeta SD** (total y libre).
- Es lo que permite los medios en `.media`, los paquetes de portadas, las opciones en `.config`, el gestor de partidas, la extracción de la BIOS y la actualización desde el menú. Compatible con todo lo que hacía el MCU 00.11.

**Loader NGCD 12**
- La pantalla del SD Loader muestra la versión como **NGCD 00.12**.
- 🚀 **Carga el menú NGCD solo al encender**, desde la carpeta `.boot` (o `_BOOT`, en tarjetas antiguas).
- 🛟 **Modo seguro**: manteniendo A, B, C o D al encender, va directo al menú original del SD Loader.
- **Pantalla de aviso** cuando la tarjeta no tiene el menú: **A** = menú del SD Loader, **C** = actualizar con el `.WAD` de la raíz.
- **Lectura silenciosa** a petición del menú (sin lluvia al leer la tarjeta).
- LED con la opción **Apagado**.
- Región, animación al encender y LED elegidos en el menú valen ya en el próximo juego.

---

## 🛠️ Herramientas (página, generate_usb.py)

### 📅 Noviembre de 2026 (menú 1.0)
- **Página**: la cabecera muestra la versión del menú (1.0) y del firmware.
- **Página y `generate_usb.py`**: **Formato de portadas y pantallas: PAK o Individual**, con la conversión de lo que ya está en la tarjeta (`--individual` en el generador).

### 📅 Noviembre de 2026 (menús 0.52 a 0.63)
- **`generate_usb.py` rehecho con el esquema de la página** (`.boot`, `.media`, `.config`) y ahora **arregla los discos** para el SD Loader: `.chd` (chdman), `.nrg`, `.img` + `.ccd`, `.iso`/`.img`/`.bin` sin `.cue`, `.iso` + mp3/ogg/flac (las pistas pasan a `.wav`), `.zip`/`.7z`, juego suelto en la raíz y `.cue` con TAB.
- La página **solo copia** el menú y el firmware de la carpeta del kit, y solo cuando cambiaron; grabar de nuevo no regraba lo que ya está en la tarjeta.
- La página copia el menú a `.boot` y avisa cuando la consola todavía tiene el loader antiguo.
- Portadas de 96 con 16 paletas para el Carrusel, creadas también para las portadas que ya están en la tarjeta.

### 📅 Noviembre de 2026 (menús 0.6 a 0.30)
- **Página web** que graba la tarjeta entera: Paso a paso, Cómo usar, Manual, Novedades, Renombrar carpetas, Buscar el juego (para el juego sin portada), avisos de nombres de más de 25 letras y de más de 200 juegos, oír las músicas del menú.
- **`generate_usb.py`**: portadas, pantallas, vídeos y textos de los juegos, con el asistente por pasos.
