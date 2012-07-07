#!/usr/bin/python

import psycopg2
import sys, utils, json, yaml, config
from splunklib.client import connect

def main():

    # Parse the YAML file that contains queries
    file = open('queries.yml')
    queries = yaml.load(file.read())
    
    # Connect to splunk
    splunk_conn = connect(**config.SPLUNK_CREDENTIALS)
    
    # Connect to the db
    db_conn = psycopg2.connect(config.DB_CREDENTIALS)
    db_cur = db_conn.cursor()
    
    # Run queries
    for query_dict in queries:
        # Taking the first element of the dictionary
        # This is because of the YAML format
        query = query_dict.values()[0]
        
        # Get response in JSON format
        response = splunk_conn.jobs.create(query['query'], exec_mode="oneshot", output_mode="json")
        
        print "Processing query: %s" % query['name']
        data = json.loads(str(response))
        
        # Store results in db
        db_cur.execute("INSERT INTO log_statistic (report_type, data) VALUES (%s, %s);",
            ("Test report: " + str(query['name']), str(data)))
    
    # Commit, close connection    
    db_conn.commit()
    db_cur.close()
    db_conn.close()

if __name__ == "__main__":
    main()
    