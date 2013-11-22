

def has_certificate(pkg):
    return 'odi-certificate' in pkg.extras

def get_certificate_data(pkg):
    import json
    return json.loads(pkg.extras.get('odi-certificate'))
