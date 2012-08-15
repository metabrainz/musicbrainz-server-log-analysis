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

import random
import unittest
from StringIO import StringIO
from string import Template

class TestSanitizer(unittest.TestCase):
    # List of input data to use for testing
    input_list = []

    def setUp(self):
        # Create input data templates
        template = {
            'username' : [
                Template("""1000000000.000 127.0.0.1 "GET /user/${username}/edits/open?page=1 HTTP/1.1" 200 9202 z=- up=10.1.1.20:80 ms=2.956 ums=2.956 ol=- h=musicbrainz.org """),
                Template("""1000000000.000 127.0.0.1 "GET /search/edits?auto_edit_filter=&order=asc&negation=0&combinator=and&conditions.0.field=vote&conditions.0.operator=%3D&conditions.0.voter_id=1234567890&conditions.0.args=no&conditions.1.field=artist&conditions.1.operator=subscribed&conditions.1.name=&conditions.1.=&conditions.1.args.0=&conditions.1.user_id=1234567890&conditions.2.field=status&conditions.2.operator=%3D&conditions.2.args=1&conditions.3.field=editor&conditions.3.operator=!%3D&conditions.3.name=${username}&conditions.3.=&conditions.3.args.0=1234567890&field=Please+choose+a+condition HTTP/1.1" 200 35410 z=9.25 up=10.1.1.17:80 ms=8.376 ums=8.220 ol=- h=musicbrainz.org """)
            ],
            'userid' : [
                Template("""1000000000.000 127.0.0.1 "GET /show/user/?userid=${userid} HTTP/1.0" 404 10880 z=- up=10.1.1.23:80 ms=0.793 ums=0.793 ol=- h=musicbrainz.org """),
                Template("""1000000000.000 127.0.0.1 "GET /mod/search/pre/voted.html?userid=${userid} HTTP/1.0" 404 10906 z=- up=10.1.1.17:80 ms=0.859 ums=0.859 ol=- h=musicbrainz.org """),
                Template("""1000000000.000 127.0.0.1 "GET /verify-email?email=not_a_real_email%40not_a_real_website.com&chk=0&time=0&userid=${userid} HTTP/1.1" 200 2949 z=4.02 up=10.1.1.23:80 ms=0.810 ums=0.810 ol=- h=musicbrainz.org """),
                Template("""1000000000.000 127.0.0.1 "GET /search/edits?auto_edit_filter=&order=asc&negation=0&combinator=and&conditions.0.field=vote&conditions.0.operator=%3D&conditions.0.voter_id=${userid}&conditions.0.args=no&conditions.1.field=artist&conditions.1.operator=subscribed&conditions.1.name=&conditions.1.=&conditions.1.args.0=&conditions.1.user_id=${userid}&conditions.2.field=status&conditions.2.operator=%3D&conditions.2.args=1&conditions.3.field=editor&conditions.3.operator=!%3D&conditions.3.name=not_a_real_username&conditions.3.=&conditions.3.args.0=${userid}&field=Please+choose+a+condition HTTP/1.1" 200 35410 z=9.25 up=10.1.1.17:80 ms=8.376 ums=8.220 ol=- h=musicbrainz.org """)
            ],
            'email' : [
                Template("""1000000000.000 127.0.0.1 "GET /verify-email?email=${email}&chk=0&time=0&userid=1234567890 HTTP/1.1" 200 2949 z=4.02 up=10.1.1.23:80 ms=0.810 ums=0.810 ol=- h=musicbrainz.org """)
            ]
        }

        # Define sample data
        sample_data = {
            'username' : ['bob123', 'alice456', '%3cplaintext%3e'],
            'userid' : ['012345', '456789', '789abc'],
            'email' : ['lorem%40ipsum.com', 'dolor%40sit.co.uk', 'amet%40consectetuer.museum']
        }

        # Populate input data list using templates and sample data
        # Store the sensitive part for each case to make assertion easier
        for k, v in template.iteritems():
            for i in range(100):
                tpl = random.choice(v)
                tpl_data = random.choice(sample_data[k])
                input_dict = {
                    'line' : tpl.substitute({k : tpl_data}),
                    'sensitive' : tpl_data}
                self.input_list.append(input_dict)

    # Log sanitizer test
    def test_sanitizer(self):
        import log_sanitizer

        for i in range(len(self.input_list)):
            # stdin, containing 1 line of input
            stdin = StringIO(self.input_list[i]['line'])

            # stdout for log_sanitizer.main()
            stdout = StringIO()

            # Sanitize test data
            log_sanitizer.main(stdin=stdin, stdout=stdout)

            # Get output
            output = stdout.getvalue().strip()

            print output
            
            # Check whether sensitive data was replaced
            self.assertEqual(output.find(self.input_list[i]['sensitive']), -1)

if __name__ == '__main__':
    unittest.main()