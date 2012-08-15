MusicBrainz-server-log-analysis
    A repository for my Google Summer of Code project. A short description for each important file follows:

admin/

    bin/push_to_splunk.sh
        Shell script, that pushes sanitized logs to splunk. Written by Robert Kaye.
        
querying/

    config_default.py
        Default configurations/credentials for the database and splunk.
        
    entity_tables.yml
        YAML file that stores entity (artist, release-group, etc.) table names, the corresponding name tables, and redirect tables.
        
    queries.yml
        YAML file that stores queries to run on Splunk, with additional metadata, that we use for processing and display
        
    queries_test.yml
        The same as the queries file, except the queries are limited to a very small subset of data, so the querying runs much faster. This is used for testing purposes.
        
    run_queries.py
        The actual querying script. It parses the YAML file that stores queries, then runs them on the Splunk server. After processing the results, it stores them in the database

sanitizing/

    log_sanitizer.py
        Sanitizes logs, changing any IP addresses or sensitive data. The sensitive parts are hashed with SHA-1, then converted to base64 for brevity.

    log_sanitizer_test.py
        Tests the results of log_sanitizer.py