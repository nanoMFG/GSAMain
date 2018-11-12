
COMPILE = ./py3_compilefiles
DESTDIR = ../bin
INSTALL = install -D --mode 0444
SUBDIRS := gresq

# Edit the CYPYTHON_SUFFIX to match python version
# Add src files to SRCS as needed
CPYTHON_SUFFIX = cpython-36
SRCS := GSARaman.py GSADashboard.py GSAImage.py GSAQuery.py \
        GSARecipe.py GSAStats.py GSASubmit.py models.py

# Generate a list of objects based on python mangling rules
#TMP := $(patsubst %,%__pycache__/,$(dir ${SRCS}))
#OBJ := $(patsubst %.py,%.${CPYTHON_SUFFIX}.pyc,$(notdir ${SRCS}))
#OBJS:= $(join ${TMP}, ${OBJ})
OBJS:= $(patsubst %.py,__pycache__/%.${CPYTHON_SUFFIX}.pyc,${SRCS})

#.PHONY: print_vars
all: ${OBJS} ${SUBDIRS}

$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

#print_vars:
#	for x in ${OBJS}; do \
#	    echo $$x ; \
#	done

__pycache__/%.${CPYTHON_SUFFIX}.pyc: %.py
	${COMPILE} $<

#gresq/__pycache__/%.${CPYTHON_SUFFIX}.pyc: gresq/%.py
#	${COMPILE} $<


install: $(addprefix install_,$(OBJS)) ${SUBDIRS}

$(addprefix install_,$(OBJS)): install_%: %
	${INSTALL} $< $(DESTDIR)/$(patsubst __pycache__/%,%,$<)

clean: ${OBJS}
	${RM} $^

distclean: clean

.PHONY: install all clean distclean ${SUBDIRS}

