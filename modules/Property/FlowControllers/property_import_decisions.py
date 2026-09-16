"""The same pre-write decision rules for property checks and import execution."""
from copy import deepcopy

from .MainAddProperties import MainAddPropertiesFlow
from ....languages.translation_keys import TranslationKeys as K


def _normalize(text):
    return ' '.join(str(text or '').split()).casefold()


def _address_matches(display_address, street, full_street):
    """Compare the cadastral address with the address the backend shows.

    The backend composes one line from the fields the import sent: street, house number,
    settlement, municipality and county. The import knows only the cadastral address, so
    it is compared with the first one or two parts of that line. Anything else counts as
    an address that was changed in the backend and still needs a decision.
    """

    parts = [part for part in (segment.strip() for segment in str(display_address or '').split(',')) if part]
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
    elif not _address_matches(item.get('displayAddress'), street, full_street) and not newer:
        result.update(action='needs_decision', reason=K.PROPERTY_ADD_BACKEND_DIFFERS)
    return result
