### Maintaining Makefile for nanoHUB Install
The Makefiles are setup to support deployment of the application as a nanoHUB tool.  The top-level Makefile lives here in ``src``.  As new ``*.py`` files are added to the project, they must also be added to the ``SRCS`` variable in their respective Makefile in order to be correctly installed.

```
SRCS := GSARaman.py GSADashboard.py GSAImage.py GSAQuery.py \
        GSARecipe.py GSAStats.py GSASubmit.py models.py
```

### Testing the Install

To install:
```
> cd src
> make
> make install
```
Test by executing ``GSADashboard.pyc`` in ``/bin``.
