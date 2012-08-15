#!/usr/bin/python

#    Copyright (C) 2012 Daniel Bali
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import psycopg2
import sys, utils, json, yaml, config

from splunklib.client import connect
from splunklib.binding import HTTPError

# Test mode, and YAML files
TEST_MODE = True
QUERIES = 'queries.yml'
QUERIES_TEST = 'queries_test.yml'
ENTITY_TABLES = 'entity_tables.yml'

def look_up_mbid_list(mbid_list, mbid_dict, query_template, entity_tables, table_key, cursor):
    for entity_dict in entity_tables['entity_tables']:
        entity = entity_dict.values()[0]
        
        if mbid_list:
            # Look up id in table with the given key (entity or redirect)
            # Look up name in table specified by name_table
            lookup_query = query_template % (entity[table_key], entity['name_table'], "%s")
            
            try:
                cursor.execute(lookup_query, (tuple(mbid_list),))
            except Exception, e:
                print "Query was: %s" % lookup_query
                print e.pgerror
                sys.exit(1)
            
            # 0: mbid, 1: name
            for record in cursor.fetchall():
                mbid_dict[record[0]] = {
                    'name': record[1],
                    'entity': entity['name']
                }
                mbid_list.remove(record[0])

def main():

    # Parse the YAML file that contains queries
    if TEST_MODE:
        file = open(QUERIES_TEST)
    else:
        file = open(QUERIES)
    queries = yaml.load(file.read())
    
    # Parse YAML file for entity name and redirect tables
    file = open(ENTITY_TABLES)
    entity_tables = yaml.load(file.read())
    
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
            try:
                data_json = json.loads(str(response))
            except ValueError, e:
                print "Warning: no results returned for query '%s'" % splunk_query['name']
                data_json = [{'message': 'No results found'}]
            
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
                
                # Store name and entity type for mbids
                mbid_dict = {}
                look_up_mbid_list(mbid_list, mbid_dict, entity_query_template, entity_tables, 'entity_table', db_cursor)
                            
                # Try to look up tables/ids with redirect tables   
                # for mbids that weren't found in "normal" tables
                look_up_mbid_list(mbid_list, mbid_dict, redirect_query_template, entity_tables, 'redirect_table', db_cursor)
                        
            # Filter data where it's needed
            if splunk_query.has_key('filter'):
                for filter_dict in splunk_query['filter']:
                    filter = filter_dict.values()[0]
                    data_json = [line for line in data_json if line[filter['column']] not in filter['values']]
            
            for line in data_json:
                
                # Remove "private" key-value pairs
                for key in line.keys():
                    if key.startswith('_'):
                        line.pop(key)
                
                # Correct percent rounding to maximum 2 decimal places
                if 'percent' in line:
                    line['percent'] = str(round(float(line['percent']), 2))
                
                # Store names instead of mbids in JSON
                if 'mbid' in line:
                    if line['mbid'] in mbid_dict:
                        # Create a link to the entity here
                        link = '<a href="/%s/%s">%s</a>'
                        line['name'] = link % (mbid_dict[line['mbid']]['entity'], line['mbid'], mbid_dict[line['mbid']]['name'].decode('utf-8'))
                    else:
                        # If name was not found, display the mbid
                        line['name'] = '[%s]' % line['mbid']
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
    