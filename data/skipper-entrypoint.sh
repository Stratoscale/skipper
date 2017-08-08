#!/usr/bin/env bash

getent passwd ${SKIPPER_USERNAME} > /dev/null
if [ x"$?" != x"0" ]; then
	useradd -u ${SKIPPER_UID} --non-unique -M "${SKIPPER_USERNAME}"
fi

if [ $(getent group docker) ]; then
	groupmod -o -g ${SKIPPER_DOCKER_GID} docker
else
	groupadd -g ${SKIPPER_DOCKER_GID} --non-unique docker
fi

usermod -G root,docker ${SKIPPER_USERNAME}

su -m ${SKIPPER_USERNAME} -c "$@"

