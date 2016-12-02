#!/usr/bin/env bash

set FLASK_DEBUG=1
set FLASK_APP=server.py

python -m flask run --host=0.0.0.0