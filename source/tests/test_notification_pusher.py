import gevent
import unittest
import mock
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
        pass

    def tearDown(self):
        notification_pusher.logger = self.logger_temp
        pass

    def test_notification_worker(self):
        test_task_data = {
            'f1': 1,
            'f2': 2,
            'callback_url': 'test_url'
        }

        m_task_queue = mock.MagicMock()
        test_task = TestTask(42, test_task_data)

        with mock.patch('threading.current_thread', mock.Mock()):
            with mock.patch('requests.post', mock.Mock(return_value=mock.Mock())):
                notification_pusher.notification_worker(test_task, m_task_queue)
                m_calls = m_task_queue.method_calls
                self.assertEqual(len(m_calls), 1)
                self.assertEqual(m_calls[0][0], 'put')
                self.assertEqual(m_calls[0][1], ((test_task, 'ack'),))

    def test_notification_worker_fail(self):
        import requests
        test_task_data = {
            'f1': 1,
            'f2': 2,
            'callback_url': 'test_url'
        }

        m_task_queue = mock.MagicMock()
        test_task = TestTask(42, test_task_data)

        with mock.patch('threading.current_thread', mock.Mock()):
            with mock.patch('requests.post', mock.Mock(side_effect=[requests.RequestException()])):
                notification_pusher.notification_worker(test_task, m_task_queue)
                m_calls = m_task_queue.method_calls
                self.assertEqual(len(m_calls), 1)
                self.assertEqual(m_calls[0][0], 'put')
                self.assertEqual(m_calls[0][1], ((test_task, 'bury'),))

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

