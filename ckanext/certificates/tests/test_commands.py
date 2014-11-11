from nose.tools import assert_equal

from ckanext.certificates.commands import CertificateCommand


class TestSiteUrlFilter:
    def test_regex(self):
        config = {'ckanext.certificates.site_url_regex': 'http://data.gov.uk'}
        compiled, regex = CertificateCommand._get_site_url_filter(config)
        assert_equal(regex, 'http://data.gov.uk')
        assert compiled.search('http://data.gov.uk/dataset/a')
        assert not compiled.search('http://other_site/dataset/a')
        assert compiled.search(' http://data.gov.uk/dataset/a')

    def test_string(self):
        config = {'ckanext.certificates.site_url': 'http://data.gov.uk'}
        compiled, regex = CertificateCommand._get_site_url_filter(config)
        assert_equal(regex, '^https?\\:\\/\\/(www.)?data\\.gov\\.uk.*')
        assert compiled.search('http://data.gov.uk/dataset/a')
        assert compiled.search('http://www.data.gov.uk/dataset/a')
        assert compiled.search('https://data.gov.uk/dataset/a')
        assert not compiled.search('http://other_site/dataset/a')
        assert not compiled.search(' http://data.gov.uk/dataset/a')

    def test_string2(self):
        config = {'ckanext.certificates.site_url': 'https://www.data.gov.uk'}
        compiled, regex = CertificateCommand._get_site_url_filter(config)
        assert_equal(regex, '^https?\\:\\/\\/(www.)?data\\.gov\\.uk.*')


class TestGetPackageNameFromUrl:
    def test_simple(self):
        url = 'http://data.gov.uk/dataset/gbc_planning_applications'
        package = CertificateCommand._get_package_name_from_url(url)
        assert_equal('gbc_planning_applications', package)

    def test_trailing_slash(self):
        url = 'http://data.gov.uk/dataset/gbc_planning_applications/'
        package = CertificateCommand._get_package_name_from_url(url)
        assert_equal('gbc_planning_applications', package)
