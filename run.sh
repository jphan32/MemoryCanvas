#!/bin/bash

PID=./gradio.pid
if [[ -f "$PID" ]]; then
    kill -15 `cat $PID` || kill -9 `cat $PID`
fi

mkdir -p ./logs

if [ -f .env ]; then
    export $(cat .env | xargs)

nohup python -u app.py >> ./logs/app.log 2>&1 &
echo $! > $PID
