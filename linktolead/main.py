"""
Main entry point for the linktolead CLI tool.

This module provides the main functionality for the linktolead tool, which
extracts job and company information from LinkedIn PDFs, processes it, and sends it to HubSpot.
"""

import json
import logging
import os
import sys
import argparse
from typing import Dict, Any, Optional

from linktolead import config, llm_processor, hubspot
from linktolead.pdf_parser import LinkedInPDFParser
from linktolead.scraper import LinkedInScraper

# Set up logging
logger = logging.getLogger(__name__)

def main() -> int:
    """Main entry point for the linktolead tool.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    # Initialize variables to manage resources
    pdf_parser = None
    linkedin_scraper = None
    scraped_data = None
    processed_data = None
    
    try:
        # Load configuration
        cfg = config.load_config()
        if not cfg:
            logger.error("Failed to load configuration")
            return 1
        
        # Configure logging based on config
        log_level = getattr(logging, cfg.get('log_level', 'INFO').upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Parse command-line arguments
        parser = argparse.ArgumentParser(description='Extract LinkedIn job and company data from PDFs')
        parser.add_argument('--job-pdf', type=str, help='Path to the LinkedIn job PDF file')
        parser.add_argument('--company-pdf', type=str, help='Path to the LinkedIn company PDF file')
        parser.add_argument('--job-url', type=str, help='LinkedIn job URL to scrape (alternative to PDF)')
        parser.add_argument('--company-url', type=str, help='LinkedIn company URL to scrape (alternative to PDF)')
        parser.add_argument('--no-headless', action='store_true', help='Run browser with UI visible (for URL scraping)')
        parser.add_argument('--output', type=str, help='Path to output JSON file (optional)')
        parser.add_argument('--no-hubspot', action='store_true', help='Do not send data to HubSpot')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        parser.add_argument('--llm', action='store_true', help='Force enable LLM processing')
        parser.add_argument('--no-llm', action='store_true', help='Force disable LLM processing')
        
        args = parser.parse_args()
        
        # If --debug flag is set, override the log level
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Validate input arguments - need either PDFs or URLs
        use_pdfs = args.job_pdf or args.company_pdf
        use_urls = args.job_url or args.company_url
        
        if not use_pdfs and not use_urls:
            logger.error("Need either PDF files (--job-pdf/--company-pdf) or URLs (--job-url/--company-url)")
            parser.print_help()
            return 1
        
        # Log the configuration
        logger.info("Starting linktolead with:")
        if args.job_pdf:
            logger.info(f"  Job PDF: {args.job_pdf}")
        if args.company_pdf:
            logger.info(f"  Company PDF: {args.company_pdf}")
        if args.job_url:
            logger.info(f"  Job URL: {args.job_url}")
        if args.company_url:
            logger.info(f"  Company URL: {args.company_url}")
        if args.output:
            logger.info(f"  Output file: {args.output}")
        if args.no_hubspot:
            logger.info("  HubSpot integration disabled")
        
        # Override headless mode if specified
        if args.no_headless:
            logger.info("  Browser UI will be visible (non-headless mode)")
            cfg['headless'] = False
        
        # Override LLM settings if specified
        if args.llm:
            logger.info("  Forcing LLM processing ON (via command line)")
            cfg['llm_enabled'] = True
        elif args.no_llm:
            logger.info("  Forcing LLM processing OFF (via command line)")
            cfg['llm_enabled'] = False
        
        # Get data either from PDFs or by scraping
        if use_pdfs:
            # Parse PDFs
            logger.info("Initializing LinkedIn PDF parser")
            pdf_parser = LinkedInPDFParser()
            
            # Parse job PDF if provided
            job_data = {}
            if args.job_pdf:
                logger.info(f"Parsing job PDF: {args.job_pdf}")
                job_data = pdf_parser.parse_job_pdf(args.job_pdf)
            
            # Parse company PDF if provided
            company_data = {}
            if args.company_pdf:
                logger.info(f"Parsing company PDF: {args.company_pdf}")
                company_data = pdf_parser.parse_company_pdf(args.company_pdf)
            
            # Combine the data
            if job_data or company_data:
                scraped_data = pdf_parser.combine_data(job_data, company_data)
                logger.info(f"Successfully parsed PDFs")
            else:
                logger.error("No data extracted from PDFs")
                return 1
        
        else:  # use_urls
            # Validate LinkedIn credentials for scraping
            linkedin_email = cfg.get('linkedin_email')
            linkedin_password = cfg.get('linkedin_password')
            if not linkedin_email or not linkedin_password:
                logger.error("LinkedIn credentials not found in configuration")
                return 1
            
            # Initialize the LinkedIn scraper
            logger.info("Initializing LinkedIn scraper")
            linkedin_scraper = LinkedInScraper(
                email=linkedin_email,
                password=linkedin_password,
                state_path=cfg.get('playwright_state_path', 'playwright_state.json'),
                headless=cfg.get('headless', True)
            )
            
            try:
                # Scrape the LinkedIn pages
                logger.info("Logging in to LinkedIn and scraping data...")
                linkedin_scraper.ensure_logged_in()
                scraped_data = linkedin_scraper.scrape_all(args.job_url, args.company_url)
                
                if not scraped_data:
                    logger.error("Failed to scrape data from LinkedIn")
                    return 1
                
                logger.info(f"Successfully scraped data from LinkedIn")
            except Exception as e:
                logger.exception(f"Error during LinkedIn scraping: {e}")
                return 1
        
        # Process the data using LLM if configured
        if cfg.get('llm_enabled', False):
            logger.info("Processing data with LLM...")
            processed_data = llm_processor.process_data_with_llm(scraped_data, cfg)
            if not processed_data:
                logger.error("Failed to process data with LLM")
                return 1
            logger.info("Successfully processed data with LLM")
        else:
            logger.info("LLM processing disabled. Using raw scraped data.")
            processed_data = scraped_data
        
        # Format data for HubSpot
        hubspot_data = {}
        if 'formatter' in sys.modules:
            from linktolead import formatter
            hubspot_data = formatter.format_for_hubspot(processed_data, cfg.get('defaults', {}))
        else:
            hubspot_data = hubspot.format_for_hubspot(processed_data)
        
        # Write output to file if specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(hubspot_data, f, indent=2)
            logger.info(f"Output written to {args.output}")
        
        # Send data to HubSpot if not disabled
        if not args.no_hubspot:
            hubspot_api_key = cfg.get('hubspot_api_key') or os.environ.get('HUBSPOT_API_KEY')
            if not hubspot_api_key:
                logger.error("HubSpot API key not found, cannot send data to HubSpot")
                return 1
            
            # Show data and ask for confirmation
            print("\nData to be sent to HubSpot:")
            print(json.dumps(hubspot_data, indent=2))
            confirmation = input("\nSend this data to HubSpot? (y/N): ")
            
            if confirmation.lower() in ['y', 'yes']:
                logger.info("Sending data to HubSpot...")
                
                # Check if we're using the new HubSpotClient class
                if hasattr(hubspot, 'HubSpotClient'):
                    # New API client approach
                    hubspot_client = hubspot.HubSpotClient(hubspot_api_key)
                    
                    if not hubspot_client.test_connection():
                        logger.error("Failed to connect to HubSpot API")
                        return 1
                    
                    company_id, deal_id = hubspot_client.create_deal_with_company(hubspot_data)
                    if company_id and deal_id:
                        logger.info(f"Successfully created company ({company_id}) and deal ({deal_id}) in HubSpot")
                        print(f"✅ Successfully created company ({company_id}) and deal ({deal_id}) in HubSpot!")
                    else:
                        logger.error("Failed to create company and deal in HubSpot")
                        return 1
                else:
                    # Legacy approach
                    hubspot_response = hubspot.send_to_hubspot(hubspot_data, hubspot_api_key)
                    if hubspot_response:
                        logger.info("Successfully sent data to HubSpot")
                        print("Successfully sent data to HubSpot!")
                    else:
                        logger.error("Failed to send data to HubSpot")
                        return 1
            else:
                logger.info("User chose not to send data to HubSpot")
                print("Data not sent to HubSpot.")
        
        logger.info("linktolead completed successfully")
        return 0
    
    except KeyboardInterrupt:
        logger.info("Operation canceled by user")
        print("\nOperation canceled by user.")
        return 1
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    
    finally:
        # Ensure the LinkedIn scraper is properly closed, regardless of success or failure
        if linkedin_scraper is not None:
            try:
                logger.info("Closing LinkedIn scraper")
                linkedin_scraper.close()
            except Exception as e:
                logger.error(f"Error closing LinkedIn scraper: {e}")


if __name__ == '__main__':
    sys.exit(main()) 