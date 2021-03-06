import os
import shutil
import tempfile
import json

import pytest
import halt

from uncrumpled.core import dbapi
from util import get_all_data


class MixIn():
    profile = 'a profile'
    book = 'abook'
    hotkey = ['f5']
    program = 'firefox'
    specific = None
    loose = None
    def setup_class(cls):
        cls.tdir = tempfile.mkdtemp()

    def teardown_class(cls):
        shutil.rmtree(cls.tdir)

    def setup_method(self, func):
        '''create fresh database for each test method'''
        self.db = os.path.join(self.tdir, func.__name__+'.db')
        try:
            os.remove(self.db)
        except FileNotFoundError:
            pass
        dbapi.new_db(self.db)


class TestHotkeys(MixIn):

    def test_hotkey_create(self):
        rv = dbapi.hotkey_create(self.db, self.profile, self.book, self.hotkey)
        assert rv
        data = get_all_data(self.db, 'Hotkeys')[0]
        assert data[0] == self.profile
        assert data[1] == self.book
        assert data[2] == json.dumps(self.hotkey)

        rv = dbapi.hotkey_create(self.db, self.profile, self.book, self.hotkey)
        assert not rv


    def test_hotkey_delete(self):
        rv = dbapi.hotkey_delete(self.db, self.profile, self.book, self.hotkey)
        assert not rv

        dbapi.hotkey_create(self.db, self.profile, self.book, self.hotkey)

        rv = dbapi.hotkey_delete(self.db, self.profile, self.book, self.hotkey)
        assert rv
        data = get_all_data(self.db, 'Hotkeys')
        assert not data


    def test_hotkey_get(self):
        rv = dbapi.hotkey_get(self.db, self.profile, self.book)
        assert not rv

        dbapi.hotkey_create(self.db, self.profile, self.book, self.hotkey)
        rv = dbapi.hotkey_get(self.db, self.profile, self.book)
        assert rv == self.hotkey


class TestProfile(MixIn):
    def test_profile_create(self):
        rv = dbapi.profile_create(self.db, self.profile)
        assert rv
        cond = "where Name == '{}'".format(self.profile)
        data = halt.load_column(self.db, 'Profiles', ('*',), cond)[0]
        assert data[0] == self.profile
        assert data[1] != True # the active column

        rv = dbapi.profile_create(self.db, self.profile)
        assert not rv


    def test_profile_set_active(self):
        dbapi.profile_create(self.db, self.profile)
        dbapi.profile_set_active(self.db, self.profile)
        cond = "where Name == '{}'".format(self.profile)
        data = halt.load_column(self.db, 'Profiles', ('Active',), cond)[0][0]
        assert data == True
        cond = "where Name == '{}'".format('default')
        data = halt.load_column(self.db, 'Profiles', ('Active',), cond)[0][0]
        assert data == False


    def test_profile_get_active(self):
        dbapi.profile_create(self.db, self.profile)
        dbapi.profile_set_active(self.db, self.profile)
        rv = dbapi.profile_get_active(self.db)
        assert rv == self.profile

    def test_profile_update(self):
        data = {'some': 'data'}
        rv = dbapi.profile_update(self.db, self.profile, data)
        assert not rv

        dbapi.profile_create(self.db, self.profile)
        rv = dbapi.profile_update(self.db, self.profile, data)
        assert rv


class TestBook(MixIn):
    def test_update(self):
        data = {'some': 'data'}
        rv = dbapi.book_update(self.db, self.book, self.profile, data)
        assert not rv

        dbapi.book_create(self.db, self.profile, self.book, self.hotkey)
        rv = dbapi.book_update(self.db, self.book, self.profile, data)
        assert rv


class TestPage(MixIn):
    def test_page_create_specific(self):
        self.specific = 'something specific'
        dbapi.page_create(self.db, self.profile, self.book,
                          self.program, self.specific, self.loose)
        data = get_all_data(self.db, 'Pages')[0]
        assert data[4] == self.specific


    def test_page_update_from_id(self):
        data_in = {'some': 'data'}
        page_id = dbapi.page_create(self.db, self.profile, self.book,
                                    self.program, self.specific, self.loose)

        rv = dbapi.page_update_from_id(self.db, page_id + 1, data_in)
        assert not rv

        rv = dbapi.page_update_from_id(self.db, page_id, data_in)
        assert rv

        data_out = get_all_data(self.db, 'Pages')[0]
        assert data_out[-1] == halt.stringify(data_in)

