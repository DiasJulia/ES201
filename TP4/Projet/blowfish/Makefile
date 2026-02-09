# Makefile Blowfish — RISC-V (gem5 SE)

# ---------- TOOLCHAIN ----------
CC     = riscv64-linux-gnu-gcc
AR     = riscv64-linux-gnu-ar
RANLIB = riscv64-linux-gnu-ranlib


# Options perf
#OPTS= -DBF_PTR
#OPTS= -DBF_PTR2
OPTS=

# Gem5 SE: statique conseillé (RISC-V 64)
CFLAG  = -static -O3 -fomit-frame-pointer -Wall -std=c99 \
         -fno-pie -no-pie \
         -march=rv64gc -mabi=lp64d \
         -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables
CFLAGS = $(OPTS) $(CFLAG)

# Assembler version: on force la version C (pas les asm x86)
BF_ENC = bf_enc.o

LIBOBJ = bf_skey.o bf_ecb.o $(BF_ENC) bf_cbc.o bf_cfb64.o bf_ofb64.o
LIBSRC = bf_skey.c bf_ecb.c bf_enc.c bf_cbc.c bf_cfb64.c bf_ofb64.c
HEADERS= bf_locl.h blowfish.h bf_pi.h

BLIB   = libblowfish.a

TARGET = bf.riscv

# Optionnel: outils de test en RISC-V
TEST_BINS = bftest.riscv bfspeed.riscv

all: $(BLIB) $(TARGET)

# -------- Library --------
$(BLIB): $(LIBOBJ)
	/bin/rm -f $(BLIB)
	$(AR) cr $(BLIB) $(LIBOBJ)
	$(RANLIB) $(BLIB)

# -------- Main binary --------
$(TARGET): bf.o $(BLIB)
	$(CC) $(CFLAGS) -o $(TARGET) bf.o $(BLIB)

# -------- Optional test binaries --------
bftest.riscv: bftest.o $(BLIB)
	$(CC) $(CFLAGS) -o $@ bftest.o $(BLIB)

bfspeed.riscv: bfspeed.o $(BLIB)
	$(CC) $(CFLAGS) -o $@ bfspeed.o $(BLIB)

tests: $(BLIB) $(TEST_BINS)

# -------- Generic compile rules --------
%.o: %.c $(HEADERS) Makefile
	$(CC) $(CFLAGS) -c $< -o $@

check: all
	file $(TARGET) $(TEST_BINS) 2>/dev/null || true

clean:
	/bin/rm -f *.o core tags $(TARGET) $(TEST_BINS) $(BLIB) .nfs* *.old *.bak output*
	/bin/rm -f asm/*.o

.PHONY: all clean tests check
