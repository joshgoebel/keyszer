#!/bin/bash

DELAY=20

./bin/keyszer $@ &
PID=$!

function cleanup()
{
  kill $PID 2> /dev/null
}
trap cleanup EXIT
trap cleanup KILL

sleep 2
echo "(!!) Preparing to kill in $DELAY seconds."

sleep $DELAY
kill $PID 2> /dev/null
true
