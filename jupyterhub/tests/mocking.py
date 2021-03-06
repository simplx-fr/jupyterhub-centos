"""mock utilities for testing"""

import sys
from datetime import timedelta
from tempfile import NamedTemporaryFile
import threading

from unittest import mock

import requests

from tornado import gen
from tornado.concurrent import Future
from tornado.ioloop import IOLoop

from ..spawner import LocalProcessSpawner
from ..app import JupyterHub
from ..auth import PAMAuthenticator
from .. import orm

from pamela import PAMError

def mock_authenticate(username, password, service='login'):
    # just use equality for testing
    if password == username:
        return True
    else:
        raise PAMError("Fake")


def mock_open_session(username, service):
    pass


class MockSpawner(LocalProcessSpawner):
    
    def make_preexec_fn(self, *a, **kw):
        # skip the setuid stuff
        return
    
    def _set_user_changed(self, name, old, new):
        pass
    
    def user_env(self, env):
        return env
    
    def _cmd_default(self):
        return [sys.executable, '-m', 'jupyterhub.tests.mocksu']


class SlowSpawner(MockSpawner):
    """A spawner that takes a few seconds to start"""
    
    @gen.coroutine
    def start(self):
        yield super().start()
        yield gen.sleep(2)
    
    @gen.coroutine
    def stop(self):
        yield gen.sleep(2)
        yield super().stop()


class NeverSpawner(MockSpawner):
    """A spawner that will never start"""
    
    def _start_timeout_default(self):
        return 1
    
    def start(self):
        """Return a Future that will never finish"""
        return Future()


class FormSpawner(MockSpawner):
    options_form = "IMAFORM"
    
    def options_from_form(self, form_data):
        options = {}
        options['notspecified'] = 5
        if 'bounds' in form_data:
            options['bounds'] = [int(i) for i in form_data['bounds']]
        if 'energy' in form_data:
            options['energy'] = form_data['energy'][0]
        if 'hello_file' in form_data:
            options['hello'] = form_data['hello_file'][0]
        return options


class MockPAMAuthenticator(PAMAuthenticator):
    def _admin_users_default(self):
        return {'admin'}
    
    def system_user_exists(self, user):
        # skip the add-system-user bit
        return not user.name.startswith('dne')
    
    def authenticate(self, *args, **kwargs):
        with mock.patch.multiple('pamela',
                authenticate=mock_authenticate,
                open_session=mock_open_session,
                close_session=mock_open_session,
                ):
            return super(MockPAMAuthenticator, self).authenticate(*args, **kwargs)

class MockHub(JupyterHub):
    """Hub with various mock bits"""

    db_file = None
    confirm_no_ssl = True
    
    def _ip_default(self):
        return '127.0.0.1'
    
    def _authenticator_class_default(self):
        return MockPAMAuthenticator
    
    def _spawner_class_default(self):
        return MockSpawner
    
    def init_signal(self):
        pass
    
    def start(self, argv=None):
        self.db_file = NamedTemporaryFile()
        self.db_url = 'sqlite:///' + self.db_file.name
        
        evt = threading.Event()
        
        @gen.coroutine
        def _start_co():
            assert self.io_loop._running
            # put initialize in start for SQLAlchemy threading reasons
            yield super(MockHub, self).initialize(argv=argv)
            # add an initial user
            user = orm.User(name='user')
            self.db.add(user)
            self.db.commit()
            yield super(MockHub, self).start()
            yield self.hub.server.wait_up(http=True)
            self.io_loop.add_callback(evt.set)
        
        def _start():
            self.io_loop = IOLoop()
            self.io_loop.make_current()
            self.io_loop.add_callback(_start_co)
            self.io_loop.start()
        
        self._thread = threading.Thread(target=_start)
        self._thread.start()
        ready = evt.wait(timeout=10)
        assert ready
    
    def stop(self):
        super().stop()
        self._thread.join()
        IOLoop().run_sync(self.cleanup)
        # ignore the call that will fire in atexit
        self.cleanup = lambda : None
        self.db_file.close()
    
    def login_user(self, name):
        r = requests.post(self.proxy.public_server.url + 'hub/login',
            data={
                'username': name,
                'password': name,
            },
            allow_redirects=False,
        )
        assert r.cookies
        return r.cookies

