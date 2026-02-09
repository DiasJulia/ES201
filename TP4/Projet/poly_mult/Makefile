# Makefile RISC-V — poly_mult (gem5 SE)

# Choose the toolchain you have:
#   - riscv64-linux-gnu-gcc (common on Debian/Ubuntu)
#   - riscv64-unknown-linux-gnu-gcc (cross toolchain)
CC = riscv64-linux-gnu-gcc

CFLAGS = -O3 -static -fno-pie -no-pie -Wall -std=c99 \
         -march=rv64gc -mabi=lp64d \
         -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables

TARGET = poly_mult.riscv
SRC    = poly_mult.c

all: $(TARGET)

$(TARGET): $(SRC) Makefile
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

check: $(TARGET)
	file $(TARGET) && readelf -h $(TARGET) | grep -E "Machine|Class|Type"

clean:
	rm -f $(TARGET) *.o
	rm -rf m5out_* stats.txt

.PHONY: all clean check
