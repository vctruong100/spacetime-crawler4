import unittest
from unittest.mock import patch, MagicMock
from helpers.robot_parser import can_fetch, respect_delay, get_rparser, user_agent, politeness

class TestRobotParser(unittest.TestCase):

    @patch('helpers.robot_parser.RobotFileParser')
    def test_get_rparser(self, mock_parser):
        """
        Tests that get_rparser correctly sets the URL for the robots.txt file and reads it.
        """
        url = 'http://example.com'
        mock_rp = MagicMock()  # Create a mock RobotFileParser instance
        mock_parser.return_value = mock_rp  # Set the return value of the RobotFileParser constructor to the mock instance

        result = get_rparser(url)  # Call the function being tested

        mock_rp.set_url.assert_called_once_with('http://example.com/robots.txt') 
        mock_rp.read.assert_called_once()  # Verify read was called to fetch the content
        self.assertEqual(result, mock_rp)  

    @patch('helpers.robot_parser.get_rparser')  
    def test_can_fetch(self, mock_get_parser):
        """
        Tests that can_fetch correctly uses the robot parser to determine if a URL can be fetched based on robots.txt rules.
        """
        url = 'http://example.com/page'
        mock_rp = MagicMock()  
        mock_get_parser.return_value = mock_rp 
        mock_rp.can_fetch.return_value = True  

        result = can_fetch(url)  # Call can_fetch with the test URL

        mock_get_parser.assert_called_once_with(url)  
        mock_rp.can_fetch.assert_called_once_with(user_agent, url)  # Check if can_fetch was called with correct parameters
        self.assertTrue(result) 

    @patch('helpers.robot_parser.get_rparser')
    @patch('time.sleep')
    def test_respect_delay(self, mock_sleep, mock_get_parser):
        """
        Tests that respect_delay fetches the crawl-delay from robots.txt and respects it by pausing the crawler appropriately.
        """
        url = 'http://example.com'
        mock_rp = MagicMock()  
        mock_get_parser.return_value = mock_rp
        mock_rp.crawl_delay.return_value = 1 

        respect_delay(url)  # Call respect_delay which should enforce the delay

        mock_get_parser.assert_called_once_with(url) 
        mock_sleep.assert_called_once_with(max(politeness, 1))

if __name__ == "__main__":
    unittest.main()
