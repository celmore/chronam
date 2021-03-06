from __future__ import absolute_import, print_function

from cStringIO import StringIO
from optparse import make_option

import pymarc

from chronam.core import index
from chronam.core.models import Title

from . import LoggingCommand


class Command(LoggingCommand):
    """
    Management command for purging title records which have an 856 field
    containing a link to Chronicling America, and which appear to be records
    for an electronic only version of a title 245 $h == [electronic resource].

    The script is careful not to purge any records that have issues attached
    to them.  See https://rdc.lctl.gov/trac/ndnp/ticket/375 for context.

    If you want to see the records that will be purged use the --pretend
    option.
    """

    option_list = LoggingCommand.option_list + (
        make_option('-p', '--pretend', dest='pretend', action='store_true'),
    )

    def handle(self, **options):
        for title in Title.objects.filter(urls__value__icontains='chroniclingamerica'):
            record = pymarc.parse_xml_to_array(StringIO(title.marc.xml))[0]
            if record['245']['h'] == '[electronic resource].':
                if options['pretend']:
                    self.stdout.write(title)
                else:
                    self.stdout.write("deleting %s [%s] from solr index")
                    index.delete_title(title)
                    self.stdout.write("purging %s [%s]" % (title, title.lccn))
                    title.delete()
        if not options['pretend']:
            index.commit()
