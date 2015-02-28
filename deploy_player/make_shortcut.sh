#!/bin/sh

BASEDIR=$( cd "$( dirname "$0" )" && pwd )
echo $BASEDIR

TEXT="
[Desktop Entry]\n
Version=1.0\n
Name=Pupil Player\n
Comment=Pupil Player Software\n
Exec= '${BASEDIR}/pupil_player/pupil_player' %f %d\n
Icon= ${BASEDIR}/pupil_player/icon.ico\n
Terminal=true\n
Type=Application\n
Categories=Application;"


echo $TEXT > pupil_player.desktop
chmod 775 pupil_player.desktop