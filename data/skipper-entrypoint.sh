#!/usr/bin/env bash

getent passwd ${SKIPPER_USERNAME} > /dev/null
if [ x"$?" != x"0" ]; then
	useradd -u ${SKIPPER_UID} --non-unique -M "${SKIPPER_USERNAME}"
fi

groupadd -g ${SKIPPER_DOCKER_GID} --non-unique docker
usermod -G root,docker ${SKIPPER_USERNAME}


while true; do
	su -m ${SKIPPER_USERNAME} -c "$@"
	if [ x$? == x0 ]; then
	    break
	fi
done
