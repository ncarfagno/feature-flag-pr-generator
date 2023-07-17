#!/bin/sh

pip install Flask PyGithub
DIR="$( cd "$( dirname "$0" )" && pwd )"

python $DIR/src/app.py
