COMPILE = . /etc/environ.sh; use -e -r anaconda3-5.1; python -m compileall
DESTDIR = ../../bin/gresq
INSTALL = install -D --mode 0444
#SUBDIRS := database util dashboard

# Edit the CYPYTHON_SUFFIX to match python version
# Add src files to SRCS as needed
CPYTHON_SUFFIX = cpython-36
SRCS := __init__.py __main__.py run_dashboard.py config.py recipe.py

# Generate a list of objects based on python mangling rules
#OBJS:= $(patsubst %.py,__pycache__/%.${CPYTHON_SUFFIX}.pyc,${SRCS})
OBJS:= $(patsubst %.py,%.pyc,${SRCS})

#all: ${OBJS} ${SUBDIRS}
all: ${OBJS}

#$(SUBDIRS):
#	$(MAKE) -C $@ $(MAKECMDGOALS)

__pycache__/%.${CPYTHON_SUFFIX}.pyc: %.py
	${COMPILE} $<

%.pyc: __pycache__/%.${CPYTHON_SUFFIX}.pyc
	cp $< $@

install: $(addprefix install_,${OBJS})

$(addprefix install_,$(OBJS)): install_%: %
	${INSTALL} $< $(DESTDIR)/$<

clean:
	rm -rf *.pyc __pycache__

distclean: clean
	rm -rf ${DESTDIR}/*.pyc
	rm -rf ${DESTDIR}

.PHONY: all clean distclean

