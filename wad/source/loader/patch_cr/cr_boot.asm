; CyberRep (Rodrigo Tadeu Pasetchny) - 2026
; Extensao do Neo CD SD Loader (GPL, mesmo licenciamento do projeto original)
;
; 1) Recado do boot.iso: o programa do boot.iso grava em $11C7F0 o valor 'CRBT' e em
;    $11C7F4 o indice do jogo escolhido (o mesmo indice que o MCU devolve no GETGAMES)
;    e chama SYS_CDPLAYER. O menu volta, le o recado e carrega o jogo.
; 2) Autoboot: na primeira vez que o menu monta a lista depois de ligar/resetar,
;    se existir uma pasta ".boot" (NGC17) ou "_BOOT" (com .cue) ela e carregada sozinha.
;    Segurando A, B, C ou D nesse momento, fica no menu normal.
; O carregamento usa exatamente o mesmo caminho do botao A (LoadGame).

CR_MAGIC    equ $43524254       ; 'CRBT'

; Assinatura que o boot.iso procura ("Loader: CR10"), seguida do modelo do patch
; (1 = front, 2 = top 1/2, 3 = top 3): o menu mostra a foto do console certo.
CRSignature:
    dc.b "CRWAD18",0          ; NGC18 (mostrado como NGCD 00.12): modo de seguranca (botao segurado) e A/C na tela de aviso. NGC17: procura .boot e depois _BOOT. NGC16: tela sem cartao/BOOT legivel (paleta 0, sem arco-iris) e sem a opcao do menu do SD Loader; inclui NGC14 (leitura silenciosa)
    dc.b TARGET,0

; CR8: no inicio do SetupMain decide se o video fica apagado (vai carregar boot.iso/jogo).
; Mesmo fluxo do CR1 (que carregou o boot.iso no console), so que sem aparecer na tela.
CRDecideHide:
    clr.b   CRHide
    cmpi.l  #CR_MAGIC,CRMailMagic
    beq     .esconde                ; Jogo pedido pelo boot.iso
    tst.b   CRAutoBootDone
    bne     .fim                    ; Autoboot ja feito: menu normal
    move.b  REG_P1CNT,d0            ; Botao segurado ao ligar (ativo em 0) = menu normal
    and.b   REG_P2CNT,d0
    not.b   d0
    andi.b  #$F0,d0
    beq     .esconde
    ; NGC17: MODO DE SEGURANCA - com o botao segurado vai direto ao menu do SD Loader: sem autoboot (.boot/_BOOT)
    ; e sem a tela de aviso (antes o aviso aparecia igual e nao tinha saida)
    st.b    CRMsgSkip
    st.b    CRAutoBootDone
    bra     .fim
.esconde:
    st.b    CRHide
    move.b  #0,REG_ENVIDEO
.fim:
    rts

; CR9: substitui os "move.b #1,REG_ENVIDEO" da tela de loading do BIOS (e do DMAClearPalettes).
; Com o video escondido (indo para o boot.iso/jogo), a tela do macaco "NOW LOADING" nao aparece.
CRVideoOnLoad:
    tst.b   CRHide
    bne     .fim
    move.b  #1,REG_ENVIDEO
.fim:
    rts

; CR9: fim do DMAClearPalettes. CRHide $FF = ainda carregando (fica apagado);
; 2 = loading acabou e as paletas estao pretas -> liga o video para o jogo/boot.iso.
CRVideoOnPal:
    cmpi.b  #$FF,CRHide             ; st.b = $FF: ainda carregando
    beq     .fim
    clr.b   CRHide
    move.b  #1,REG_ENVIDEO
.fim:
    rts

; Liga o video (mostra o menu) se estava apagado
CRShowVideo:
    tst.b   CRHide
    beq     .fim
    clr.b   CRHide
    move.b  #1,REG_ENVIDEO
.fim:
    rts

; Chamado no fim do SetupMain (lista de jogos ja montada em FileList)
CRSetupPending:
    move.l  d6,-(sp)                ; NGC17: d6 = o 1o caractere procurado ('.' ou '_')
    move.b  #$FF,CRPendingLoad
    clr.b   CRPendingAuto
    tst.w   TotalFileCount
    beq     .done                   ; Sem cartao/sem jogos: nada a fazer

    ; 1) Recado do boot.iso tem prioridade
    cmpi.l  #CR_MAGIC,CRMailMagic
    bne     .nomail
    move.b  CRMailIndex,CRPendingLoad   ; CR9: consumido so no CRRunPending
    bra     .done
.nomail:

    ; 2) Autoboot, so uma vez por ligada
    tst.b   CRAutoBootDone
    bne     .done                   ; CR9: marcado so no CRRunPending

    ; NGC17: procura ".boot" (padrao ODE, como .config/.media/.saves) e, se nao tiver, "_BOOT" (cartoes antigos)
    move.b  #'.',d6
.pass:
    lea     FileList,a0
    move.w  TotalFileCount,d7
    subq.w  #1,d7
.search:
    lea     2(a0),a1                ; Nome comeca depois de flags+indice
    cmp.b   (a1)+,d6
    bne     .next
    move.b  (a1)+,d0
    andi.b  #$DF,d0                 ; Maiuscula
    cmpi.b  #'B',d0
    bne     .next
    move.b  (a1)+,d0
    andi.b  #$DF,d0
    cmpi.b  #'O',d0
    bne     .next
    move.b  (a1)+,d0
    andi.b  #$DF,d0
    cmpi.b  #'O',d0
    bne     .next
    move.b  (a1)+,d0
    andi.b  #$DF,d0
    cmpi.b  #'T',d0
    bne     .next
    tst.b   (a1)                    ; Nome tem que acabar aqui ("_BOOT")
    bne     .next
    move.b  1(a0),CRPendingLoad     ; Indice do MCU (mesmo byte que o botao A usa)
    st.b    CRPendingAuto
    bra     .done
.next:
    lea     32(a0),a0
    dbra    d7,.search
    cmpi.b  #'_',d6
    beq     .done                   ; ja tentou as duas
    move.b  #'_',d6
    bra     .pass
.done:
    move.l  (sp)+,d6
    rts


; Chamado a cada quadro do menu principal, antes do teste do botao A
CRRunPending:
    move.b  CRPendingLoad,d1
    cmpi.b  #$FF,d1
    beq     .none
    move.b  #$FF,CRPendingLoad      ; Executa so uma vez
    clr.l   CRMailMagic             ; CR9: consome o recado aqui (sobrevive a SetupMain repetido)
    st.b    CRAutoBootDone
    tst.b   CRPendingAuto
    beq     .go
    clr.b   CRPendingAuto
    ; Autoboot: botao A/B/C/D segurado (P1 ou P2) cancela e fica no menu
    move.b  BIOS_P1CURRENT,d0
    or.b    BIOS_P2CURRENT,d0
    andi.b  #$F0,d0
    bne     .cancelado
.go:
    ; CR10: o menu (boot.iso) pode ter mudado as opcoes do loader na memoria do console:
    ; rele antes de carregar (regiao) e manda as cores do LED ao MCU
    move.b  d1,-(sp)
    jsr     LoadSettings
    st.b    SetMCUConfig
    jsr     GetMCUStatus
    move.b  (sp)+,d1
    move.w  #$0000,FixWriteConfig   ; Igual ao caminho do botao A
    moveq.l #0,d0
    move.b  d1,d0
    jsr     LoadGame
    ; Conferido so agora (como o proprio LoadGame): se nao comecou a carregar, mostra o menu
    cmpi.w  #SCREEN_MAIN,CurrentScreen
    bne     .cancelado              ; Abriu mensagem de erro
    tst.b   IsLoading
    beq     .cancelado
    btst.b  #7,CDValidFlag
    beq     .cancelado
.none:
    rts
.cancelado:
    jmp     CRShowVideo


; ---- NGC13: a tela de aviso ----
; Ligou o console e nao ha nada para carregar: sem cartao, ou o cartao nao tem a pasta _BOOT (BOOT.ISO).
; Em vez do menu do SD Loader, uma tela no estilo do nosso menu com o aviso. Colocar o cartao carrega o menu
; sozinho (o MCU avisa e o SetupMain roda de novo); A abre o menu do SD Loader (ate desligar).
SCREEN_CRMSG equ 2

CRNothingToLoad:
    clr.b   CRMsgOn
    tst.b   CRMsgSkip
    bne     .fim                    ; ja escolheu o menu do SD Loader
    tst.b   CRAutoBootDone
    bne     .fim                    ; ja carregou o menu (voltou de um jogo): o menu normal
    st.b    CRMsgOn
    move.w  #SCREEN_CRMSG,CurrentScreen
    move.b  #1,REG_DISBLSPR         ; sem os sprites do menu do SD Loader
    move.w  #$0112,BACKDROP         ; o fundo do nosso menu
    jsr     ClearFix
    move.w  #$0500,FixWriteConfig   ; NGC15: paleta 0 (legivel) tambem no titulo - a paleta 1 do loader era o "arco-iris"
    lea     CRStrTitle,a0
    move.w  #FIXMAP+8+(9*32),d0
    jsr     WriteFix
    btst.b  #7,MCUStatus
    bne     .temcartao
    lea     CRStrNoCard1,a0
    move.w  #FIXMAP+11+(7*32),d0
    jsr     WriteFix
    lea     CRStrNoCard2,a0
    move.w  #FIXMAP+12+(10*32),d0
    jsr     WriteFix
    lea     CRStrNoCard3,a0
    move.w  #FIXMAP+15+(3*32),d0
    jsr     WriteFix
    lea     CRStrNoCard4,a0
    move.w  #FIXMAP+16+(3*32),d0
    jsr     WriteFix
    bra     .keys
.temcartao:
    lea     CRStrNoBoot1,a0
    move.w  #FIXMAP+11+(8*32),d0
    jsr     WriteFix
    lea     CRStrNoBoot2,a0
    move.w  #FIXMAP+12+(11*32),d0
    jsr     WriteFix
    lea     CRStrNoBoot3,a0
    move.w  #FIXMAP+15+(3*32),d0
    jsr     WriteFix
    lea     CRStrNoBoot4,a0
    move.w  #FIXMAP+16+(3*32),d0
    jsr     WriteFix
.keys:                              ; NGC17: as teclas (A = menu do SD Loader, C = atualizar pelo .WAD da raiz)
    lea     CRStrKeys1,a0
    move.w  #FIXMAP+20+(3*32),d0
    jsr     WriteFix
    lea     CRStrKeys2,a0
    move.w  #FIXMAP+21+(3*32),d0
    jsr     WriteFix
.fim:
    rts

; VBlank da tela de aviso: o cartao entrou (o MCU avisa) -> monta tudo de novo (o autoboot carrega o menu);
; A -> o menu do SD Loader
CRMsgVBL:
    move.b  d0,REG_DIPSW
    move.w  #$0112,BACKDROP         ; o fundo do nosso menu (o loader troca o backdrop depois do SetupMain)
    ; NGC17: A = o menu do SD Loader (ate desligar)
    TESTCHANGE CNT_A
    beq     .no_a
    st.b    CRMsgSkip
    clr.b   CRMsgOn
    jmp     SetupMain
.no_a:
    ; NGC17: C = atualizar pelo .WAD da raiz (o mesmo "Update firmware" do menu do SD Loader). Monta o menu do SD Loader
    ; antes: se nao der (sem .WAD), a mensagem do loader aparece la e o usuario continua no menu.
    TESTCHANGE CNT_C
    beq     .no_c
    btst.b  #7,MCUStatus
    beq     .no_c                   ; sem cartao: nada a atualizar
    st.b    CRMsgSkip
    clr.b   CRMsgOn
    jsr     SetupMain
    jmp     DoUpdate
.no_c:
    tst.b   CardEvent
    beq     .fim                    ; sem cartao: so espera o cartao (nao ha a opcao de ir ao menu do SD Loader)
    clr.b   CardEvent
    clr.b   CRMsgOn
    jmp     SetupMain
.fim:
    rts

; (a fonte do loader nao tem acentos)
CRStrTitle:
    dc.b "NEO GEO CD - SD LOADER",0
CRStrNoCard1:
    dc.b "Cartao SD nao identificado",0
CRStrNoCard2:
    dc.b "SD card not detected",0
CRStrKeys1:
    dc.b "A: menu do SD Loader  C: atualizar",0
CRStrKeys2:
    dc.b "A: SD Loader menu  C: update (WAD)",0
CRStrNoCard3:
    dc.b "Coloque o cartao com a pasta .boot",0
CRStrNoCard4:
    dc.b "Insert a card with the .boot folder",0
CRStrNoBoot1:
    dc.b "BOOT.ISO nao encontrado",0
CRStrNoBoot2:
    dc.b "BOOT.ISO not found",0
CRStrNoBoot3:
    dc.b "Copie a pasta .boot para o cartao",0
CRStrNoBoot4:
    dc.b "Copy the .boot folder to the card",0
    ALIGN 2


; ---- NGC14: leitura silenciosa ----
; No console, enquanto o MCU le o cartao e os dados passam pelo CPLD, aparecem tracinhos brancos na imagem
; ("chuvisco"). O menu liga CRQuiet antes de pedir um arquivo: o setor so e pedido e os dados so sao copiados
; enquanto a TV nao desenha (linhas $1F0-$1FF e $0F8-$10B do contador). Fica mais lento (uns 1,2 KB por quadro),
; mas nada aparece. As interrupcoes ficam ligadas. Se o contador de linhas nunca disser VBlank, segue sem esperar.

; Espera a janela (com limite de tempo). Estraga d0 e d6.
CRQuietWait:
    move.w  #$7FFF,d6
.w:
    move.b  d0,REG_DIPSW
    move.w  REG_LSPCMODE,d0
    lsr.w   #7,d0
    cmpi.w  #$01F0,d0
    bhs     .ok
    cmpi.w  #$010C,d0
    blo     .ok
    dbra    d6,.w
.ok:
    rts

; a1: destino; SectorLoadSize(a5) bytes (ate 2048). Grupos de 8 bytes, cada um so dentro da janela.
CRGetSectorQuiet:
    move.l  d6,-(sp)
	lea     CPLDREG_DATA,a0
	lea     CPLDREG_STAT,a2
	moveq.l #$0004,d1
    move.l  SectorLoadSize(a5),d7
.group:
    jsr     CRQuietWait
    cmpi.l  #8,d7
    blo     .bytes
	move.l  (a0),(a1)+
	move.l  (a0),(a1)+
    subq.l  #8,d7
    beq     .done
.wait:                         ; CPLDREG_STAT bit 2 (REFILL_PENDING)
    move.w  (a2),d0
    and.w   d1,d0
    bne     .wait
    bra     .group
.bytes:                        ; o resto (menos de 8 bytes)
	move.l  (a0),d0
    REPT 4
	rol.l   #8,d0
    move.b  d0,(a1)+
	subq.l  #1,d7
	beq     .done
	ENDM
	move.l  (a0),d0
    REPT 4
	rol.l   #8,d0
    move.b  d0,(a1)+
	subq.l  #1,d7
	beq     .done
	ENDM
.done:
	move.b  d0,REG_DIPSW
    move.l  (sp)+,d6
    rts
