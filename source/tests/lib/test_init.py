import unittest
import mock
from source import lib
import re
import rstr


class InitTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_prepare_url(self):
        url = 'http://a.b.com/name with space.php;c=a b'
        excepted_url = 'http://a.b.com/name%20with%20space.php;c=a+b'

        prepared_url = lib.prepare_url(url)

        self.assertEquals(excepted_url,
                          prepared_url,
                          'prepare_url works badly')

    def test_prepare_url_none(self):
        url = None
        excepted_url = None

        prepared_url = lib.prepare_url(url)

        self.assertEquals(excepted_url,
                          prepared_url,
                          'prepare_url works badly with url=None')

    def test_get_counters(self):
        page = ''

        for counter_name, regexp in lib.COUNTER_TYPES:
            page += rstr.xeger(regexp)

        counters = lib.get_counters(page)

        assert len(counters) == len(lib.COUNTER_TYPES), 'Not all counter found, or too mny counters found'

    def test_get_counters_empty(self):
        self.assertEquals(
            lib.get_counters("<html>some text without urls</html>"),
            [],
            'No counters exist in  this page')
