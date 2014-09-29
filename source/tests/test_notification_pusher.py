import gevent
import unittest
import mock
import source.notification_pusher as notification_pusher


class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
        self.RUNNER = False

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

