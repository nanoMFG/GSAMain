COMPILE = . /etc/environ.sh; use -e -r anaconda3-5.1; python -m compileall
DESTDIR = ../../bin/gresq
INSTALL = install -D --mode 0444

# Edit the CYPYTHON_SUFFIX to match python version
# Add src files to SRCS as needed
CPYTHON_SUFFIX = cpython-36
SRCS := __init__.py app.py citrine_data.py config.py csv2db.py database.py \
        forge2db.py recipe.py

# Generate a list of objects based on python mangling rules
#OBJS:= $(patsubst %.py,__pycache__/%.${CPYTHON_SUFFIX}.pyc,${SRCS})
OBJS:= $(patsubst %.py,%.pyc,${SRCS})

all: ${OBJS}

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

