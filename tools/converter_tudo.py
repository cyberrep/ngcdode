#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
converter_tudo.py (NEO GEO CD) - converte TODA a biblioteca de midias para o formato do Neo Geo CD.

Le as pastas de ORIGEM (dentro da pasta das midias):
    covers/        imagens das capas (png, jpg, webp...)
    screenshots/   imagens das telas
    videos/        videos (mp4, avi, mkv...): a previa da lista (opcao Lista: Video)

e cria a pasta  media/  no formato que o cartao e a pagina (index.html) usam:
    media/covers/<jogo>.ngi        capa 96x96 (caixa de CD)
    media/covers128/<jogo>.ngi     capa grande 128x128 (exibicao Carrossel, menu 41)
    media/covers96/<jogo>.ngi      capa 96x96 com 16 paletas (capas de dentro do Carrossel e lados do Carrossel FX, menu 62)
    media/covers64/<jogo>.ngi      capa pequena 64x64 (modo Capas e lados do Carrossel; no cartao: .media/covers)
    media/covers_mini/<jogo>.ngi   capinha 24x24 (painel Ultimo jogo)
    media/screenshots/<jogo>.ngi   tela 96x72
    media/videos/<jogo>.ngv        video: 15 s, 96x72, 12 quadros/s (precisa de numpy e ffmpeg:
                                   instala sozinho o numpy e o imageio-ffmpeg se faltarem)
    media/index.json               lista do que existe (para a pagina e o GitHub)

So converte o que e NOVO ou foi ALTERADO (guarda tamanho e data de cada origem em
converter_tudo.estado.json, na pasta das midias).

USO:
  py converter_tudo.py                 (pergunta, passo a passo)
  py converter_tudo.py --sim           (sem perguntas: usa as respostas da ultima vez)
  py converter_tudo.py --refazer       (refaz tudo)
  py converter_tudo.py --nucleos 2      (videos: so 2 ao mesmo tempo)
  py converter_tudo.py --limpar        (apaga da media/ o que nao tem mais origem)
  py converter_tudo.py --midias "C:\...\Midias Neo Geo" --sim
PRECISA: Python (o Pillow e instalado sozinho).
"""
import os, sys, time, argparse, configparser, json


def _ensure_pkg(pip_name, import_name):
    import importlib, subprocess
    try:
        return importlib.import_module(import_name)
    except ImportError:
        pass
    print("Instalando %s (uma vez so)..." % pip_name)
    for extra in ([], ["--user"], ["--break-system-packages"]):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name] + extra)
            return importlib.import_module(import_name)
        except Exception:
            continue
    return None


if _ensure_pkg("pillow", "PIL") is None:
    sys.exit("Nao consegui instalar o Pillow: py -m pip install pillow")

# ====== MODULO EMBUTIDO: ngcd_media ======
# -*- coding: utf-8 -*-
r"""
ngcd_media.py - capas e telas no formato do Neo Geo CD (usado pelo generate_usb e pelo converter_tudo).

O Neo Geo CD nao tem imagem em bitmap: tudo na tela e sprite (tiles de 16x16) ou a camada fix
(8x8). Cada tile tem 15 cores + transparente, escolhidas de 256 paletas de 16 cores (cor de 5 bits
por canal). Entao uma imagem vira:
    - uma grade de tiles 16x16 (a capa 96x128 = 6x8 = 48 tiles, a tela 128x96 = 8x6 = 48)
    - uma paleta de 15 cores para cada tile (reducao por "median cut" dentro do tile)
    - os tiles no formato do .SPR do Neo Geo CD

Arquivo .ngi (Neo Geo Image), tudo big-endian:
     0  "NGI1"
     4  u16 largura em tiles   6  u16 altura em tiles
     8  u16 paletas            10  u16 tiles
    12  mapa: 1 u16 por tile da grade, coluna por coluna (de cima para baixo):
        (paleta << 9) | tile   (tile 0x1FF = vazio/transparente)
    ..  paletas: 16 u16 cada (cor 0 = transparente), cor do Neo Geo
    ..  tiles: 128 bytes cada (formato .SPR do Neo Geo CD)

O generate_usb poe as imagens dentro do _BOOT/BOOT.ISO (o menu le do proprio CD):
    MEDIA.PRG       indice: nome da pasta de cada jogo -> numero da capa e da tela
    Cnnnn.PRG       cabecalho + mapa + paletas da capa nnnn      Cnnnn.SPR  os tiles
    Snnnn.PRG / Snnnn.SPR   o mesmo para a tela
"""
import os, re, sys, struct, unicodedata, io, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:      # o generate_usb instala o Pillow sozinho
    Image = None

IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')
COVER = (96, 96)         # capa: caixa de CD (quadrada), moldura da lista do menu
BIG = (128, 128)         # capa grande do Carrossel (Lnnnn.PRG = o .ngi inteiro, 8x8 tiles, ate 64 paletas)
GRID = (64, 64)          # capa pequena da exibicao CAPAS (Gnnnn.PRG = o .ngi inteiro)
SHOT = (96, 72)          # tela (4:3): fica em 96x80 (.ngi), a ultima meia fileira (8px) transparente
EMPTY_TILE = 0x1FF
COVER_CORNER = (2, 1)     # cantos arredondados da capa (pixels transparentes)


# ------------------------------------------------------------------ nomes
def norm(name):
    """Titulo comparavel: sem acento, sem (tags), so letras e numeros."""
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    s = s.replace('_', ' ').replace('&', ' and ')
    s = re.sub(r'[\(\[][^\)\]]*[\)\]]', ' ', s)
    s = re.sub(r'^(.*), (the|a|o)\s*$', r'\2 \1', s.strip())
    return re.sub(r'[^a-z0-9]+', '', s)


# ------------------------------------------------------------------ cor do Neo Geo
def ng_color(r, g, b):
    """RGB 8 bits -> cor do Neo Geo (5 bits por canal; o bit baixo de cada um fica nos bits 14-12)."""
    r, g, b = r >> 3, g >> 3, b >> 3
    return ((r & 1) << 14) | ((g & 1) << 13) | ((b & 1) << 12) | ((r >> 1) << 8) | ((g >> 1) << 4) | (b >> 1)


def ng_rgb(c):
    r = ((c >> 7) & 0x1E) | ((c >> 14) & 1)
    g = ((c >> 3) & 0x1E) | ((c >> 13) & 1)
    b = ((c << 1) & 0x1E) | ((c >> 12) & 1)
    return ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2))


def encode_spr(idx):
    """Tile 16x16 (indices 0..15) no formato do .SPR do Neo Geo CD: bytes 0-63 = metade direita,
    64-127 = esquerda; cada linha = 4 bytes na ordem plano 1, 0, 3, 2; bit 0 = pixel da esquerda."""
    out = bytearray(128)
    for half, x0 in ((0, 8), (64, 0)):
        for y in range(16):
            row = idx[y * 16 + x0:y * 16 + x0 + 8]
            for plane, pos in ((0, 1), (1, 0), (2, 3), (3, 2)):
                v = 0
                for b in range(8):
                    if row[b] >> plane & 1:
                        v |= 1 << b
                out[half + y * 4 + pos] = v
    return bytes(out)


def decode_spr(data):
    idx = [0] * 256
    for half, x0 in ((0, 8), (64, 0)):
        for y in range(16):
            for plane, pos in ((0, 1), (1, 0), (2, 3), (3, 2)):
                v = data[half + y * 4 + pos]
                for b in range(8):
                    if v >> b & 1:
                        idx[y * 16 + x0 + b] |= 1 << plane
    return idx


# ------------------------------------------------------------------ preparo da imagem
_LIN = [((v / 255.0) / 12.92) if v / 255.0 <= 0.04045 else (((v / 255.0) + 0.055) / 1.055) ** 2.4 for v in range(256)]


def _to_srgb(x):
    if x <= 0.0:
        return 0
    if x >= 1.0:
        return 255
    s = x * 12.92 if x <= 0.0031308 else 1.055 * (x ** (1 / 2.4)) - 0.055
    return int(s * 255.0 + 0.5)


def _resize_linear(img, size):
    """Reduz em luz linear (cor certa nos degrades) pela media de area, e devolve RGB (o conversor do 3DO 1.5)."""
    bands = []
    for band in img.split():
        f = Image.new('F', band.size)
        f.putdata([_LIN[v] for v in band.tobytes()])
        # como o 3DO 1.5: media de area (caixa) ao reduzir; bicubica so quando amplia
        f = f.resize(size, Image.BOX if (size[0] <= band.size[0] and size[1] <= band.size[1]) else Image.BICUBIC)
        out = Image.new('L', size)
        out.putdata([_to_srgb(v) for v in f.getdata()])
        bands.append(out)
    return Image.merge('RGB', bands)


def _trim_borders(img, tol=24):
    from PIL import ImageChops
    corner = img.getpixel((0, 0))
    diff = ImageChops.difference(img, Image.new('RGB', img.size, corner)).convert('L').point(lambda v: 255 if v > tol else 0)
    box = diff.getbbox()
    if not box:
        return img
    l, t, r, b = box
    if (r - l) < img.width * 0.5 or (b - t) < img.height * 0.5:
        return img
    if (l >= 2) + (t >= 2) + (img.width - r >= 2) + (img.height - b >= 2) < 3:
        return img
    return img.crop(box)


def prepare(path_or_img, box, fill):
    """Abre a imagem e deixa no tamanho da caixa. fill=True: preenche a caixa toda (corta o minimo do
    centro); fill=False: cabe inteira (centralizada, o resto fica transparente)."""
    im = path_or_img if hasattr(path_or_img, 'size') else Image.open(path_or_img)
    im.load()
    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    im = im.convert('RGBA')
    canvas = Image.new('RGBA', im.size, (0, 0, 0, 255))
    canvas.alpha_composite(im)
    flat = _trim_borders(canvas.convert('RGB'))
    tw, th = box
    if fill:
        fw, fh = flat.size
        if fw * th > fh * tw:
            cw = max(1, round(fh * tw / th))
            flat = flat.crop(((fw - cw) // 2, 0, (fw - cw) // 2 + cw, fh))
        elif fw * th < fh * tw:
            ch = max(1, round(fw * th / tw))
            flat = flat.crop((0, (fh - ch) // 2, fw, (fh - ch) // 2 + ch))
        size = (tw, th)
    else:
        s = min(tw / flat.width, th / flat.height)
        size = (max(1, round(flat.width * s)), max(1, round(flat.height * s)))
    img = _resize_linear(flat, size) if size != flat.size else flat
    # nitidez leve do 3DO 1.5: c + (4c - vizinhos) / 5 (raio 1, forca 0,2), sem pontilhado
    img = img.convert('RGB').filter(ImageFilter.Kernel((3, 3), [0, -1, 0, -1, 9, -1, 0, -1, 0], 5))
    out = Image.new('RGBA', box, (0, 0, 0, 0))
    out.paste(img, ((tw - size[0]) // 2, (th - size[1]) // 2))
    if fill:
        p = out.load()
        for r, n in enumerate(COVER_CORNER):
            for y in (r, th - 1 - r):
                for x in list(range(n)) + list(range(tw - n, tw)):
                    p[x, y] = (0, 0, 0, 0)
    return out


# ------------------------------------------------------------------ imagem -> tiles + paletas
def _tile_quantize(tile):
    """Tile RGBA 16x16 -> (indices 0..15, paleta de cores ng). Ate 15 cores por median cut."""
    px = list(tile.getdata())
    opaque = [p for p in px if p[3] >= 128]
    if not opaque:
        return [0] * 256, []
    rgb = Image.new('RGB', (len(opaque), 1))
    rgb.putdata([p[:3] for p in opaque])
    uniq = {ng_color(*c) for c in rgb.getdata()}
    if len(uniq) <= 15:
        pal = sorted(uniq)
        look = {c: i + 1 for i, c in enumerate(pal)}
        return [look[ng_color(*p[:3])] if p[3] >= 128 else 0 for p in px], pal
    q = rgb.quantize(colors=15, method=Image.MEDIANCUT, dither=Image.NONE)
    qp = q.getpalette()[:45]
    cent = [[float(qp[i * 3]), float(qp[i * 3 + 1]), float(qp[i * 3 + 2])] for i in range(15)]
    pts = [p[:3] for p in opaque]
    # refina o median cut com k-means (Lloyd, peso de luminancia): ~1,7 dB melhor nas capas
    W3 = (0.9, 1.77, 0.33)
    for _ in range(8):
        sums = [[0.0, 0.0, 0.0, 0] for _ in cent]
        for r, g, b in pts:
            bi, bd = 0, 1e18
            for i, c in enumerate(cent):
                d = W3[0] * (r - c[0]) ** 2 + W3[1] * (g - c[1]) ** 2 + W3[2] * (b - c[2]) ** 2
                if d < bd:
                    bd, bi = d, i
            sm = sums[bi]; sm[0] += r; sm[1] += g; sm[2] += b; sm[3] += 1
        moved = False
        for i, sm in enumerate(sums):
            if sm[3]:
                nc = [sm[0] / sm[3], sm[1] / sm[3], sm[2] / sm[3]]
                if max(abs(nc[k] - cent[i][k]) for k in range(3)) > 0.5:
                    moved = True
                cent[i] = nc
        if not moved:
            break
    pal = []
    for c in cent:
        v = ng_color(int(round(c[0])), int(round(c[1])), int(round(c[2])))
        if v not in pal:
            pal.append(v)
    rgbs = [ng_rgb(c) for c in pal]
    cache, out = {}, []
    for p in px:
        if p[3] < 128:
            out.append(0); continue
        key = p[:3]
        if key not in cache:
            bi, bd = 0, 1e18
            for i, c in enumerate(rgbs):
                d = W3[0] * (key[0] - c[0]) ** 2 + W3[1] * (key[1] - c[1]) ** 2 + W3[2] * (key[2] - c[2]) ** 2
                if d < bd:
                    bd, bi = d, i
            cache[key] = bi + 1
        out.append(cache[key])
    return out, pal


def image_to_ngi(img):
    """Imagem RGBA (largura e altura multiplas de 16) -> bytes do .ngi."""
    wt, ht = img.width // 16, img.height // 16
    pals, tiles, tile_ix, pal_ix, mapping = [], [], {}, {}, []
    for c in range(wt):
        for r in range(ht):
            idx, pal = _tile_quantize(img.crop((c * 16, r * 16, c * 16 + 16, r * 16 + 16)))
            if not pal:
                mapping.append(EMPTY_TILE)
                continue
            key = tuple(pal)
            if key not in pal_ix:
                pal_ix[key] = len(pals); pals.append(pal)
            data = encode_spr(idx)
            if data not in tile_ix:
                tile_ix[data] = len(tiles); tiles.append(data)
            mapping.append((pal_ix[key] << 9) | tile_ix[data])
    out = bytearray(b'NGI1')
    out += struct.pack('>HHHH', wt, ht, len(pals), len(tiles))
    out += struct.pack('>%dH' % len(mapping), *mapping)
    for p in pals:
        out += struct.pack('>16H', 0x8000, *(p + [0] * (15 - len(p))))
    for t in tiles:
        out += t
    return bytes(out)


MID = (96, 96)           # menu 62: capa de 96 com ate 16 paletas (covers96): as de dentro do Carrossel e os lados do FX


def image_to_ngi_pal(img, maxpal=16):
    """Imagem RGBA -> .ngi com no maximo maxpal paletas (o Carrossel guarda cada capa numa celula de 16 paletas).
    Os tiles sao agrupados pela cor media (k-means) e cada grupo ganha UMA paleta de 15 cores (a mesma quantizacao
    dos tiles, sobre os pixels do grupo todo)."""
    wt, ht = img.width // 16, img.height // 16
    crops, feats = [], []
    for c in range(wt):
        for r in range(ht):
            t = img.crop((c * 16, r * 16, c * 16 + 16, r * 16 + 16))
            px = [p for p in t.getdata() if p[3] >= 128]
            crops.append(t)
            if px:
                n = len(px)
                feats.append((sum(p[0] for p in px) / n, sum(p[1] for p in px) / n, sum(p[2] for p in px) / n))
            else:
                feats.append(None)
    live = [i for i, f in enumerate(feats) if f is not None]
    k = min(maxpal, len(live))
    grp = [-1] * len(crops)
    if k:
        # inicio: os mais distantes entre si (deterministico)
        cent = [feats[live[0]]]
        while len(cent) < k:
            best, bi = -1, live[0]
            for i in live:
                d = min((feats[i][0] - c[0]) ** 2 + (feats[i][1] - c[1]) ** 2 + (feats[i][2] - c[2]) ** 2 for c in cent)
                if d > best:
                    best, bi = d, i
            cent.append(feats[bi])
        for _ in range(12):
            for i in live:
                grp[i] = min(range(k), key=lambda j: (feats[i][0] - cent[j][0]) ** 2 * 0.9 + (feats[i][1] - cent[j][1]) ** 2 * 1.77 + (feats[i][2] - cent[j][2]) ** 2 * 0.33)
            nc = []
            for j in range(k):
                m = [feats[i] for i in live if grp[i] == j]
                nc.append(tuple(sum(v[q] for v in m) / len(m) for q in range(3)) if m else cent[j])
            if nc == cent:
                break
            cent = nc
    pals, tiles, tile_ix, mapping, gpal = [], [], {}, [], {}
    for j in sorted(set(g for g in grp if g >= 0)):
        members = [i for i in live if grp[i] == j]
        strip = Image.new('RGBA', (16 * len(members), 16), (0, 0, 0, 0))
        for n, i in enumerate(members):
            strip.paste(crops[i], (16 * n, 0))
        idx, pal = _tile_quantize(strip)
        gpal[j] = (len(pals), idx, members)
        pals.append(pal)
    tile_of = {}
    for j, (pi, idx, members) in gpal.items():
        W = 16 * len(members)
        for n, i in enumerate(members):
            t = [idx[y * W + 16 * n + x] for y in range(16) for x in range(16)]
            tile_of[i] = (pi, t)
    for i in range(len(crops)):
        if i not in tile_of:
            mapping.append(EMPTY_TILE); continue
        pi, t = tile_of[i]
        data = encode_spr(t)
        if data not in tile_ix:
            tile_ix[data] = len(tiles); tiles.append(data)
        mapping.append((pi << 9) | tile_ix[data])
    out = bytearray(b'NGI1')
    out += struct.pack('>HHHH', wt, ht, len(pals), len(tiles))
    out += struct.pack('>%dH' % len(mapping), *mapping)
    for p in pals:
        out += struct.pack('>16H', 0x8000, *(p + [0] * (15 - len(p))))
    for t in tiles:
        out += t
    return bytes(out)


def mid_from_ngi(data):
    """A capa de 96 com 16 paletas (covers96) a partir da capa .ngi de 96x96."""
    im = ngi_to_png(data)
    if im.size != MID:
        bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im)
        return image_to_ngi_pal(prepare(bg, MID, True))
    return image_to_ngi_pal(im)


def convert(path, kind):
    """kind = 'cover', 'grid' (capa pequena) ou 'shot' -> bytes do .ngi."""
    if kind == 'cover':
        return image_to_ngi(prepare(path, COVER, True))
    if kind == 'grid':
        return image_to_ngi(prepare(path, GRID, True))
    if kind == 'big':
        return image_to_ngi(prepare(path, BIG, True))
    if kind == 'mid':
        return image_to_ngi_pal(prepare(path, MID, True))
    im = prepare(path, SHOT, False)                  # tela 4:3 sem recorte (encaixa dentro de 96x72)
    pad = Image.new('RGBA', (SHOT[0], (SHOT[1] + 15) // 16 * 16), (0, 0, 0, 0))   # 96x80: ultima meia fileira transparente
    pad.paste(im, (0, 0))
    return image_to_ngi(pad)


def ngi_parse(data):
    if data[:4] != b'NGI1':
        raise ValueError('nao e um .ngi')
    wt, ht, npal, nt = struct.unpack_from('>HHHH', data, 4)
    o = 12
    mapping = list(struct.unpack_from('>%dH' % (wt * ht), data, o)); o += 2 * wt * ht
    pals = [list(struct.unpack_from('>16H', data, o + 32 * i)) for i in range(npal)]; o += 32 * npal
    tiles = [data[o + 128 * i:o + 128 * (i + 1)] for i in range(nt)]
    return wt, ht, mapping, pals, tiles


def ngi_to_png(data):
    """Mostra o .ngi como ele vai aparecer no console (para conferir no PC)."""
    wt, ht, mapping, pals, tiles = ngi_parse(data)
    im = Image.new('RGBA', (wt * 16, ht * 16), (0, 0, 0, 0))
    p = im.load()
    for i, e in enumerate(mapping):
        if e == EMPTY_TILE:
            continue
        c, r = divmod(i, ht)
        idx = decode_spr(tiles[e & 0x1FF])
        pal = pals[e >> 9]
        for k, v in enumerate(idx):
            if v:
                p[c * 16 + k % 16, r * 16 + k // 16] = ng_rgb(pal[v]) + (255,)
    return im


def mini_ngi(path_or_img):
    """A capinha do ultimo jogo (Knnnn.PRG): a capa reduzida para 24x24 num quadro de 32x32 (2x2 tiles).
    24 (nao 28) deixa 4 px de folga ao redor: a capa fica DENTRO da moldura fina do painel, sem encostar nela."""
    m = prepare(path_or_img, (24, 24), True)
    out = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    out.paste(m, (4, 4))
    return image_to_ngi(out)


def mini_from_ngi(data):
    im = ngi_to_png(data)
    bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im)
    return mini_ngi(bg)


def grid_from_ngi(data):
    """A capa pequena (64x64) a partir da capa .ngi (quando nao ha a imagem original)."""
    im = ngi_to_png(data)
    bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im)
    return image_to_ngi(prepare(bg, GRID, True))


def big_from_ngi(data):
    """A capa grande (128x128) a partir da capa .ngi de 96x96 (quando nao ha a imagem original): ampliada."""
    im = ngi_to_png(data)
    bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im)
    return image_to_ngi(prepare(bg, BIG, True))


def ngi_split(data):
    """.ngi -> (cabecalho para o .PRG do CD, tiles para o .SPR do CD)."""
    wt, ht, npal, nt = struct.unpack_from('>HHHH', data, 4)
    head = 12 + 2 * wt * ht + 32 * npal
    return data[:head], data[head:head + 128 * nt]


# ------------------------------------------------------------------ indice MEDIA.PRG
# ------------------------------------------------------------------ textos dos jogos (gamelist) e nomes oficiais (Redump)
def gl_norm(name):
    """Como o 3DO casa os nomes: sem extensao, sem (etiquetas), sem acento, sem artigo, so letras e numeros."""
    s = re.sub(r'\.(cue|iso|ngi|png|jpe?g|webp|bmp|gif|txt)$', '', name, flags=re.I)
    s = re.sub(r'\([^)]*\)|\[[^\]]*\]', ' ', s)
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower().replace('&', ' and ').replace('_', ' ')
    s = re.sub(r',\s*(the|a|an)\b', ' ', s)
    s = re.sub(r'^\s*(the|a|an)\s+', ' ', s)
    return re.sub(r'[^a-z0-9]+', '', s)


GL_KEYS = {'year': 'year', 'ano': 'year', 'developer': 'developer', 'desenvolvedor': 'developer', 'desenvolvedora': 'developer',
           'publisher': 'publisher', 'publicadora': 'publisher', 'produtora': 'publisher', 'genre': 'genre', 'genero': 'genre',
           'gênero': 'genre', 'description': 'description', 'descricao': 'description', 'descrição': 'description',
           'region': 'region', 'regiao': 'region', 'região': 'region', 'country': 'region', 'pais': 'region', 'país': 'region'}

REGION_WORDS = {'jap': 'JAP', 'japan': 'JAP', 'japao': 'JAP', 'japon': 'JAP', 'jp': 'JAP', 'jpn': 'JAP',
                'usa': 'USA', 'us': 'USA', 'eua': 'USA', 'estadosunidos': 'USA', 'eeuu': 'USA', 'america': 'USA',
                'eur': 'EUR', 'europe': 'EUR', 'europa': 'EUR', 'eu': 'EUR', 'bra': 'BRA', 'brasil': 'BRA', 'brazil': 'BRA',
                'kor': 'KOR', 'korea': 'KOR', 'coreia': 'KOR', 'corea': 'KOR', 'wld': 'WLD', 'world': 'WLD', 'mundo': 'WLD',
                'asi': 'ASI', 'asia': 'ASI', 'exp': 'EXP', 'export': 'EXP', 'exportacao': 'EXP'}


def region_from_text(v):
    """Region=Japão / USA, Europa / JAP/USA (gamelist) -> codigos do menu ("JAP/USA")."""
    out = []
    for w in re.split(r'[/,;|]', v or ''):
        k = re.sub(r'[^a-z]', '', ''.join(c for c in unicodedata.normalize('NFD', w.lower()) if unicodedata.category(c) != 'Mn'))
        c = REGION_WORDS.get(k)
        if c and c not in out:
            out.append(c)
    return '/'.join(out[:2])


def parse_gamelist(text):
    """gamelist.xx.txt: blocos separados por linha em branco; [Titulo] (varias linhas = apelidos) e Chave=Valor.
    Devolve {nome normalizado: campos}; o primeiro nome do bloco fica em campos['title']."""
    out = {}
    for block in re.split(r'\n\s*\n', text.replace('\r', '')):
        names, f = [], {}
        for line in block.split('\n'):
            m = re.match(r'^\[(.+)\]\s*$', line)
            if m:
                names.append(m.group(1)); continue
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                k = GL_KEYS.get(k.strip().lower())
                if k:
                    f[k] = re.sub(r'\s+', ' ', v).strip()
        if names and f:
            f['title'] = names[0]
            for n in names:
                out.setdefault(gl_norm(n), f)
    return out


def parse_dat(text):
    """gamelist.dat (Logiqx/Redump): os nomes oficiais dos discos."""
    import html
    return [html.unescape(t) for t in re.findall(r'<game name="([^"]+)"', text)]


REGION_TAGS = (('usa', 'USA'), ('us', 'USA'), ('japan', 'JAP'), ('jp', 'JAP'), ('europe', 'EUR'), ('eu', 'EUR'),
               ('brazil', 'BRA'), ('brasil', 'BRA'), ('korea', 'KOR'), ('world', 'WLD'), ('asia', 'ASI'), ('export', 'EXP'))


def region_codes(name):
    """As regioes da 1a etiqueta conhecida do nome: "(USA, Europe)" -> "USA/EUR" (ate 2)."""
    for grp in re.findall(r'\(([^)]*)\)', name):
        codes = []
        for w in grp.split(','):
            w = w.strip().lower()
            for t, c in REGION_TAGS:
                if w == t and c not in codes:
                    codes.append(c)
        if codes:
            return '/'.join(codes[:2])
    return ''


def title_parts(title):
    """'Fire Suplex ~ 3 Count Bout (World) (En,Ja)' -> ['Fire Suplex ~ 3 Count Bout (World) (En,Ja)', 'Fire Suplex', '3 Count Bout']"""
    base = re.sub(r'\([^)]*\)', '', title).strip()
    return [title] + [p.strip() for p in base.split(' ~ ')] if ' ~ ' in base else [title]


def game_info(folder, gl, dat):
    """Os dados do jogo da pasta: texto do gamelist (pelo nome da pasta, ou pelos nomes do disco na Redump)
    e a regiao (da etiqueta da pasta, ou do disco da Redump que casou)."""
    keys = [gl_norm(p) for p in title_parts(folder)]
    region = region_codes(folder)
    matches = [t for t in dat if any(gl_norm(p) in keys for p in title_parts(t))] if dat else []
    if matches and not region:
        order = ('WLD', 'USA', 'EUR', 'JAP')
        rs = [region_codes(t) for t in matches]
        region = next((r for o in order for r in rs if r.startswith(o)), rs[0])
    for t in matches:
        keys += [gl_norm(p) for p in title_parts(t)]
    f = next((gl[k] for k in keys if k in gl), None) if gl else None
    info = dict(f or {})
    # regiao: a etiqueta da pasta ("(Japan)") vale mais; depois Region= do gamelist; depois o disco da Redump
    own = region_codes(folder)
    info['region'] = own or region_from_text(info.get('region', '')) or region
    return info


def latin1(s, n=None):
    """Texto para o menu (Latin-1, sem as aspas e travessoes tipograficos)."""
    s = (s or '').replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('–', '-').replace('—', '-').replace('…', '...')
    b = s.encode('latin-1', 'replace')
    return b if n is None else b[:n]


def load_gamelists(folder, lang='pt'):
    """Le gamelist.<idioma>.txt (ou o pt se nao houver) e gamelist.dat de uma pasta. Devolve (gl, dat)."""
    gl, dat = {}, []
    for name in ('gamelist.%s.txt' % lang, 'gamelist.pt.txt', 'gamelist.txt'):
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            gl = parse_gamelist(open(p, encoding='utf-8-sig', errors='replace').read()); break
    p = os.path.join(folder, 'gamelist.dat')
    if os.path.isfile(p):
        dat = parse_dat(open(p, encoding='utf-8', errors='replace').read())
    return gl, dat


def display_title(t):
    """O titulo para o console: sem as etiquetas entre ( ) e [ ]."""
    return re.sub(r'\s+', ' ', re.sub(r'\s*[\(\[][^\)\]]*[\)\]]', '', t or '')).strip()


def media_index(entries, version=10):
    """entries = [(nome da pasta, capa ou None, tela ou None[, descricao ou None, info])].
    MEDIA.PRG versao 7: "NGMI", u16 quantos, u16 versao (6: Cnnnn/Snnnn.PRG = o .ngi inteiro, sem .SPR; Gnnnn.PRG = capa pequena; 7: MUSIC.PRG; 8: video em pedacos Vnnnn.PRG + VnnnnA.PRG...; 9: Knnnn.PRG = capinha 28x28), depois 128 bytes por jogo:
      0 nome (32, Latin-1, 0 no fim)  32 u16 capa  34 u16 tela  36 u16 descricao (Dnnnn.PRG)  38 u16 video (Vnnnn.PRG = o .ngv inteiro; versao 3 tinha .PRG + .SPR)
      40 ano (6)  46 regiao (10, "USA/JAP")  56 genero (16)  72 desenvolvedora (28)  100 produtora (28)
    (0xFFFF = nao tem; textos com 0 no fim)."""
    out = bytearray(b'NGMI') + struct.pack('>HH', len(entries), version)   # 10: 160 bytes por jogo, 128-159 = titulo; 11: toda capa tem a grande (Lnnnn.PRG)
    for e in entries:
        name, cov, sht = e[:3]
        dsc = e[3] if len(e) > 3 else None
        info = e[4] if len(e) > 4 else {}
        vid = e[5] if len(e) > 5 else None
        rec = bytearray(160)
        nb = latin1(name, 31)
        rec[0:len(nb)] = nb
        tb = latin1(display_title(info.get('title', '')), 31)
        rec[128:128 + len(tb)] = tb
        struct.pack_into('>HHHH', rec, 32, 0xFFFF if cov is None else cov, 0xFFFF if sht is None else sht,
                         0xFFFF if dsc is None else dsc, 0xFFFF if vid is None else vid)
        for off, ln, key in ((40, 6, 'year'), (46, 10, 'region'), (56, 16, 'genre'), (72, 28, 'developer'), (100, 28, 'publisher')):
            v = latin1(info.get(key, ''), ln - 1)
            rec[off:off + len(v)] = v
        out += rec
    return bytes(out)


def desc_file(info):
    """A descricao do jogo (Dnnnn.PRG): Latin-1 com 0 no fim (ate 1000 letras), ou None."""
    d = info.get('description', '') if info else ''
    return latin1(d[:1000]) + b'\0' if d else None


# ------------------------------------------------------------------ ISO 9660 (nivel 1, so a raiz)
def build_iso(files, volume='NGCDMENU'):
    """files = [(nome 8.3 em MAIUSCULAS, bytes)] -> imagem ISO 9660 (setores de 2048), como o xorriso
    -iso-level 1. So a pasta raiz (o Neo Geo CD le assim os arquivos do IPL.TXT)."""
    S = 2048
    files = sorted(files, key=lambda f: f[0])

    def both16(v):
        return struct.pack('<H', v) + struct.pack('>H', v)

    def both32(v):
        return struct.pack('<I', v) + struct.pack('>I', v)

    def dirrec(name_b, lba, size, isdir):
        ln = 33 + len(name_b)
        ln += ln & 1
        r = bytearray(ln)
        r[0] = ln
        r[2:10] = both32(lba)
        r[10:18] = both32(size)
        r[18:25] = bytes([125, 11, 17, 12, 0, 0, 0])     # 2025-11-17 12:00
        r[25] = 2 if isdir else 0
        r[28:32] = both16(1)
        r[32] = len(name_b)
        r[33:33 + len(name_b)] = name_b
        return bytes(r)

    # layout: 0-15 sistema, 16 PVD, 17 terminador, 18 tabela L, 19 tabela M, 20.. raiz, depois arquivos
    recs_len = 34 + 34 + sum(((33 + len(n) + 2) + ((33 + len(n) + 2) & 1)) for n, _ in files)
    root_secs = (recs_len + S - 1) // S
    root_lba = 20
    lba = root_lba + root_secs
    placed = []
    for n, d in files:
        placed.append((n, d, lba))
        lba += max(1, (len(d) + S - 1) // S)
    total = lba
    root = bytearray()
    root += dirrec(b'\0', root_lba, root_secs * S, True)
    root += dirrec(b'\1', root_lba, root_secs * S, True)
    for n, d, l in placed:
        rec = dirrec((n + ';1').encode('ascii'), l, len(d), False)
        if len(root) % S + len(rec) > S:                # registro nao atravessa setor
            root += b'\0' * (S - len(root) % S)
        root += rec
    root += b'\0' * (root_secs * S - len(root))
    pt_l = bytes([1, 0]) + struct.pack('<I', root_lba) + struct.pack('<H', 1) + b'\0\0'
    pt_m = bytes([1, 0]) + struct.pack('>I', root_lba) + struct.pack('>H', 1) + b'\0\0'
    pvd = bytearray(S)
    pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1
    pvd[8:40] = b' ' * 32
    pvd[40:72] = volume.encode('ascii')[:32].ljust(32)
    pvd[80:88] = both32(total)
    pvd[120:124] = both16(1); pvd[124:128] = both16(1); pvd[128:132] = both16(S)
    pvd[132:140] = both32(len(pt_l))
    pvd[140:144] = struct.pack('<I', 18); pvd[148:152] = struct.pack('>I', 19)
    pvd[156:190] = dirrec(b'\0', root_lba, root_secs * S, True)
    for a, b in ((190, 318), (318, 446), (446, 574), (574, 702), (702, 739), (739, 776), (776, 813)):
        pvd[a:b] = b' ' * (b - a)
    pvd[813:830] = b'2025111712000000\0'
    pvd[830:847] = b'2025111712000000\0'
    pvd[847:864] = b'0000000000000000\0'
    pvd[864:881] = b'0000000000000000\0'
    pvd[881] = 1
    term = bytearray(S); term[0] = 255; term[1:6] = b'CD001'; term[6] = 1
    img = bytearray(16 * S) + pvd + term
    img += pt_l + b'\0' * (S - len(pt_l))
    img += pt_m + b'\0' * (S - len(pt_m))
    img += root
    for n, d, l in placed:
        assert len(img) == l * S
        img += d + b'\0' * ((-len(d)) % S if d else S)
    return bytes(img)


def boot_cue(iso_name='BOOT.ISO', music=()):
    """BOOT.CUE: o ISO (faixa 1) e as musicas (faixas 2.., audio de CD em arquivos .BIN separados)."""
    out = 'FILE "%s" BINARY\r\n  TRACK 01 MODE1/2048\r\n    INDEX 01 00:00:00\r\n' % iso_name
    for k, b in enumerate(music):
        out += 'FILE "%s" BINARY\r\n  TRACK %02d AUDIO\r\n    INDEX 01 00:00:00\r\n' % (b, k + 2)
    return out


# ------------------------------------------------------------------ videos (previa da lista)
# O conversor (ngcd_video.py) vem embutido comprimido e so e carregado quando ha video:
# precisa de numpy e ffmpeg, que sao instalados na primeira vez.
VIDEO_SRC_B64 = "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"
_vm = None


def video_mod():
    global _vm
    if _vm is None:
        import importlib, subprocess
        try:
            importlib.import_module('numpy')
        except ImportError:
            print('\n  Instalando numpy (uma vez so)...')
            for extra in ([], ['--user'], ['--break-system-packages']):
                if subprocess.call([sys.executable, '-m', 'pip', 'install', 'numpy'] + extra) == 0:
                    break
            importlib.invalidate_caches()
            importlib.import_module('numpy')
        if VIDEO_SRC_B64.startswith('@@'):          # rodando do fonte
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import ngcd_video as m
            _vm = m
        else:
            import types, base64, zlib
            ns = {'__name__': 'ngcd_video'}
            exec(zlib.decompress(base64.b64decode(VIDEO_SRC_B64)).decode('utf-8'), ns)
            _vm = types.SimpleNamespace(**ns)
    return _vm


def _low_priority():
    """o processo da conversao com prioridade baixa: o computador continua leve para o resto"""
    try:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x40)   # IDLE
        else:
            os.nice(15)
    except Exception:
        pass


VIDEO_CORES = None      # quantos videos ao mesmo tempo (None = metade dos nucleos)


def _video_job(job):
    src, dst = job
    data = video_mod().convert(src)
    tmp = dst + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, dst)
    return job


def convert_videos(jobs):
    """converte varios videos ao mesmo tempo, um por nucleo do processador.
    jobs: [(origem, destino .ngv)]. Devolve (feitos, [(job, erro)])."""
    import time, concurrent.futures as cf
    if not jobs:
        return [], []
    video_mod().ffmpeg_exe()                    # instala numpy/ffmpeg antes de abrir os processos
    for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[k] = '1'                     # cada processo usa 1 nucleo (senao brigam entre si)
    cpu = os.cpu_count() or 1
    nuc = max(1, min(VIDEO_CORES or max(1, cpu // 2), cpu, len(jobs)))
    ok, err, t0 = [], [], time.time()

    def show(i):
        el = time.time() - t0
        rest = el / i * (len(jobs) - i) if i else 0
        sys.stdout.write('\r  videos: %d de %d  (%d ao mesmo tempo, faltam ~%d min %02d s)    '
                         % (i, len(jobs), nuc, rest // 60, rest % 60))
        sys.stdout.flush()
    show(0)
    todo = list(jobs)
    try:
        with cf.ProcessPoolExecutor(max_workers=nuc, initializer=_low_priority) as pool:
            futs = {pool.submit(_video_job, j): j for j in jobs}
            for fu in cf.as_completed(futs):
                j = futs[fu]
                try:
                    fu.result(); ok.append(j)
                except cf.process.BrokenProcessPool:
                    raise
                except Exception as e:
                    err.append((j, str(e)[:100]))
                todo.remove(j)
                show(len(ok) + len(err))
    except Exception as e:                      # sem processos (ambiente limitado): um de cada vez
        print('\n  (sem processos paralelos: %s; seguindo um de cada vez)' % str(e)[:60])
        _low_priority()
        for j in todo:
            try:
                _video_job(j); ok.append(j)
            except Exception as e2:
                err.append((j, str(e2)[:100]))
            show(len(ok) + len(err))
    sys.stdout.write('\n')
    return ok, err



HERE = os.path.dirname(os.path.abspath(__file__))
INI = os.path.join(HERE, "converter_tudo.ini")
ESTADO = "converter_tudo.estado.json"
ORIGENS = {"covers": {"covers", "cover", "capa", "capas"},
           "covers128": {"covers", "cover", "capa", "capas"},     # a capa grande do Carrossel sai das mesmas imagens
           "covers96": {"covers", "cover", "capa", "capas"},      # menu 62: a de 96 com 16 paletas, tambem
           "covers64": {"covers", "cover", "capa", "capas"},      # menu 63: a pequena (modo Capas)
           "covers_mini": {"covers", "cover", "capa", "capas"},   # menu 63: a capinha do Ultimo jogo
           "screenshots": {"screenshots", "screenshot", "tela", "telas"},
           "videos": {"videos", "video"}}
VIDEO_EXT = ('.mp4', '.avi', '.mkv', '.mov', '.webm', '.m4v', '.mpg', '.mpeg', '.wmv', '.flv')
PADRAO = {"midias": os.getcwd(), "capas": "s", "telas": "s", "videos": "s", "refazer": "n"}
OUT_EXT = {"covers": ".ngi", "covers128": ".ngi", "covers96": ".ngi", "covers64": ".ngi", "covers_mini": ".ngi", "screenshots": ".ngi", "videos": ".ngv"}


def find_dir(base, names):
    try:
        for d in sorted(os.listdir(base)):
            if d.lower() in names and os.path.isdir(os.path.join(base, d)):
                return os.path.join(base, d)
    except OSError:
        pass
    return None


def fontes(midias, tipo, exts):
    d = find_dir(midias, ORIGENS[tipo])
    if not d:
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d)
                  if os.path.isfile(os.path.join(d, f)) and not f.startswith("._") and os.path.splitext(f)[1].lower() in exts)


def tam_txt(n):
    return ("%.1f MB" % (n / 1048576.0)) if n >= 1048576 else ("%d KB" % ((n + 1023) // 1024))


def perg(txt, padrao):
    r = input("%s [%s]: " % (txt, padrao)).strip().strip('"')
    return r or padrao


def perg_sn(txt, padrao):
    while True:
        r = perg(txt + " (s/n)", padrao).lower()[:1]
        if r in ("s", "n", "y"):
            return "s" if r in ("s", "y") else "n"


def converter(c):
    import concurrent.futures as cf
    midias = c["midias"]
    out = os.path.join(midias, "media")
    try:
        estado = json.load(open(os.path.join(midias, ESTADO), encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    linhas, erros, t0 = [], [], time.time()
    nuc = max(1, (os.cpu_count() or 2) - 1)
    for tipo, kind, on in (("covers", "cover", c["capas"] == "s"), ("covers128", "big", c["capas"] == "s"),
                           ("covers96", "mid", c["capas"] == "s"), ("covers64", "grid", c["capas"] == "s"),
                           ("covers_mini", "mini", c["capas"] == "s"),
                           ("screenshots", "shot", c["telas"] == "s"),
                           ("videos", "video", c.get("videos", "s") == "s")):
        if not on:
            continue
        ext = OUT_EXT[tipo]
        srcs = fontes(midias, tipo, VIDEO_EXT if kind == "video" else IMG_EXT)
        if kind == "video" and not srcs:
            continue
        dest = os.path.join(out, tipo)
        os.makedirs(dest, exist_ok=True)
        fazer = []
        for s in srcs:
            o = os.path.join(dest, os.path.splitext(os.path.basename(s))[0] + ext)
            st = os.stat(s)
            sig = {"tam": st.st_size, "data": int(st.st_mtime)}
            key = tipo + "/" + os.path.basename(o)
            if kind == "video" and c["refazer"] != "s" and os.path.isfile(o) and os.path.getmtime(o) >= st.st_mtime:
                estado[key] = sig           # ja convertido (mesmo se a ultima vez foi interrompida)
                continue
            if c["refazer"] == "s" or not os.path.isfile(o) or estado.get(key) != sig:
                fazer.append((s, o, key, sig))
        feitos = 0

        def um(t):
            data = video_mod().convert(t[0]) if kind == "video" else mini_ngi(t[0]) if kind == "mini" else convert(t[0], kind)
            open(t[1], "wb").write(data)
            return t
        if kind == "video":         # um processo por nucleo (numpy de verdade em paralelo)
            ok, err = convert_videos([(t[0], t[1]) for t in fazer])
            for t in fazer:
                if (t[0], t[1]) in ok:
                    estado[t[2]] = t[3]
            for (src, _), e in err:
                erros.append("videos: %s: %s" % (os.path.basename(src), e))
            feitos = len(fazer)
        else:
          with cf.ThreadPoolExecutor(max_workers=nuc) as pool:
            for fu in cf.as_completed([pool.submit(um, t) for t in fazer]):
                feitos += 1
                try:
                    s, o, key, sig = fu.result()
                    estado[key] = sig
                except Exception as e:
                    erros.append("%s: %s" % (tipo, str(e)[:120]))
                sys.stdout.write("\r  %s: %d de %d   " % (tipo, feitos, len(fazer))); sys.stdout.flush()
        if fazer:
            sys.stdout.write("\n")
        linhas.append("%s: %d convertidas, %d ja estavam em dia" % (tipo, len(fazer), len(srcs) - len(fazer)))
        # sobras: .ngi sem origem
        tem = {os.path.splitext(os.path.basename(s))[0].lower() for s in srcs}
        sobra = [f for f in os.listdir(dest) if f.lower().endswith(ext) and os.path.splitext(f)[0].lower() not in tem]
        if sobra and srcs:
            if c.get("limpar") == "s":
                for f in sobra:
                    os.remove(os.path.join(dest, f)); estado.pop(tipo + "/" + f, None)
                linhas.append("  %d sobras apagadas" % len(sobra))
            else:
                linhas.append("  %d arquivos sem origem (rode com --limpar para apagar)" % len(sobra))
    json.dump(estado, open(os.path.join(midias, ESTADO), "w", encoding="utf-8"), indent=0, sort_keys=True)
    # media/index.json: a lista que a pagina (index.html) le do GitHub
    idx = {}
    for tipo in ("covers", "covers128", "covers96", "covers64", "covers_mini", "screenshots", "videos"):
        d = os.path.join(out, tipo)
        idx[tipo] = sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.lower().endswith(OUT_EXT[tipo])) if os.path.isdir(d) else []
    json.dump(idx, open(os.path.join(out, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n=== Pronto ===")
    for l in linhas:
        print("  " + l)
    for tipo in ("covers", "covers128", "covers96", "covers64", "covers_mini", "screenshots", "videos"):
        d = os.path.join(out, tipo)
        if os.path.isdir(d):
            fs = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(OUT_EXT[tipo])]
            print("  media/%-12s %5d arquivos  %10s" % (tipo, len(fs), tam_txt(sum(os.path.getsize(f) for f in fs))))
    print("  Tempo: %d s" % (time.time() - t0))
    if erros:
        print("\n  FALHAS (%d):" % len(erros))
        for e in erros[:15]:
            print("    " + e)


def main():
    ap = argparse.ArgumentParser(description="Converte capas e telas para a pasta media/ (formato do Neo Geo CD).")
    ap.add_argument("--midias")
    ap.add_argument("--sem-capas", action="store_true")
    ap.add_argument("--sem-telas", action="store_true")
    ap.add_argument("--sem-videos", action="store_true")
    ap.add_argument("--nucleos", type=int, help="quantos videos ao mesmo tempo (padrao: metade dos nucleos)")
    ap.add_argument("--refazer", action="store_true")
    ap.add_argument("--limpar", action="store_true")
    ap.add_argument("--sim", action="store_true")
    a = ap.parse_args()
    c = dict(PADRAO)
    ini = configparser.ConfigParser()
    if os.path.isfile(INI):
        try:
            ini.read(INI, encoding="utf-8")
            c.update({k: v for k, v in ini["converter"].items() if k in PADRAO})
        except Exception:
            pass
    c["refazer"] = "n"
    if a.midias:
        c["midias"] = a.midias
    if not a.sim:
        print("\n=== Neo Geo CD - converter tudo ===\n")
        while True:
            c["midias"] = perg("1. Pasta das midias (onde estao covers e screenshots)", c["midias"])
            if os.path.isdir(c["midias"]):
                break
            print("   Essa pasta nao existe.")
        print("   Achei: %d capas, %d telas, %d videos.\n" % (len(fontes(c["midias"], "covers", IMG_EXT)), len(fontes(c["midias"], "screenshots", IMG_EXT)),
                                                       len(fontes(c["midias"], "videos", VIDEO_EXT))))
        c["capas"] = perg_sn("2. Converter as CAPAS (todos os tamanhos: 128, 96, 96 de 16 paletas, 64 e a capinha 24)?", c["capas"])
        c["telas"] = perg_sn("3. Converter as TELAS (96x72)?", c["telas"])
        c["videos"] = perg_sn("4. Converter os VIDEOS (previa de 15 s; usa metade dos nucleos, em prioridade baixa)?", c["videos"])
        c["refazer"] = perg_sn("5. Refazer TUDO? (n = so o que e novo ou mudou)", "n")
    if a.sem_capas: c["capas"] = "n"
    if a.sem_telas: c["telas"] = "n"
    if a.sem_videos: c["videos"] = "n"
    if a.nucleos:
        global VIDEO_CORES
        VIDEO_CORES = a.nucleos
    if a.refazer: c["refazer"] = "s"
    c["limpar"] = "s" if a.limpar else "n"
    if not os.path.isdir(c["midias"]):
        raise SystemExit("Pasta nao existe: " + c["midias"])
    ini["converter"] = {k: v for k, v in c.items() if k in ("midias", "capas", "telas", "videos")}
    try:
        ini.write(open(INI, "w", encoding="utf-8"))
    except OSError:
        pass
    converter(c)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido. O que ja foi convertido fica.")
