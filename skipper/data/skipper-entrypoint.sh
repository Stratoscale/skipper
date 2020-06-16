#!/usr/bin/env bash

if ! [ -z "${SKIPPER_DOCKER_GID}" ];then
  SKIP_HOME_DIR_PARAM=""
  # if home directory already exists, useradd should not try to create it
  [ -d /home/${SKIPPER_USERNAME} ] && SKIP_HOME_DIR_PARAM="--no-create-home"

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


  if grep -q docker /etc/group; then
     usermod -G root,docker ${SKIPPER_USERNAME}
  else
     usermod -G root ${SKIPPER_USERNAME}
  fi


  su -m ${SKIPPER_USERNAME} -c "$@"
else
  bash -c "$@"
fi
