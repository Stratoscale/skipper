#!/usr/bin/env bash

if ! [ -z "${SKIPPER_DOCKER_GID}" ];then

  HOME_DIR=${HOME}
  SKIP_HOME_DIR_PARAM=""

  # if home directory already exists, useradd should not try to create it
  [ -d ${HOME_DIR} ] && SKIP_HOME_DIR_PARAM="--no-create-home"

  getent passwd ${SKIPPER_USERNAME} > /dev/null
  if [ x"$?" != x"0" ]; then
    useradd -u ${SKIPPER_UID} --non-unique ${SKIP_HOME_DIR_PARAM} "${SKIPPER_USERNAME}"
  fi

  chown ${SKIPPER_USERNAME}:${SKIPPER_USERNAME} ${HOME_DIR}

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

  if sudo -l -U ${SKIPPER_USERNAME} 2> /dev/null; then
    # for debian distros (maybe for others too) -m flag resets the PATH variable
    # so we need to use sudo -E to preserve the PATH
    sudo -sE -u ${SKIPPER_USERNAME} $@
  else 
    su -m ${SKIPPER_USERNAME} -c "$@"
  fi
else
  bash -c "$@"
fi
