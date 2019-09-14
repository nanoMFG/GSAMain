
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(dir $(mkfile_path))
DESTDIR := $(realpath ${current_dir}../bin)

all:
	@echo "Run 'make install'"

gsaraman:
	cd .. && pip install -t ${DESTDIR} ./gsaraman

gresq: gsaraman
	cd .. && pip install -t ${DESTDIR} .

install: gresq

clean:
	rm -rf ${DESTDIR}/gresq
	rm -rf ${DESTDIR}/bin
	rm -rf ${DESTDIR}/GrResQ*
	rm -rf ${DESTDIR}/gsaraman

distclean: clean

.PHONY: all install clean distclean
