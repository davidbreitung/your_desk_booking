"""Graph client with guarded resource-calendar deletion and sanitized errors."""
import asyncio
import base64
import json
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import time
from urllib.parse import urlsplit, urlencode, quote
from uuid import UUID

import aiohttp

BASE = "https://graph.microsoft.com/v1.0/"
USERS = BASE + "users/delta?$select=id,displayName,mail,userPrincipalName,proxyAddresses,accountEnabled,userType,department,jobTitle"
GROUPS = BASE + "groups/delta?$select=id,displayName,description,securityEnabled,mail,members"
PLACE_TYPES = ("desk", "room", "workspace")


class GraphError(Exception):
    """Sanitized error with optional server-required cooldown."""
    def __init__(self, code, retry_after=0):
        self.code, self.retry_after = code, retry_after
        super().__init__(code)


def credentials(data):
    result = dict(data)
    try:
        for key in ("tenant_id", "client_id"):
            value = UUID(str(result.get(key, "")).strip())
            if not value.int:
                raise ValueError
            result[key] = str(value)
        if not isinstance(result.get("client_secret"), str) or not result["client_secret"].strip():
            raise ValueError
        interval = result.get("sync_interval", 15)
        if isinstance(interval, bool) or int(interval) != float(interval) or not 5 <= int(interval) <= 1440:
            raise ValueError
        result["sync_interval"] = int(interval)
    except (ValueError, TypeError, OverflowError) as err:
        raise GraphError("invalid_config") from err
    return result


def graph_url(url):
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "graph.microsoft.com"
            or not parts.path.startswith("/v1.0/") or parts.fragment):
        raise GraphError("invalid_response")
    return url


def retry_seconds(value, fallback):
    try:
        return max(0, int(value))
    except (ValueError, TypeError):
        try:
            return max(0, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return fallback


class GraphClient:
    def __init__(self, session, config):
        self.session, self.config = session, credentials(config)
        self.token, self.expires = None, 0
        self.blocked_until = 0

    async def _request(self, method, url, *, binary=False, **kwargs):
        if time.monotonic() < self.blocked_until:
            raise GraphError("rate_limited", self.blocked_until - time.monotonic())
        for attempt in range(4):
            try:
                async with self.session.request(method, url, allow_redirects=False,
                        timeout=aiohttp.ClientTimeout(total=45), **kwargs) as response:
                    status = response.status
                    if status == 429 or status in (502, 503, 504):
                        delay = retry_seconds(response.headers.get("Retry-After"), 2 ** attempt)
                        if delay > 30 or attempt == 3:
                            self.blocked_until = time.monotonic() + delay
                            raise GraphError("rate_limited" if status == 429 else "cannot_connect", delay)
                    elif status >= 400 or status < 200 or status >= 300:
                        if status == 400 and method == "GET":
                            error = await response.json()
                            if isinstance(error, dict) and error.get("error", {}).get("code") in ("syncStateNotFound", "resyncRequired", "resyncChangesApplyDifferences", "resyncChangesUploadDifferences"):
                                raise GraphError("delta_expired")
                        raise GraphError({401: "invalid_auth", 403: "insufficient_permissions", 404: "not_found", 412: "event_changed",
                                          410: "delta_expired"}.get(status, "invalid_auth" if method == "POST" and status == 400 else "graph_error"))
                    else:
                        if status == 204:
                            return {}
                        if binary:
                            data = bytearray()
                            async for chunk in response.content.iter_chunked(16384):
                                data.extend(chunk)
                                if len(data) > 262144:
                                    raise GraphError("invalid_response")
                            mime = "image/jpeg" if data.startswith(b"\xff\xd8\xff") else "image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else None
                            if not mime:
                                raise GraphError("invalid_response")
                            return bytes(data), mime
                        result = await response.json()
                        if not isinstance(result, dict):
                            raise GraphError("invalid_response")
                        return result
                await asyncio.sleep(delay)
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
                raise GraphError("cannot_connect") from err

    async def _token(self):
        if self.token and time.monotonic() < self.expires:
            return self.token
        data = await self._request("POST",
            f"https://login.microsoftonline.com/{self.config['tenant_id']}/oauth2/v2.0/token",
            data={"client_id": self.config["client_id"], "client_secret": self.config["client_secret"],
                  "scope": "https://graph.microsoft.com/.default", "grant_type": "client_credentials"})
        if not isinstance(data.get("access_token"), str):
            raise GraphError("invalid_auth")
        self.token = data["access_token"]
        self.expires = time.monotonic() + max(0, int(data.get("expires_in", 3600)) - 120)
        return self.token

    async def get(self, url):
        url = graph_url(url)
        for attempt in range(2):
            token = await self._token()
            try:
                return await self._request("GET", url, headers={"Authorization": f"Bearer {token}"})
            except GraphError as err:
                if err.code != "invalid_auth" or attempt:
                    raise
                self.token = None

    async def test_connection(self):
        # Test both actual delta resources, without advancing/persisting a cursor.
        await self.get(USERS)
        await self.get(GROUPS)
        for kind in PLACE_TYPES:
            await self.get(BASE + "places/microsoft.graph." + kind)

    async def profile_photo(self, object_id):
        url = graph_url(BASE + "users/" + quote(object_id, safe="") + "/photos/96x96/$value")
        for attempt in range(2):
            token = await self._token()
            try:
                return await self._request("GET",url,binary=True,headers={"Authorization":f"Bearer {token}"})
            except GraphError as err:
                if err.code != "invalid_auth" or attempt:
                    raise
                self.token = None

    async def has_calendar_write(self):
        token = await self._token()
        try:
            part = token.split('.')[1]
            claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
            return 'Calendars.ReadWrite' in claims.get('roles', [])
        except (ValueError, IndexError, TypeError):
            return False

    async def resource_event(self, mailbox, event_id):
        return await self.get(BASE + 'users/' + quote(mailbox, safe='') + '/events/' + quote(event_id, safe='') +
            '?$select=id,start,end,organizer,isCancelled,showAs,responseStatus,type,changeKey')

    async def send_mail(self, sender, recipient, subject, body):
        """Never replay a potentially accepted POST (including 5xx/timeouts)."""
        token = await self._token()
        url = graph_url(BASE + 'users/' + quote(sender, safe='') + '/sendMail')
        payload = {'message': {'subject': subject, 'body': {'contentType': 'Text', 'content': body},
                   'toRecipients': [{'emailAddress': {'address': recipient}}]}, 'saveToSentItems': True}
        try:
            async with self.session.request('POST', url, json=payload,
                    headers={'Authorization': f'Bearer {token}'}, allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=45)) as response:
                if response.status == 202:
                    return 'accepted'
                if response.status == 429:
                    raise GraphError('rate_limited', retry_seconds(response.headers.get('Retry-After'), 60))
                if response.status in (400, 401, 403, 404):
                    raise GraphError({400:'invalid_mail',401:'invalid_auth',403:'insufficient_permissions',404:'mailbox_not_found'}[response.status])
                raise GraphError('mail_delivery_unknown')
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise GraphError('mail_delivery_unknown') from err

    async def delete_resource_event(self, mailbox, event):
        # Delete only a concrete occurrence/copy in the desk mailbox. Never
        # dereference organizer mailboxes or seriesMasterId, never delete Places.
        if event.get('type') not in ('singleInstance','occurrence','exception') or not event.get('@odata.etag'):
            raise GraphError('unsafe_event')
        url = graph_url(BASE + 'users/' + quote(mailbox, safe='') + '/events/' + quote(event['id'], safe=''))
        for attempt in range(2):
            token = await self._token()
            try:
                await self._request('DELETE', url, headers={'Authorization': f'Bearer {token}', 'If-Match':event['@odata.etag']})
                return
            except GraphError as err:
                if err.code == 'not_found':
                    return
                if err.code != 'invalid_auth' or attempt:
                    raise
                self.token = None

    async def calendar_view(self, mailbox, start, end):
        query = urlencode({"startDateTime": start.isoformat(), "endDateTime": end.isoformat(),
            "$select": "id,start,end,organizer,isCancelled,showAs,responseStatus", "$top": 1000})
        url = BASE + "users/" + quote(mailbox, safe="") + "/calendarView?" + query
        events, visited = [], set()
        while url:
            if url in visited:
                raise GraphError("invalid_response")
            visited.add(url)
            page = await self.get(url)
            if not isinstance(page.get("value"), list):
                raise GraphError("invalid_response")
            events.extend(page["value"])
            url = page.get("@odata.nextLink")
            if url:
                graph_url(url)
        return events

    async def places(self):
        """Places has no delta API: commit only complete paginated inventories."""
        result = {}
        for kind in PLACE_TYPES:
            url = BASE + "places/microsoft.graph." + kind
            visited = set()
            while url:
                if url in visited:
                    raise GraphError("invalid_response")
                visited.add(url)
                page = await self.get(url)
                if not isinstance(page.get("value"), list):
                    raise GraphError("invalid_response")
                for item in page["value"]:
                    if not isinstance(item, dict):
                        raise GraphError("invalid_response")
                    # placeId survives mailbox changes; older responses may only have id.
                    key = item.get("placeId") or item.get("id")
                    if not isinstance(key, str) or not key or key in result:
                        raise GraphError("invalid_response")
                    result[key] = {**item, "kind": kind}
                url = page.get("@odata.nextLink")
                if url:
                    graph_url(url)
        return result

    async def delta(self, initial, cursor, previous, groups=False):
        result = deepcopy(previous) if cursor else {}
        url = cursor or initial
        visited = set()
        while url:
            if url in visited:
                raise GraphError("invalid_response")
            visited.add(url)
            page = await self.get(url)
            if not isinstance(page.get("value"), list):
                raise GraphError("invalid_response")
            for item in page["value"]:
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    raise GraphError("invalid_response")
                key = item["id"]
                if "@removed" in item:
                    result.pop(key, None)
                    continue
                record = result.setdefault(key, {"id": key})
                record.update({k: v for k, v in item.items() if not k.startswith("@") and k not in ("members@delta", "members@odata.nextLink")})
                if groups:
                    if "members@odata.nextLink" in item:
                        raise GraphError("invalid_response")
                    members = set(record.get("members", []))
                    for member in item.get("members@delta", []):
                        if not isinstance(member, dict) or not isinstance(member.get("id"), str):
                            raise GraphError("invalid_response")
                        if "@removed" in member:
                            members.discard(member["id"])
                        else:
                            members.add(member["id"])
                    record["members"] = sorted(members)
            url = page.get("@odata.nextLink")
            if not url:
                cursor = page.get("@odata.deltaLink")
                if not cursor:
                    raise GraphError("invalid_response")
                return result, graph_url(cursor)

    async def snapshot(self, cache):
        if cache.get("schema") != 3:
            cache = {}  # Old delta cursors cannot add newly selected fields.
        for attempt in range(2):
            try:
                users, user_cursor = await self.delta(USERS, cache.get("user_cursor"), cache.get("users", {}))
                groups, group_cursor = await self.delta(GROUPS, cache.get("group_cursor"), cache.get("groups", {}), True)
                places = await self.places()
                return {"users": users, "groups": groups, "user_cursor": user_cursor, "group_cursor": group_cursor,
                        "places": places, "schema": 3,
                        "tenant_id": self.config["tenant_id"], "client_id": self.config["client_id"]}
            except GraphError as err:
                if err.code != "delta_expired" or attempt:
                    raise
                cache = {}
