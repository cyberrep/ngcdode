# 📝 Histórico de versões

[← Voltar ao início](README.pt.md) · [English](CHANGELOG.md) · **Português** · [Español](CHANGELOG.es.md)

Tudo o que mudou no **menu** (`BOOT.ISO`), no **firmware NGCD** (loader + MCU) e nas **ferramentas** (página web e `generate_usb.py`), da versão mais nova para a mais antiga.

- [Menu — 1.0](#-menu--10)
- [Menu — antes da 1.0 (versões 0.x)](#-menu--antes-da-10-versões-0x)
- [Firmware NGCD](#-firmware-ngcd)
- [Ferramentas (página, generate_usb.py)](#-ferramentas-página-generate_usbpy)

---

## 🚀 Menu — 1.0

Primeira versão pública. Reúne tudo o que foi feito nas versões de desenvolvimento (0.x), descritas abaixo, e acrescenta:

- 📊 **Barras do SD e da NVRAM redesenhadas.** O nome na letra do menu com sombra, o trilho escuro com o usado em cor (azul no SD, amarelo na NVRAM) e o espaço livre alinhado à direita, com as letras mais juntas.
- 🌙 **Protetor de tela como no 3DO**: o nosso logo e cada console, **um de cada vez**, passeando pela tela escura; a cada 2 batidas na borda troca de imagem. Os textos e as barras do menu não aparecem mais por cima.
- 📜 **Nome comprido rola até o fim**: com o MCU NGCD 00.12 o menu lê o nome inteiro da pasta (até 63 letras; antes parava na 25ª) e o título do gamelist inteiro (antes parava na 31ª).
- 💿 **Capa padrão com os cantos arredondados**, como as capas de verdade.
- 🎞️ **Carrossel FX mais fluido**: lê antes as capas para o lado em que você está andando, 2 passos à frente.
- **Drive de CD**: saiu a opção "Iniciar pelo drive de CD" das Opções; a caixa **CD** do menu principal já faz isso.
- 🔧 **Ajustes do teste no console**: barras do SD e da NVRAM mais compridas, com o número mais espaçado e a unidade (G, M, K) um pouco à direita; teste de controle com o rodapé padrão (botão **B**: segure para sair); número de série na mesma linha dos outros itens; aba **CONSOLE** no gerenciador de armazenamento; protetor de tela sem pedaços sumindo enquanto o menu ainda carregava capas ou vídeo.
- **Sobre** mostra **Menu 1.00**, o firmware do loader, o MCU e o CPLD.

O que a 1.0 tem, em resumo: 6 modos de exibição (Lista, Capas, Carrossel, Carrossel FX, Vitrine e Faixa), prévia em vídeo, capas e telas em pacote, favoritos, recentes e estatísticas, filtro por gênero e país, ficha de cada jogo em 3 idiomas, gerenciador de saves, caixa CD para o drive de CD, extração da BIOS, atualização do firmware pelo console, 10 músicas, 10 fundos e protetor de tela.

---

## 🧪 Menu — antes da 1.0 (versões 0.x)

As versões de desenvolvimento, da mais nova para a mais antiga.

### 📦 0.70 — Capas em pacote e Carrossel FX deslizando

**Capas e telas em pacote**
- 📦 **Todas as capas num arquivo só** (`.media/covers/cover.pak`, com os 5 tamanhos de cada jogo) e as telas em outro (`.media/screenshots/screenshots.pak`). O menu abre o pacote uma vez e vai direto à imagem, em vez de procurar cada arquivo numa pasta com centenas deles.
- Imagem fora do pacote, ou cartão sem pacote: o menu usa os arquivos soltos.
- Na página, *Mídias → Cartão*: **Formato das capas e telas: PAK ou Individual**. Ao trocar de formato, a página converte o que já está no cartão.

**Carrossel FX**
- 🎞️ **As capas deslizam ao andar**: cada uma vai da sua posição para a da vizinha, girando e mudando de tamanho.
- **Bem mais rápido**: as contas de multiplicar e dividir do menu passaram a usar as instruções do próprio processador (o menu inteiro ficou mais leve), cada capa só muda de tamanho e posição a cada quadro, e a capa grande do vizinho já fica na memória.
- A capa padrão (jogo sem capa) também fica virada para o centro, com reflexo.
- Corrigidos: uma faixa de outra capa embaixo do reflexo (só no console) e a barra do topo e o rodapé cortados do lado direito.

### 📦 0.63 — Correções do teste no console
- Carrossel FX não trava mais ao entrar sem as capas de 96.
- Vitrine e Faixa sem os pontinhos na descrição; Faixa sem meia capa por cima da capa padrão.
- Botões do rodapé mais juntos, para caber na TV.

### 📦 0.62 — Carrossel FX, Vitrine e Faixa
- 🖼️ **Três modos de exibição novos**: **Carrossel FX** (capas dos lados viradas para o centro, em trapézio, com reflexo no chão), **Vitrine** (capa grande, ficha e a descrição inteira com rolagem) e **Faixa** (tela e dados em cima, fileira de capas embaixo).
- **Carrossel com as capas de dentro maiores** (96, entre a de fora e a do centro), numa capa nova de 16 paletas.
- Rodapé de Jogos com **C FAV**, **D INFO** e o botão **SELECT FILTRO**; SELECT ou START abrem o filtro.

### 📦 0.59 a 0.61 — Filtro, extração da BIOS e menu em módulos
- 🔎 **Filtro** por gênero e país, com caixinhas `[ ]`/`[X]`, quantos jogos passam e os botões **A MARCAR**, **B OK**, **C LIMPAR**.
- 💾 **Extrair ROM**: o console copia a própria BIOS (512 KB) para `.roms/` (ex. `frontload_japao.bin`), sem duplicar.
- 🧩 **Menu em módulos**: Opções, saves, drive de CD, filtro e os modos novos só são lidos quando abrem. A memória fixa do menu ganhou ~68 KB livres.
- Os atalhos do loader (A+B+C+D com START/SELECT) não saem mais do menu sem querer.
- Lista com Vídeo: jogo sem vídeo mostra "Sem vídeo".
- Medidor de tempo do CD na faixa de informações da lista.
- A pasta dos firmwares instalados passou a ser `.wad`.

### 📦 0.52 a 0.58 — Cartão no padrão ODE
- 🗂️ **Tudo no padrão ODE**: o menu em `.boot`, as mídias em `.media`, as opções, favoritos, recentes, estatísticas e a lista de jogos em `.config` (`ngcd*.ode`, texto, uma opção por linha), os saves em `.saves`.
- **Mídias fora do `BOOT.ISO`**: o menu ficou pequeno e as capas são lidas direto do cartão, pelo nome do jogo.
- **Vídeo da lista sem travar**: lido aos poucos, começa assim que o primeiro quadro chega.
- **Capas guardadas na memória** e as vizinhas lidas com o controle parado.
- **Topo como no 3DO**: logo no meio, barras do SD e da NVRAM, bandeira da região.
- Opções novas: Barra do SD, Barra da NVRAM e Bandeira (mostrar/esconder).
- Carrossel com a moldura por fora da capa e tamanhos em degraus (48, 64, 128).
- O firmware já instalado não é regravado a cada vez que liga.

### 📦 0.31 a 0.45 — Caixa do jogo nova e Carrossel
- 🎠 **Carrossel**: capa grande de 128 × 128 no centro e duas de cada lado.
- **Info dos jogos**: sobre a mídia ou abaixo dela; tela e vídeo em 4:3.
- **Fim dos riscos ao carregar** capa, tela e vídeo: as cores só são gravadas enquanto a TV não desenha.
- A imagem anterior fica na caixa até a nova estar pronta.
- **Protetor de tela** com os dois consoles e o logo; bandeira da região no topo.
- Vezes jogado na barra de baixo.
- **Espaço do cartão SD** com o MCU NGCD 00.12.

### 📦 0.21 a 0.30 — Caixa CD, saves e leitura silenciosa
- 💿 **Caixa CD** na tela principal, com o disco girando: inicia o CD que está no leitor.
- 💾 **Gerenciador de armazenamento**: console e cartão SD, copiar, restaurar e apagar saves; backup da memória inteira.
- 🤫 **Leitura silenciosa**: o cartão só é lido enquanto a TV não desenha (sem chuvisco na imagem).
- **Sem piscadas**: cada tela é montada por trás e aparece inteira.
- **Nome oficial dos jogos** (Título ou Pasta).
- Faixas translúcidas na capa (transparência de 0 a 100%), capinha do último jogo, Sobre e Agradecimentos.

### 📦 0.1 a 0.20 — A base
- **0.20** — Janela padrão para perguntas, andamento e resultado; drive de CD, modo desenvolvedor, Debug DIPs e medidor de tempo.
- **0.17** — 🎵 10 músicas de fundo, com volume e Aleatória; vídeo começando mais rápido.
- **0.15 e 0.16** — Modo Capas (grade); Opções em sanfona; Letras para o menu todo.
- **0.10 a 0.14** — 🎬 Vídeo na lista; capas com brilho; descrição com margens e troca de jogo.
- **0.7 a 0.9** — Sons, 9 fundos de tela, faixas de ano/país e estrela/gênero; 3 idiomas e os dados de cada jogo; 16 arranjos da tela principal; estrela com efeito ao favoritar.
- **0.4 a 0.6** — ⭐ Favoritos, recentes e estatísticas; teste de controle, ajuste de imagem, acentos; informações do console e do SD Loader; capas e telas.
- **0.1 a 0.3** — A primeira versão: tela principal, lista de jogos e a fonte do padrão ODE; o loader carrega o menu sozinho ao ligar; opções e saves no cartão; região, logo e LEDs do loader.

---

## 🧩 Firmware NGCD

O firmware vem num `.WAD` com três partes: o **loader** (o remendo da BIOS do console), o **MCU** (o programa do microcontrolador do SD Loader) e o **CPLD**. Veja a explicação no [README](README.pt.md#-o-que-tem-no-firmware-wad-loader-mcu-e-cpld).

### NGCD 00.12 (loader NGCD 12 · MCU NGCD 00.12 · CPLD 00.03)

**MCU NGCD 00.12**
- 📁 **Comandos de arquivo** para o menu: abrir, ler em qualquer ponto (*seek*), gravar, listar pastas, criar pastas, apagar e renomear.
- 📊 **Espaço do cartão SD** (total e livre).
- É o que permite as mídias em `.media`, os pacotes de capas, as opções em `.config`, o gerenciador de saves, a extração da BIOS e a atualização pelo menu. Compatível com tudo o que o MCU 00.11 fazia.

**Loader NGCD 12**
- A tela do SD Loader mostra a versão como **NGCD 00.12**.
- 🚀 **Carrega o menu NGCD sozinho ao ligar**, da pasta `.boot` (ou `_BOOT`, nos cartões antigos).
- 🛟 **Modo de segurança**: segurando A, B, C ou D ao ligar, vai direto ao menu original do SD Loader.
- **Tela de aviso** quando o cartão não tem o menu: **A** = menu do SD Loader, **C** = atualizar pelo `.WAD` da raiz.
- **Leitura silenciosa** a pedido do menu (sem chuvisco ao ler o cartão).
- LED com a opção **Desligado**.
- Região, animação ao ligar e LEDs escolhidos no menu valem já no próximo jogo.

---

## 🛠️ Ferramentas (página, generate_usb.py)

### 📅 Novembro de 2026 (menu 1.0)
- **Página**: o cabeçalho mostra a versão do menu (1.0) e do firmware.
- **Página e `generate_usb.py`**: **Formato das capas e telas: PAK ou Individual**, com a conversão do que já está no cartão (`--individual` no gerador).

### 📅 Novembro de 2026 (menus 0.52 a 0.63)
- **`generate_usb.py` refeito no esquema da página** (`.boot`, `.media`, `.config`) e agora **acerta os discos** para o SD Loader: `.chd` (chdman), `.nrg`, `.img` + `.ccd`, `.iso`/`.img`/`.bin` sem `.cue`, `.iso` + mp3/ogg/flac (as faixas viram `.wav`), `.zip`/`.7z`, jogo solto na raiz e `.cue` com TAB.
- A página **só copia** o menu e o firmware da pasta do kit, e só quando mudaram; gravar de novo não regrava o que já está no cartão.
- A página copia o menu para `.boot` e avisa quando o console ainda está com o loader antigo.
- Capas de 96 de 16 paletas para o Carrossel, criadas também para as capas que já estão no cartão.

### 📅 Novembro de 2026 (menus 0.6 a 0.30)
- **Página web** que grava o cartão inteiro: Passo a passo, Como usar, Manual, Novidades, Renomear pastas, Procurar o jogo (para o jogo sem capa), aviso de nomes com mais de 25 letras e de mais de 200 jogos, ouvir as músicas do menu.
- **`generate_usb.py`**: capas, telas, vídeos e textos dos jogos, com o assistente em passos.
