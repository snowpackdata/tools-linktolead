"""
HubSpot API client module.

Handles interactions with the HubSpot API for creating and updating objects.
"""

import logging
import requests
import json
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class HubSpotAPIError(Exception):
    """Exception for HubSpot API errors."""
    pass

class HubSpotClient:
    """Client for interacting with the HubSpot API."""
    
    def __init__(self, api_key: str, api_version: str = "v3"):
        """
        Initialize the HubSpot client.
        
        Args:
            api_key: HubSpot API key
            api_version: HubSpot API version to use (default: v3)
        """
        self.api_key = api_key
        self.api_version = api_version
        self.base_url = f"https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"HubSpot client initialized with API version {api_version}")
    
    def test_connection(self) -> bool:
        """
        Test the connection to the HubSpot API.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            # Make a simple request to the status endpoint
            url = f"{self.base_url}/crm/{self.api_version}/objects/deals"
            params = {"limit": 1}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                logger.info("HubSpot API connection test successful")
                return True
            else:
                logger.error(f"HubSpot API connection failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.exception(f"Error testing HubSpot API connection: {e}")
            return False
    
    def create_company(self, company_data: Dict[str, Any]) -> str:
        """
        Create a company in HubSpot.
        
        Args:
            company_data: Company data formatted for HubSpot API
            
        Returns:
            str: ID of the created company
            
        Raises:
            HubSpotAPIError: If the API call fails
        """
        url = f"{self.base_url}/crm/{self.api_version}/objects/companies"
        
        try:
            logger.info(f"Creating company: {company_data.get('properties', {}).get('name', 'Unknown')}")
            response = requests.post(url, headers=self.headers, json=company_data)
            
            if response.status_code in (200, 201):
                company_id = response.json().get("id")
                logger.info(f"Company created successfully with ID: {company_id}")
                return company_id
            else:
                error_msg = f"Failed to create company. Status: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                raise HubSpotAPIError(error_msg)
        except requests.RequestException as e:
            error_msg = f"Request error creating company: {e}"
            logger.exception(error_msg)
            raise HubSpotAPIError(error_msg)
    
    def create_deal(self, deal_data: Dict[str, Any], company_id: Optional[str] = None) -> str:
        """
        Create a deal in HubSpot.
        
        Args:
            deal_data: Deal data formatted for HubSpot API
            company_id: Optional ID of the company to associate with the deal
            
        Returns:
            str: ID of the created deal
            
        Raises:
            HubSpotAPIError: If the API call fails
        """
        url = f"{self.base_url}/crm/{self.api_version}/objects/deals"
        
        # Prepare deal data
        deal_payload = deal_data.copy()
        
        # Add company association if provided
        if company_id:
            # Create an associations array if it doesn't exist
            if "associations" not in deal_payload:
                deal_payload["associations"] = []
            
            # Add the company association
            deal_payload["associations"].append({
                "to": {"id": company_id},
                "types": [{
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": 1  # Deal to Company association type
                }]
            })
        
        try:
            logger.info(f"Creating deal: {deal_payload.get('properties', {}).get('dealname', 'Unknown')}")
            response = requests.post(url, headers=self.headers, json=deal_payload)
            
            if response.status_code in (200, 201):
                deal_id = response.json().get("id")
                logger.info(f"Deal created successfully with ID: {deal_id}")
                return deal_id
            else:
                error_msg = f"Failed to create deal. Status: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                raise HubSpotAPIError(error_msg)
        except requests.RequestException as e:
            error_msg = f"Request error creating deal: {e}"
            logger.exception(error_msg)
            raise HubSpotAPIError(error_msg)
    
    def create_deal_with_company(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Create both a company and a deal in HubSpot with proper association.
        
        Args:
            data: Dictionary containing both company and deal data
            
        Returns:
            Tuple[str, str]: Tuple of (company_id, deal_id)
            
        Raises:
            HubSpotAPIError: If any API call fails
        """
        try:
            # First create the company
            company_data = data.get("company", {})
            company_id = self.create_company(company_data)
            
            # Then create the deal and associate it with the company
            deal_data = data.get("deal", {})
            deal_id = self.create_deal(deal_data, company_id)
            
            logger.info(f"Successfully created and associated company {company_id} and deal {deal_id}")
            return company_id, deal_id
        except HubSpotAPIError as e:
            # Re-raise the exception - the caller will handle it
            raise
        except Exception as e:
            error_msg = f"Unexpected error creating deal with company: {e}"
            logger.exception(error_msg)
            raise HubSpotAPIError(error_msg)

# Example usage
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Load API key from environment for testing
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        print("Error: HUBSPOT_API_KEY environment variable not set.")
        exit(1)
    
    # Create a client and test connection
    client = HubSpotClient(api_key)
    if client.test_connection():
        print("✅ Connection to HubSpot API successful.")
    else:
        print("❌ Failed to connect to HubSpot API.")
        exit(1)
    
    # Example data
    # Note: This is just for example purposes - don't run this in production as it will create real objects
    if False:  # Safety check to prevent accidental creation
        example_data = {
            "company": {
                "properties": {
                    "name": "Example Test Company (API Demo)",
                    "industry": "Technology",
                    "website": "https://example.com"
                }
            },
            "deal": {
                "properties": {
                    "dealname": "Test Deal from API Demo",
                    "pipeline": "default",
                    "dealstage": "appointmentscheduled"
                },
                "associations": [
                    {
                        "to": {"id": "{COMPANY_ID}"}, 
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 1
                            }
                        ]
                    }
                ]
            }
        }
        
        # Create the objects
        try:
            company_id, deal_id = client.create_deal_with_company(example_data)
            print(f"✅ Created company ({company_id}) and deal ({deal_id}).")
        except HubSpotAPIError as e:
            print(f"❌ Error: {e}") 