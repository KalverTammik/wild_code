"""The same pre-write decision rules for property checks and import execution."""
from copy import deepcopy

from .MainAddProperties import MainAddPropertiesFlow
from ....languages.translation_keys import TranslationKeys as K


# Address conflicts a reviewer may resolve by writing the import data over the backend record.
ADDRESS_REASONS = (K.PROPERTY_ADD_BACKEND_DIFFERS, K.PROPERTY_IMPORT_ADDRESS_MISSING)


def _normalize(text):
    return ' '.join(str(text or '').split()).casefold()


def _first_location(address):
    """The part the backend line starts with when there is no street: settlement, else municipality, else county."""

    for key in ('city', 'state', 'county'):
        value = str(address.get(key) or '').strip()
        if value and value.upper() != 'NULL':
            return value
    return ''


def _address_matches(display_address, street, full_street, location=''):
    """Compare the cadastral address with the address the backend shows.

    The backend composes one line from the fields the import sent: street, house number,
    settlement, municipality and county. The import knows only the cadastral address, so
    it is compared with the first one or two parts of that line. Anything else counts as
    an address that was changed in the backend and still needs a decision.

    A cadastral unit without an address is sent with an empty street, so the backend line
    then starts with the first location part. That is agreement, not a conflict.
    """

    parts = [part for part in (segment.strip() for segment in str(display_address or '').split(',')) if part]
    if not _normalize(street):
        return not parts or _normalize(parts[0]) == _normalize(location)
    shown = {
        _normalize(display_address),
        _normalize(parts[0] if parts else ''),
        _normalize(' '.join(parts[:2])),
    }
    return _normalize(street) in shown or _normalize(full_street) in shown


def classify_property_import(data, import_date, main_date, info):
    """Return an action and a snapshot; this function never writes anything."""
    tunnus = str(data['cadastralUnit']['number'])
    address = data['address']
    street = str(address.get('street') or '').strip()
    full_street = ' '.join(part for part in (street, str(address.get('houseNumber') or '').strip()) if part)
    location = _first_location(address)
    item = info.get('property') or {}
    newer = MainAddPropertiesFlow._is_import_newer(import_date, info.get('LastUpdated'), main_date)
    result = {
        'tunnus': tunnus, 'action': 'update', 'reason': None, 'import_newer': newer,
        'import_address': full_street, 'backend_address': item.get('displayAddress') or '',
        'import_date': import_date or '', 'backend_date': info.get('LastUpdated') or '',
        'main_date': main_date or '', 'backend_info': deepcopy(info),
    }
    if info.get('exists') is None:
        result.update(action='error', reason=K.PROPERTY_ADD_LOOKUP_FAILED)
    elif info.get('archived_only'):
        result.update(action='needs_decision', reason=K.ATTENTION_CAUSE_ARCHIVED_ONLY)
    elif int(info.get('active_count') or 0) > 1:
        result.update(action='needs_decision', reason=K.PROPERTY_ADD_AMBIGUOUS)
    elif info['exists'] is False:
        result['action'] = 'create'
    elif not item.get('id') or str(item.get('cadastralUnitNumber')) != tunnus:
        result.update(action='error', reason=K.PROPERTY_ADD_LOOKUP_FAILED)
    elif not _address_matches(item.get('displayAddress'), street, full_street, location) and not newer:
        # Without a cadastral address, applying the import would erase the backend street.
        reason = K.PROPERTY_ADD_BACKEND_DIFFERS if street else K.PROPERTY_IMPORT_ADDRESS_MISSING
        result.update(action='needs_decision', reason=reason)
    return result
