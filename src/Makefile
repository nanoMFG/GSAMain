
#COMPILE = ./py3_compilefiles
COMPILE = . /etc/environ.sh; use -e -r anaconda3-5.1; python -m compileall
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(dir $(mkfile_path))
DESTDIR := $(realpath ${current_dir}../bin)
#DESTDIR = ../bin
DATADIR = ../data
DATADESTDIR = ../bin/data
INSTALL = install -D --mode 0444
SUBDIRS := gresq gresq/util gresq/database gresq/dashboard gresq/dashboard/gsaimage/src/gsaimage

# Edit the CYPYTHON_SUFFIX to match python version
# Add src files to SRCS as needed
CPYTHON_SUFFIX = cpython-36
SRCS :=
DATAFILES := varmap.csv varmap2.csv recipe_2018_11_08.csv

DATAOBJS := $(patsubst %,${DATADESTDIR}/%,${DATAFILES})

# Generate a list of objects
OBJS:= $(patsubst %.py,%.pyc,${SRCS})

all: ${OBJS} ${SUBDIRS}

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS) DESTDIR=${DESTDIR}/$@

# Implict rules to generate *.pyc targets
__pycache__/%.${CPYTHON_SUFFIX}.pyc: %.py
	${COMPILE} $<

%.pyc: __pycache__/%.${CPYTHON_SUFFIX}.pyc
	cp $< $@

${DATADESTDIR}/%:
	${INSTALL} ${DATADIR}/$(@F) $@

install: $(addprefix install_,${OBJS}) ${SUBDIRS} ${DATAOBJS}

$(addprefix install_,$(OBJS)): install_%: %
	${INSTALL} $< $(DESTDIR)/$<

clean: ${SUBDIRS}
	rm -rf *.pyc __pycache__

distclean: clean
	rm -rf ${DESTDIR}/*.pyc
	rm -rf ${DATADESTDIR}

.PHONY: install all clean distclean ${SUBDIRS}
