#!/usr/bin/python
import sys, getopt, re, hashlib, base64

# Salts used for the SHA-1 hash
salt = {'ip' : 'change me!',
        'username' : 'change me!',
        'userid' : 'change me!',
        'email' : 'change me!'}

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
    return base64.b64encode_urlsafe(hashlib.sha1(key).digest())

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
        # Split line into: timestamp, ip, http method, rest of line
        [timestamp, ip, http_method, url, rest] = line.split(' ', 4)

        # Hash IP
        ip_hash = hash(salt['ip'], ip)

        # Match regexes
        for r in regex:
            # Replace the current field's value
            url = r['exp'].sub(replace(r['field']), url)

        # Print line
        stdout.write('%s %s %s %s %s' % (timestamp, ip_hash, http_method, url, rest))

if __name__ == "__main__":
    main()
