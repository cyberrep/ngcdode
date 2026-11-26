# Build do programa do MCU (ProdApp) fora do STM32CubeIDE
# uso: make -f build_mcu.mk SRC=<pasta ProdApp> OUT=<pasta saida> NAME=<nome>
CC=arm-none-eabi-gcc
OC=arm-none-eabi-objcopy
ARCH=-mcpu=cortex-m7 -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb
DEFS=-DSTM32F730xx -DUSE_FULL_LL_DRIVER -DUSE_HAL_DRIVER $(EXTRA_DEFS)
OPT?=-O3
FFOPT?=$(OPT)
INC=-I$(SRC)/Inc -I$(SRC)/Drivers/STM32F7xx_HAL_Driver/Inc -I$(SRC)/Drivers/STM32F7xx_HAL_Driver/Inc/Legacy \
 -I$(SRC)/Drivers/CMSIS/Device/ST/STM32F7xx/Include -I$(SRC)/Drivers/CMSIS/Include \
 -I$(SRC)/Middlewares/Third_Party/FatFs/src -I$(SRC)/Middlewares/ST/STM32_USB_Device_Library/Core/Inc \
 -I$(SRC)/Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc
CFLAGS=$(ARCH) $(DEFS) $(INC) -std=gnu11 -ffunction-sections -fdata-sections -Wall -Wno-unused -g0
OBJS=$(shell sed 's/"//g' $(SRC)/Release/objects.list)
O=$(addprefix $(OUT)/,$(OBJS))
all: $(OUT)/$(NAME).bin
$(OUT)/Middlewares/Third_Party/FatFs/src/ff.o: $(SRC)/Middlewares/Third_Party/FatFs/src/ff.c
	@mkdir -p $(dir $@); $(CC) $(CFLAGS) $(FFOPT) -c $< -o $@
$(OUT)/%.o: $(SRC)/%.c
	@mkdir -p $(dir $@); $(CC) $(CFLAGS) $(OPT) -c $< -o $@
$(OUT)/%.o: $(SRC)/%.s
	@mkdir -p $(dir $@); $(CC) $(ARCH) -c -x assembler-with-cpp $< -o $@
$(OUT)/$(NAME).elf: $(O)
	$(CC) -o $@ $(O) $(ARCH) -T$(SRC)/STM32F730R8TX_FLASH_OFFSET.ld --specs=nosys.specs --specs=nano.specs -Wl,-Map=$(OUT)/$(NAME).map -Wl,--gc-sections -static -Wl,--start-group -lc -lm -Wl,--end-group
$(OUT)/$(NAME).bin: $(OUT)/$(NAME).elf
	$(OC) -O binary $< $@
	@arm-none-eabi-size $<; ls -l $@
