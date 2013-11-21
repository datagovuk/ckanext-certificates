import re

import requests
from lxml import etree
from cStringIO import StringIO

NS_MAP = {'ns': 'http://www.w3.org/2005/Atom'}
Q_NAME = re.compile("{(?P<ns>.*)}(?P<element>.*)")

def test():
    data = """
<entry>
<title>OS OpenData 1:250 000 Scale Colour Raster</title>
<link href="http://certificates.theodi.org/datasets/374"/>
<content>Basic Level Certificate</content>
<updated>2013-10-22T08:16:32+00:00</updated>
<id>http://certificates.theodi.org/datasets/374</id>
</entry>
    """
    e = StringIO(data)
    node = etree.parse(e)
    print entry_to_dict(node)


def entry_to_dict(entry):
    d = {}
    for node in entry.xpath('*'):

        # Strip out the namespace from the tag name
        match = Q_NAME.search(node.tag)
        name = match.groupdict().get("element") if match else node.tag

        if name == 'link':
            rel = node.get('rel')
            href = node.get('href')

            if rel in ['about', 'alternate']:
                d[rel] = href
            elif rel == 'http://schema.theodi.org/certificate#badge':
                if node.get('type') == 'text/html':
                    d['badge_html'] = href
                elif node.get('type') == 'application/javascript':
                    d['badge_json'] = href
            else:
                d[name] = href
        else:
            d[name] = node.text
    return d

def generate_entries(log, url="https://certificates.theodi.org/datasets.feed"):
    for entry in fetch_entries(log):
        yield entry_to_dict(entry)


def fetch_entries(log, url="https://certificates.theodi.org/datasets.feed"):
    done = False

    while not done:
        req = requests.get(url)
        data = StringIO(req.content)

        try:
            doc = etree.parse(data)
        except Exception, e:
            log.exception(e)
            log.debug(data)
            return

        for entry in doc.xpath("/ns:feed/ns:entry", namespaces=NS_MAP):
            yield entry

        self_url = doc.xpath("/ns:feed/ns:link[@rel='self']", namespaces=NS_MAP)[0].get('href')
        last_url = doc.xpath("/ns:feed/ns:link[@rel='last']", namespaces=NS_MAP)[0].get('href')

        log.debug("SELF URL: {0}".format(self_url))
        log.debug("LAST URL: {0}".format(last_url))

        if self_url == last_url:
            log.debug("Feed has run out of pages, all done.")
            done = True
        else:
            log.debug("Feed has another page of data, fetching...")
            url = doc.xpath("/ns:feed/ns:link[@rel='next']", namespaces=NS_MAP)[0].get('href')

        del doc
        data.close()
