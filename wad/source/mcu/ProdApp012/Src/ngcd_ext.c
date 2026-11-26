/*
 * NGCD extension commands for the Neo CD SD Loader MCU firmware.
 * Copyright (C) 2026 NGCD project. Based on Neo CD SD Loader by Sean Gonsalves (furrtek).
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * See ngcd_ext.h for the protocol.
 *
 * Files used:
 *   fil_data  - unchanged: CD data/audio track of the selected game (and our OPENCD)
 *   fil_ext   - file A: random-access reads (OPEN/READ/CLOSE), with FatFs fast seek
 *   fil_wr    - file W: writes (OPENW, then STORESAVE 2 + words, then CLOSEW)
 * Reading with fil_ext does not disturb the CD track the console has open, so a menu
 * running from a CD image can read its media files without re-selecting its own CD.
 */
#include <string.h>
#include "ngcd_ext.h"
#include "console_cmd.h"
#include "cdda.h"
#include "leds.h"

extern void LoadReplyFIFO();
extern void SetStatus(const uint8_t cmd, const uint8_t flag, const uint8_t value);

FIL fil_wr;
FIL *store_fil = &fil_data;

static FIL fil_ext;
static uint8_t ext_open = 0, wr_open = 0;
static DWORD ext_clmt[64];          /* fast seek link map (up to 31 fragments) */

/* READ prefetch (same idea as LOADSECT's double buffering) */
static uint8_t pf_valid = 0;
static uint32_t pf_off, pf_len;
static bwbuffer_t *pf_buf;

static void put16(uint8_t *p, uint32_t v) { p[0] = v >> 8; p[1] = v; }
static void put32(uint8_t *p, uint32_t v) { p[0] = v >> 24; p[1] = v >> 16; p[2] = v >> 8; p[3] = v; }
static uint32_t get32(volatile uint8_t *p) { return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | p[3]; }

void ngcd_ext_invalidate(void) {
	pf_valid = 0;
}

/* Path at data[4..]; must be terminated before data[63]. Returns NULL if invalid. */
static char *get_path(void) {
	char *p = (char *)&cmd_buffer.data[4];
	if (!p[0] || !memchr(p, 0, NGCD_PATH_MAX + 1))
		return NULL;
	return p;
}

static void reply(uint8_t err) {
	SetStatus(MCU_CMD_NGCD, err ? CMD_NOK : CMD_OK, err);
}

/* Read len bytes at off from file A into buf, with a complete reply header. Returns bytes read. */
static uint32_t read_into(bwbuffer_t *buf, uint32_t off, uint32_t len) {
	UINT br = 0;
	FRESULT fr;

	setLED(led_color_load);
	fr = f_lseek(&fil_ext, off);
	if (fr == FR_OK)
		fr = f_read(&fil_ext, &buf->byte[8], len, &br);
	setLED(led_color_idle);

	buf->byte[0] = (fr == FR_OK) ? (MCU_CMD_NGCD | 0xF0) : MCU_CMD_NGCD;
	buf->byte[1] = (uint8_t)fr;
	put16(&buf->byte[2], br);
	put32(&buf->byte[4], off);
	return (fr == FR_OK) ? br : 0;
}

static void cmd_read(void) {
	uint32_t off = get32(&cmd_buffer.data[2]);
	uint32_t len = ((uint32_t)cmd_buffer.data[6] << 8) | cmd_buffer.data[7];
	uint32_t br;

	if (!ext_open) { pf_valid = 0; reply(NGCD_E_NOTOPEN); return; }
	if (!len || len > NGCD_READ_MAX) { pf_valid = 0; reply(NGCD_E_LENGTH); return; }

	if (pf_valid && pf_off == off && pf_len == len) {
		/* Already read while the console was busy with the previous block */
		reply_buff_ptr = pf_buf;
	} else {
		reply_buff_ptr = &reply_buff_a;
		read_into(reply_buff_ptr, off, len);
	}
	br = ((uint32_t)reply_buff_ptr->byte[2] << 8) | reply_buff_ptr->byte[3];

	/* Answer now, then read the next block into the other buffer */
	LoadReplyFIFO();
	flag_exec = 0;

	if ((reply_buff_ptr->byte[0] & 0xF0) == 0xF0 && br == len) {
		pf_buf = (reply_buff_ptr == &reply_buff_a) ? &reply_buff_b : &reply_buff_a;
		pf_off = off + len;
		pf_len = len;
		read_into(pf_buf, pf_off, pf_len);
		pf_valid = 1;
	} else
		pf_valid = 0;
}

static void cmd_open(void) {
	char *path = get_path();
	FRESULT fr;

	if (ext_open) { f_close(&fil_ext); ext_open = 0; }
	if (!path) { reply(NGCD_E_PATH); return; }

	fr = f_open(&fil_ext, path, FA_READ);
	if (fr != FR_OK) { reply(fr); return; }
	ext_open = 1;

	/* Fast seek: O(1) seeks on big files. If the file is too fragmented for the
	   table, just fall back to normal (cluster chain) seeking. */
	ext_clmt[0] = sizeof(ext_clmt) / sizeof(ext_clmt[0]);
	fil_ext.cltbl = ext_clmt;
	if (f_lseek(&fil_ext, CREATE_LINKMAP) != FR_OK)
		fil_ext.cltbl = 0;

	reply(0);
	put32(&reply_buff_a.byte[2], f_size(&fil_ext));
	reply_buff_a.byte[6] = fil_ext.cltbl ? 1 : 0;	/* 1 = fast seek active */
}

static void cmd_openw(void) {
	char *path = get_path();
	uint8_t mode = cmd_buffer.data[2];
	FRESULT fr;
	BYTE fa;

	if (wr_open) { f_close(&fil_wr); wr_open = 0; }
	store_fil = &fil_data;
	if (!path) { reply(NGCD_E_PATH); return; }

	if (mode == NGCD_W_CREATE) fa = FA_WRITE | FA_CREATE_ALWAYS;
	else if (mode == NGCD_W_NEW) fa = FA_WRITE | FA_CREATE_NEW;
	else if (mode == NGCD_W_APPEND) fa = FA_WRITE | FA_OPEN_ALWAYS;
	else if (mode == NGCD_W_UPDATE) fa = FA_WRITE | FA_OPEN_EXISTING;
	else { reply(NGCD_E_ARGS); return; }

	fr = f_open(&fil_wr, path, fa);
	if (fr == FR_EXIST) { reply(NGCD_E_EXISTS); return; }
	if (fr != FR_OK) { reply(fr); return; }
	if (mode == NGCD_W_APPEND && (fr = f_lseek(&fil_wr, f_size(&fil_wr))) != FR_OK) {
		f_close(&fil_wr);
		reply(fr);
		return;
	}

	wr_open = 1;
	store_fil = &fil_wr;	/* STORESAVE 2 + words now go to this file */
	storing_error = 0;
	reply(0);
	put32(&reply_buff_a.byte[2], f_size(&fil_wr));
}

static void cmd_closew(void) {
	uint8_t err = 0;

	if (!wr_open) { reply(NGCD_E_NOTOPEN); return; }
	if (storing_error) { err = NGCD_E_WRITE; storing_error = 0; }
	FRESULT fr = f_close(&fil_wr);
	if (!err && fr != FR_OK) err = fr;
	wr_open = 0;
	store_fil = &fil_data;
	reply(err);
}

static void cmd_setpos(void) {
	uint32_t off = get32(&cmd_buffer.data[2]);
	FRESULT fr;

	if (!wr_open) { reply(NGCD_E_NOTOPEN); return; }
	fr = f_lseek(&fil_wr, off);
	if (fr == FR_OK && (cmd_buffer.data[6] & 1))
		fr = f_truncate(&fil_wr);
	reply(fr);
	put32(&reply_buff_a.byte[2], f_size(&fil_wr));
}

static void cmd_mkdir(void) {
	char *path = get_path();
	uint32_t i, n;
	FRESULT fr;

	if (!path) { reply(NGCD_E_PATH); return; }
	n = strlen(path);
	strcpy(buffer_temp, path);
	while (n > 1 && buffer_temp[n - 1] == '/') buffer_temp[--n] = 0;

	/* Create every level, like mkdir -p */
	for (i = 1; i < n; i++) {
		if (buffer_temp[i] == '/') {
			buffer_temp[i] = 0;
			f_mkdir(buffer_temp);
			buffer_temp[i] = '/';
		}
	}
	fr = f_mkdir(buffer_temp);
	if (fr == FR_EXIST) {
		FILINFO fno;
		if (f_stat(buffer_temp, &fno) == FR_OK && (fno.fattrib & AM_DIR)) {
			reply(0);
			reply_buff_a.byte[1] = 1;	/* already existed */
		} else
			reply(NGCD_E_EXISTS);		/* a file with that name */
		return;
	}
	reply(fr);
}

static void cmd_delete(void) {
	char *path = get_path();
	if (!path) { reply(NGCD_E_PATH); return; }
	reply(f_unlink(path));
}

static void cmd_rename(void) {
	char *from = get_path(), *to;
	uint8_t *end = (uint8_t *)&cmd_buffer.data[63];
	FRESULT fr;

	if (!from) { reply(NGCD_E_PATH); return; }
	to = from + strlen(from) + 1;
	if ((uint8_t *)to >= end || !to[0] || !memchr(to, 0, end - (uint8_t *)to + 1)) { reply(NGCD_E_PATH); return; }

	fr = f_rename(from, to);
	if (fr == FR_EXIST) {
		if (!(cmd_buffer.data[2] & 1)) { reply(NGCD_E_EXISTS); return; }
		/* Overwrite: safe-save pattern (write new file, then rename over the old one) */
		fr = f_unlink(to);
		if (fr == FR_OK)
			fr = f_rename(from, to);
	}
	reply(fr);
}

static void cmd_stat(void) {
	char *path = get_path();
	FILINFO fno;
	FRESULT fr;

	if (!path) { reply(NGCD_E_PATH); return; }
	fr = f_stat(path, &fno);
	reply(fr);
	if (fr == FR_OK) {
		reply_buff_a.byte[2] = fno.fattrib;
		put32(&reply_buff_a.byte[3], fno.fsize);
		put16(&reply_buff_a.byte[8], fno.fdate);
		put16(&reply_buff_a.byte[10], fno.ftime);
	}
}

/* Records: attr(1) size(4) fdate(2) ftime(2) namelen(1) name(namelen, no terminator) */
static void cmd_listdir(void) {
	char *path = get_path();
	uint32_t first = ((uint32_t)cmd_buffer.data[2] << 8) | cmd_buffer.data[3];
	uint32_t idx = 0, count = 0, pos = 8, more = 0, n;
	uint8_t *b = reply_buff_a.byte;
	DIR dir;
	FILINFO fno;
	FRESULT fr;

	if (!path) { reply(NGCD_E_PATH); return; }
	fr = f_opendir(&dir, path);
	if (fr != FR_OK) { reply(fr); return; }

	for (;;) {
		fr = f_readdir(&dir, &fno);
		if (fr != FR_OK || !fno.fname[0]) break;
		if (idx++ < first) continue;
		n = strlen(fno.fname);
		if (count == 255 || pos + 10 + n > BWBUFFER_SIZE_B) { more = 1; break; }
		b[pos] = fno.fattrib;
		put32(&b[pos + 1], fno.fsize);
		put16(&b[pos + 5], fno.fdate);
		put16(&b[pos + 7], fno.ftime);
		b[pos + 9] = n;
		memcpy(&b[pos + 10], fno.fname, n);
		pos += 10 + n;
		count++;
	}
	f_closedir(&dir);

	if (fr != FR_OK) { reply(fr); return; }
	reply(0);
	b[1] = count;
	b[2] = more;
	put16(&b[4], pos - 8);	/* bytes of records */
}

static void cmd_free(void) {
	FATFS *fs;
	DWORD nclst;
	FRESULT fr = f_getfree("0:", &nclst, &fs);

	reply(fr);
	if (fr == FR_OK) {
		uint8_t *b = reply_buff_a.byte;
		b[2] = fs->fs_type;		/* 1 FAT12, 2 FAT16, 3 FAT32 */
		put32(&b[8], ((fs->n_fatent - 2) * fs->csize) >> 1);	/* total KB (512-byte sectors) */
		put32(&b[12], (nclst * fs->csize) >> 1);				/* free KB */
		put32(&b[16], fs->csize * 512);							/* cluster bytes */
	}
}

static void cmd_opencd(void) {
	char *path = get_path();
	FRESULT fr;

	if (!path) { reply(NGCD_E_PATH); return; }
	CDDA_Stop();
	f_close(&fil_data);
	data_mode = MODE_NULL;
	fr = f_open(&fil_data, path, FA_READ);
	if (fr != FR_OK) { reply(fr); return; }
	/* Same trick as the custom background: serve the file as 2048-byte sectors */
	data_mode = MODE_DATA;
	data_sector_size = 2048;
	prev_CD_LBA = -1;
	reply(0);
	put32(&reply_buff_a.byte[2], f_size(&fil_data));
}

static void cmd_info(void) {
	uint8_t *b = reply_buff_a.byte;
	reply(0);
	b[1] = NGCD_EXT_VERSION;
	put16(&b[2], NGCD_CAP_FREE | NGCD_CAP_READ | NGCD_CAP_WRITE | NGCD_CAP_DIRS |
			NGCD_CAP_LIST | NGCD_CAP_OPENCD | NGCD_CAP_PREFETCH);
	b[4] = VERSION_MAJOR;
	b[5] = VERSION_MINOR;
	b[6] = NGCD_PATH_MAX;
	b[7] = 0;
	memcpy(&b[8], "NGCX", 4);
	put16(&b[12], NGCD_READ_MAX);
	put16(&b[14], MAX_FILES);
}

void ngcd_ext_exec(void) {
	uint8_t sub = cmd_buffer.data[1];

	if (sub != NGCD_READ)
		pf_valid = 0;

	switch (sub) {
		case NGCD_INFO: cmd_info(); break;
		case NGCD_FREE: cmd_free(); break;
		case NGCD_OPEN: cmd_open(); break;
		case NGCD_READ: cmd_read(); break;
		case NGCD_CLOSE:
			if (ext_open) { f_close(&fil_ext); ext_open = 0; reply(0); }
			else reply(NGCD_E_NOTOPEN);
			break;
		case NGCD_OPENW: cmd_openw(); break;
		case NGCD_MKDIR: cmd_mkdir(); break;
		case NGCD_DELETE: cmd_delete(); break;
		case NGCD_RENAME: cmd_rename(); break;
		case NGCD_STAT: cmd_stat(); break;
		case NGCD_SETPOS: cmd_setpos(); break;
		case NGCD_LISTDIR: cmd_listdir(); break;
		case NGCD_OPENCD: cmd_opencd(); break;
		case NGCD_CLOSEW: cmd_closew(); break;
		default: reply(NGCD_E_SUBCMD); break;
	}
}
