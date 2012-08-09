#!/bin/sh

HOSTNAME=`hostname`
SRC=/var/log/nginx/archive/musicbrainz-full-access.log-????????
DEST=logs@pino.mb:incoming/$HOSTNAME

rsync -z $SRC $DEST
