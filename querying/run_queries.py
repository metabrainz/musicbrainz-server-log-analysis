#!/usr/bin/python

import psycopg2
import sys, utils, json, yaml, config
from splunklib.client import connect

def main():

    # Parse the YAML file that contains queries
    file = open('queries.yml')
    queries = yaml.load(file.read())
    
    # Connect to splunk
    try:
        splunk_conn = connect(**config.SPLUNK_CREDENTIALS)
    except:
        print "Couldn't connect to Splunk server"
        sys.exit(1)
    
    # Connect to the db
    try:
        db_conn = psycopg2.connect(config.DB_CREDENTIALS)
    except Exception, e:
            print e.pgerror
            sys.exit(1)
            
    db_cur = db_conn.cursor()
    
    # Run queries
    for query_dict in queries:
        # Taking the first element of the dictionary
        # This is because of the YAML format
        query = query_dict.values()[0]
        
        # Get response in JSON format
        try:
            response = splunk_conn.jobs.create(query['query'], exec_mode="oneshot", output_mode="json")
        except:
            print "Error running Splunk query: %s" % (query['query'])
            sys.exit(1)
            
        print "Processing query: %s" % query['name']
        data_json = json.loads(str(response))
        data_json_wrapper = {'data': data_json, 'name': query['name']}
        data = json.dumps(data_json_wrapper)
        
        try:
            # Store results in db, commit
            db_cur.execute("INSERT INTO log_statistic (report_type, data) VALUES (%s, %s);",
                ("Test report type", str(data)))
            db_conn.commit()
        except Exception, e:
            # Print error, return exit code 1
            print e.pgerror
            sys.exit(1)
            
    # Close connection
    db_cur.close()
    db_conn.close()
    
    # Exit code 0
    sys.exit(0)

if __name__ == "__main__":
    main()
    