"""
Module for processing scraped data using LLM models.

This module provides functionality to enhance and clean up job and company descriptions
using LLM models, either via the 'llm' Python library or directly through transformers.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import llm conditionally to avoid dependency issues when LLM is not enabled
try:
    import llm
    LLM_LIBRARY_AVAILABLE = True
    logger.info("llm library is available for processing")
except ImportError:
    LLM_LIBRARY_AVAILABLE = False
    logger.warning("llm library not found. Install with 'pip install llm llm-mlx' to use LLM processing.")

def _process_with_llm_library(content: str, prompt_template: str, model_id: str) -> str:
    """
    Process text using the llm Python library.
    
    Args:
        content: Text content to process
        prompt_template: Template for the prompt
        model_id: Model identifier (e.g., 'mlx-community/Mistral-7B-Instruct-v0.3-4bit')
        
    Returns:
        str: Processed content
    """
    try:
        # Format the prompt with the content
        prompt = prompt_template.format(content=content)
        
        # Get the model (llm library will handle downloading if needed)
        model = llm.get_model(model_id)
        logger.debug(f"Using LLM model: {model_id}")
        
        # Generate the response
        response = model.prompt(prompt)
        result = response.text().strip()
        
        logger.debug(f"LLM processing completed successfully ({len(result)} chars)")
        return result
    except Exception as e:
        logger.exception(f"Error processing with llm library: {e}")
        # Return original content on error
        return content

def _generate_job_description_prompt(content: str) -> str:
    """
    Create a prompt template for job description cleaning.
    """
    return """
    Below is a LinkedIn job description. 
    Please clean it up, remove HTML artifacts, and organize it into clear sections. 
    Focus on responsibilities, requirements, and benefits if present.
    Keep the original meaning intact.
    
    Original Job Description:
    {content}
    
    Cleaned Job Description:
    """.format(content=content)

def _generate_company_description_prompt(content: str) -> str:
    """
    Create a prompt template for company description cleaning.
    """
    return """
    Below is a LinkedIn company description. 
    Please clean it up, remove any HTML artifacts, and organize it into a clear, concise format.
    Keep the original meaning intact.
    
    Original Company Description:
    {content}
    
    Cleaned Company Description:
    """.format(content=content)

def process_data_with_llm(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process scraped data using an LLM to clean up and improve descriptions.
    
    Args:
        data: Dictionary containing scraped data
        config: Configuration dictionary with LLM settings
        
    Returns:
        Dict[str, Any]: Processed data dictionary
    """
    # Return original data if LLM is not enabled
    if not config.get('llm_enabled', False):
        logger.info("LLM processing is disabled. Returning original data.")
        return data
    
    # Check for llm library availability if using that method
    if config.get('llm_method') == 'llm-library' and not LLM_LIBRARY_AVAILABLE:
        logger.error("LLM processing method is set to 'llm-library' but the library is not installed")
        logger.warning("Falling back to original data without LLM processing")
        return data
    
    logger.info(f"Processing data with LLM using method: {config.get('llm_method')}")
    
    # Create a copy of the data to avoid modifying the original
    processed_data = data.copy()
    
    # Process job description if present
    if 'job_description' in processed_data and processed_data['job_description']:
        logger.info("Processing job description with LLM...")
        
        content = processed_data['job_description']
        prompt = _generate_job_description_prompt(content)
        
        if config.get('llm_method') == 'llm-library':
            processed_data['job_description'] = _process_with_llm_library(
                content, 
                prompt, 
                config.get('llm_model_id', 'mlx-community/Mistral-7B-Instruct-v0.3-4bit')
            )
        else:
            logger.warning(f"Unsupported LLM method: {config.get('llm_method')}. Using original content.")
    
    # Process company description if present
    if 'company_description' in processed_data and processed_data['company_description']:
        logger.info("Processing company description with LLM...")
        
        content = processed_data['company_description']
        prompt = _generate_company_description_prompt(content)
        
        if config.get('llm_method') == 'llm-library':
            processed_data['company_description'] = _process_with_llm_library(
                content, 
                prompt, 
                config.get('llm_model_id', 'mlx-community/Mistral-7B-Instruct-v0.3-4bit')
            )
        else:
            logger.warning(f"Unsupported LLM method: {config.get('llm_method')}. Using original content.")
    
    logger.info("LLM processing completed")
    return processed_data

# Example usage
if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Example data
    example_data = {
        "job_description": "We are looking for an experienced ML engineer to join our team...",
        "company_description": "TechCorp is a leading technology company in the field of...",
    }
    
    # Example config
    example_config = {
        "llm_enabled": True,
        "llm_method": "llm-library",
        "llm_model_id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
    }
    
    # Test processing
    print("Testing LLM processing (this would actually run if llm library is installed)...")
    # processed_data = process_data_with_llm(example_data, example_config)
    # print(processed_data) 