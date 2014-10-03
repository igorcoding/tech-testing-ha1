import unittest
import mock
import source.lib.utils as utils


class Args:
    pass


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

        os_setsid.assert_called_once_with()
        self.assertTrue(os_fork.called, 'fork() has not been called')
        self.assertFalse(os_exit.called, 'exit should not have been called')

    def test_daemonize_child_parent(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, 42])):
            with mock.patch('os._exit', mock.Mock()) as os_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()

        os_exit.assert_called_once_with(0)

    def test_daemonize_child_oserror(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, OSError("err")])):
            with mock.patch('os._exit', mock.Mock()):
                with mock.patch('os.setsid', mock.Mock()):
                    self.assertRaises(Exception, utils.daemonize)

    def test_daemonize_oserror(self):
        exc = OSError("err")

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
        conf = {
            'TEST1': 'hi1',
            'TEST2': {
                'key1': 'val1'
            },
            'test3': 'stop!'
        }
        with mock.patch('source.lib.utils.exec_py_file', mock.Mock(return_value=conf)):
            result = utils.load_config_from_pyfile('/file/path')

        parsed_conf = utils.Config()
        parsed_conf.TEST1 = conf['TEST1']
        parsed_conf.TEST2 = conf['TEST2']

        self.assertEqual(result.TEST1, parsed_conf.TEST1)
        self.assertEqual(result.TEST2, parsed_conf.TEST2)
        self.assertRaises(AttributeError, lambda: getattr(result, 'test3'))

    def test_parse_cmd_args(self):
        import argparse

        descr = 'test_app'
        config_path = '/file/path'
        pid = 42
        args = '%s -c %s -d -P %d' % (descr, config_path, pid)
        obj = utils.parse_cmd_args(args.split(' ')[1:], descr)
        self.assertEqual(obj, argparse.Namespace(config=config_path, daemon=True, pidfile=str(pid)))

    def test_check_network_status_success(self):
        url = 'dummy.org'
        with mock.patch('urllib2.urlopen', mock.Mock()):
            self.assertTrue(utils.check_network_status(url, 60))

    def test_check_network_status_fail_urlerror(self):
        import urllib2

        url = 'dummy.org'
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=[urllib2.URLError('because')])):
            self.assertFalse(utils.check_network_status(url, 60))

    def test_check_network_status_fail_socket_error(self):
        import socket

        url = 'dummy.org'
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=[socket.error()])):
            self.assertFalse(utils.check_network_status(url, 60))

    def test_check_network_status_fail_value_error(self):
        url = 'dummy.org'
        with mock.patch('urllib2.urlopen', mock.Mock(side_effect=[ValueError])):
            self.assertFalse(utils.check_network_status(url, 60))

    @mock.patch('source.lib.utils.Process')
    def test_spawn_workers(self, process_mock):
        num = 10
        utils.spawn_workers(num, mock.Mock(), mock.Mock(), mock.Mock())
        self.assertTrue(process_mock.called)
        self.assertEqual(process_mock.call_count, num)

    def test_prepare_daemon_pid(self):
        args = Args()
        args.daemon = True
        args.pidfile = '/file/path'

        conf = mock.Mock()
        args.config = conf
        self._prepare(args)

    def test_prepare_daemon_nopid(self):
        args = Args()
        args.daemon = True
        args.pidfile = None

        conf = mock.Mock()
        args.config = conf
        self._prepare(args)

    def test_prepare_nondaemon_pid(self):
        args = Args()
        args.daemon = False
        args.pidfile = '/file/path'

        conf = mock.Mock()
        args.config = conf
        self._prepare(args)

    def test_prepare_nondaemon_nopid(self):
        args = Args()
        args.daemon = False
        args.pidfile = None

        conf = mock.Mock()
        args.config = conf
        self._prepare(args)

    def _prepare(self, args):
        with mock.patch('os.path', mock.MagicMock()), \
             mock.patch('source.lib.utils.daemonize'), \
             mock.patch('source.lib.utils.create_pidfile'), \
             mock.patch('source.lib.utils.load_config_from_pyfile', mock.Mock(return_value=args.config)):
            ret_conf = utils.prepare(args)
        self.assertEqual(ret_conf, args.config)



