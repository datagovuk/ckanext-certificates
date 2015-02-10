from ckanext.certificates.tasks import create_certificate, update_certificate
from nose.tools import assert_equal, assert_true, assert_false, assert_in
import mock
import json

import ckan.model as model

class TestAPIBase(object):
    def setUp(self):
        self.post_patcher = mock.patch('requests.post')
        self.post = self.post_patcher.start()

        self.get_patcher = mock.patch('requests.get')
        self.get = self.get_patcher.start()

        model.repo.rebuild_db()

        model.repo.new_revision()
        package = model.Package(name='foo')
        model.Session.add(package)
        model.Session.commit()

    def tearDown(self):
        self.post_patcher.stop()
        self.get_patcher.stop()


class TestCreateCertificate(TestAPIBase):
    def test_post_is_made(self):
        create_certificate({'name': 'foo'})
        assert_true(self.post.called)

    def test_url(self):
        create_certificate({'name': 'foo'})
        args, kwargs = self.post.call_args
        url = args[0]
        assert_true(url.startswith('http://192.168.11.11:3000'))
        assert_true(url.endswith('/datasets'))

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

    def test_badge_fetch(self):
        self.post().json.return_value = {"success": "pending",
                                         "dataset_url": "http://example.com/foo"}

        self.get.side_effect = [
            mock.Mock(status_code=200,
                      json=mock.Mock(return_value={"success": "pending",
                                                   "dataset_url": "http://example.com/foo"})),
            mock.Mock(status_code=200,
                      json=mock.Mock(return_value={"success": True,
                                                   "dataset_url": "http://example.com/foo",
                                                   "dataset_id": 78})),
            mock.Mock(status_code=200,
                      content='''{"certificate": {"level": "FooLevel",
                                                  "created_at": "FooCreated",
                                                  "jurisdiction": "FooJurisdiction",
                                                  "dataset": {"title": "FooTitle"}}}'''),
        ]

        create_certificate({'name': 'foo'})

        assert_equal(3, self.get.call_count)

        package = model.Package.get('foo')
        assert_in('odi-certificate', package.extras)
        badge = json.loads(package.extras['odi-certificate'])
        assert_equal('FooLevel', badge['level'])
        assert_equal('FooCreated', badge['created_at'])
        assert_equal('FooJurisdiction', badge['jurisdiction'])
        assert_equal('FooTitle', badge['title'])

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
        assert_false(self.post.called)

    def test_update_if_certificate(self):
        update_certificate(self.pkg_dict)
        assert_true(self.post.called)

    def test_url(self):
        update_certificate(self.pkg_dict)
        args, kwargs = self.post.call_args
        url = args[0]
        assert_true(url.startswith('http://192.168.11.11:3000'))
        assert_true(url.endswith('/datasets/42/certificates'))

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

    def test_badge_fetch(self):
        self.post().json.return_value = {"success": "pending",
                                         "dataset_url": "http://example.com/foo"}

        self.get.side_effect = [
            mock.Mock(status_code=200,
                      json=mock.Mock(return_value={"success": "pending",
                                                   "dataset_url": "http://example.com/foo"})),
            mock.Mock(status_code=200,
                      json=mock.Mock(return_value={"success": True,
                                                   "dataset_url": "http://example.com/foo",
                                                   "dataset_id": 78})),
            mock.Mock(status_code=200,
                      content='''{"certificate": {"level": "FooLevel",
                                                  "created_at": "FooCreated",
                                                  "jurisdiction": "FooJurisdiction",
                                                  "dataset": {"title": "FooTitle"}}}'''),
        ]

        update_certificate(self.pkg_dict)

        assert_equal(3, self.get.call_count)

        package = model.Package.get('foo')
        assert_in('odi-certificate', package.extras)
        badge = json.loads(package.extras['odi-certificate'])
        assert_equal('FooLevel', badge['level'])
        assert_equal('FooCreated', badge['created_at'])
        assert_equal('FooJurisdiction', badge['jurisdiction'])
        assert_equal('FooTitle', badge['title'])
