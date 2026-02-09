# Makefile — RISC-V (gem5 SE)

# ---------- TOOLCHAIN ----------
CC = riscv64-linux-gnu-gcc


CFLAGS = -O3 -static -fno-pie -no-pie -Wall -std=c99 \
         -march=rv64gc -mabi=lp64d \
         -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables

all: dijkstra_large.riscv dijkstra_small.riscv

dijkstra_large.riscv: dijkstra_large.c Makefile
	$(CC) $(CFLAGS) dijkstra_large.c -o dijkstra_large.riscv

dijkstra_small.riscv: dijkstra_small.c Makefile
	$(CC) $(CFLAGS) dijkstra_small.c -o dijkstra_small.riscv

check: all
	file dijkstra_large.riscv dijkstra_small.riscv

clean:
	rm -f dijkstra_large.riscv dijkstra_small.riscv *.o
	rm -rf m5out_* output*

.PHONY: all clean check
