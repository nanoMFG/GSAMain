
COMPILE = ./py3_compilefiles
DESTDIR = ../bin
INSTALL = install -D --mode 0444
SUBDIRS := gresq

# Edit the CYPYTHON_SUFFIX to match python version
# Add src files to SRCS as needed
CPYTHON_SUFFIX = cpython-36
SRCS := GSARaman.py GSADashboard.py GSAImage.py GSAQuery.py \
        GSARecipe.py GSAStats.py GSASubmit.py models.py

# Generate a list of objects
OBJS:= $(patsubst %.py,%.pyc,${SRCS})

all: ${OBJS} ${SUBDIRS}

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

# Implict rules to generate *.pyc targets
__pycache__/%.${CPYTHON_SUFFIX}.pyc: %.py
	${COMPILE} $<

%.pyc: __pycache__/%.${CPYTHON_SUFFIX}.pyc
	cp $< $@


install: $(addprefix install_,${OBJS}) ${SUBDIRS}

$(addprefix install_,$(OBJS)): install_%: %
	${INSTALL} $< $(DESTDIR)/$<

clean: ${SUBDIRS}
	rm -rf *.pyc __pycache__

distclean: clean
	rm -rf ${DESTDIR}/*.pyc

.PHONY: install all clean distclean ${SUBDIRS}

