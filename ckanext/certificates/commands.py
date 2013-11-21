import os
import sys

import ckanext.certificates.client as client

from ckan.lib.cli import CkanCommand

class CertificateCommand(CkanCommand):
    """
    Fetch certificates from theodi.org

    Fetches and parses the ODI atom feed (https://certificates.theodi.org/datasets.feed)
    checking each entry to see if it exists within the local site. If so then the
    URL of the HTML rendering, and the URL of the JSON describing the certificate are
    stored in package extras (odi-certificate-html and odi-certificate-json).
    """
    summary = __doc__.strip().split('\n')[0]
    usage = '\n' + __doc__
    max_args = 0
    min_args = 0

    def __init__(self, name):
        super(CertificateCommand, self).__init__(name)

    def setup_logging(self):
        import logging
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)
        self.log.debug("Database access initialised")

    def command(self):
        # Load configuration
        self._load_config()

        # Initialise database access
        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)
        model.repo.new_revision()

        # Logging, post-config
        self.setup_logging()

        # Use the generate_entries generator to get all of
        # the entries from the ODI Atom feed.  This should
        # correctly handle all of the pages within the feed.
        for entry in client.generate_entries(self.log):
            pkg = self._get_package(entry)
            print entry



    def _get_package(self, entry):
        """
        Pulls data from the entry in an attempt to find a local package,
        which, if successful is returned.  None is returned if the package
        has been deleted, or is not a package for this site.
        """
        import ckan.model as model

        return None

