from pathlib import Path
import json
from copy import deepcopy

root = Path(__file__).parent / 'custom_components/desk_booking'
for name in ('strings.json', 'translations/en.json', 'translations/de.json'):
    p = root / name
    d = json.loads(p.read_text(encoding='utf-8'))
    de = name.endswith('de.json')
    opt = d['options']
    opt['step']['init']['menu_options'].update({
        'bookings': 'Buchungen' if de else 'Bookings',
        'desk': 'Schreibtisch bearbeiten' if de else 'Edit desk',
        'employee': 'Mitarbeiter bearbeiten' if de else 'Edit employee'})
    opt['step']['bookings'] = {'title': 'Buchungen' if de else 'Bookings',
        'description': 'Kalenderberechtigung: Calendars.ReadBasic.All (Anwendung), mit Administratorzustimmung. Suchzeitraum: 365 Tage.' if de else 'Requires Calendars.ReadBasic.All application permission with admin consent. Search horizon: 365 days.',
        'data': {'booking_interval': 'Aktualisierung alle (Minuten)' if de else 'Update interval (minutes)'}}
    for kind in ('desk', 'employee'):
        opt['step'][kind] = {'title': opt['step']['init']['menu_options'][kind], 'data': {'record': 'Auswahl' if de else 'Select'}}
        opt['step'][kind+'_edit'] = deepcopy(d['config_subentries'][kind]['step']['reconfigure'])
        opt.setdefault('error', {}).update(d['config_subentries'][kind].get('error', {}))
        d['config_subentries'][kind]['step'].pop('user', None)
        d['config_subentries'][kind]['initiate_flow'].pop('user', None)
    opt['error']['invalid_booking_interval'] = 'Bitte 1 bis 1440 ganze Minuten wählen.' if de else 'Choose 1 to 1440 whole minutes.'
    opt.setdefault('abort', {})['no_synced_records'] = 'Noch keine passenden Objekte synchronisiert.' if de else 'No matching records synchronized yet.'
    d['config_subentries']['group'] = {'entry_type': 'Group'}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
p = root / 'manifest.json'
d = json.loads(p.read_text()); d['version'] = '0.8.0'
p.write_text(json.dumps(d, indent=2)+'\n')
