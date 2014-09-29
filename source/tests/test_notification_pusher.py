import gevent
import unittest
import mock
import source.notification_pusher as notification_pusher


class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
        self.RUNNER = False

    def test_create_pidfile(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('source.notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                notification_pusher.create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_load_config_from_pyfile(self):

        result = notification_pusher.load_config_from_pyfile('source/tests/test_config/test_conf.py')
        assert result.TEST1 == 'hi1'
        assert result.TEST2 == 'hi2'
        assert result.TEST3 == {
            'key1': 'val1',
            'key2': 'val2'
        }

    def test_install_signal_handlers(self):
        temp_signal = gevent.signal
        gevent_signal_mock = mock.Mock()
        gevent.signal = gevent_signal_mock
        notification_pusher.install_signal_handlers()

        assert gevent_signal_mock.called
        # import signal
        # for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        #     gevent_signal_mock.assert_called_with(signum, notification_pusher.stop_handler, signum)
        gevent.signal = temp_signal

