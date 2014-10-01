import gevent
import requests
import unittest
import mock
from source.lib.utils import Config
import source.notification_pusher as notification_pusher


class TaskData:
    def __init__(self, data):
        self.data = data

    def copy(self):
        return self.data


class TestTask:
    def __init__(self, task_id, data):
        self.task_id = task_id
        self.data = TaskData(data)


class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
        self.logger_temp = notification_pusher.logger
        notification_pusher.logger = mock.Mock()

    def tearDown(self):
        notification_pusher.logger = self.logger_temp

    @mock.patch('source.notification_pusher.current_thread', mock.Mock())
    @mock.patch('source.notification_pusher.requests.post', mock.Mock(return_value=mock.Mock()))
    def test_notification_worker(self):
        test_task_data = {
            'f1': 1,
            'f2': 2,
            'callback_url': 'test_url'
        }

        m_task_queue = mock.MagicMock()
        test_task = TestTask(42, test_task_data)

        notification_pusher.notification_worker(test_task, m_task_queue)
        m_calls = m_task_queue.method_calls
        self.assertEqual(len(m_calls), 1)
        self.assertEqual(m_calls[0][0], 'put')
        self.assertEqual(m_calls[0][1], ((test_task, 'ack'),))

    @mock.patch('source.notification_pusher.current_thread', mock.Mock())
    @mock.patch('source.notification_pusher.requests.post', mock.Mock(side_effect=[requests.RequestException()]))
    def test_notification_worker_fail(self):
        test_task_data = {
            'f1': 1,
            'f2': 2,
            'callback_url': 'test_url'
        }

        m_task_queue = mock.MagicMock()
        test_task = TestTask(42, test_task_data)

        notification_pusher.notification_worker(test_task, m_task_queue)
        m_calls = m_task_queue.method_calls
        self.assertEqual(len(m_calls), 1)
        self.assertEqual(m_calls[0][0], 'put')
        self.assertEqual(m_calls[0][1], ((test_task, 'bury'),))

    @mock.patch('source.notification_pusher.stop_handler', mock.Mock())
    @mock.patch('source.notification_pusher.gevent')
    def test_install_signal_handlers(self, gevent_mock):
        notification_pusher.install_signal_handlers()

        import signal

        sigs = [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]

        called_sigs = [x for x in sigs]
        for signum in sigs:
            for call in gevent_mock.method_calls:
                if call[0] == 'signal' and call[1][0] == signum:
                    called_sigs.remove(signum)

        def arr_to_str(arr):
            return '[' + ', '.join([str(elem) for elem in arr]) + ']'

        self.assertEqual(len(called_sigs), 0, "These signals have not been called: %s" % arr_to_str(called_sigs))


    @mock.patch('source.notification_pusher.current_thread', mock.MagicMock())
    def test_stop_handler(self):
        sig = 42
        temp_run_app = notification_pusher.run_application
        temp_exit_code = notification_pusher.exit_code

        notification_pusher.stop_handler(sig)
        self.assertEqual(notification_pusher.run_application, False)
        self.assertEqual(notification_pusher.exit_code, notification_pusher.SIGNAL_EXIT_CODE_OFFSET + sig)

        notification_pusher.run_application = temp_run_app
        notification_pusher.exit_code = temp_exit_code

    def test_done_with_processed_tasks(self):
        queue_m = mock.Mock()
        task = mock.Mock()
        queue_m.get_nowait = mock.Mock(return_value=(task, 'test_method'))
        queue_m.qsize = mock.Mock(return_value=1)

        notification_pusher.done_with_processed_tasks(queue_m)

        assert task.test_method.called, "task's method not called"

    def test_done_with_processed_tasks_db_exception_handling(self):
        queue_m = mock.Mock()
        task = mock.Mock()
        queue_m.get_nowait = mock.Mock(return_value=(task, 'test_method'))
        queue_m.qsize = mock.Mock(return_value=1)

        import tarantool
        task.test_method = mock.Mock(side_effect=tarantool.DatabaseError())

        try:
            notification_pusher.done_with_processed_tasks(queue_m)
        except tarantool.DatabaseError:
            assert False, 'tarantool.DatabaseError raised from notification_pusher'

    def test_done_with_processed_tasks_gevent_exception_handling(self):
        #TODO: gevent_queue.Empty
        queue_m = mock.Mock()
        task = mock.Mock()
        queue_m.get_nowait = mock.Mock(return_value=(task, 'test_method'))
        queue_m.qsize = mock.Mock(return_value=1)

        import tarantool
        task.test_method = mock.Mock(side_effect=tarantool.DatabaseError())

        try:
            notification_pusher.done_with_processed_tasks(queue_m)
        except tarantool.DatabaseError:
            assert False, 'tarantool.DatabaseError raised from notification_pusher'

    @mock.patch('source.notification_pusher.Greenlet', mock.MagicMock())
    @mock.patch('source.lib.utils.Config')
    @mock.patch('gevent.queue.Queue')
    @mock.patch('tarantool_queue.tarantool_queue.Task')
    @mock.patch('gevent.pool.Pool')
    def test_start_worker_with_task(self, worker_pool_m, task_m, queue_m, config):
        worker_pool_m.add = mock.Mock()

        notification_pusher.start_worker_with_task(config, queue_m, task_m, worker_pool_m)
        self.assertEqual(worker_pool_m.add.call_count, 1)

    @mock.patch('source.notification_pusher.gevent_queue.Queue')
    @mock.patch('source.notification_pusher.Pool')
    @mock.patch('source.notification_pusher.tarantool_queue.Queue')
    def test_configure_infrastructure(self, Queue, Pool, GQueue):
        config = Config()
        config.QUEUE_HOST = 'test'
        config.QUEUE_PORT = 8888
        config.QUEUE_SPACE = 'space'
        config.QUEUE_TUBE = 'tube'
        config.WORKER_POOL_SIZE = 100500
        config.QUEUE_TAKE_TIMEOUT = 0
        config.SLEEP = 0

        notification_pusher.configure_infrastructure(config)

        Queue.assert_called_with(
            host=config.QUEUE_HOST, port=config.QUEUE_PORT, space=config.QUEUE_SPACE
        )

        Pool.assert_called_with(config.WORKER_POOL_SIZE)
        GQueue.assert_called_with()


    @mock.patch('source.lib.utils.Config')
    @mock.patch('gevent.queue.Queue')
    @mock.patch('tarantool_queue.tarantool_queue.Tube')
    @mock.patch('gevent.pool.Pool')
    @mock.patch("source.notification_pusher.start_worker_with_task")
    @mock.patch("source.notification_pusher.done_with_processed_tasks", mock.Mock())
    def test_start_workers(self, start_worker_with_task_m, worker_pool, tube, processed_task_queue, config):
        free_workers_count = 10
        worker_pool.free_count = mock.Mock(return_value=free_workers_count)

        notification_pusher.start_workers(config, processed_task_queue, tube, worker_pool)

        self.assertEquals(start_worker_with_task_m.call_count, free_workers_count)
