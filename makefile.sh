#!/bin/bash

pyside6-rcc src/ui/resource.qrc -o src/ui/resource_rc.py
pipreqs ./ --encoding=utf8
