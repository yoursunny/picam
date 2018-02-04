#!/bin/bash
find -name '*.py' | xargs autopep8 --in-place
