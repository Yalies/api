#!/usr/bin/env bash
# E501 Line too long
# E402 Import not at top of file
# E265 block comment should start with '# '
pycodestyle *.py app/*.py --ignore=E501,E402,E265
