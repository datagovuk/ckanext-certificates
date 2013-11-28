import json
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

        from pylons import config

        site_url = config.get('ckan.site_url')

        # Use the generate_entries generator to get all of
        # the entries from the ODI Atom feed.  This should
        # correctly handle all of the pages within the feed.
        for entry in client.generate_entries(self.log):

            # We have to handle the case where the rel='about' might be missing, if so
            # we'll ignore it and catch it next time
            if not entry.get('about', '').startswith(site_url):
                self.log.debug('Ignoring {0}'.format(entry.get('about','No rel="about"')))
                continue

            pkg = self._get_package_from_url(entry.get('about'))
            if not pkg:
                self.log.error("Unable to find package for {0}".format(entry.get('about')))
                continue

            # Build the JSON subset we want to describe the certificate
            badge_data = client.get_badge_data(self.log, entry['alternate'])
            badge_data['cert_title'] = entry.get('content', '')

            pkg.extras['odi-certificate'] = json.dumps(badge_data)
            model.Session.add(pkg)

        model.Session.commit()

    def _get_package_from_url(self, url):
        """
        Pulls data from the entry in an attempt to find a local package,
        which, if successful is returned.  None is returned if the package
        has been deleted, or is not a package for this site.
        """
        from urlparse import urlparse
        import ckan.model as model

        # Package name is the last part of the URL
        obj = urlparse(url)
        name = obj.path.split('/')[-1]

        return model.Package.get(name)

