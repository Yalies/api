import re

class Source:
    PHONE_COUNTRY_CODE_RE = re.compile(r'^\+1? ')
    PHONE_DISALLOWED_CHARACTERS_RE = re.compile(r'[A-Za-z\(\) \-\.]')

    def clean_phone(phone):
        if not phone:
            return phone
        if type(phone) == int:
            phone = str(phone)
        phone = self.PHONE_COUNTRY_CODE_RE.sub('', phone)
        phone = self.DISALLOWED_CHARACTERS_RE.sub('', phone)
        return phone
