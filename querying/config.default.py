#!/usr/bin/python

# Database connection details
db_host = '127.0.0.1'
db_port = 5432
db_name = 'musicbrainz_db'
db_user = 'user'
db_password = 'password'

db_template = "host=%s port=%s dbname=%s user=%s"
DB_CREDENTIALS = db_template % (db_host, db_port, db_name, db_user)

# Splunk connection credentials
splunk_username = 'user'
splunk_password = 'password'
splunk_host = 'localhost'
splunk_scheme = 'https'
splunk_port = 8089

SPLUNK_CREDENTIALS = {'username' : splunk_username, 'password' : splunk_password,
    'host' : splunk_host, 'scheme' : splunk_scheme, 'port' : splunk_port}
