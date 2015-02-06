from ckanext.certificates.tasks import create_certificate, update_certificate
from nose.tools import assert_equal
import mock
import json

class TestAPIBase(object):
    def setUp(self):
        self.patcher = mock.patch('requests.post')
        self.post = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

class TestCreateCertificate(TestAPIBase):
    def test_post_is_made(self):
        create_certificate({'name': 'foo'})
        assert_equal(True, self.post.called)

    def test_url(self):
        create_certificate({'name': 'foo'})
        args, kwargs = self.post.call_args
        url = args[0]
        assert_equal(True, url.startswith('http://192.168.11.11:3000'))
        assert_equal(True, url.endswith('/datasets'))

    def test_content_type(self):
        create_certificate({'name': 'foo'})
        args, kwargs = self.post.call_args
        content_type = kwargs['headers']['content-type']
        assert_equal('application/json', content_type)

    def test_auth(self):
        create_certificate({'name': 'foo'})
        args, kwargs = self.post.call_args
        auth = kwargs['auth']
        assert_equal('dgu@example.com', auth.username)
        assert_equal('DxmzWJnwKoXBSaDWyzeh', auth.password)

    def test_data(self):
        create_certificate({'name': 'foo'})
        args, kwargs = self.post.call_args
        data = json.loads(kwargs['data'])
        assert_equal('GB', data['jurisdiction'])
        assert_equal('http://test.ckan.net/dataset/foo',
                     data['dataset']['documentationUrl'])

class TestUpdateCertificate(TestAPIBase):
    def setUp(self):
        super(TestUpdateCertificate, self).setUp()
        self.pkg_dict = {
            'name': 'foo',
            'extras': [{'key': 'odi-certificate',
                        'value': '{"certificate_url": "foo/42/bar"}'}]
        }

    def test_no_update_if_no_certificate(self):
        update_certificate({'name': 'foo'})
        assert_equal(False, self.post.called)

    def test_update_if_certificate(self):
        update_certificate(self.pkg_dict)
        assert_equal(True, self.post.called)

    def test_url(self):
        update_certificate(self.pkg_dict)
        args, kwargs = self.post.call_args
        url = args[0]
        assert_equal(True, url.startswith('http://192.168.11.11:3000'))
        assert_equal(True, url.endswith('/datasets/42/certificates'))

    def test_auth(self):
        update_certificate(self.pkg_dict)
        args, kwargs = self.post.call_args
        auth = kwargs['auth']
        assert_equal('dgu@example.com', auth.username)
        assert_equal('DxmzWJnwKoXBSaDWyzeh', auth.password)

    def test_data(self):
        update_certificate(self.pkg_dict)
        args, kwargs = self.post.call_args
        data = json.loads(kwargs['data'])
        assert_equal('GB', data['jurisdiction'])
        assert_equal('http://test.ckan.net/dataset/foo',
                     data['dataset']['documentationUrl'])
