'''
To test actual endpoints create a valid config file and point to it.

Example:

CIRCONUS_CONFIG=/tmp/test_circonus_config.ini tox


'''
import os

from tempfile import NamedTemporaryFile
from unittest import TestCase

from circonusapi import circonusapi, config


class ConfigTestCase(TestCase):

    def test_no_config_file(self):
        cfg = config.load_config(configfile='nope', nocache=True)
        self.assertEqual(cfg.sections(), [])

    def test_single_config_file(self):
        with NamedTemporaryFile(mode='w+') as tmp_file:
            tmp_file.file.write(
                '''
[general]
default_account=sampleaccount
appname=sample appname

[tokens]
sampleaccount=AAAAAAAA-1234-5678-9999-BBBBBBBB
'''
            )
            tmp_file.file.flush()
            tmp_file.file.seek(0)
            cfg = config.load_config(
                configfile=tmp_file.name,
                nocache=True
            )
            self.assertEqual(cfg.get('general', 'appname'), 'sample appname')
            cfg_cached = config.load_config()
            self.assertEqual(cfg_cached.get('general', 'appname'), 'sample appname')


    def test_two_merged_config_files(self):
        config_txt_1 = '''
[general]
default_account=sampleaccount
appname=sample appname
'''
        config_txt_2 = '''
[tokens]
sampleaccount=AAAAAAAA-1234-5678-9999-BBBBBBBB
'''
        with NamedTemporaryFile(mode='w+') as tmp_file_1:
            with NamedTemporaryFile(mode='w+') as tmp_file_2:
                tmp_file_1.write(config_txt_1)
                tmp_file_2.write(config_txt_2)
                for cfl in [tmp_file_1, tmp_file_2]:
                    cfl.file.flush()
                    cfl.file.seek(0)
                cfg = config.load_config(
                    configfile=[
                        tmp_file_1.name,
                        tmp_file_2.name
                    ],
                    nocache=True
                )
            self.assertEqual(cfg.get('general', 'appname'), 'sample appname')
            self.assertEqual(cfg.get('tokens', 'sampleaccount'), 'AAAAAAAA-1234-5678-9999-BBBBBBBB')


class CirconusAPITestCase(TestCase):

    def setUp(self):
        config_file = os.environ.get('CIRCONUS_CONFIG')
        cfg = config.load_config(configfile=config_file, nocache=True)
        account = cfg.get('general', 'default_account')
        appname = cfg.get('general', 'appname')
        token = cfg.get('tokens', account)
        api = circonusapi.CirconusAPI(token)
        api.appname = appname
        self.config = cfg
        self.api = api

    def test_brokers(self):
        brokers = self.api.list_broker()
        self.assertTrue(len(brokers) > 10)

    def test_wrong_method(self):
        try:
            result = self.api.list_foobar()
        except AttributeError:
            pass

    def test_data_wrong_format(self):
        '''
        Test 'data' endpoint and whether errors properly deserialized.

        '''
        try:
            result = self.api.get_data(123)
        except circonusapi.CirconusAPIError as e:
            self.assertEqual(e.code, 400)
            self.assertTrue('format' in e.message)

    def test_check_bundle(self):
        bundles = self.api.list_check_bundle()
        self.assertTrue(type(bundles) is list)

