"""
HubSpot mapping module.

This module defines how scraped data fields map to HubSpot API fields.
"""

# Standard properties for a HubSpot Company
COMPANY_FIELD_MAPPING = {
    # HubSpot field name: Source data field name
    "name": "company_name",
    "description": "company_description",
    "website": "company_website",
    "industry": "company_industry",
    "linkedin_company_page": "company_url",
    "city": "company_location_city",
    "state": "company_location_state",
    "country": "company_location_country",
    "size": "company_size",
    "founded_year": "company_founded",
    "about_us": "company_about",
    # Add more mappings as needed
}

# Standard properties for a HubSpot Deal
DEAL_FIELD_MAPPING = {
    # HubSpot field name: Source data field name
    "dealname": "job_title",
    "description": "job_description",
    "linkedin_job_url": "job_url",
    "job_function": "job_function",
    "employment_type": "job_employment_type",
    "experience_level": "job_experience_level", 
    "location": "job_location",
    "salary_range": "job_salary",
    "application_deadline": "job_deadline",
    "date_posted": "job_posted_date",
    # Add more mappings as needed
}

def get_company_properties(data, defaults=None):
    """
    Maps scraped company data to HubSpot company properties.
    
    Args:
        data: Dictionary containing scraped data
        defaults: Optional dictionary containing default values
        
    Returns:
        Dict: Properties formatted for HubSpot API
    """
    defaults = defaults or {}
    company_properties = {}
    
    # Map standard fields from the data using the mapping
    for hubspot_field, source_field in COMPANY_FIELD_MAPPING.items():
        if source_field in data and data[source_field]:
            company_properties[hubspot_field] = data[source_field]
    
    # Add any additional default properties with 'company_' prefix from the defaults
    for key, value in defaults.items():
        if key.startswith('company_') and value:
            # Remove 'company_' prefix for HubSpot API
            hubspot_field = key[8:]
            # Only set if not already set from scraped data
            if hubspot_field not in company_properties:
                company_properties[hubspot_field] = value
    
    # Essential fields that need to be present - use defaults or placeholders
    if 'name' not in company_properties and 'company_name' in data:
        company_properties['name'] = data['company_name']
    
    return company_properties

def get_deal_properties(data, defaults=None):
    """
    Maps scraped job data to HubSpot deal properties.
    
    Args:
        data: Dictionary containing scraped data
        defaults: Optional dictionary containing default values
        
    Returns:
        Dict: Properties formatted for HubSpot API
    """
    defaults = defaults or {}
    deal_properties = {}
    
    # Map standard fields from the data using the mapping
    for hubspot_field, source_field in DEAL_FIELD_MAPPING.items():
        if source_field in data and data[source_field]:
            deal_properties[hubspot_field] = data[source_field]
    
    # Set required HubSpot deal fields from defaults
    if defaults.get('deal_stage_id'):
        deal_properties['dealstage'] = defaults['deal_stage_id']
    
    if defaults.get('deal_pipeline_id'):
        deal_properties['pipeline'] = defaults['deal_pipeline_id']
        
    if defaults.get('deal_owner_id'):
        deal_properties['hubspot_owner_id'] = defaults['deal_owner_id']
    
    # Add any additional default properties with 'deal_' prefix from the defaults
    for key, value in defaults.items():
        if key.startswith('deal_') and key not in ['deal_stage_id', 'deal_pipeline_id', 'deal_owner_id'] and value:
            # Remove 'deal_' prefix for HubSpot API
            hubspot_field = key[5:]
            # Only set if not already set from scraped data
            if hubspot_field not in deal_properties:
                deal_properties[hubspot_field] = value
    
    # Create a default deal name if none exists
    if 'dealname' not in deal_properties:
        company_name = data.get('company_name', 'Unknown Company')
        job_title = data.get('job_title', 'Unknown Position')
        deal_properties['dealname'] = f"{job_title} at {company_name}"
    
    return deal_properties 