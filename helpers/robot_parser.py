from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import configparser

def read_config(config_file="config.ini"):
    """
    Reads the configuration file and returns the user agent and politeness delay.
    
    :param config_file str: The configuration file
    :return: The user agent and politeness delay
    :rtype: tuple
    
    """

    config = configparser.ConfigParser()
    config.read(config_file)

    user_agent = config['Agent']['USERAGENT']
    politeness = float(config['Politeness']['POLITENESS'])

    return user_agent, politeness



def get_rparser(url):
    """
    Returns a RobotFileParser object for the given URL.
    
    :param url str: The URL
    :return: The RobotFileParser object
    :rtype: RobotFileParser

    """
    # Extract the network location part of the URL
    parsed_url = urlparse(url)

    # Create a RobotFileParser object
    rparser = RobotFileParser()
    rparser.set_url(f"http://{parsed_url.scheme}://{parsed_url.netloc}/robots.txt")
    rparser.read()

    return rparser

