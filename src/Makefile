
DESTDIR = ../bin
INSTALL = install -D --mode 0444
SRCS := models.py GSADashboard.py tst/GSARaman.py


OBJS := $(patsubst %.py,%.pyc,${SRCS})

%.pyc: %.py
	py_compilefiles $<

all: ${OBJS}

install: $(addprefix install_,$(OBJS))

$(addprefix install_,$(OBJS)): install_%: %
	${INSTALL} $< $(DESTDIR)/$<

PHONY: install $(addprefix install_,$(OBJS))

clean: ${OBJS}
	${RM} $^ \
	${RM} $(DESTDIR)/$<

distclean: clean

.PHONY: all clean distclean

