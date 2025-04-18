"""
Configuration handling module.

Loads configuration from environment variables and YAML files.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional

# Setup basic logging for config loading issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define project root path (used throughout the module)
PROJECT_ROOT = Path(__file__).parent.parent  # Assumes config.py is in linktolead/

def load_config() -> Dict[str, Any]:
    """
    Loads configuration settings from environment variables and YAML file.

    Priority for config files:
    1. Environment variables (takes precedence)
    2. .linktolead_config.yaml in project root
    
    Returns:
        Dict[str, Any]: Configuration dictionary with all settings
    """
    # Try to load from .env file if it exists
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        logger.info(f"Loading configuration from .env file: {env_path}")
        load_dotenv(env_path)
    else:
        logger.info("No .env file found, using environment variables")
    
    # Define configuration with defaults
    config = {
        # API keys
        'openai_api_key': os.environ.get('OPENAI_API_KEY'),
        'hubspot_api_key': os.environ.get('HUBSPOT_API_KEY'),
        
        # Logging
        'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
        
        # LLM settings
        'llm_model': os.environ.get('LLM_MODEL', 'gpt-4-turbo'),
        'llm_temperature': float(os.environ.get('LLM_TEMPERATURE', '0.1')),
        'llm_max_tokens': int(os.environ.get('LLM_MAX_TOKENS', '4000')),
        
        # HubSpot settings
        'hubspot_api_version': os.environ.get('HUBSPOT_API_VERSION', 'v3'),
    }
    
    # Log config (excluding sensitive keys)
    safe_config = {k: v for k, v in config.items() if k not in ['openai_api_key', 'hubspot_api_key']}
    logger.debug(f"Loaded configuration: {safe_config}")
    
    # Check required keys and log warnings
    if not config['openai_api_key']:
        logger.warning("OpenAI API key not found in environment or .env file")
    
    if not config['hubspot_api_key']:
        logger.warning("HubSpot API key not found in environment or .env file")
    
    return config

# Example usage (for testing purposes)
    # Load environment variables from .env file
    dotenv_path = PROJECT_ROOT / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
        logger.info(f"Loaded environment variables from: {dotenv_path}")
    else:
        logger.info(f".env file not found at {dotenv_path}, relying on system environment variables.")

    # Load sensitive/required settings from environment variables
    config['hubspot_api_key'] = os.getenv('HUBSPOT_API_KEY')
    config['linkedin_email'] = os.getenv('LINKEDIN_EMAIL')
    config['linkedin_password'] = os.getenv('LINKEDIN_PASSWORD')
    
    # Default to project root for state file (keep all files in project directory)
    config['playwright_state_path'] = os.getenv(
        'PLAYWRIGHT_STATE_PATH', 
        str(PROJECT_ROOT / 'playwright_state.json')
    )

    # --- Load YAML configuration ---
    yaml_config = {}
    yaml_path = PROJECT_ROOT / '.linktolead_config.yaml'

    if yaml_path.exists():
        try:
            with open(yaml_path, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}  # Handle empty file
            logger.info(f"Loaded configuration from: {yaml_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file {yaml_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading config file {yaml_path}: {e}")
    else:
        logger.warning(f"Configuration file not found: {yaml_path}")
        logger.info("Creating default configuration file from template...")
        template_path = PROJECT_ROOT / '.linktolead_config.yaml.example'
        if template_path.exists():
            try:
                with open(template_path, 'r') as src, open(yaml_path, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"Created default configuration file: {yaml_path}")
                # Try to load the newly created file
                with open(yaml_path, 'r') as f:
                    yaml_config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Failed to create default configuration: {e}")
        else:
            logger.error(f"Configuration template not found: {template_path}")

    # --- Browser Settings ---
    # Headless mode (default to true)
    config['headless'] = yaml_config.get('headless', True)
    logger.info(f"Browser headless mode: {config['headless']}")

    # --- Platform configuration (source and destination) ---
    # Default platform settings
    config['platform'] = {
        'source': {
            'type': 'linkedin',  # Default source platform
        },
        'destination': {
            'type': 'hubspot',   # Default destination platform
            'api_version': 'v3'  # Default API version
        }
    }
    
    # Override with YAML settings if available
    if 'platform' in yaml_config:
        if 'source' in yaml_config['platform']:
            config['platform']['source'].update(yaml_config['platform']['source'])
        if 'destination' in yaml_config['platform']:
            config['platform']['destination'].update(yaml_config['platform']['destination'])
    
    # --- Load HubSpot defaults from config ---
    config['defaults'] = {
        'deal_owner_id': yaml_config.get('default_deal_owner_id', ''),
        'deal_stage_id': yaml_config.get('default_deal_stage_id', 'appointmentscheduled'),
        'deal_pipeline_id': yaml_config.get('default_deal_pipeline_id', 'default'),
    }
    
    # Add any additional custom properties from yaml_config with 'default_' prefix
    for key, value in yaml_config.items():
        if key.startswith('default_') and key not in ['default_deal_owner_id', 'default_deal_stage_id', 'default_deal_pipeline_id']:
            # Remove 'default_' prefix and add to defaults
            property_name = key[8:]  # Remove 'default_' prefix
            config['defaults'][property_name] = value
    
    logger.info(f"Loaded default HubSpot values: {config['defaults']}")
    
    # --- LLM Configuration ---
    # Default LLM settings (disabled by default)
    config['llm_enabled'] = yaml_config.get('llm_enabled', False)
    
    # LLM method and model ID
    config['llm_method'] = yaml_config.get('llm_method', 'llm-library')
    config['llm_model_id'] = yaml_config.get('llm_model_id', 'mlx-community/Mistral-7B-Instruct-v0.3-4bit')
    
    if config['llm_enabled']:
        logger.info(f"LLM processing is enabled with method: {config['llm_method']}, model: {config['llm_model_id']}")
    else:
        logger.info("LLM processing is disabled. Using direct scraped data.")

    # --- Validation ---
    # Check required environment variables
    required_env_vars = ['hubspot_api_key', 'linkedin_email', 'linkedin_password']
    missing_vars = [var for var in required_env_vars if not config.get(var)]
    if missing_vars:
        logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}. Please set them in your environment or a .env file.")

    # Check required configuration values
    if config['defaults']['deal_owner_id'] == '':
        logger.warning("HubSpot Deal Owner ID is not set. Please update your configuration file.")

    return config

# Example usage (for testing purposes)
if __name__ == "__main__":
    loaded_config = load_config()
    print("Loaded Configuration:")
    import json
    print(json.dumps(loaded_config, indent=2)) 