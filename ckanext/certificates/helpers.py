import json

def has_certificate(pkg):
    """
    Can be used in the template to determine if the package has a
    certificate. Returns a boolean.
    """
    return 'odi-certificate' in pkg.extras and get_certificate_data(pkg) is not None

def get_certificate_data(pkg):
    """
    Returns the dictionary containing information about the certificate for the
    given package
    """
    try:
        return json.loads(pkg.extras.get('odi-certificate'))
    except ValueError:
        return None
