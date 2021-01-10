#!/bin/bash

ps aux | grep get-power.py | grep -v grep | awk '{ print "kill -9", $2 }' | sh

wait

python /temporary/PWR/get-power.py 

