# LinkToLead HubSpot Tool

A CLI tool to scrape LinkedIn job and company pages and create corresponding Deal and Company entries in HubSpot.

## Features

* **LinkedIn Scraping**: Extracts job and company details from LinkedIn.
* **Data Processing**: Structures data for HubSpot Deal and Company objects.
  * Optional LLM Processing: Uses LLM models via the `llm` Python library to clean and enhance scraped data.
* **Terminal Preview**: Provides a clear preview of data before sending to HubSpot.
* **Inline Editing**: Allows editing data directly before submission if needed.
* **HubSpot Integration**: Creates Company and Deal records with proper associations.
* **Configurable Defaults**: Loads default field values from a local config file.
* **Modular Design**: Supports potential future expansion to other sources and destinations.

## Quick Start

### Prerequisites

* macOS (Linux may work but is not officially supported)
* Python 3.8 or higher
* A HubSpot account with API access
* A LinkedIn account

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd linktolead
   ```

2. **Run the setup script:**

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   This script will:
   * Install uv if not already installed
   * Install dependencies
   * Install Playwright browsers
   * Create template config files 
   * Install the package in development mode
   * Optionally install LLM dependencies

3. **Edit your credentials:**
   
   Update your `.env` file with:
   ```
   HUBSPOT_API_KEY=your_hubspot_api_key
   LINKEDIN_EMAIL=your_linkedin_email
   LINKEDIN_PASSWORD=your_linkedin_password
   ```

4. **Configure your settings:**
   
   Review and edit `.linktolead_config.yaml` to customize default settings.

5. **Run the tool:**
   ```bash
   linktolead "https://www.linkedin.com/jobs/view/1234567890/" "https://www.linkedin.com/company/example-corp/"
   ```

## Workflow

1. **Input**: Provide LinkedIn job and company URLs.
2. **Authentication**: Tool authenticates with LinkedIn (using stored session if available).
3. **Scraping**: Extracts relevant job and company details from LinkedIn.
4. **Processing**: 
   * If LLM enabled: Processes data with LLM model to clean and enhance it.
   * Otherwise: Uses raw scraped data.
5. **Formatting**: Structures data for HubSpot API.
6. **Preview**: Displays structured data in terminal.
7. **Confirmation**: 
   * If approved (Y): Sends data to HubSpot.
   * If rejected (n): Opens data in text editor for changes, then re-prompts for approval.
8. **API Submission**: Creates Company and Deal objects in HubSpot with proper association.
9. **Confirmation**: Displays success message with created object IDs.

## Detailed Configuration

### Environment Variables (.env)

```env
# HubSpot API Key (required)
HUBSPOT_API_KEY=your_hubspot_api_key

# LinkedIn Credentials (required for scraping)
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password

# Path to Playwright state file (optional)
PLAYWRIGHT_STATE_PATH=path/to/playwright_state.json
```

### About the Playwright State File

The Playwright state file saves your LinkedIn authentication session information. This allows the tool to:

1. Skip the full login process on subsequent runs
2. Avoid LinkedIn's security triggers from repeated logins
3. Work around potential CAPTCHA challenges

By default, it's saved as `playwright_state.json` in the project directory. You can specify a custom location using the `PLAYWRIGHT_STATE_PATH` environment variable. If you encounter login issues, try deleting this file to force a fresh login.

### Configuration File (.linktolead_config.yaml)

```yaml
# HubSpot Deal Settings
default_deal_owner_id: "12345"
default_deal_stage_id: "appointmentscheduled" 
default_deal_pipeline_id: "default"

# Browser Settings
headless: true  # Run browser without UI (default)

# LLM Processing Settings
llm_enabled: false
llm_method: "llm-library"
llm_model_id: "mlx-community/Mistral-7B-Instruct-v0.3-4bit"

# Platform Configuration
platform:
  source:
    type: "linkedin"
  destination:
    type: "hubspot"
    api_version: "v3"
```

## Advanced Usage

### LLM Integration

To enable LLM-based data processing:

1. **Install LLM dependencies:**
   ```bash
   uv pip install -e ".[llm]"
   ```

2. **Update your configuration:**
   ```yaml
   llm_enabled: true
   llm_method: "llm-library"
   llm_model_id: "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
   ```

   This uses the [llm](https://llm.datasette.io/) Python library with the [llm-mlx](https://github.com/simonw/llm-mlx) plugin for Mac-native model execution.

3. **Run with LLM processing:**
   ```bash
   linktolead --llm "https://www.linkedin.com/jobs/view/..." "https://www.linkedin.com/company/..."
   ```

### Command Line Options

```
usage: linktolead [-h] [--no-headless] [--debug] [--llm] [--no-llm] job_url company_url

Scrape LinkedIn Job and Company pages and send data to HubSpot.

positional arguments:
  job_url         Full URL of the LinkedIn job posting.
  company_url     Full URL of the LinkedIn company page.

optional arguments:
  -h, --help      show this help message and exit
  --no-headless   Run browser with UI visible (default is headless)
  --debug         Enable debug logging
  --llm           Force enable LLM processing (overrides config)
  --no-llm        Force disable LLM processing (overrides config)
```

## Development

* This project uses `uv` for dependency management.
* Run the tool in development with: `uv run linktolead/main.py <job_url> <company_url>`
* Add dependencies with: `uv add package_name`
* Update dependencies with: `uv sync`

## Future Plans

### Data Sources

Future versions could support scraping job and company data from multiple sources:

* Indeed.com job postings
* ZipRecruiter job postings
* AngelList/Wellfound job postings
* Company websites
* Direct API integrations with job boards

Implementation would involve:
* Creating new scraper modules for each source
* Adding source-specific selectors and extraction logic
* Standardizing the data format across sources
* Updating the `platform.source.type` config to support the new sources

### Destinations

Future versions could support sending data to multiple CRM or ATS systems:

* Salesforce CRM
* Zoho CRM
* Greenhouse ATS
* Lever ATS
* Custom API endpoints

Implementation would involve:
* Creating new API client modules for each destination
* Standardizing the data format
* Updating the `platform.destination.type` config to support new destinations

### LLM Improvements

Future enhancements to the LLM integration could include:

* Support for more models via llm plugins
* Advanced data extraction features
* Sentiment analysis of job descriptions
* Salary estimation when not explicitly stated
* Skill and experience level classification

## Logging

Logs are stored in `app.log` in the project directory.

## Troubleshooting

* **LinkedIn Authentication Issues**: Delete `playwright_state.json` and run again to force a new login.
* **HubSpot API Errors**: Verify your API key has proper scopes (deals, companies).
* **LLM Integration Errors**: Ensure you have the required dependencies installed with `pip install -e ".[llm]"`.

## License

MIT
