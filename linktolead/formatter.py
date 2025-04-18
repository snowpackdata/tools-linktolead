"""
Data formatting module.

Formats scraped data for the destination platform (e.g., HubSpot).
"""

import logging
from typing import Dict, Any

from .mappings import hubspot as hubspot_mapping

logger = logging.getLogger(__name__)

def format_for_hubspot(data: Dict[str, Any], defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Format scraped data for HubSpot API.
    
    Args:
        data: Dictionary containing scraped data
        defaults: Dictionary with default values from config
        
    Returns:
        Dict: Formatted data ready for HubSpot API
    """
    logger.info("Formatting data for HubSpot API")
    
    # Ensure we have defaults
    defaults = defaults or {}
    
    # Create the formatted output structure
    formatted_data = {
        "company": {
            "properties": {}
        },
        "deal": {
            "properties": {}
        }
    }
    
    # Map company data to HubSpot properties
    formatted_data["company"]["properties"] = hubspot_mapping.get_company_properties(data, defaults)
    
    # Map deal data to HubSpot properties
    formatted_data["deal"]["properties"] = hubspot_mapping.get_deal_properties(data, defaults)
    
    # Log the mapped field counts
    logger.info(f"Mapped {len(formatted_data['company']['properties'])} company fields and {len(formatted_data['deal']['properties'])} deal fields")
    
    return formatted_data

# Future: LLM integration placeholder
class LLMDataFormatter(DataFormatter):
    """
    Enhanced formatter that uses a local LLM to extract and structure data.
    This is a placeholder for future implementation.
    """
    
    def __init__(self, defaults: Dict[str, Any] = None, llm_config: Dict[str, Any] = None):
        """
        Initialize with LLM configuration.
        
        Args:
            defaults: Dictionary of default values for HubSpot fields.
            llm_config: Configuration for the local LLM.
        """
        super().__init__(defaults)
        self.llm_config = llm_config or {}
        logger.info("LLMDataFormatter initialized (placeholder).")
    
    def format_for_hubspot(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format data using LLM-enhanced extraction.
        
        Args:
            scraped_data: Raw scraped data.
            
        Returns:
            Formatted data for HubSpot.
        """
        logger.info("LLM-based formatting would happen here (placeholder).")
        # For now, just use the basic formatter
        return super().format_for_hubspot(scraped_data)

# Example usage
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Example scraped data
    example_data = {
        "job": {
            "title": "Senior Software Engineer",
            "location": "San Francisco, CA (Remote)",
            "description": "We're looking for a skilled developer... Salary range: $120k - $150k depending on experience."
        },
        "company": {
            "name": "Example Tech",
            "website": "https://example.com",
            "industry": "Software Development",
            "size": "51-200 employees",
            "headquarters": "San Francisco, CA"
        }
    }
    
    # Example defaults
    example_defaults = {
        "deal_owner_id": "12345",
        "deal_stage_id": "appointmentscheduled",
        "deal_pipeline_id": "default"
    }
    
    # Test formatting
    formatter = DataFormatter(example_defaults)
    formatted_data = formatter.format_for_hubspot(example_data)
    
    import json
    print("Formatted Data:")
    print(json.dumps(formatted_data, indent=2)) 