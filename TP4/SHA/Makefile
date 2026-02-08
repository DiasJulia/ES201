# Makefile RISC-V (gem5 SE)
CC_HOST=gcc
CC_RISCV=riscv64-linux-gnu-gcc

CFLAGS_COMMON=-O3 -Wall -std=c99 -DLITTLE_ENDIAN
# Gem5 SE: binaire statique conseillé
CFLAGS_RISCV=-O3 -Wall -std=c99 -DLITTLE_ENDIAN -static

all: sha sha.riscv

# binaire natif (debug rapide sur la machine hôte)
sha: sha_driver.c sha.c
	$(CC_HOST) $(CFLAGS_COMMON) -o $@ sha_driver.c sha.c

# binaire RISC-V pour gem5
sha.riscv: sha_driver.c sha.c
	$(CC_RISCV) $(CFLAGS_RISCV) -o $@ sha_driver.c sha.c

clean:
	rm -f sha sha.riscv *.o m5out_* results_sha.txt
