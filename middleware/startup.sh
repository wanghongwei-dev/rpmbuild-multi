#!/bin/bash

export UVICORN_HOST=0.0.0.0
export UVICORN_PORT=8000
export BACKEND_PORT=5000
uvicorn middleware:app --host $UVICORN_HOST --port $UVICORN_PORT >> middleware.log 2>&1 &
