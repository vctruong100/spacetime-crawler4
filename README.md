# Web Crawler Project

## Introduction
This project involves the implementation and operation of a Web crawler designed to navigate specific domains and gather data about web pages. The main objective is to extract meaningful information from targeted URLs and analyze various metrics such as unique page counts, word frequencies, and subdomain exploration within the specified domains. This crawler is particularly tailored to efficiently manage web crawling while adhering to operational constraints and politeness policies. It is specifically configured to operate within the ICS server, requiring a connection to the UCI network or a UCI VPN. Users have the flexibility to modify seed URLs (in config.ini) to crawl websites outside the ICS server as needed.

## Features
- **Unique Page Detection**: Counts and identifies unique pages by URL, ignoring URL fragments.
- **Content Analysis**: Identifies the longest page by word count and analyzes common word frequencies excluding English stop words.
- **Subdomain Mapping**: Catalogues subdomains within the `ics.uci.edu` domain and counts unique pages within each subdomain.
- **Data Collection**: Optional local storage of crawled pages for further analysis.
- **Politeness Compliance**: Honors crawl-delay directives and manages request frequencies to prevent server overload.

## Prerequisites and Installation
1. **Python Installation**: Ensure Python 3.8 or later is installed on your system.
    ```sh
    python --version
    ```
2. **Clone the Crawler Repository**: Fork or clone the crawler code from the provided GitHub repository.
    ```sh
    git clone [repository link]
    ```
3. **Install Dependencies**: Navigate to the project directory and install required Python packages.
    ```sh
    pip install -r requirements.txt
    ```

## Running the Crawler
1. **Start the Crawler**: Execute the crawler script from within the project directory.
    ```sh
    python crawler.py
    ```
   Note: This crawler is designed to run on the ICS server which requires either a UCI network connection or a VPN if accessing from outside campus. However, users can change the seed URLs in the configuration to target different domains if desired.

## Resources
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [lxml Documentation](https://lxml.de/)
- [HTTP Status Codes Overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

