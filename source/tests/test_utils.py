import unittest
import mock
import source.notification_pusher as notification_pusher


class UtilsTestCase(unittest.TestCase):
    def test_daemonize_parent(self):
        test_pid = 42

        with mock.patch('os.fork', mock.Mock(return_value=test_pid)):
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                notification_pusher.daemonize()
                os_exit.assert_called_once_with(0)

    def test_daemonize_child(self):
        test_pid = 0

        with mock.patch('os.fork', mock.Mock(return_value=test_pid)) as os_fork:
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                    notification_pusher.daemonize()

        os_setsid.assert_called_once()
        os_fork.assert_called_once()
        assert not os_exit.called

    def test_daemonize_oserror(self):
        exc = OSError()
        exc.errno = 42
        exc.strerror = "42 error"

        with mock.patch('os.fork', mock.Mock(side_effect=exc)):
            self.assertRaises(Exception, notification_pusher.daemonize)


