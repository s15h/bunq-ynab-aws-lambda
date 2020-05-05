import json
import string

from logger import configure_logger
from parameter_store import ParameterStore

LOGGER = configure_logger(__name__)


class Configuration:
    """Class used for loading configuration from different sources.
    """

    def __init__(self, location):
        self.location = location
        l = location.split(':')
        try:
            self.type = l[0]
            self.path = l[1]
            LOGGER.debug('Using {0} with path {1}'.format(self.type, self.path))
        except:
            LOGGER.debug('Failed to parse location. Expecting "type:path", e.g. "file:./config.json"')
            raise
        self.value = json.loads(self.load())

    def load(self):
        LOGGER.info('Loading configuration from {0}'.format(self.location))
        if self.type == 'ssm':
            config = self.load_ssm()
        elif self.type == 'file':
            config = self.load_file()
        else:
            LOGGER.debug('Load FAIL')
            raise Exception('Config type should be file or ssm, got {0}'.format(self.type))

        if self.validate(config):
            return config
        else:
            raise Exception('Config validation failed.')

    def load_ssm(self):
        parameter_store = ParameterStore()
        resp = parameter_store.fetch_parameter(self.path)
        return resp

    def load_file(self):
        with open(self.path, 'r') as f:
            data = f.read()
            return data

    def save(self, config):
        json_string = json.dumps(config, sort_keys=True, indent=2)
        LOGGER.info('Saving new config: {0}'.format(json_string))
        if self.type == 'ssm':
            self.save_ssm(json_string)
        elif self.type == 'file':
            self.save_file(json_string)

    def save_ssm(self, json_string):
        parameter_store = ParameterStore()
        resp = parameter_store.put_parameter(self.path, json_string)
        LOGGER.debug(resp)
        return resp

    def save_file(self, json_string):
        with open(self.path, 'w') as f:
            f.write(json_string)

    def validate(self, config):
        c = json.loads(config)
        l = [['bunq', 'api_token'], ['ynab', 'accesstoken']]
        for i in l:
            token = c.get(i[0]).get(i[1])
            assert token, '{0} "{1}" is missing!'.format(i[0], i[1])
            assert len(token) == 64, '{0} "{1}" is incorrect, expected 64 chars!'.format(i[0], i[1])
            assert all(
                chars in string.hexdigits for chars in token), '{0} "{1}" is incorrect, should be hexadecimal!'.format(
                i[0], i[1])

        LOGGER.info('Config valid!')
        # assert c.get('bunq').get('api_token'), 'Bunq "api_token" is incorrect, missing!'
        # assert len(c.get('bunq').get('api_token')) == 64, 'Bunq "api_token" is incorrect, expected 64 chars!'
        # assert all(c in string.hexdigits for c in c.get('bunq').get('api_token')), 'Bunq "api_token" is incorrect, should be hex!'

        # assert c.get('ynab').get('accesstoken'), 'YNAB "accesstoken" is missing!'
        # assert len(c.get('ynab').get('accesstoken')) == 64, 'Bunq "api_token" is incorrect, expected 64 chars.'
        # assert all(c in string.hexdigits for c in c.get('ynab').get('accesstoken'))
        return True
