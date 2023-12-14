#!/bin/sh
LOG_FILE=log.txt
python3 server.py >> $LOG_FILE 2>&1 &