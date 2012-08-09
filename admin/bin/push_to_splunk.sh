#!/bin/sh

HOSTNAME=`hostname`
SRC=/var/log/nginx/archive/musicbrainz-full-access.log-`date +%Y%m%d`
DEST=logs@pino.mb:incoming/$HOSTNAME

if [ -e $SRC ]
then
	rsync -z $SRC $DEST
fi
