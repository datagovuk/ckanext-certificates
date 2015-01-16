import json
import re
import logging
import datetime

from ckan.lib.cli import CkanCommand


class CertificateCommand(CkanCommand):
    """
    Fetch certificates from theodi.org

    Fetches and parses the ODI atom feed
    (https://certificates.theodi.org/datasets.feed) checking each entry to see
    if it exists within the local site. If so then information about the
    certificate is stored as JSON in package extras as "odi-certificate".
    """
    summary = __doc__.strip().split('\n')[0]
    usage = '\n' + __doc__
    max_args = 0
    min_args = 0

    def __init__(self, name):
        super(CertificateCommand, self).__init__(name)
        self.parser.add_option('--hours', dest='hours',
            help='Filter to the most recent X hours of changes')
        self.parser.add_option('--days', dest='days',
            help='Filter to the most recent X days of changes')

    def command(self):
        # Load configuration
        self._load_config()

        # Initialise database access
        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)

        # Logging, post-config
        log = logging.getLogger(__name__)
        log.setLevel(logging.DEBUG)
        log.debug("Database access initialised")

        from pylons import config

        # 'site_url_filter' decides whether a certificate is from this site or
        # not from its 'about' field
        site_url_filter, site_url_filter_regex = \
            CertificateFetcher._get_site_url_filter(config)
        log.debug('Site url filter (regex): %s', site_url_filter_regex)

        # Time filter
        time_filter_h = int(self.options.hours or 0)
        time_filter_d = int(self.options.days or 0)
        since_datetime = datetime.datetime.utcnow() - \
            datetime.timedelta(days=time_filter_d, hours=time_filter_h)

        CertificateFetcher.fetch(site_url_filter, since_datetime)


class CertificateFetcher(object):

    @classmethod
    def fetch(cls, site_url_filter, since_datetime):
        import ckan.model as model
        from running_stats import StatsList
        log = logging.getLogger(__name__)
        stats = StatsList()

        # Use the generate_entries generator to get all of
        # the entries from the ODI Atom feed.  This should
        # correctly handle all of the pages within the feed.
        import ckanext.certificates.client as client
        for entry in client.generate_entries(since=since_datetime):

            # We have to handle the case where the rel='about' might be
            # missing, if so we'll ignore it and catch it next time
            about = entry.get('about', '')
            if not about:
                log.debug(stats.add('Ignore - no rel="about" specifying the dataset',
                                    '%s "%s" %s' % (about, entry['title'], entry['id'])))
                continue

            if not site_url_filter.search(about):
                log.debug(stats.add('Ignore - "about" field does not reference this site',
                                    '%s "%s" %s' % (about, entry['title'], entry['id'])))
                continue

            if not '/dataset/' in entry['about']:
                log.debug(stats.add('Ignore - is "about" DGU but not a dataset',
                                    '%s "%s" %s' % (about, entry['about'], entry['id'])))
                continue

            pkg = cls._get_package_from_url(entry.get('about'))
            if not pkg:
                log.error(stats.add('Unable to find the package',
                                    '%s "%s" %s %r' % (about, entry['about'], entry['id'], entry.get('about'))))
                continue

            # Build the JSON subset we want to describe the certificate
            badge_data = client.get_badge_data(entry['alternate'])
            if not badge_data:
                log.info(stats.add('Error fetching badge data - skipped',
                                   '%s "%s" %s' % (about, entry['title'], entry['id'])))
                continue
            badge_data['cert_title'] = entry.get('content', '')  # e.g. 'Basic Level Certificate'

            badge_json = json.dumps(badge_data)
            if pkg.extras.get('odi-certificate') == badge_json:
                log.debug(stats.add('Certificate unchanged',
                                         badge_data['certificate_url']))
            else:
                operation = 'updated' if 'odi-certificate' in pkg.extras \
                    else 'added'
                model.repo.new_revision()
                pkg.extras['odi-certificate'] = json.dumps(badge_data)
                log.debug(stats.add('Certificate %s' % operation,
                               '"%s" %s' % (badge_data['title'],
                                            badge_data['certificate_url'])))
                model.Session.commit()

        log.info('Summary:\n' + stats.report())

    @classmethod
    def _get_package_from_url(cls, url):
        """
        Pulls data from the entry in an attempt to find a local package,
        which, if successful is returned.  None is returned if the package
        has been deleted, or is not a package for this site.
        """
        import ckan.model as model

        name = cls._get_package_name_from_url(url)
        return model.Package.get(name)

    @staticmethod
    def _get_package_name_from_url(url):
        from urlparse import urlparse

        # Package name is the last part of the URL
        obj = urlparse(url)
        name = obj.path.rstrip('/').split('/')[-1]
        return name

    @staticmethod
    def _get_site_url_filter(config):
        site_url_regex = config.get('ckanext.certificates.site_url_regex')
        if not site_url_regex:
            site_url = config.get('ckanext.certificates.site_url') or \
                config.get('ckan.site_url')
            site_url_regex = '^' + re.escape(site_url) + '.*'
            # allow https variation
            site_url_regex = re.sub(r'https?\\:', r'https?\:', site_url_regex)
            # allow www. variation
            site_url_regex = re.sub(r'\\/\\/(www\\\.)?', r'\/\/(www.)?',
                                    site_url_regex)
        site_url_filter = re.compile(site_url_regex)
        return site_url_filter, site_url_regex
