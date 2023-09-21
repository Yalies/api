import flask
from app import app
from .flask_cas.cas_urls import create_cas_login_url, create_cas_logout_url, create_cas_validate_url
from xmltodict import parse
try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen


def validate(ticket):
    """
    Will attempt to validate the ticket. If validation fails, then False
    is returned. If validation is successful, then True is returned
    and the validated username is saved in the session under the
    key `CAS_USERNAME_SESSION_KEY` while tha validated attributes dictionary
    is saved under the key 'CAS_ATTRIBUTES_SESSION_KEY'.
    Copied and modified from Flask-CAS.
    """

    cas_username_session_key = app.config['CAS_USERNAME_SESSION_KEY']
    cas_attributes_session_key = app.config['CAS_ATTRIBUTES_SESSION_KEY']

    cas_validate_url = create_cas_validate_url(
        app.config['CAS_SERVER'],
        app.config['CAS_VALIDATE_ROUTE'],
        # Modified the next line
        flask.url_for('login', origin=flask.session.get('CAS_AFTER_LOGIN_SESSION_URL'), _external=True),
        ticket)

    xml_from_dict = {}
    is_valid = False

    try:
        xmldump = urlopen(cas_validate_url).read().strip().decode('utf8', 'ignore')
        xml_from_dict = parse(xmldump)
        print(xml_from_dict)
        is_valid = True if 'cas:authenticationSuccess' in xml_from_dict['cas:serviceResponse'] else False
    except ValueError:
        app.logger.error('CAS returned unexpected result')

    if is_valid:
        xml_from_dict = xml_from_dict['cas:serviceResponse']['cas:authenticationSuccess']
        username = xml_from_dict['cas:user']
        flask.session[cas_username_session_key] = username

        if 'cas:attributes' in xml_from_dict:
            attributes = xml_from_dict['cas:attributes']

            if 'cas:memberOf' in attributes:
                if not isinstance(attributes['cas:memberOf'], list):
                    attributes['cas:memberOf'] = attributes['cas:memberOf'].lstrip('[').rstrip(']').split(',')
                    for group_number in range(0, len(attributes['cas:memberOf'])):
                        attributes['cas:memberOf'][group_number] = attributes['cas:memberOf'][group_number].lstrip(' ').rstrip(' ')
                else:
                    for index in range(0, len(attributes['cas:memberOf'])):
                        attributes['cas:memberOf'][index] = attributes['cas:memberOf'][index].lstrip('[').rstrip(']').split(',')
                        for group_number in range(0, len(attributes['cas:memberOf'][index])):
                            attributes['cas:memberOf'][index][group_number] = attributes['cas:memberOf'][index][group_number].lstrip(' ').rstrip(' ')

            flask.session[cas_attributes_session_key] = attributes

    return is_valid, xml_from_dict.get('cas:user')
