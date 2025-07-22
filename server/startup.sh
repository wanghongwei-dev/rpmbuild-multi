#!/bin/bash

export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export MIDDLEWARE_HOST=127.0.0.1
export MIDDLEWARE_PORT=8000
python3 -u app.py >> app.log 2>&1 &
