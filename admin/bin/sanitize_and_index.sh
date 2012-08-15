#!/bin/sh

INCOMING=~/incoming/*/*
SANITIZE=~/musicbrainz-server-log-analysis/sanitizing/log_sanitizer.py
TMP_DIR=/tmp/logs
SPLUNK=/usr/local/splunk/bin/splunk

mkdir -p $TMP_DIR

for FILE in `ls $INCOMING`
do
	echo `date`: Sanitizing $FILE
	TMP_FILE=$TMP_DIR'/'musicbrainz-access-`date +%Y%m%d`'.log'
	python $SANITIZE < $FILE > $TMP_FILE
	echo `date`: Importing $FILE to splunk
	$SPLUNK add oneshot $TMP_FILE -sourcetype nginx_log -auth import:logloglog
	rm -f $TMP_FILE
	rm -f $FILE
done

rmdir $TMP_DIR
