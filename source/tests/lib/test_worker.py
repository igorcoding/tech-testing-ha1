import unittest
import mock
import source.lib.worker as worker

class WorkerTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('source.lib.worker.get_tube')
    @mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]))
    @mock.patch('source.lib.worker.handle_next_task')
    def test_worker_stops_on_parent_dead(self, handle_next_task_mock, get_tube_mock):
        config = mock.Mock()
        parent_pid = 10

        with mock.patch.dict(get_tube_mock.opt, {}):
            worker.worker(config, parent_pid)

            self.assertEquals(handle_next_task_mock.call_count, 1,
                              'Handling not stopped on parent death')

    @mock.patch('source.lib.worker.get_redirect_history_from_task')
    def test_handle_next_task_bad_task(self, get_redirect_history_from_task_mock):
        config = mock.Mock()
        input_tube = mock.Mock()
        output_tube = mock.Mock()

        input_tube.take = mock.Mock(return_value=None)

        worker.handle_next_task(config, input_tube, output_tube)

        assert not get_redirect_history_from_task_mock.called, 'Attempt to work with invalid task'

    @mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=(mock.Mock(), mock.Mock())))
    def test_handle_next_task_task_acknowledged(self):
        config = mock.Mock()
        input_tube = mock.Mock()
        output_tube = mock.Mock()

        task = mock.Mock()
        task.meta = mock.Mock(return_value={'pri': 'pri'})

        input_tube.take = mock.Mock(return_value=task)

        worker.handle_next_task(config, input_tube, output_tube)

        assert task.ack.called, 'task.ack() not called'

    def test_handle_next_task_task_acknowledged_no_input(self):
        config = mock.Mock()
        input_tube = mock.Mock()
        output_tube = mock.Mock()

        task = mock.Mock()
        task.meta = mock.Mock(return_value={'pri': 'pri'})

        input_tube.take = mock.Mock(return_value=task)

        data = mock.Mock()

        with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=(False, data))):
            worker.handle_next_task(config, input_tube, output_tube)

        output_tube.put.assert_called_with(data)

    @mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=(mock.Mock(), mock.Mock())))
    def test_handle_next_task_db_error(self):
        config = mock.Mock()
        input_tube = mock.Mock()
        output_tube = mock.Mock()

        task = mock.Mock()
        task.ack = mock.Mock(side_effect=worker.DatabaseError)
        task.meta = mock.Mock(return_value={'pri': 'pri'})

        input_tube.take = mock.Mock(return_value=task)

        try:
            worker.handle_next_task(config, input_tube, output_tube)
        except worker.DatabaseError:
            assert False, 'DatabaseError not cached in handle_next_task()'

    @mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=(['ERROR'], [], [])))
    def test_get_redirect_history_from_task_with_error(self):
        task = mock.Mock()
        task.data = {'url': 'url', 'url_id': 'url_id', 'recheck': False}

        is_input, data = worker.get_redirect_history_from_task(task, 10)

        assert is_input, 'ERROR in history_types but is_input is False'

    @mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=(['ERROR'], [], [])))
    def test_get_redirect_history_from_task_with_error_and_recheck(self):
        task = mock.Mock()
        suspicious = True
        task.data = {'url': 'url', 'url_id': 'url_id', 'recheck': True, 'suspicious': suspicious}

        is_input, data = worker.get_redirect_history_from_task(task, 10)

        self.assertEquals(data['suspicious'], suspicious, 'suspicious is not so suspicious')