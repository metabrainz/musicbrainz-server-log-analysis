#!/usr/bin/python

import psycopg2
import sys, utils, json, yaml, config

from splunklib.client import connect
from splunklib.binding import HTTPError

TEST_MODE = True

def look_up_mbid_list(mbid_list, mbid_dict, query_template, table_mapping, cursor):
    for table, name_table in table_mapping.iteritems():
        if mbid_list:
            lookup_query = query_template % (table, name_table, "%s")
            
            try:
                cursor.execute(lookup_query, (tuple(mbid_list),))
            except Exception, e:
                print "Query was: %s" % lookup_query
                print e.pgerror
                sys.exit(1)
            
            for record in cursor.fetchall():
                # TODO: enable dict access, with string indices
                mbid_dict[record[0]] = record[1]
                mbid_list.remove(record[0])

def main():

    # Parse the YAML file that contains queries
    if TEST_MODE:
        file = open('queries_test.yml')
    else:
        file = open('queries.yml')
    queries = yaml.load(file.read())
    
    # Connect to splunk
    try:
        splunk_conn = connect(**config.SPLUNK_CREDENTIALS)
    except HTTPError, e:
        print "Splunk error: %s" % str(e.message)
        sys.exit(1)
    
    # Connect to the db
    try:
        db_conn = psycopg2.connect(config.DB_CREDENTIALS)
        db_cursor = db_conn.cursor()
    except psycopg2.OperationalError, e:
        print e
        sys.exit(1)
    
    # Loop through each category
    for category_dict in queries['categories']:
        category = category_dict.values()[0]
        
        # Loop through each query in a category
        for query_dict in category['queries']:
            splunk_query = query_dict.values()[0]
            
            # Get Splunk query response
            try:
                response = splunk_conn.jobs.create(splunk_query['query'], exec_mode='oneshot', output_mode='json')
            except HTTPError, e:
                print "Splunk error: %s" % str(e.message)
                sys.exit(1)
            
            # Load JSON    
            print "Processing query: %s: %s" % (category['name'], splunk_query['name'])
            data_json = json.loads(str(response))
            
            # Try to find mbids in the response
            mbid_list = []
            for line in data_json:
                if 'mbid' in line:
                    mbid_list.append(line['mbid'])
            
            if mbid_list:
                # Form query to find names for mbids
                entity_query_template = """
                    select x.gid, x_n.name 
                    from %s x, %s x_n 
                    where x.gid in %s 
                    and x.name = x_n.id;
                """
                
                redirect_query_template = """
                    select x_r.gid, x_n.name 
                    from %s x_r, %s x_n 
                    where x_r.gid in %s
                    and x_r.new_id = x_n.id
                """
                
                # Mapping of entity tables, and name tables
                entity_tables = {
                    'artist'        : 'artist_name',
                    'release_group' : 'release_name',
                    'release'       : 'release_name',
                    'recording'     : 'track_name',
                    'work'          : 'work_name',
                    'label'         : 'label_name'
                }
                redirect_tables = {
                    'artist_gid_redirect'        : 'artist_name',
                    'release_group_gid_redirect' : 'release_name',
                    'release_gid_redirect'       : 'release_name',
                    'recording_gid_redirect'     : 'track_name',
                    'work_gid_redirect'          : 'work_name',
                    'label_gid_redirect'         : 'label_name',
                }
                
                # Store mbid - name pairs in a dict
                mbid_dict = {}
                look_up_mbid_list(mbid_list, mbid_dict, entity_query_template, entity_tables, db_cursor)
                            
                # Try to look up tables/ids with redirect tables   
                # for mbids that weren't found in "normal" tables
                look_up_mbid_list(mbid_list, mbid_dict, redirect_query_template, redirect_tables, db_cursor)
                        
            for line in data_json:
                # Remove "private" key-value pairs
                for key in line.keys():
                    if key.startswith('_'):
                        line.pop(key)
                # Store names next to mbids in JSON
                if 'mbid' in line:
                    if line['mbid'] in mbid_dict:
                        line['name'] = mbid_dict[line['mbid']]
                    else:
                        line['name'] = '{Name not found}'
                    # Do not display mbids
                    del line['mbid']
            
            # Create a wrapper for JSON data
            data_json_wrapper = {
                'data'    : data_json, 
                'name'    : splunk_query['name'],
                'display' : splunk_query['display']}
            
            data = json.dumps(data_json_wrapper)
            
            try:
                # Store results in db, commit
                db_cursor.execute("INSERT INTO log_statistic (category, data) VALUES (%s, %s);",
                    (category['name'], str(data)))
                db_conn.commit()
            except Exception, e:
                # Rollback
                db_conn.rollback()
                
                # Print error, return exit code 1
                print e.pgerror
                sys.exit(1)
                
    # Close connection
    db_cursor.close()
    db_conn.close()
    
    # Exit code 0
    sys.exit(0)
            

if __name__ == '__main__':
    main()
    