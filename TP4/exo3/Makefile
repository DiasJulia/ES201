# Makefile RISC-V (gem5 SE) — matrices
CC_HOST=gcc
CC_RISCV=riscv64-linux-gnu-gcc

CFLAGS_COMMON=-O3 -Wall -std=c99 -DLITTLE_ENDIAN
# Gem5 SE: binaire statique conseillé
CFLAGS_RISCV=-O3 -Wall -std=c99 -DLITTLE_ENDIAN -static

PROGS=normale pointer tempo unrol

all: $(PROGS) $(PROGS:%=%.riscv)

# Binaires natifs (debug rapide sur la machine hôte)
normale: normale.c
	$(CC_HOST) $(CFLAGS_COMMON) -o $@ $<

pointer: pointer.c
	$(CC_HOST) $(CFLAGS_COMMON) -o $@ $<

tempo: tempo.c
	$(CC_HOST) $(CFLAGS_COMMON) -o $@ $<

unrol: unrol.c
	$(CC_HOST) $(CFLAGS_COMMON) -o $@ $<

# Binaires RISC-V (gem5 SE)
normale.riscv: normale.c
	$(CC_RISCV) $(CFLAGS_RISCV) -o $@ $<

pointer.riscv: pointer.c
	$(CC_RISCV) $(CFLAGS_RISCV) -o $@ $<

tempo.riscv: tempo.c
	$(CC_RISCV) $(CFLAGS_RISCV) -o $@ $<

unrol.riscv: unrol.c
	$(CC_RISCV) $(CFLAGS_RISCV) -o $@ $<

clean:
	rm -f $(PROGS) $(PROGS:%=%.riscv) *.o
	rm -rf m5out_* results_cache.txt

.PHONY: all clean
