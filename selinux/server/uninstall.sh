#!/bin/sh

NAME="pulp-server"
SELINUX_VARIANTS="mls strict targeted"
MODULE_TYPE="apps"
INSTALL_DIR="/usr/share"

for selinuxvariant in ${selinux_variants}
do
    /usr/sbin/semodule -s ${selinuxvariant} -r ${NAME} &> /dev/null || :
    rm -f ${INSTALL_DIR}/${selinuxvariant}/${NAME}.pp
done

rm -f ${INSTALL_DIR}/selinux/devel/include/${MODULE_TYPE}/${NAME}.if