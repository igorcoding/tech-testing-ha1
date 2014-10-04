import unittest
import mock
import rstr
from source import lib


class InitTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def get_redirect_html(self, page):
        return r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url={0}">
                </head>
                <body>
                </body>
            </html>""".format(page)

    def get_default_html(self):
        return r"""
            <html>
                <head>
                </head>
                <body>
                </body>
            </html>"""

    def test_prepare_url(self):
        url = 'http://a.b.com/name with space.php;c=a b'
        excepted_url = 'http://a.b.com/name%20with%20space.php;c=a+b'

        prepared_url = lib.prepare_url(url)

        self.assertEquals(excepted_url,
                          prepared_url,
                          'prepare_url works badly')

    def test_prepare_url_exception(self):
        url = 'what ever'

        netlock_m = mock.MagicMock()
        netlock_m.encode = mock.Mock(side_effect=UnicodeError)
        urlparse_m = mock.Mock(return_value=('a', netlock_m, 'b', 'c', 'd', 'e'))

        with mock.patch('source.lib.urlparse', urlparse_m):
            try:
                lib.prepare_url(url)
            except UnicodeError:
                assert False, 'UnicodeError not cached in prepare_url()'

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

        self.assertEqual(len(counters), len(lib.COUNTER_TYPES), 'Not all counter found, or too mny counters found')

    def test_get_counters_empty(self):
        self.assertEquals(
            lib.get_counters("<html>some text without urls</html>"),
            [],
            'No counters exist in  this page')
        pass

    def _actual_test_make_pycurl_request(self, redirect_url, resp_test, url, useragent):
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

        if useragent:
            curl_m.setopt.assert_any_call(curl_m.USERAGENT, useragent)

    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_make_pycurl_request(self):
        url = 'http://test_url.net'
        resp_test = 'hello from test_url.net'
        redirect_url = 'http://another_url.org'
        useragent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'

        self._actual_test_make_pycurl_request(redirect_url, resp_test, url, useragent)

    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_make_pycurl_request_no_useragent(self):
        url = 'http://test_url.net'
        resp_test = 'hello from test_url.net'
        redirect_url = 'http://another_url.org'
        useragent = None

        self._actual_test_make_pycurl_request(redirect_url, resp_test, url, useragent)

    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_make_pycurl_request_with_redirect_url(self):
        url = 'http://test_url.net'
        resp_test = 'hello from test_url.net'
        redirect_url = None
        useragent = None

        self._actual_test_make_pycurl_request(redirect_url, resp_test, url, useragent)

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
        content = self.get_redirect_html('page.html')

        url_prefix = 'http://mail.ru'

        url = lib.check_for_meta(content, url_prefix)

        assert url, 'No meta tag found'
        assert url.startswith(url_prefix), 'supplied url prefix not took in account'

    def test_check_for_meta_no_meta(self):
        content = self.get_default_html()
        url_prefix = 'http://mail.ru'

        url = lib.check_for_meta(content, url_prefix)

        assert url is None, 'url found but no url was specified'

    def test_check_for_meta_no_equal_sign(self):
        content = r"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url">
                </head>
                <body>
                </body>
            </html>"""

        url_prefix = 'http://mail.ru'

        url = lib.check_for_meta(content, url_prefix)

        assert url is None, 'url found but no url was specified (no equal sign)'

    def test_check_for_meta_bad_html(self):
        content = """
            <html>
                <head>
                    <meta http-equiv="refresh" content="5url={0}">
                </head>
                <body>
                </body>
            </html>"""

        url_prefix = 'http://mail.ru'

        url = lib.check_for_meta(content, url_prefix)

        self.assertEquals(url, None, 'such bad html should be parsed')

    def test_get_url_http(self):
        url = 'http://mail.ru'
        timeout = 10
        expected_redirect_url = 'page.html'
        expected_content = self.get_redirect_html('page.html')
        expected_redirect_type = lib.REDIRECT_HTTP

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, expected_redirect_url))):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertEquals(redirect_url, expected_redirect_url, 'redirect_url not match')
            self.assertEquals(content, expected_content, 'content not match')
            self.assertEquals(redirect_type, expected_redirect_type, 'redirect_type is not correct')

    def test_get_url_html(self):
        url = 'http://mail.ru'
        timeout = 10
        expected_redirect_url = 'http://mail.ru/page.html'
        expected_content = self.get_redirect_html('page.html')
        expected_redirect_type = lib.REDIRECT_META

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, None))):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertEquals(redirect_url, expected_redirect_url, 'redirect_url not match')
            self.assertEquals(content, expected_content, 'content not match')
            self.assertEquals(redirect_type, expected_redirect_type, 'redirect_type is not correct')

    def test_get_url_html_no_meta(self):
        url = 'http://mail.ru'
        timeout = 10
        expected_redirect_url = None
        expected_content = self.get_redirect_html('page.html')
        expected_redirect_type = None

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, None))):
            with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=None)):
                redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertEquals(redirect_url, expected_redirect_url, 'redirect_url not match')
            self.assertEquals(content, expected_content, 'content not match')
            self.assertEquals(redirect_type, expected_redirect_type, 'redirect_type is not correct')

    def test_get_url_market(self):
        timeout = 10
        expected_redirect_url = 'market://something'
        expected_content = self.get_redirect_html('market://something/page.html')

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, None))),\
            mock.patch('source.lib.fix_market_url') as fix_market_url_m:
            redirect_url, redirect_type, content = lib.get_url(expected_redirect_url, timeout)

            assert fix_market_url_m.called, 'fix_market_url() not called'

    def test_get_url_http_new_redirect_and_ok_redirect(self):
        url = 'http://mail.ru'
        timeout = 10
        expected_redirect_url = rstr.xeger(lib.OK_REDIRECT)
        expected_content = self.get_redirect_html('page.html')

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(expected_content, expected_redirect_url))):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertIsNone(redirect_url, 'redirect_url is not None')
            self.assertIsNone(redirect_type, 'redirect_type is not None')
            self.assertEqual(content, expected_content, 'content not match')

    def test_get_url_error(self):
        url = 'http://mail.ru'
        timeout = 10

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            redirect_url, redirect_type, content = lib.get_url(url, timeout)

            self.assertEquals(redirect_type, 'ERROR', 'ValueError not handled')

    def test_get_redirect_history(self):
        expected_history_types = ['meta_tag', 'meta_tag']
        expected_history_urls = ['http://mail.ru/', 'http://mail.ru/a.html', 'http://mail.ru/b.html']
        expected_counters = []

        content1 = self.get_redirect_html('a.html')
        content2 = self.get_redirect_html('b.html')
        content_no_redirect = self.get_default_html()

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (expected_history_urls[1], expected_history_types[0], content1),
            (expected_history_urls[2], expected_history_types[1], content2),
            (None, None, content_no_redirect)
        ])):
            history_types, history_urls, counters = lib.get_redirect_history(expected_history_urls[0], timeout=10)
            self.assertEquals(history_urls, expected_history_urls, 'history_urls not match')
            self.assertEquals(history_types, expected_history_types, 'history_types not match')
            self.assertEquals(counters, expected_counters, 'counters not match')

    def test_get_redirect_history_max_redirects(self):
        expected_history_types = ['meta_tag', 'meta_tag']
        expected_history_urls = ['http://mail.ru/', 'http://mail.ru/a.html', 'http://mail.ru/b.html']

        content1 = self.get_redirect_html('a.html')
        content2 = self.get_redirect_html('b.html')
        content_no_redirect = self.get_default_html()

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (expected_history_urls[1], expected_history_types[0], content1),
            (expected_history_urls[2], expected_history_types[1], content2),
            (None, None, content_no_redirect)
        ])):
            history_types, history_urls, counters = lib.get_redirect_history(expected_history_urls[0],
                                                                             timeout=10,
                                                                             max_redirects=1)
            # 2 means 1 source url + 1 redirect from it
            self.assertEquals(len(history_urls), 2, 'max_redirects limit not works')

    def test_get_redirect_history_error(self):
        expected_history_types = ['ERROR', 'meta_tag']
        expected_history_urls = ['http://mail.ru/', 'http://mail.ru/a.html', 'http://mail.ru/b.html']

        content1 = self.get_redirect_html('a.html')
        content2 = self.get_redirect_html('b.html')
        content_no_redirect = self.get_default_html()

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (expected_history_urls[1], expected_history_types[0], content1),
            (expected_history_urls[2], expected_history_types[1], content2),
            (None, None, content_no_redirect)
        ])):
            history_types, history_urls, counters = lib.get_redirect_history(expected_history_urls[0],
                                                                             timeout=10)
            # 2 means 1 source url + 1 redirect from it
            self.assertEquals(len(history_urls), 2, 'continued redirecting after ERROR type')

    def test_get_redirect_history_ok(self):
        expected_history_types = ['meta_tag', 'meta_tag']
        expected_history_urls = ['http://odnoklassniki.ru/', 'http://mail.ru/a.html', 'http://mail.ru/b.html']

        content1 = self.get_redirect_html('a.html')
        content2 = self.get_redirect_html('b.html')
        content_no_redirect = self.get_default_html()

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (expected_history_urls[1], expected_history_types[0], content1),
            (expected_history_urls[2], expected_history_types[1], content2),
            (None, None, content_no_redirect)
        ])):
            history_types, history_urls, counters = lib.get_redirect_history(expected_history_urls[0],
                                                                             timeout=10)

            self.assertEquals(len(history_urls), 1, 'should return after odnoklassniki.ru')
