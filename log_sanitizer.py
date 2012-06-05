#!/usr/bin/python
import sys, getopt, re, hashlib

# Salts used for the SHA-1 hash
salt = {'ip' : 'change me!',
        'username' : 'change me!',
        'userid' : 'change me!',
        'email' : 'change me!'}

# List containing dicts of regexes that find sensitive data, 
# and field names that refer to regex fields and salts
regex = [{'exp': '/user/(?P<username>[^\? /]+)', 
          'field' : 'username'},
         {'exp': '(\?|&)email=(?P<email>[^&]+)', 
          'field' : 'email'},
         {'exp': '(\?|&)userid=(?P<userid>\d+)', 
          'field' : 'userid'},
         {'exp': '(\?|&)conditions\.(\d)+\.user_id=(?P<userid>\d+)', 
          'field' : 'userid'},
         {'exp': '(\?|&)conditions\.(\d)+\.name=(?P<username>[^ /]+)',
          'field' : 'username'},
         {'exp': '(\?|&)conditions\.(\d)+\.voter_id=(?P<userid>\d+)',
          'field' : 'userid'},
         {'exp': '(\?|&)conditions\.(\d)+\.args\.(\d)+=(?P<userid>\d+)',
          'field' : 'userid'}]

def hash(salt, value):
    return hashlib.sha1(salt + value).hexdigest()

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
        parts = line.split(' ', 3)

        # Hash IP
        ip_hash = hash(salt['ip'], parts[1])

        # Match regexes
        for r in regex:
            # Replace the current field's value
            parts[3] = r['exp'].sub(replace(r['field']), parts[3])

        # Print line
        stdout.write('%s %s %s %s' % (parts[0], ip_hash, parts[2], parts[3]))

if __name__ == "__main__":
    main()