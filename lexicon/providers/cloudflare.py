from __future__ import absolute_import
import json
import logging

import requests
from lexicon.providers.base import Provider as BaseProvider


LOGGER = logging.getLogger(__name__)

NAMESERVER_DOMAINS = ['cloudflare.com']


def ProviderParser(subparser):
    subparser.add_argument(
        "--auth-username", help="specify email address for authentication")
    subparser.add_argument(
        "--auth-token", help="specify token for authentication")


class Provider(BaseProvider):

    def __init__(self, config):
        super(Provider, self).__init__(config)
        self.domain_id = None
        self.api_endpoint = 'https://api.cloudflare.com/client/v4'

    def authenticate(self):

        payload = self._get('/zones', {
            'name': self.domain,
            'status': 'active'
        })

        if not payload['result']:
            raise Exception('No domain found')
        if len(payload['result']) > 1:
            raise Exception('Too many domains found. This should not happen')

        self.domain_id = payload['result'][0]['id']

    # Create record. If record already exists with the same content, do nothing'

    def create_record(self, type, name, content):
        data = {'type': type, 'name': self._full_name(
            name), 'content': content}
        if self._get_lexicon_option('ttl'):
            data['ttl'] = self._get_lexicon_option('ttl')

        payload = {'success': True}
        try:
            payload = self._post(
                '/zones/{0}/dns_records'.format(self.domain_id), data)
        except requests.exceptions.HTTPError as err:
            already_exists = next((True for error in err.response.json()[
                                  'errors'] if error['code'] == 81057), False)
            if not already_exists:
                raise

        LOGGER.debug('create_record: %s', payload['success'])
        return payload['success']

    # List all records. Return an empty list if no records found
    # type, name and content are used to filter records.
    # If possible filter during the query, otherwise filter after response is received.
    def list_records(self, type=None, name=None, content=None):
        filter = {'per_page': 100}
        if type:
            filter['type'] = type
        if name:
            filter['name'] = self._full_name(name)
        if content:
            filter['content'] = content

        payload = self._get(
            '/zones/{0}/dns_records'.format(self.domain_id), filter)

        records = []
        for record in payload['result']:
            processed_record = {
                'type': record['type'],
                'name': record['name'],
                'ttl': record['ttl'],
                'content': record['content'],
                'id': record['id']
            }
            records.append(processed_record)

        LOGGER.debug('list_records: %s', records)
        return records

    # Create or update a record.
    def update_record(self, identifier, type=None, name=None, content=None):

        data = {}
        if type:
            data['type'] = type
        if name:
            data['name'] = self._full_name(name)
        if content:
            data['content'] = content
        if self._get_lexicon_option('ttl'):
            data['ttl'] = self._get_lexicon_option('ttl')

        payload = self._put(
            '/zones/{0}/dns_records/{1}'.format(self.domain_id, identifier), data)

        LOGGER.debug('update_record: %s', payload['success'])
        return payload['success']

    # Delete an existing record.
    # If record does not exist, do nothing.
    def delete_record(self, identifier=None, type=None, name=None, content=None):
        delete_record_id = []
        if not identifier:
            records = self.list_records(type, name, content)
            delete_record_id = [record['id'] for record in records]
        else:
            delete_record_id.append(identifier)

        LOGGER.debug('delete_records: %s', delete_record_id)

        for record_id in delete_record_id:
            self._delete(
                '/zones/{0}/dns_records/{1}'.format(self.domain_id, record_id))

        LOGGER.debug('delete_record: %s', True)
        return True

    # Helpers
    def _request(self, action='GET',  url='/', data=None, query_params=None):
        if data is None:
            data = {}
        if query_params is None:
            query_params = {}
        r = requests.request(action, self.api_endpoint + url, params=query_params,
                             data=json.dumps(data),
                             headers={
                                 'X-Auth-Email': self._get_provider_option('auth_username'),
                                 'X-Auth-Key': self._get_provider_option('auth_token'),
                                 'Content-Type': 'application/json'
                             })
        # if the request fails for any reason, throw an error.
        r.raise_for_status()
        return r.json()
