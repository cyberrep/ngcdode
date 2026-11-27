/*
 * NGCD extension commands for the Neo CD SD Loader MCU firmware.
 * Copyright (C) 2026 NGCD project. Based on Neo CD SD Loader by Sean Gonsalves (furrtek).
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * All original commands (0..13) are unchanged. Everything new lives under
 * command 14 (MCU_CMD_NGCD), with a subcommand in param byte 1.
 *
 * Command buffer layout (cmd_buffer.data[]):
 *   [0]  = 14
 *   [1]  = subcommand
 *   [2..3] = small arguments (see each subcommand)
 *   [4..63] = path, zero-terminated (max NGCD_PATH_MAX chars). The console may send
 *             up to 64 bytes per command; the stock loader/menus always send 32.
 *
 * Reply (reply buffer, read by the console as words):
 *   [0] = 0xFE ok / 0x0E error
 *   [1] = value (error code on failure, see NGCD_E_*; FatFs FRESULT codes are 1..19)
 *   [2..7] = small results (big endian)
 *   [8..] = data
 */
#ifndef __NGCD_EXT_H__
#define __NGCD_EXT_H__

#include "main.h"

#define MCU_CMD_NGCD        14

#define NGCD_EXT_VERSION    1
#define NGCD_PATH_MAX       59      /* data[4..62] + terminator at data[63] */
#define NGCD_READ_MAX       6144    /* bytes per READ (3 x 2048) */

/* Subcommands */
#define NGCD_INFO       0x00    /* -> "NGCX", ext version, caps, MCU version, limits */
#define NGCD_FREE       0x01    /* -> total KB, free KB, cluster bytes, FS type */
#define NGCD_OPEN       0x02    /* path -> open for reading (file A). [2..5] size */
#define NGCD_READ       0x03    /* [2..5] offset, [6..7] length -> [2..3] bytes read, data at [8] */
#define NGCD_CLOSE      0x04    /* close file A */
#define NGCD_OPENW      0x05    /* [2] mode, path -> open for writing (file W) */
#define NGCD_MKDIR      0x06    /* path (all levels) -> value 1 if it already existed */
#define NGCD_DELETE     0x07    /* path (file or empty folder) */
#define NGCD_RENAME     0x08    /* [2] bit0 = overwrite; old path, '\0', new path */
#define NGCD_STAT       0x09    /* path -> [2] attr, [3..6] size; data: fdate, ftime */
#define NGCD_SETPOS     0x0A    /* [2..5] offset, [6] bit0 = truncate there (file W) */
#define NGCD_LISTDIR    0x0B    /* [2..3] first entry, path -> records */
#define NGCD_OPENCD     0x0C    /* path -> serve this file as the CD data track (LOADSECT) */
#define NGCD_CLOSEW     0x0D    /* close file W (reports earlier write errors) */

/* OPENW modes */
#define NGCD_W_CREATE   0       /* create or truncate */
#define NGCD_W_NEW      1       /* fail (NGCD_E_EXISTS) if it exists */
#define NGCD_W_APPEND   2       /* open or create, position at end */
#define NGCD_W_UPDATE   3       /* open existing, position 0, no truncate */

/* Our error codes (FatFs FRESULT values 1..19 are passed through as-is) */
#define NGCD_E_PATH     100     /* empty or too long path */
#define NGCD_E_NOTOPEN  101     /* file A / W not open */
#define NGCD_E_LENGTH   102     /* bad READ length */
#define NGCD_E_SUBCMD   103     /* unknown subcommand */
#define NGCD_E_WRITE    104     /* a write during the transfer failed */
#define NGCD_E_EXISTS   105     /* OPENW NEW / RENAME without overwrite: target exists */
#define NGCD_E_ARGS     106     /* bad arguments */

/* Capability bits (INFO [6..7] / data) */
#define NGCD_CAP_FREE   0x0001
#define NGCD_CAP_READ   0x0002
#define NGCD_CAP_WRITE  0x0004
#define NGCD_CAP_DIRS   0x0008
#define NGCD_CAP_LIST   0x0010
#define NGCD_CAP_OPENCD 0x0020
#define NGCD_CAP_PREFETCH 0x0040

extern FIL fil_wr;
extern FIL *store_fil;

void ngcd_ext_exec(void);
void ngcd_ext_invalidate(void);

#endif
