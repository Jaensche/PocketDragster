# Pocket Dragster - Game Boy drag racer
# Build:  make          -> build/pocketdragster.gb
#         make clean
#         make run      -> opens ROM in Emulicious (set EMULICIOUS path)

GBDK_HOME  ?= gbdk
LCC        := $(GBDK_HOME)/bin/lcc

PROJECT    := pocketdragster
ROM_TITLE  := POCKETDRAGSTER

SRCDIR     := src
RESDIR     := res
OBJDIR     := build/obj
ROM        := build/$(PROJECT).gb

# Cartridge header: MBC5, no RAM/battery (0x19).
# -debug emits .cdb/.noi/.map so Emulicious can do C source-level debugging.
LCCFLAGS   := -Wa-l -Wl-m -Wl-j -debug \
              -Wm-yn"$(ROM_TITLE)" -Wm-yt0x19 -autobank

CFLAGS     := -I$(SRCDIR) -I$(RESDIR)

CSOURCES   := $(wildcard $(SRCDIR)/*.c) $(wildcard $(RESDIR)/*.c)
ASMSOURCES := $(wildcard $(SRCDIR)/*.s)
OBJS       := $(patsubst %.c,$(OBJDIR)/%.o,$(notdir $(CSOURCES))) \
              $(patsubst %.s,$(OBJDIR)/%.o,$(notdir $(ASMSOURCES)))

vpath %.c $(SRCDIR) $(RESDIR)
vpath %.s $(SRCDIR)

EMULICIOUS ?= Emulicious/Emulicious.jar

.PHONY: all clean run sim

all: $(ROM)

$(OBJDIR)/%.o: %.c $(wildcard $(SRCDIR)/*.h) $(RESDIR)/tiles.h $(RESDIR)/splash.h | $(OBJDIR)
	$(LCC) $(CFLAGS) $(LCCFLAGS) -c -o $@ $<

$(OBJDIR)/%.o: %.s | $(OBJDIR)
	$(LCC) $(LCCFLAGS) -c -o $@ $<

$(ROM): $(OBJS)
	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)

$(OBJDIR):
	mkdir -p $@

# Generated tile data (committed, so Python is only needed when editing art)
$(RESDIR)/tiles.c $(RESDIR)/tiles.h: tools/gen_tiles.py
	python3 tools/gen_tiles.py

$(RESDIR)/splash.c $(RESDIR)/splash.h: tools/gen_splash.py tools/gen_tiles.py
	python3 tools/gen_splash.py

run: $(ROM)
	java -jar $(EMULICIOUS) $(ROM)

# Host-side physics tuning harness
sim: build/sim
	./build/sim

build/sim: tools/sim.c $(SRCDIR)/physics.c $(SRCDIR)/physics.h
	mkdir -p build
	gcc -O2 -Wall -Wextra -o $@ tools/sim.c $(SRCDIR)/physics.c

clean:
	rm -rf build
