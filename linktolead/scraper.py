"""
Playwright scraping module for LinkedIn.

Handles browser automation, login, and data extraction from job and company pages.
"""

import logging
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Page, BrowserContext

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """Manages Playwright browser instance and scraping logic for LinkedIn."""

    LOGIN_URL = "https://www.linkedin.com/login"
    FEED_URL = "https://www.linkedin.com/feed/"

    def __init__(self, email: str, password: str, state_path: str = "playwright_state.json", headless: bool = False):
        """
        Initializes the scraper.

        Args:
            email (str): LinkedIn login email.
            password (str): LinkedIn login password.
            state_path (str): Path to save/load browser state (cookies, local storage).
            headless (bool): Whether to run the browser in headless mode (without UI).
        """
        self.email = email
        self.password = password
        self.state_path = Path(state_path)
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        logger.info(f"LinkedInScraper initialized. State file: {self.state_path}, Headless: {self.headless}")

    def _launch_browser(self):
        """Launches Playwright browser and creates a context."""
        if not self.browser:
            logger.info("Launching Playwright browser...")
            self.playwright = sync_playwright().start()
            # Use Chromium by default, could make this configurable
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            logger.info(f"Browser launched (headless={self.headless}).")

        if not self.context:
            if self.state_path.exists():
                logger.info(f"Loading browser state from {self.state_path}")
                self.context = self.browser.new_context(storage_state=self.state_path)
            else:
                logger.info("No existing state file found. Creating new browser context.")
                self.context = self.browser.new_context()
            self.context.set_default_timeout(60000) # 60 seconds default timeout
            logger.info("Browser context created.")

        if not self.page:
            self.page = self.context.new_page()
            logger.info("New page created.")

    def _is_logged_in(self, page: Page) -> bool:
        """Checks if the user appears to be logged in."""
        try:
            # Look for a common element only present when logged in, e.g., profile picture link
            # This selector might need adjustment based on LinkedIn UI changes
            page.wait_for_selector('img[alt*="profile photo"], #profile-nav-item', timeout=5000) # Short timeout
            logger.info("User appears to be logged in (found profile element).")
            return True
        except PlaywrightTimeoutError:
            logger.info("User does not appear to be logged in (did not find profile element quickly).")
            return False

    def _perform_login(self, page: Page):
        """Handles the login process."""
        logger.info(f"Navigating to login page: {self.LOGIN_URL}")
        page.goto(self.LOGIN_URL, wait_until='domcontentloaded')

        try:
            logger.info("Attempting to fill login credentials...")
            page.fill("#username", self.email)
            page.fill("#password", self.password)
            page.click("button[type='submit']")
            logger.info("Credentials submitted.")

            # Wait for potential redirects, OTP/2FA prompts, or feed page load
            logger.info("Waiting for navigation after login submission (up to 90s for potential 2FA)...")
            # Check for common post-login elements OR error messages
            page.wait_for_url(f"**/{self.FEED_URL}**", timeout=90000) # Wait longer for manual 2FA
            # Alternative check if feed url isn't reliable:
            # page.wait_for_selector('#profile-nav-item, .feed-identity-module', timeout=90000)

            if self._is_logged_in(page):
                logger.info("Login successful. Saving state...")
                self.context.storage_state(path=self.state_path)
                logger.info(f"Browser state saved to {self.state_path}")
            else:
                logger.error("Login appeared to fail after submitting credentials (logged-in element not found).")
                # Check for common error messages (selectors might change)
                error_message = page.locator(".form__input--error, #error-for-password").text_content(timeout=1000)
                if error_message:
                    logger.error(f"LinkedIn error message detected: {error_message.strip()}")
                raise ConnectionError("LinkedIn login failed. Please check credentials or handle 2FA if prompted.")

        except PlaywrightTimeoutError:
            logger.error("Timeout waiting for page state after login submission. Manual intervention (like 2FA) might be required.")
            # Attempt to save state anyway, in case the user completed 2FA manually
            try:
                self.context.storage_state(path=self.state_path)
                logger.info(f"Browser state saved to {self.state_path} (post-timeout attempt)")
            except Exception as save_err:
                logger.error(f"Failed to save state after timeout: {save_err}")
            raise ConnectionRefusedError("Login timed out. Please run again and complete 2FA/Captcha if required in the browser window.")
        except Exception as e:
            logger.exception("An unexpected error occurred during login.")
            raise e # Re-raise the exception

    def ensure_logged_in(self):
        """Ensures the browser is launched and the user is logged in."""
        self._launch_browser()
        assert self.page is not None, "Page object should be initialized"

        try:
            # Go to a page that requires login to check status
            logger.info(f"Checking login status by navigating to feed: {self.FEED_URL}")
            self.page.goto(self.FEED_URL, wait_until='domcontentloaded')
            if self.page.url.startswith(self.LOGIN_URL) or not self._is_logged_in(self.page):
                logger.warning("Not logged in or redirected to login page. Attempting login.")
                self._perform_login(self.page)
            else:
                logger.info("Already logged in.")
                # Optionally refresh state file even if already logged in
                # self.context.storage_state(path=self.state_path)
        except Exception as e:
            logger.error(f"Error during login check/process: {e}")
            self.close()
            raise

    def scrape_job_page(self, job_url: str) -> dict:
        """Scrapes relevant details from a LinkedIn job page."""
        if not self.page:
            raise RuntimeError("Scraper not initialized or login failed. Call ensure_logged_in() first.")

        logger.info(f"Navigating to job page: {job_url}")
        try:
            self.page.goto(job_url, wait_until='domcontentloaded')
            # Add slight delay for dynamic content
            time.sleep(2)

            # --- Placeholder Selectors --- 
            # These WILL need refinement based on actual LinkedIn structure
            job_title_selector = ".job-title, .top-card-layout__title, h1"
            description_selector = ".job-details-jobs-unified-top-card__primary-description-container, #job-details, .jobs-description__content"
            location_selector = ".job-location, .top-card-layout__location"
            # company_name_selector = ".job-company-name, .top-card-layout__second-subline div a"

            logger.info("Extracting job details...")
            job_data = {
                "title": self.page.locator(job_title_selector).first.text_content(timeout=10000).strip(),
                "description": self.page.locator(description_selector).first.inner_html(timeout=5000), # Get inner HTML to preserve formatting
                "location": self.page.locator(location_selector).first.text_content(timeout=5000).strip(),
                # Add more fields as needed (e.g., employment type, seniority)
            }
            logger.info(f"Extracted job data: { {k: (v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v) for k, v in job_data.items()} }") # Log snippet
            return job_data

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout extracting job details from {job_url}: {e}. Selectors might be outdated.")
            # Capture screenshot for debugging
            screenshot_path = f"error_job_{int(time.time())}.png"
            self.page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to {screenshot_path}")
            raise ValueError(f"Could not find expected elements on job page {job_url}. Selectors may need updating.") from e
        except Exception as e:
            logger.exception(f"Error scraping job page {job_url}")
            raise

    def scrape_company_page(self, company_url: str) -> dict:
        """Scrapes relevant details from a LinkedIn company page."""
        if not self.page:
            raise RuntimeError("Scraper not initialized or login failed. Call ensure_logged_in() first.")

        # LinkedIn company URLs often lack '/about', navigate to the main page first
        # and then click the 'About' tab if necessary.
        about_url = company_url.rstrip('/') + '/about/'
        logger.info(f"Navigating to company about page: {about_url}")

        try:
            self.page.goto(about_url, wait_until='domcontentloaded')
            time.sleep(2) # Allow content to load

            # If redirection happened or 'about' isn't standard, try finding the about section
            if "/about" not in self.page.url:
                logger.warning(f"Direct navigation to {about_url} failed or redirected. Current URL: {self.page.url}. Attempting to find About info on main page.")
                # Look for elements typically found on the About page/section
                self.page.wait_for_selector('section[data-test-id="about-us__container"], dl', timeout=10000)

            logger.info("Extracting company details from About section...")

            # --- Placeholder Selectors for About Page --- 
            # These WILL need refinement based on actual LinkedIn structure
            # Selectors often target definition list <dl> items
            company_name_selector = "h1, .top-card-layout__title, .org-top-card-summary__title"
            website_selector = 'a[href*="://"][data-tracking-control-name="org-about-us-website-link"]', # More specific
            industry_selector = 'dd:has-text("Industry") + dt, div:has-text("Industry") + div' # Look for label + value
            size_selector = 'dd:has-text("Company size") + dt, div:has-text("Company size") + div a' # Often within a link
            # headquarters_selector = 'dd:has-text("Headquarters") + dt'

            # Helper to extract text based on a preceding label (common pattern)
            def get_detail_by_label(label_text: str) -> str | None:
                try:
                    # Try common patterns: div containing label then sibling div/span with value
                    value = self.page.locator(f'div:has(span:text-is("{label_text}")) + div').first.text_content(timeout=1000)
                    if value: return value.strip()
                    # Try definition list pattern: dt contains label, next dd has value
                    value = self.page.locator(f'dt:has-text("{label_text}") + dd').first.text_content(timeout=1000)
                    if value: return value.strip()
                    # Try another common pattern: div containing label then sibling p with value
                    value = self.page.locator(f'div:has-text("{label_text}") >> xpath=./following-sibling::p').first.text_content(timeout=1000)
                    if value: return value.strip()
                    # Fallback: Find label and get sibling text (less reliable)
                    value = self.page.locator(f':text("{label_text}") >> xpath=./following-sibling::*[1]').first.text_content(timeout=1000)
                    return value.strip() if value else None
                except PlaywrightTimeoutError:
                    logger.warning(f"Could not find value for company detail label: '{label_text}'")
                    return None
                except Exception as e:
                    logger.error(f"Error extracting detail for '{label_text}': {e}")
                    return None

            company_data = {
                "name": self.page.locator(company_name_selector).first.text_content(timeout=10000).strip(),
                "website": self.page.locator(website_selector).first.get_attribute('href', timeout=5000),
                "industry": get_detail_by_label("Industry"),
                "size": get_detail_by_label("Company size"),
                "headquarters": get_detail_by_label("Headquarters"),
                # Add more fields as needed (e.g., specialties, founded date)
            }

            # Clean up website URL if needed
            if company_data["website"] and "linkedin.com/redir/redirect?url=" in company_data["website"]:
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(company_data["website"])
                query_params = parse_qs(parsed_url.query)
                if 'url' in query_params:
                    company_data["website"] = query_params['url'][0]

            logger.info(f"Extracted company data: {company_data}")
            return company_data

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout extracting company details from {about_url}: {e}. Selectors might be outdated or page structure different.")
            screenshot_path = f"error_company_{int(time.time())}.png"
            self.page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to {screenshot_path}")
            raise ValueError(f"Could not find expected elements on company page {about_url}. Selectors may need updating.") from e
        except Exception as e:
            logger.exception(f"Error scraping company page {about_url}")
            raise

    def scrape_all(self, job_url: str, company_url: str) -> dict:
        """Scrapes both job and company pages."""
        logger.info("Starting combined scraping process...")
        try:
            self.ensure_logged_in()
            job_data = self.scrape_job_page(job_url)
            company_data = self.scrape_company_page(company_url)
            logger.info("Combined scraping completed successfully.")
            return {"job": job_data, "company": company_data}
        except Exception as e:
            logger.error(f"Scraping failed during combined process: {e}")
            # self.close() # Avoid closing here if called from main loop that handles closing
            raise # Re-raise to be caught by main loop

    def close(self):
        """Closes the Playwright browser and cleans up resources."""
        if self.page:
            try:
                self.page.close()
                logger.info("Playwright page closed.")
            except Exception as e:
                logger.warning(f"Error closing Playwright page: {e}")
            self.page = None
        if self.context:
            try:
                # Ensure state is saved before closing context if needed (handled in login)
                self.context.close()
                logger.info("Playwright context closed.")
            except Exception as e:
                logger.warning(f"Error closing Playwright context: {e}")
            self.context = None
        if self.browser:
            try:
                self.browser.close()
                logger.info("Playwright browser closed.")
            except Exception as e:
                logger.warning(f"Error closing Playwright browser: {e}")
            self.browser = None
        if self.playwright:
            try:
                self.playwright.stop()
                logger.info("Playwright instance stopped.")
            except Exception as e:
                logger.warning(f"Error stopping Playwright: {e}")
            self.playwright = None
        logger.info("Scraper cleanup finished.")

# Example Usage (for testing)
if __name__ == "__main__":
    print("Running LinkedIn Scraper example...")
    # Load credentials from .env file for testing
    from dotenv import load_dotenv
    load_dotenv()
    import os

    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        print("Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env file for testing.")
        exit(1)

    # Replace with actual URLs for testing
    test_job_url = "https://www.linkedin.com/jobs/view/3869994385/" # Example Job URL
    test_company_url = "https://www.linkedin.com/company/openai/" # Example Company URL

    scraper = LinkedInScraper(email, password)
    try:
        # scraper.ensure_logged_in()
        # print("Login check successful.")
        # job_info = scraper.scrape_job_page(test_job_url)
        # print("\n--- Job Info ---")
        # print(job_info)
        # company_info = scraper.scrape_company_page(test_company_url)
        # print("\n--- Company Info ---")
        # print(company_info)

        all_data = scraper.scrape_all(test_job_url, test_company_url)
        print("\n--- All Scraped Data ---")
        import json
        print(json.dumps(all_data, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()
        print("\nScraper closed.") 