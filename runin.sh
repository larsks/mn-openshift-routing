#!/bin/sh

pid=$(pgrep -f mininet:$1)
shift

if [ -z "$pid" ]; then
	echo "no matches"
	exit 1
fi

sudo nsenter -t $pid -n "$@"
