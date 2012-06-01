#!/usr/bin/python
import sys, getopt, re, hashlib

# Salts used for the SHA-1 hash
salt = {'ip' : 'change me!',
        'username' : 'change me!',
        'userid' : 'change me!',
        'email' : 'change me!'}

# List containing dicts of regexes that find sensitive data, 
# and field names that refer to regex fields and salts
regex = [{'exp': '/show/user/.*(\?|&)userid=(?P<userid>\d+)', 
          'field' : 'userid'},
         {'exp': '/user/(?P<username>[^ /]+)', 
          'field' : 'username'},
         {'exp': '/verify-email.*(\?|&)email=(?P<email>[^&]+)', 
          'field' : 'email'},
         {'exp': '/verify-email.*(\?|&)email=.*(\?|&)userid=(?P<userid>\d+)', 
          'field' : 'userid'},
         {'exp': '/mod/search/pre/voted.html.*(\?|&)userid=(?P<userid>\d+)', 
          'field' : 'userid'},
         {'exp': '.*(\?|&)conditions\.(\d)+\.user_id=(?P<userid>\d+)', 
          'field' : 'userid'}]

def hash(salt, value):
    return hashlib.sha1(salt + value).hexdigest()

def main():
    # Compile regexes
    for r in regex:
        r['exp'] = re.compile(r['exp'])

    # Read input
    for line in sys.stdin:
        # Split line into: timestamp, ip, http method, rest of line
        parts = line.split(' ', 3)

        # Hash IP
        ip_hash = hash(salt['ip'], parts[1])

        # Match regexes
        for r in regex:
            match = r['exp'].match(parts[3])
            if match:
                # If it matches replace the sensitive part with a hash
                match_string = match.group(r['field'])
                match_hash = hash(salt[r['field']], match_string)
                parts[3] = parts[3].replace(match_string, match_hash)

        # Print line
        print '%s %s %s %s' % (parts[0], ip_hash, parts[2], parts[3])

if __name__ == "__main__":
    main()