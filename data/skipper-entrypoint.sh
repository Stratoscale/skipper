#!/usr/bin/env bash

SKIP_HOME_DIR_PARAM=""
# if home directory for user already exists, then useradd should not try to create it,
# but we'll need to make sure that the user is owner of it
[ -d /home/${SKIPPER_USERNAME} ] && SKIP_HOME_DIR_PARAM="-M"

getent passwd ${SKIPPER_USERNAME} > /dev/null
if [ x"$?" != x"0" ]; then
	useradd -u ${SKIPPER_UID} --non-unique ${SKIP_HOME_DIR_PARAM} "${SKIPPER_USERNAME}"
fi

chown ${SKIPPER_USERNAME}:${SKIPPER_USERNAME} /home/${SKIPPER_USERNAME}

if [ $(getent group docker) ]; then
	groupmod -o -g ${SKIPPER_DOCKER_GID} docker
else
	groupadd -g ${SKIPPER_DOCKER_GID} --non-unique docker
fi

usermod -G root,docker ${SKIPPER_USERNAME}

su -m ${SKIPPER_USERNAME} -c "$@"

