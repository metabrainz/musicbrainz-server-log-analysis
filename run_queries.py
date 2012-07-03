#!/usr/bin/python

import sys, utils, csv, json, psycopg2
from splunklib.client import connect

PG_CONN_STR = """host=127.0.0.1 port=5432 dbname=musicbrainz_db_static user=plaintext"""

def main():
    
	usage = "usage: run_queries.py queries.csv"
	opts = utils.parse(sys.argv[1:], {}, ".splunkrc", usage=usage)

	# Check argument count
	if len(opts.args) < 1:
		utils.error("Query file required", 2)

	# Create reader
	reader = csv.reader(open(opts.args[0]), delimiter=',', quotechar='"')
	
	# Get header of csv file
	header = reader.next()
	
	# Load queries from queries.csv
	queries = []
	for row in reader:
		new_query = {}
		for i in range(0, len(row)):
			new_query[header[i]] = row[i]
		queries.append(new_query)
	
	# Connect to splunk
	splunk_conn = connect(**opts.kwargs)
	
	# Connect to the db
	db_conn = psycopg2.connect(PG_CONN_STR)
	db_cur = db_conn.cursor()
	
	# Run queries
	for query in queries:
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
	