"""
Terminal UI module.

Handles user interaction in the terminal, including data preview, confirmation, and editing.
"""

import tempfile
import os
import sys
import subprocess
import yaml
import json
import logging
from typing import Dict, Any, Optional, Tuple
import shutil

# Rich for prettier terminal output if available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich import print as rich_print
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Questionary for better interactive prompts if available
try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

logger = logging.getLogger(__name__)

def _format_nested_dict(data: Dict[str, Any], indent: int = 0) -> str:
    """Format a nested dictionary as a readable string with indentation."""
    lines = []
    indent_str = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(_format_nested_dict(value, indent + 1))
        else:
            # Truncate long string values for display
            if isinstance(value, str) and len(value) > 100:
                display_value = f"{value[:100]}... (truncated)"
            else:
                display_value = value
            lines.append(f"{indent_str}{key}: {display_value}")
    
    return "\n".join(lines)

def _format_hubspot_data(data: Dict[str, Any]) -> str:
    """Format HubSpot data for terminal display."""
    formatted_data = []
    
    # Deal info
    if "deal" in data:
        deal_props = data["deal"].get("properties", {})
        deal_section = ["Deal:"]
        for key, value in deal_props.items():
            # Skip very long values like full job descriptions
            if isinstance(value, str) and len(value) > 100 and key in ["job_description_raw"]:
                value = f"{value[:100]}... (truncated)"
            deal_section.append(f"  {key}: {value}")
        formatted_data.append("\n".join(deal_section))
    
    # Company info
    if "company" in data:
        company_props = data["company"].get("properties", {})
        company_section = ["Company:"]
        for key, value in company_props.items():
            company_section.append(f"  {key}: {value}")
        formatted_data.append("\n".join(company_section))
    
    return "\n\n".join(formatted_data)

def display_data_for_confirmation(data: Dict[str, Any]) -> None:
    """
    Display the structured data in the terminal for user confirmation.
    
    Args:
        data: Dictionary containing the HubSpot deal and company data.
    """
    logger.info("Displaying data for confirmation.")
    
    # Use Rich library if available for better formatting
    if RICH_AVAILABLE:
        console = Console()
        
        deal_yaml = yaml.dump(data["deal"]["properties"], sort_keys=False, default_flow_style=False)
        company_yaml = yaml.dump(data["company"]["properties"], sort_keys=False, default_flow_style=False)
        
        console.print("\n🚀 Ready to send to HubSpot:", style="bold green")
        
        # Deal panel
        console.print(Panel(
            Syntax(deal_yaml, "yaml", theme="monokai", line_numbers=False),
            title="Deal",
            expand=False
        ))
        
        # Company panel
        console.print(Panel(
            Syntax(company_yaml, "yaml", theme="monokai", line_numbers=False),
            title="Company",
            expand=False
        ))
    else:
        # Fallback to plain text formatting
        print("\n🚀 Ready to send to HubSpot:\n")
        print(_format_hubspot_data(data))

def prompt_for_confirmation(prompt_text: str = "Approve sending data to HubSpot?") -> bool:
    """
    Prompt the user for confirmation (Y/n).
    
    Args:
        prompt_text: The prompt to display to the user.
        
    Returns:
        bool: True if confirmed, False if rejected.
    """
    logger.info(f"Prompting user: {prompt_text}")
    
    if QUESTIONARY_AVAILABLE:
        return questionary.confirm(
            f"\n✅ {prompt_text}",
            default=True
        ).ask()
    else:
        # Fallback to manual input
        response = input(f"\n✅ {prompt_text} [Y/n]: ").strip().lower()
        return response == 'y' or response == 'yes' or response == ''

def _get_editor() -> str:
    """Get the user's preferred text editor."""
    # Check for EDITOR environment variable (standard on Unix-like systems)
    editor = os.environ.get('EDITOR')
    
    # Try common fallbacks based on platform if EDITOR is not set
    if not editor:
        if sys.platform.startswith('win'):
            # On Windows, try notepad
            if shutil.which('notepad'):
                editor = 'notepad'
        else:
            # On Unix-like systems, try nano, then vim, then emacs
            for fallback in ['nano', 'vim', 'vi', 'emacs']:
                if shutil.which(fallback):
                    editor = fallback
                    break
    
    # If we still don't have an editor, try platform-specific defaults
    if not editor:
        if sys.platform == 'darwin':  # macOS
            editor = 'open -t'  # Opens in TextEdit
        elif sys.platform.startswith('win'):
            editor = 'notepad'  # Notepad as a last resort on Windows
        else:
            # Final fallback for Linux/Unix, if nano is available, use it
            editor = 'nano'
    
    logger.info(f"Using editor: {editor}")
    return editor

def _edit_data_in_temp_file(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Write data to a temporary YAML file, open it in the user's editor, and read it back.
    
    Args:
        data: The data to edit.
        
    Returns:
        The edited data, or None if editing failed.
    """
    # Create a temporary file with a .yaml extension
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as temp_file:
        temp_path = temp_file.name
        
        # Add a helpful header comment
        temp_file.write("# Edit the data below and save the file when done.\n")
        temp_file.write("# Warning: Do not change the structure of this YAML file.\n\n")
        
        # Write data as YAML
        yaml.dump(data, temp_file, sort_keys=False, default_flow_style=False)
    
    logger.info(f"Created temporary YAML file for editing: {temp_path}")
    
    try:
        # Get the user's preferred editor
        editor = _get_editor()
        
        # Show instructions to the user
        print(f"\nOpening data in your editor ({editor}) for manual correction...")
        print(f"File location: {temp_path}")
        print("Save the file and exit the editor when you are done.")
        
        # Open the editor
        editor_cmd = f"{editor} {temp_path}"
        result = subprocess.run(editor_cmd, shell=True)
        
        if result.returncode != 0:
            logger.error(f"Editor process exited with error code {result.returncode}")
            print(f"Error: Editor exited with code {result.returncode}")
            return None
        
        # Read the edited file
        with open(temp_path, "r") as edited_file:
            edited_content = edited_file.read()
        
        # Parse the YAML content
        try:
            edited_data = yaml.safe_load(edited_content)
            logger.info("Successfully loaded edited data from YAML file.")
            return edited_data
        except yaml.YAMLError as e:
            logger.error(f"Error parsing edited YAML: {e}")
            print(f"Error: Could not parse the edited file. YAML syntax error: {e}")
            return None
    except Exception as e:
        logger.exception(f"Error during file editing: {e}")
        print(f"Error: Failed to edit the data: {e}")
        return None
    finally:
        # Always clean up the temporary file
        try:
            os.unlink(temp_path)
            logger.info(f"Removed temporary file: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {temp_path}: {e}")

def handle_editing(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle the editing workflow for the data.
    
    Args:
        data: The data to edit.
        
    Returns:
        The edited data, or None if editing was cancelled or failed.
    """
    logger.info("Starting data editing workflow.")
    
    # Currently, we only support the temp file approach
    # In the future, direct terminal editing could be implemented here
    # as an alternative method
    
    try:
        edited_data = _edit_data_in_temp_file(data)
        if edited_data:
            logger.info("Data was successfully edited.")
            return edited_data
        else:
            logger.warning("Data editing failed or was cancelled.")
            return None
    except Exception as e:
        logger.exception(f"Unexpected error in editing workflow: {e}")
        print(f"Error: An unexpected error occurred during editing: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Set up basic logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Test data
    test_data = {
        "deal": {
            "properties": {
                "dealname": "Senior Developer at Example Corp",
                "dealstage": "appointmentscheduled",
                "pipeline": "default",
                "job_description_raw": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20,
                "job_location": "Remote"
            }
        },
        "company": {
            "properties": {
                "name": "Example Corp",
                "industry": "Technology",
                "website": "https://example.com",
                "numberofemployees": "501-1,000 employees"
            }
        }
    }
    
    # Test display
    display_data_for_confirmation(test_data)
    
    # Test confirmation
    if prompt_for_confirmation():
        print("User confirmed.")
    else:
        print("User rejected. Testing editing...")
        edited_data = handle_editing(test_data)
        if edited_data:
            print("\nEdited data:")
            display_data_for_confirmation(edited_data) 