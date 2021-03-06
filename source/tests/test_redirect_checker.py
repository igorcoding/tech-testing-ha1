import mock
import unittest
from source import redirect_checker
from source.lib.utils import Config


class MyActiveChildren:
    m = mock.Mock()

    def __init__(self, length):
        self.arr = [self.m] * length

    def __len__(self):
        return len(self.arr)

    def __iter__(self):
        return iter(self.arr)


class Args:
    pass


class RedirectCheckerTestCase(unittest.TestCase):
    def setUp(self):
        self.logger_temp = redirect_checker.logger
        redirect_checker.logger = mock.Mock()
        pass

    def tearDown(self):
        redirect_checker.logger = self.logger_temp

    @mock.patch('source.redirect_checker.active_children', mock.Mock())
    @mock.patch('source.redirect_checker.utils.check_network_status', mock.Mock(return_value=True))
    @mock.patch('source.redirect_checker.worker', mock.Mock())
    @mock.patch('source.lib.utils.spawn_workers')
    def test_main_loop_iteration_network_access(self, spawn_workers_m):
        config = Config()
        config.CHECK_URL = 'test_url'
        config.HTTP_TIMEOUT = 10
        config.WORKER_POOL_SIZE = 30

        with mock.patch('source.redirect_checker.active_children', lambda: MyActiveChildren(10)):
            redirect_checker.main_loop_iteration(config, 42)

        self.assertEqual(spawn_workers_m.called, True)

    @mock.patch('source.redirect_checker.utils.check_network_status', mock.Mock(return_value=True))
    @mock.patch('source.redirect_checker.worker', mock.Mock())
    @mock.patch('source.lib.utils.spawn_workers')
    def test_main_loop_iteration_no_free_workers(self, spawn_workers_m):
        config = Config()
        config.CHECK_URL = 'test_url'
        config.HTTP_TIMEOUT = 10
        config.WORKER_POOL_SIZE = 10

        with mock.patch('source.redirect_checker.active_children', lambda: MyActiveChildren(10)):
            redirect_checker.main_loop_iteration(config, 42)

        self.assertEqual(spawn_workers_m.called, False)

    @mock.patch('source.redirect_checker.worker', mock.Mock())
    @mock.patch('source.lib.utils.check_network_status', mock.Mock(return_value=False))
    def test_main_loop_iteration_no_network_access(self):
        config = Config()
        config.CHECK_URL = 'test_url'
        config.HTTP_TIMEOUT = 10

        children = mock.Mock()
        children.terminate = mock.Mock()

        length = 10
        active_children = [children] * length

        active_children_fun = mock.Mock(return_value=active_children)

        with mock.patch('source.redirect_checker.active_children', active_children_fun):
            redirect_checker.main_loop_iteration(config, 42)

        self.assertEquals(children.terminate.call_count,
                          length,
                          'Not all active children have been terminated')

    @mock.patch('os.getpid', mock.Mock(return_value=24))
    @mock.patch('source.redirect_checker.run_application', mock.Mock())
    def test_main_loop(self):
        config = mock.Mock()
        config.SLEEP = 42

        def break_run(*args, **kwargs):
            redirect_checker.run_application = False

        with mock.patch('source.redirect_checker.main_loop_iteration', mock.MagicMock()) as main_loop_iter:
            with mock.patch('source.redirect_checker.sleep', mock.Mock(side_effect=break_run)) as main_loop_sleep:
                redirect_checker.main_loop(config)
        self.assertTrue(main_loop_iter.called)
        self.assertEqual(main_loop_iter.call_count, 1)
        main_loop_sleep.assert_called_once_with(config.SLEEP)

    @mock.patch('source.redirect_checker.utils.parse_cmd_args', mock.Mock())
    @mock.patch('source.redirect_checker.main_loop')
    @mock.patch('source.redirect_checker.dictConfig', mock.Mock())
    def test_main(self, main_loop_m):
        config = mock.Mock()
        config.EXIT_CODE = 42

        with mock.patch('source.lib.utils.prepare', mock.Mock(return_value=config)):
            ret_code = redirect_checker.main([1, 2, 3, 4])

        main_loop_m.assert_called_once_with(config)
        self.assertEqual(ret_code, config.EXIT_CODE)
