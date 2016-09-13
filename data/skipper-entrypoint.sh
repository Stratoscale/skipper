#!/usr/bin/env bash

getent passwd ${SKIPPER_USERNAME} > /dev/null
if [ x"$?" != x"0" ]; then
	useradd "${SKIPPER_USERNAME}"
fi

su -m ${SKIPPER_USERNAME} -c "$@"

