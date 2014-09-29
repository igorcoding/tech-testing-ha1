import unittest
import mock
import source.lib.utils as utils


class UtilsTestCase(unittest.TestCase):
    def test_daemonize_parent(self):
        test_pid = 42

        with mock.patch('os.fork', mock.Mock(return_value=test_pid)):
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                utils.daemonize()
                os_exit.assert_called_once_with(0)

    def test_daemonize_child(self):
        test_pid = 0

        with mock.patch('os.fork', mock.Mock(return_value=test_pid)) as os_fork:
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                with mock.patch('os.setsid', mock.Mock()) as os_setsid:
                    utils.daemonize()

        os_setsid.assert_called_once()
        os_fork.assert_called_once()
        assert not os_exit.called

    def test_daemonize_oserror(self):
        exc = OSError()
        exc.errno = 42
        exc.strerror = "42 error"

        with mock.patch('os.fork', mock.Mock(side_effect=exc)):
            self.assertRaises(Exception, utils.daemonize)

    def test_create_pidfile(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('source.lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_load_config_from_pyfile(self):

        result = utils.load_config_from_pyfile('source/tests/test_config/test_conf.py')
        assert result.TEST1 == 'hi1'
        assert result.TEST2 == 'hi2'
        assert result.TEST3 == {
            'key1': 'val1',
            'key2': 'val2'
        }




