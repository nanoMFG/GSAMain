
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(dir $(mkfile_path))
DESTDIR := $(abspath $(current_dir)../bin)

all:
	@echo "Run 'make install'"

gsaraman:
	cd .. && pip install -t ${DESTDIR} ./gsaraman

gsaimage:
	cd .. && pip install -t ${DESTDIR} ./gsaimage

gresq: gsaraman gsaimage
	cd .. && pip install -t ${DESTDIR} .

install:
	. /etc/environ.sh; use -e -r anaconda3-5.1; $(MAKE) gresq

clean:
	rm -rf ${DESTDIR}/*.dist-info

distclean: clean
	rm -rf ${DESTDIR}/gresq
	rm -rf ${DESTDIR}/bin
	rm -rf ${DESTDIR}/GrResQ*
	rm -rf ${DESTDIR}/gsaraman
	rm -rf ${DESTDIR}/gsaimage

.PHONY: all install clean distclean
