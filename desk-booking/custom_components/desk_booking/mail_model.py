"""Pure, deliberately limited mail templates and reminder eligibility."""
from datetime import datetime, timedelta
from string import Formatter
import re

PLACEHOLDERS = ('mitarbeiter', 'ressource', 'beginn', 'ende', 'verfallzeit', 'dashboard_link')
DEFAULTS = {
    'sender': 'booking@example.invalid', 'dashboard_link': '',
    'start_enabled': False, 'start_minutes': 15,
    'start_subject': 'Deine Reservierung: {ressource}',
    'start_body': 'Hallo {mitarbeiter},\ndeine Reservierung für {ressource} beginnt am {beginn} und endet am {ende}.\n{dashboard_link}',
    'expiry_enabled': False, 'expiry_minutes': 5,
    'expiry_subject': 'Erinnerung: Bitte bei {ressource} einchecken',
    'expiry_body': 'Hallo {mitarbeiter},\nbitte checke bei {ressource} ein. Ohne Check-in verfällt deine Reservierung am {verfallzeit}.\n{dashboard_link}',
}


def email(value):
    if not isinstance(value, str) or len(value) > 254 or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', value):
        raise ValueError('Bitte eine gültige E-Mail-Adresse angeben.')
    return value.strip()


def template(value, subject=False):
    if not isinstance(value, str) or not value.strip() or len(value) > (255 if subject else 10000):
        raise ValueError('Betreff oder Inhalt fehlt oder ist zu lang.')
    if subject and any(ord(c) < 32 for c in value):
        raise ValueError('Der Betreff darf keine Zeilenumbrüche enthalten.')
    for _, field, spec, conversion in Formatter().parse(value):
        if field is not None and (field not in PLACEHOLDERS or spec or conversion):
            raise ValueError('Unbekannter Platzhalter. Siehe Platzhalter-Hilfe.')
    return value


def settings(values):
    result = {**DEFAULTS, **values}
    result['sender'] = email(result['sender'])
    link = result['dashboard_link']
    if link and (not isinstance(link, str) or not link.startswith(('https://', 'http://')) or any(ord(c)<32 for c in link)):
        raise ValueError('Dashboard-Link muss mit http:// oder https:// beginnen.')
    for kind in ('start', 'expiry'):
        minutes = result[kind+'_minutes']
        maximum = 29 if kind == 'expiry' else 1440
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or not 1 <= minutes <= maximum or int(minutes) != minutes:
            raise ValueError('Ungültiger Vorlauf: Start 1–1440, Verfall 1–29 Minuten.')
        result[kind+'_minutes'] = int(minutes)
        result[kind+'_enabled'] = bool(result[kind+'_enabled'])
        template(result[kind+'_subject'], True)
        template(result[kind+'_body'])
    return result


def due(event, kind, options, now, attended=False, checked=False, room=False):
    if not options.get(kind+'_enabled') or attended or checked or (room and kind == 'expiry'):
        return False
    start, end = (datetime.fromisoformat(event[k]) for k in ('start', 'end'))
    target = start if kind == 'start' else start + timedelta(minutes=30)
    return target-timedelta(minutes=options[kind+'_minutes']) <= now < min(target, end)


def values(event, person, resource, zone, link):
    start, end = (datetime.fromisoformat(event[k]) for k in ('start', 'end'))
    fmt = lambda d: d.astimezone(zone).strftime('%d.%m.%Y %H:%M')
    return dict(mitarbeiter=person, ressource=resource, beginn=fmt(start), ende=fmt(end),
                verfallzeit=fmt(start+timedelta(minutes=30)), dashboard_link=link)
