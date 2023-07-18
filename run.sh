#!/bin/sh

pip install PyGithub
DIR="$( cd "$( dirname "$0" )" && pwd )"

python $DIR/src/app.py
