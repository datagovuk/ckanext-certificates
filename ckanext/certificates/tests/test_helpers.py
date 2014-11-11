from ckanext.certificates.helpers import has_certificate, get_certificate_data
from nose.tools import assert_equal
from collections import namedtuple
import json

Package = namedtuple('Package', ['extras'])

cert = {u'1': 2, u'3': u'4'}

class TestHasCertificate(object):
    def test_no_certificate(self):
        pkg = Package({})
        assert_equal(False, has_certificate(pkg))

    def test_valid_json(self):
        pkg = Package({'odi-certificate': json.dumps(cert)})
        assert_equal(True, has_certificate(pkg))

    def test_invalid_json(self):
        pkg = Package({'odi-certificate': 'INVALID'})
        assert_equal(False, has_certificate(pkg))

class TestGetCertificateData(object):
    def test_invalid_json(self):
        pkg = Package({'odi-certificate': 'INVALID'})
        assert_equal(None, get_certificate_data(pkg))

    def test_valid_json(self):
        pkg = Package({'odi-certificate': json.dumps(cert)})
        assert_equal(cert, get_certificate_data(pkg))
