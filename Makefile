# Quarter Mile (working title) - Game Boy drag racer
# Build:  make          -> build/quartermile.gb
#         make clean
#         make run      -> opens ROM in Emulicious (set EMULICIOUS path)

GBDK_HOME  ?= gbdk
LCC        := $(GBDK_HOME)/bin/lcc

PROJECT    := quartermile
ROM_TITLE  := QUARTERMILE

SRCDIR     := src
RESDIR     := res
OBJDIR     := build/obj
ROM        := build/$(PROJECT).gb

# Cartridge header: MBC5 + RAM + battery (0x1B), 1 RAM bank (8 KB) for best-time saves.
# -debug emits .cdb/.noi/.map so Emulicious can do C source-level debugging.
LCCFLAGS   := -Wa-l -Wl-m -Wl-j -debug \
              -Wm-yn"$(ROM_TITLE)" -Wm-yt0x1B -Wm-ya1 -autobank

CFLAGS     := -I$(SRCDIR) -I$(RESDIR)

CSOURCES   := $(wildcard $(SRCDIR)/*.c) $(wildcard $(RESDIR)/*.c)
ASMSOURCES := $(wildcard $(SRCDIR)/*.s)
OBJS       := $(patsubst %.c,$(OBJDIR)/%.o,$(notdir $(CSOURCES))) \
              $(patsubst %.s,$(OBJDIR)/%.o,$(notdir $(ASMSOURCES)))

vpath %.c $(SRCDIR) $(RESDIR)
vpath %.s $(SRCDIR)

EMULICIOUS ?= Emulicious/Emulicious.jar

.PHONY: all clean run

all: $(ROM)

$(OBJDIR)/%.o: %.c $(wildcard $(SRCDIR)/*.h) | $(OBJDIR)
	$(LCC) $(CFLAGS) $(LCCFLAGS) -c -o $@ $<

$(OBJDIR)/%.o: %.s | $(OBJDIR)
	$(LCC) $(LCCFLAGS) -c -o $@ $<

$(ROM): $(OBJS)
	$(LCC) $(LCCFLAGS) -o $@ $(OBJS)

$(OBJDIR):
	mkdir -p $@

run: $(ROM)
	java -jar $(EMULICIOUS) $(ROM)

clean:
	rm -rf build
