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

import sys, getopt, re, hashlib, base64
from salts import salt

# List containing dicts of regexes that find sensitive data, 
# and field names that refer to regex fields and salts
regex = [{'exp': '/user/(?P<username>[^\? /]+)', 
          'field' : 'username'},
         {'exp': '(\?|&)email=(?P<email>[^ &]+)', 
          'field' : 'email'},
		 # In one special case the verify-email line is embedded in a /login?uri=... line
		 # This means that special characters are URL encoded, and we need to match them that way
         {'exp': '(%3F|%3f|%26)email(%3D|%3d)(?P<email>[^ %]+%40[^%]+)', 
          'field' : 'email'},		  
         {'exp': '(\?|&)userid=(?P<userid>\d+)', 
          'field' : 'userid'},
		 # This is also for the special case
         {'exp': '(%3F|%3f|%26)userid(%3D|%3d)(?P<userid>\d+)', 
          'field' : 'userid'},		  
         {'exp': '(\?|&)conditions\.(\d)+\.user_id=(?P<userid>\d+)', 
          'field' : 'userid'},
         {'exp': '(\?|&)conditions\.(\d)+\.name=(?P<username>[^ /]+)',
          'field' : 'username'},
         {'exp': '(\?|&)conditions\.(\d)+\.voter_id=(?P<userid>\d+)',
          'field' : 'userid'},
         {'exp': '(\?|&)conditions\.(\d)+\.args\.(\d)+=(?P<userid>\d+)',
          'field' : 'userid'}]
		  
hash_memo = {}
def hash(salt, value):
    global hash_memo
    key = salt + value
    if key not in hash_memo:
        hash_memo[key] = do_hash(key)
    return hash_memo[key]

def do_hash(key):
    return base64.urlsafe_b64encode(hashlib.sha1(key).digest())

# Replace function for re.sub()
# Takes the named group for the given field
# Replaces the value with a hash
def replace(field):
    def replace_string(matchobj):
        new_hash = hash(salt[field], matchobj.group(field))
        return matchobj.group(0).replace(matchobj.group(field), new_hash)
    return replace_string

def main(stdin=sys.stdin, stdout=sys.stdout):
    # Compile regexes
    for r in regex:
        r['exp'] = re.compile(r['exp'])

    # Read input
    for line in stdin:
        # Split line to parts.
        try:
            [
                timestamp,
                ip,
                http_method,
                url,
                http_version,
                http_response,
                page_size,
                z,
                up,
                ms,
                ums,
                ol,
                h
            ] = line.strip().split(' ')
        except ValueError, e:
            print line
        
        # Hash IP
        ip_hash = hash(salt['ip'], ip)

        # Match regexes
        for r in regex:
            # Replace the current field's value
            url = r['exp'].sub(replace(r['field']), url)

        # Print line
        # Remove some fields that we don't need to decrease size
        # Extra quote needed, because http_version (HTTP/1.1") was removed
        new_line = '%s %s %s %s" %s %s %s %s\n' % (
            timestamp,
            ip_hash,
            http_method,
            url,
            http_response,
            page_size,
            z,
            ums
        )
        stdout.write(new_line)

if __name__ == "__main__":
    main()
