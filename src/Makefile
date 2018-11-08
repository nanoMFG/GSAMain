
DESTDIR = ../bin
INSTALL = install -D --mode 0444
SRCS := GSADashboard.py GSAImage.py GSAQuery.py GSARaman.py \
        GSARecipe.py GSAStats.py GSASubmit.py models.py \
		gresq/citrine_data.py gresq/config.py gresq/csv2db.py gresq/database.py 

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
	${RM} $(addprefix ${DESTDIR}/,$^)

distclean: clean

.PHONY: all clean distclean

