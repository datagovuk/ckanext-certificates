import requests
import re
import json
import os
import ckan.plugins.toolkit as toolkit
from urlparse import urljoin
from pylons import config
from celery.task import task

CERTIFICATE_SERVER = config.get('ckanext.certificates.server', None)
CERTIFICATE_USER = config.get('ckanext.certificates.user', None)
CERTIFICATE_PASS = config.get('ckanext.certificates.pass', None)

def load_config():
    import paste.deploy
    import ckan

    ckan_ini_filepath = os.path.abspath(config.__file__)
    conf = paste.deploy.appconfig('config:' + ckan_ini_filepath)
    ckan.config.environment.load_environment(conf.global_conf,
                                             conf.local_conf)

def _get_request_data(pkg_name):
    """
    Returns a JSON string suitable for posting to the certificates API
    """
    site_url = config.get('ckan.site_url')
    package_url = toolkit.url_for(controller='package',
                                  action='read',
                                  id=pkg_name)
    url = urljoin(site_url, package_url)
    data = {
        'jurisdiction': 'GB',
        'dataset': {
            'documentationUrl': url
        }
    }
    return json.dumps(data)

def _post_request(relative_url, package_name):
    """
    Post a request to the certificate API
    """
    if not all([CERTIFICATE_SERVER, CERTIFICATE_USER, CERTIFICATE_PASS]):
        return

    url = urljoin(CERTIFICATE_SERVER, relative_url)
    auth = requests.auth.HTTPBasicAuth(CERTIFICATE_USER, CERTIFICATE_PASS)
    data = _get_request_data(package_name)
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=data, auth=auth, headers=headers)
    print "XXX", response.json()

@task(name='certificate.create')
def create_certificate(pkg_dict):
    """
    Send request to create new certificate when a package is created
    """
    load_config()
    _post_request('/datasets', pkg_dict['name'])

@task(name='certificate.update')
def update_certificate(pkg_dict):
    """
    Send request to update the certificate when a package is modified
    """
    load_config()

    extras = pkg_dict.get('extras', [])
    extras = dict([(extra['key'], extra['value']) for extra in extras])

    certificate = json.loads(extras.get('odi-certificate', '""'))
    if not certificate:
        return

    dataset_id = re.findall("\d+", certificate['certificate_url'])[0]
    relative_url = '/datasets/%s/certificates' % dataset_id
    _post_request(relative_url, pkg_dict['name'])
