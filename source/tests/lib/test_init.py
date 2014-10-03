import unittest
import mock
from source import lib
import re
import rstr
from source import lib


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
        pass

    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_make_pycurl_request(self):
        url = 'http://test_url.net'
        resp_test = 'hello from test_url.net'
        redirect_url = 'http://another_url.org'

        string_io_m = mock.MagicMock()
        string_io_m.getvalue = mock.Mock(return_value=resp_test)

        curl_m = mock.MagicMock()
        curl_m.getinfo = mock.Mock(return_value=redirect_url)

        with mock.patch('source.lib.to_str', mock.Mock(return_value=url)):
            with mock.patch('source.lib.to_unicode', mock.Mock(return_value=redirect_url)):
                with mock.patch('source.lib.StringIO', mock.Mock(return_value=string_io_m)):
                    with mock.patch('pycurl.Curl', mock.Mock(return_value=curl_m)):
                        resp, redirect = lib.make_pycurl_request(url, 60)

        self.assertEqual(resp, resp_test, 'Wrong response')
        self.assertEqual(redirect, redirect_url, 'Wrong redirect url')

    def test_fix_market_url_good(self):
        web_url = 'http://play.google.com/store/apps/'
        market_url = 'market://'

        test_app = 'my_cool_app/definitely'
        test_url = market_url + test_app

        url = lib.fix_market_url(test_url)

        self.assertEqual(url, web_url + test_app)

    def test_fix_market_url_bad(self):
        web_url = 'http://play.google.com/store/apps/'
        market_url = 'this-is-not-market-see-that://'

        test_app = 'my_cool_app/definitely'
        test_url = market_url + test_app

        url = lib.fix_market_url(test_url)

        self.assertNotEqual(url, web_url + test_app)