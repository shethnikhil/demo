import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import urllib.error

# Import the function to be tested
from check_url_status import check_url_status

class TestCheckURLStatus(unittest.TestCase):
    
    @patch('sys.stdout', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    def test_successful_request_no_scheme(self, mock_urlopen, mock_stdout):
        # Mocking a successful HTTP 200 response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.url = "https://example.com"
        
        # We need the context manager (__enter__ and __exit__) for 'with urlopen() as response:'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        check_url_status("example.com")
        
        output = mock_stdout.getvalue()
        
        # Verify the auto-scheme addition and correct output parsing
        self.assertIn("No scheme provided \u2014 assuming: https://example.com", output)
        self.assertIn("[OK] Status Code : 200", output)
        self.assertIn("[--] Description : OK", output)
        self.assertIn("[>>] Final URL   : https://example.com", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    def test_http_error_404(self, mock_urlopen, mock_stdout):
        # Mocking an HTTP error (e.g., 404 Not Found)
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com/notfound", 
            code=404, 
            msg="Not Found", 
            hdrs={}, 
            fp=None
        )
        
        check_url_status("https://example.com/notfound")
        
        output = mock_stdout.getvalue()
        self.assertIn("[ERR] Status Code : 404", output)
        self.assertIn("[--] Description : Not Found", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    def test_url_error_connection_refused(self, mock_urlopen, mock_stdout):
        # Mocking a connection error (e.g., host down)
        mock_urlopen.side_effect = urllib.error.URLError(reason="Connection refused")
        
        check_url_status("https://example-broken.com")
        
        output = mock_stdout.getvalue()
        self.assertIn("[!] Connection Error: Connection refused", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    def test_timeout_error(self, mock_urlopen, mock_stdout):
        # Mocking a timeout error
        mock_urlopen.side_effect = TimeoutError("Request timed out")
        
        check_url_status("https://example-timeout.com")
        
        output = mock_stdout.getvalue()
        self.assertIn("[!] Request timed out (10s limit).", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('urllib.request.urlopen')
    def test_generic_exception(self, mock_urlopen, mock_stdout):
        # Mocking a generic error during execution
        mock_urlopen.side_effect = Exception("Some weird error")
        
        check_url_status("https://example-weird.com")
        
        output = mock_stdout.getvalue()
        self.assertIn("[ERR] Unexpected error: Some weird error", output)

if __name__ == '__main__':
    unittest.main()
