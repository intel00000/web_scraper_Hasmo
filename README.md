# Consulting Web Scraper

This project aims to develop a web scraper using Python. The scraper is designed to collect data from competitor websites, news articles, and market research reports. This data will provide valuable market insights, supporting competitive analysis and strategic decision-making.

## Table of Contents

- [Project Description](#project-description)
- [Setup Instructions](#setup-instructions)
  - [Virtual Environment Setup](#virtual-environment-setup)
  - [Installing Required Libraries](#installing-required-libraries)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Running the Spiders](#running-the-spiders)
- [Contact](#contact)

## Project Description

The Web Scraper systematically gathers data to help understand market trends, competitor strategies, and overall market dynamics. Key benefits include:

- **Market Insights**: Gaining a deeper understanding of current market trends to identify emerging patterns and industry shifts.
- **Competitive Analysis**: Collecting data on competitors' offerings, pricing, marketing campaigns, and market positioning.
- **Data-Driven Decisions**: Empowering the company to make informed and strategic business decisions based on the collected data.

### Focus Areas

1. **Competitor Websites**:

   - **McKinsey & Company**: [mckinsey.com](https://www.mckinsey.com)
   - **Boston Consulting Group**: [bcg.com](https://www.bcg.com)
   - **Deloitte**: [deloitte.com](https://www2.deloitte.com)
   - **Data to Scrape**: Service offerings, case studies, client testimonials, thought leadership articles, and market insights.

2. **Industry News and Reports**:

   - **Bloomberg**: [bloomberg.com](https://www.bloomberg.com)
   - **Reuters**: [reuters.com](https://www.reuters.com)
   - **Financial Times**: [ft.com](https://www.ft.com)
   - **Data to Scrape**: Latest news articles, market reports, financial analysis, and global economic trends.

3. **Market Research Portals**:
   - **Statista**: [statista.com](https://www.statista.com)
   - **MarketResearch.com**: [marketresearch.com](https://www.marketresearch.com)
   - **IBISWorld**: [ibisworld.com](https://www.ibisworld.com)
   - **Data to Scrape**: Market research reports, industry analysis, statistics, and trends.

## Setup Instructions

### Virtual Environment Setup

1. **Clone the Repository**:

   ```sh
   git clone https://github.com/intel00000/web_scraper_Hasmo.git
   cd web_scraper_Hasmo
   ```

2. **Create a Virtual Environment**:

   - **Windows**:
     ```sh
     python -m venv venv
     ```
   - **Linux & MacOS**:
     ```sh
     python3 -m venv venv
     ```

3. **Activate the Virtual Environment**:
   - **Windows**:
     ```sh
     .\\venv\\Scripts\\Activate.ps1
     ```
   - **Linux & MacOS**:
     ```sh
     source ./venv/bin/activate
     ```

### Installing Required Libraries

1. **Install the Required Packages**:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. **Running the Spiders**:

   - If you want to enable summary and Google sheet update, obtain the openai API key and Google service account json private key

     - Create a .env file in the main folder with content

     ```sh
     OPENAI_API_KEY={Your openai API key}
     ```

     - Download the Google service account private key as json, save to the main folder and rename to credentials.json
     - it should have a format like

     ```sh
      {
      "type": "service_account",
      "project_id": "",
      "private_key_id": "",
      "private_key": "",
      "client_email": "xxx@developer.gserviceaccount.com",
      "client_id": "",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "",
      "universe_domain": "googleapis.com"
      }
     ```

   - Navigate to the desired scraper directory:

     - For Deloitte: `cd deloitte_scraper`
     - For McKinsey: `cd mckinsey_scraper`

   - To list all available spiders, run:

     ```sh
     scrapy list
     ```

   - To run a specific spider, use:

     ```sh
     scrapy crawl spider_name
     ```

     Replace `spider_name` with the name of the spider you wish to run.

   - Alternatively, to run all spiders at once, use:
     ```sh
     python run_all_spiders.py
     ```

2. **Data Storage**:

   - The scraped data will be saved in the `data/raw/` directory as CSV or JSON files.

3. **Configuring the Scraper**:

   - Adjust configuration settings, such as target URLs, data points to extract, and output formats, in the `settings.py` file within the respective scraper directory (`deloitte_scraper` or `mckinsey_scraper`).

## Project Structure

```
web_scraper_Hasmo/
├── .env                             # add your OPENAI_API_KEY here
├── .gitignore
├── credentials.json                 # Google GCP service account API
├── README.md                        # Documentation for the project
├── requirements.txt                 # List of required Python packages
│
├── data/                            # Scraped data
│   └── raw/                         # Subdirectory containing raw CSV and JSON data files
│
├── deloitte_scraper/                # Contains the Scrapy project for Deloitte data
│   ├── scrapy.cfg                   # Scrapy configuration file
│   └── deloitte_scraper/
│       ├── items.py                 # Scraped items structure
│       ├── middlewares.py           # Middlewares for Scrapy
│       ├── pipelines.py             # Pipeline for processing scraped data
│       ├── settings.py              # Scrapy settings
│       ├── spiders/                 # Spiders directory
│
├── mckinsey_scraper/                # Contains the Scrapy project for McKinsey data
│   ├── scrapy.cfg                   # Scrapy configuration file
│   └── mckinsey_scraper/
│       ├── items.py                 # Scraped items structure
│       ├── middlewares.py           # Middlewares for Scrapy
│       ├── pipelines.py             # Pipeline for processing scraped data
│       ├── settings.py              # Scrapy settings
│       ├── spiders/                 # Spiders directory
│
├── notebooks/
│   ├── bcg_capabilities.ipynb       # Notebook for scraping BCG capabilities
│   ├── bcg_industries.ipynb         # Notebook for scraping BCG industries
│   ├── bcg_search_results.ipynb     # Notebook for scraping BCG search
│   ├── helper_functions.py          # Helper functions adapted from Scrapy pipelines
│   └── scrapy.ipynb                 # Notebook for testing
│
└── scripts/                         # Directory containing testing scripts
    ├── google_sheet_testing.py      # Google Sheets pipeline
    ├── openai_testing.py            # OpenAI API pipeline
    └── sample_input.json            # Sample input JSON file for testing
    └── sample_output_with_summaries.json  # Sample output JSON with generated summaries
```

- **data/**: Directory where the scraped data is saved.
- **venv/**: Virtual environment directory.
- **config.py**: Configuration file for the scraper settings.
- **requirements.txt**: List of required Python packages.
- **scraper.py**: Main script for scraping data.
- **README.md**: Project documentation.

## Contact

For any issues, questions, or contributions, please open an issue or submit a pull request on GitHub.
