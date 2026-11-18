"""Admin-only options dialogs for visibility, removal and mail configuration."""
import voluptuous as vol
from homeassistant.helpers import selector
from datetime import timedelta, datetime, timezone
from zoneinfo import ZoneInfo
from .records import records, KINDS
from .mail_model import DEFAULTS, settings, email, values
from .graph import GraphError


PLACEHOLDER_HELP = 'In Betreff und Inhalt verfügbar:\n\n- `{mitarbeiter}` – Name des zugeordneten Mitarbeiters, z. B. Max Mustermann\n- `{ressource}` – Name des Schreibtischs/Raums\n- `{beginn}` – Beginn, z. B. 16.11.2026 09:00\n- `{ende}` – Ende in derselben Form\n- `{verfallzeit}` – Beginn + 30 Minuten (nur bei Schreibtischen relevant)\n- `{dashboard_link}` – zentral eingetragener Dashboard-Link, sonst leer\n\nZeiten verwenden die Home-Assistant-Zeitzone. Geschweifte Klammern im Klartext mit `{{` und `}}` schreiben. Keine weiteren Variablen, Formatierungen oder Programmcode. Die Vorschau ersetzt alle Platzhalter mit Beispieldaten.'

class ManagementOptions:
    async def async_step_manuals(self, user_input=None):
        if user_input is not None:
            return await self.async_step_init()
        links = '<p><a href="/desk_booking_static/docs/benutzer.html" target="_blank">Benutzerhandbuch öffnen</a></p><p><a href="/desk_booking_static/docs/administrator.html" target="_blank">Administratorhandbuch öffnen</a></p><p>Markdown-Quellen: <a href="/desk_booking_static/docs/benutzer.md" target="_blank">Benutzer</a> · <a href="/desk_booking_static/docs/administrator.md" target="_blank">Administrator</a></p>'
        # HTML must be an ICU argument, not literal translation markup (INVALID_TAG).
        return self.async_show_form(step_id='manuals', description_placeholders={'links':links}, data_schema=vol.Schema({}))

    async def async_step_floorplan(self, user_input=None):
        from .floorplan_settings import DEFAULT_BOOKING_URL, booking_url, hash_password
        current = self.config_entry.options.get('floorplan', {})
        errors = {}
        if user_input is not None:
            try:
                updated = {**current, 'booking_url': booking_url(user_input['booking_url'])}
                if user_input.get('clear_password'):
                    updated.pop('password_hash', None)
                elif user_input.get('password'):
                    updated['password_hash'] = await self.hass.async_add_executor_job(hash_password, user_input['password'])
            except (ValueError, TypeError):
                errors['base'] = 'invalid_floorplan_settings'
            else:
                return self.async_create_entry(title='', data={**self.config_entry.options, 'floorplan': updated})
        return self.async_show_form(step_id='floorplan', errors=errors,
            description_placeholders={'password_status':'aktiv' if current.get('password_hash') else 'nicht aktiv'},
            data_schema=vol.Schema({
                vol.Required('booking_url', default=current.get('booking_url', DEFAULT_BOOKING_URL)):selector.TextSelector(),
                vol.Optional('password'):selector.TextSelector(selector.TextSelectorConfig(type='password')),
                vol.Required('clear_password', default=False):selector.BooleanSelector()}))

    async def async_step_objects(self, user_input=None):
        return self.async_show_menu(step_id='objects', menu_options=['visible_objects','hidden_objects','delete_object'])

    async def _visibility(self, hidden, user_input):
        candidates = [r for r in records(self.config_entry).values() if bool(r.data.get('hidden')) == hidden]
        if user_input is not None:
            if user_input.get('record') not in {r.subentry_id for r in candidates}:
                return self.async_abort(reason='no_synced_records')
            from .management import set_hidden
            set_hidden(self.hass, self.config_entry, user_input['record'], not hidden)
            return self.async_create_entry(title='', data=dict(self.config_entry.options))
        if not candidates:
            return self.async_abort(reason='no_synced_records')
        return self.async_show_form(step_id='hidden_objects' if hidden else 'visible_objects', data_schema=self._record_schema(candidates))

    def _record_schema(self, candidates):
        return vol.Schema({vol.Required('record'): selector.SelectSelector(selector.SelectSelectorConfig(
            options=[{'value':r.subentry_id,'label':f'{KINDS[r.subentry_type]} · {r.title} ({r.subentry_id[-6:]})'} for r in candidates], mode='dropdown'))})

    async def async_step_visible_objects(self, user_input=None):
        return await self._visibility(False, user_input)

    async def async_step_hidden_objects(self, user_input=None):
        return await self._visibility(True, user_input)

    async def async_step_delete_object(self, user_input=None):
        candidates = [r for r in records(self.config_entry).values() if not r.data.get('active',True)]
        if user_input is not None and user_input.get('record') in {r.subentry_id for r in candidates}:
            self._delete_id = user_input['record']
            return await self.async_step_delete_confirm()
        if not candidates:
            return self.async_abort(reason='no_synced_records')
        return self.async_show_form(step_id='delete_object', data_schema=self._record_schema(candidates))

    async def async_step_delete_confirm(self, user_input=None):
        record = records(self.config_entry).get(self._delete_id)
        if not record:
            return self.async_abort(reason='no_synced_records')
        error = {}
        if user_input is not None:
            if user_input.get('confirm'):
                try:
                    from .management import delete_inactive
                    await delete_inactive(self.hass, self.config_entry, record.subentry_id)
                    return self.async_create_entry(title='',data=dict(self.config_entry.options))
                except (ValueError,OSError):
                    error['base'] = 'delete_failed'
            else:
                return await self.async_step_objects()
        return self.async_show_form(step_id='delete_confirm', description_placeholders={'name':record.title}, errors=error,
            data_schema=vol.Schema({vol.Required('confirm',default=False):selector.BooleanSelector()}))

    async def async_step_mail(self, user_input=None):
        return self.async_show_menu(step_id='mail',menu_options=['mail_settings','mail_permissions','mail_placeholders','mail_preview'])

    async def async_step_mail_settings(self, user_input=None):
        current = {**DEFAULTS, **self.config_entry.options.get('mail', {})}
        errors = {}
        if user_input is not None:
            try:
                configured = settings(user_input)
            except ValueError:
                errors['base'] = 'invalid_mail_settings'
                current.update(user_input)
            else:
                return self.async_create_entry(title='',data={**self.config_entry.options,'mail':configured})
        fields = {}
        for key in DEFAULTS:
            if key.endswith('_enabled'):
                field = selector.BooleanSelector()
            elif key.endswith('_minutes'):
                field = selector.NumberSelector(selector.NumberSelectorConfig(min=1,max=29 if key.startswith('expiry') else 1440,mode='box',step=1))
            else:
                field = selector.TextSelector(selector.TextSelectorConfig(multiline=key.endswith('_body')))
            marker = vol.Optional if key == 'dashboard_link' else vol.Required
            fields[marker(key,default=current[key])] = field
        return self.async_show_form(step_id='mail_settings',errors=errors,data_schema=vol.Schema(fields))

    async def async_step_mail_permissions(self, user_input=None):
        if user_input is not None:
            return await self.async_step_mail()
        return self.async_show_form(step_id='mail_permissions',data_schema=vol.Schema({}))

    async def async_step_mail_placeholders(self, user_input=None):
        if user_input is not None:
            return await self.async_step_mail()
        return self.async_show_form(step_id='mail_placeholders',description_placeholders={'help':PLACEHOLDER_HELP},data_schema=vol.Schema({}))

    async def async_step_mail_preview(self, user_input=None):
        options = settings(self.config_entry.options.get('mail', {}))
        if user_input is not None:
            self._mail_kind = user_input['kind']
            return await self.async_step_mail_test()
        return self.async_show_form(step_id='mail_preview',data_schema=vol.Schema({vol.Required('kind',default='start'):
            selector.SelectSelector(selector.SelectSelectorConfig(options=[{'value':'start','label':'Vor Reservierungsbeginn'},{'value':'expiry','label':'Vor Verfall'}]))}))

    async def async_step_mail_test(self, user_input=None):
        options = settings(self.config_entry.options.get('mail', {}))
        now = datetime.now(timezone.utc)+timedelta(minutes=15)
        variables = values({'start':now.isoformat(),'end':(now+timedelta(hours=2)).isoformat()},'Max Mustermann','Beispiel-Schreibtisch',ZoneInfo(self.hass.config.time_zone),options['dashboard_link'])
        subject = options[self._mail_kind+'_subject'].format_map(variables)
        body = options[self._mail_kind+'_body'].format_map(variables)
        result = ''
        if user_input is not None:
            if not user_input.get('send'):
                return await self.async_step_mail()
            try:
                await self.config_entry.runtime_data.mail.send(email(user_input['recipient']),subject,body)
                await self.config_entry.runtime_data.mail.save()
                result = 'Microsoft hat die Testmail angenommen (202). Dies bestätigt noch keine Zustellung.'
            except (ValueError,OSError,GraphError) as err:
                result = 'Versand nicht bestätigt: '+ (err.code if isinstance(err,GraphError) else 'Adresse oder Speicher prüfen.')
            return self.async_show_form(step_id='mail_result',description_placeholders={'result':result},data_schema=vol.Schema({}))
        return self.async_show_form(step_id='mail_test',description_placeholders={'sender':options['sender'],'subject':subject,'body':body},data_schema=vol.Schema({
            vol.Required('recipient',default=options['sender']):selector.TextSelector(),vol.Required('send',default=False):selector.BooleanSelector()}))

    async def async_step_mail_result(self,user_input=None):
        return await self.async_step_mail()
