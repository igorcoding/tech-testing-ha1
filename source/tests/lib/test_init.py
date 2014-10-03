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
        useragent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'

        string_io_m = mock.MagicMock()
        string_io_m.getvalue = mock.Mock(return_value=resp_test)

        curl_m = mock.MagicMock()
        curl_m.getinfo = mock.Mock(return_value=redirect_url)
        curl_m.setopt = mock.Mock()

        with mock.patch('source.lib.to_str', mock.Mock(return_value=url)):
            with mock.patch('source.lib.to_unicode', mock.Mock(return_value=redirect_url)):
                with mock.patch('source.lib.StringIO', mock.Mock(return_value=string_io_m)):
                    with mock.patch('pycurl.Curl', mock.Mock(return_value=curl_m)):
                        resp, redirect = lib.make_pycurl_request(url, 60, useragent)

        self.assertEqual(resp, resp_test, 'Wrong response')
        self.assertEqual(redirect, redirect_url, 'Wrong redirect url')

        curl_m.setopt.assert_any_call(curl_m.USERAGENT, useragent)

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

    def test_check_for_meta(self):
        content = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=page.html/">
                </head>
                <body>
                </body>
            </html>"""

        url_prefix = 'http://mail.ru'

        url = lib.check_for_meta(content, url_prefix)

        assert url, 'No meta tag found'
        assert url.startswith(url_prefix), 'supplied url prefix not took in account'

    def test_get_url_http(self):
        url = 'http://mail.ru'
        timeout = 10
        expected_redirect_url = 'page.html'
        expected_content = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=page.html">
                </head>
                <body>
                </body>
            </html>"""

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, expected_redirect_url))):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertEquals(redirect_url, expected_redirect_url, 'redirect_url not match')
            self.assertEquals(content, expected_content, 'content not match')

    def test_get_url_html(self):
        url = 'http://mail.ru'
        timeout = 10
        expected_redirect_url = 'http://mail.ru/page.html'
        expected_content = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=page.html">
                </head>
                <body>
                </body>
            </html>"""

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, None))):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertEquals(redirect_url, expected_redirect_url, 'redirect_url not match')
            self.assertEquals(content, expected_content, 'content not match')

    def test_get_url_market(self):
        timeout = 10
        expected_redirect_url = 'market://something'
        expected_content = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=market://something/page.html">
                </head>
                <body>
                </body>
            </html>"""

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, None))),\
            mock.patch('source.lib.fix_market_url') as fix_market_url_m:
            redirect_url, redirect_type, content = lib.get_url(expected_redirect_url, timeout)

            assert fix_market_url_m.called, 'fix_market_url() not called'

    def test_get_url_error(self):
        url = 'http://mail.ru'
        timeout = 10
        expected_redirect_url = 'http://mail.ru/page.html'
        expected_content = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=page.html">
                </head>
                <body>
                </body>
            </html>"""

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertEquals(redirect_type, 'ERROR', 'ValueError not handled')

    def test_get_redirect_history(self):
        expected_history_types = ['meta_tag', 'meta_tag']
        expected_history_urls = ['http://mail.ru/', 'http://mail.ru/a.html', 'http://mail.ru/b.html']
        expected_counters = []

        content1 = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=a.html">
                </head>
                <body>
                </body>
            </html>"""

        content2 = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=b.html">
                </head>
                <body>
                </body>
            </html>"""

        content3 = r"""
            <html>
                <head>
                </head>
                <body>
                </body>
            </html>"""

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (expected_history_urls[1], expected_history_types[0], content1),
            (expected_history_urls[2], expected_history_types[1], content2),
            (None, None, content3)
        ])):
            history_types, history_urls, counters = lib.get_redirect_history(expected_history_urls[0], timeout=10)
            self.assertEquals(history_urls, expected_history_urls, 'history_urls not match')
            self.assertEquals(history_types, expected_history_types, 'history_types not match')
            self.assertEquals(counters, expected_counters, 'counters not match')

    def test_get_redirect_history_max_redirects(self):
        expected_history_types = ['meta_tag', 'meta_tag']
        expected_history_urls = ['http://mail.ru/', 'http://mail.ru/a.html', 'http://mail.ru/b.html']
        expected_counters = []

        content1 = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=a.html">
                </head>
                <body>
                </body>
            </html>"""

        content2 = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=b.html">
                </head>
                <body>
                </body>
            </html>"""

        content3 = r"""
            <html>
                <head>
                </head>
                <body>
                </body>
            </html>"""

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (expected_history_urls[1], expected_history_types[0], content1),
            (expected_history_urls[2], expected_history_types[1], content2),
            (None, None, content3)
        ])):
            history_types, history_urls, counters = lib.get_redirect_history(expected_history_urls[0],
                                                                             timeout=10,
                                                                             max_redirects=1)
            # 2 means 1 source url + 1 redirect from it
            self.assertEquals(len(history_urls), 2, 'max_redirects limit not works')

    def test_get_redirect_history_error(self):
        expected_history_types = ['ERROR', 'meta_tag']
        expected_history_urls = ['http://mail.ru/', 'http://mail.ru/a.html', 'http://mail.ru/b.html']
        expected_counters = []

        content1 = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=a.html">
                </head>
                <body>
                </body>
            </html>"""

        content2 = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=b.html">
                </head>
                <body>
                </body>
            </html>"""

        content3 = r"""
            <html>
                <head>
                </head>
                <body>
                </body>
            </html>"""

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (expected_history_urls[1], expected_history_types[0], content1),
            (expected_history_urls[2], expected_history_types[1], content2),
            (None, None, content3)
        ])):
            history_types, history_urls, counters = lib.get_redirect_history(expected_history_urls[0],
                                                                             timeout=10)
            # 2 means 1 source url + 1 redirect from it
            self.assertEquals(len(history_urls), 2, 'continued redirecting after ERROR type')