"""LinkedIn PDF parser module.

This module extracts structured data from LinkedIn job and company PDFs.
It uses pdfplumber to extract text and implements logic to identify and extract
relevant sections like job title, company name, responsibilities, etc.
"""

import os
import re
import logging
import pdfplumber
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class LinkedInPDFParser:
    """Parser for LinkedIn job and company PDFs.
    
    This class extracts structured data from LinkedIn job and company PDFs,
    identifying key sections and metadata to be processed by the LLM.
    """
    
    def __init__(self):
        """Initialize the LinkedIn PDF parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse_job_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract job information from a LinkedIn job PDF.
        
        Args:
            pdf_path: Path to the LinkedIn job PDF file
            
        Returns:
            Dict containing structured job data
        
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the PDF doesn't appear to be a LinkedIn job posting
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Job PDF file not found: {pdf_path}")
        
        self.logger.info(f"Parsing LinkedIn job PDF: {pdf_path}")
        
        # Extract all text from the PDF
        all_text = self._extract_text_from_pdf(pdf_path)
        
        # Parse the job details
        job_data = self._parse_job_details(all_text)
        
        # Validate we have the minimum required information
        if not job_data.get('title') or not job_data.get('company'):
            raise ValueError("Could not extract essential job information (title/company) from the PDF")
        
        job_data['source'] = pdf_path
        self.logger.info(f"Successfully extracted job data: {job_data['title']} at {job_data['company']}")
        return job_data
    
    def parse_company_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract company information from a LinkedIn company PDF.
        
        Args:
            pdf_path: Path to the LinkedIn company PDF file
            
        Returns:
            Dict containing structured company data
        
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the PDF doesn't appear to be a LinkedIn company page
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Company PDF file not found: {pdf_path}")
        
        self.logger.info(f"Parsing LinkedIn company PDF: {pdf_path}")
        
        # Extract all text from the PDF
        all_text = self._extract_text_from_pdf(pdf_path)
        
        # Parse the company details
        company_data = self._parse_company_details(all_text)
        
        # Validate we have the minimum required information
        if not company_data.get('name'):
            raise ValueError("Could not extract company name from the PDF")
        
        company_data['source'] = pdf_path
        self.logger.info(f"Successfully extracted company data: {company_data['name']}")
        return company_data
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        return text
    
    def _parse_job_details(self, text: str) -> Dict[str, Any]:
        """Parse job details from extracted text.
        
        Args:
            text: Extracted text from the job PDF
            
        Returns:
            Dictionary with structured job data
        """
        # Initialize job data structure
        job_data = {
            'title': '',
            'company': '',
            'location': '',
            'description': '',
            'responsibilities': [],
            'requirements': [],
            'company_description': '',
            'nice_to_have': [],
            'benefits': [],
            'job_type': '',
            'seniority_level': '',
            'industry': '',
            'employment_type': '',
            'job_functions': [],
        }
        
        # Extract job title and company using regex patterns
        title_pattern = r"([\w\s,\-\&]+)\sat\s([\w\s,\-\&]+)"
        title_match = re.search(title_pattern, text)
        if title_match:
            job_data['title'] = title_match.group(1).strip()
            job_data['company'] = title_match.group(2).strip()
        
        # Extract location
        location_pattern = r"(?:Location|office)\s*(?:\:|\s)\s*([\w\s,\-]+)"
        location_match = re.search(location_pattern, text, re.IGNORECASE)
        if location_match:
            job_data['location'] = location_match.group(1).strip()
        
        # Extract job description
        desc_pattern = r"(?:About the job|Job description)\s*(?:\:|\n)([\s\S]+?)(?:Responsibilities|Requirements|Qualifications|About the company|$)"
        desc_match = re.search(desc_pattern, text, re.IGNORECASE)
        if desc_match:
            job_data['description'] = desc_match.group(1).strip()
        
        # Extract responsibilities
        resp_pattern = r"(?:Responsibilities|What you'll do)\s*(?:\:|\n)([\s\S]+?)(?:Requirements|Qualifications|About the company|Benefits|$)"
        resp_match = re.search(resp_pattern, text, re.IGNORECASE)
        if resp_match:
            responsibilities_text = resp_match.group(1).strip()
            # Split by bullet points or newlines
            job_data['responsibilities'] = [
                item.strip() 
                for item in re.split(r'•|\n-|\n\*|\n\d+\.', responsibilities_text) 
                if item.strip()
            ]
        
        # Extract requirements
        req_pattern = r"(?:Requirements|Qualifications)\s*(?:\:|\n)([\s\S]+?)(?:Nice to have|Preferred|Benefits|About the company|$)"
        req_match = re.search(req_pattern, text, re.IGNORECASE)
        if req_match:
            requirements_text = req_match.group(1).strip()
            # Split by bullet points or newlines
            job_data['requirements'] = [
                item.strip() 
                for item in re.split(r'•|\n-|\n\*|\n\d+\.', requirements_text) 
                if item.strip()
            ]
        
        # Extract job type and other metadata
        job_type_pattern = r"(?:Job Type|Employment Type)\s*(?:\:|\s)\s*([\w\s,\-]+)"
        job_type_match = re.search(job_type_pattern, text, re.IGNORECASE)
        if job_type_match:
            job_data['job_type'] = job_type_match.group(1).strip()
        
        # Extract seniority level
        seniority_pattern = r"(?:Seniority Level)\s*(?:\:|\s)\s*([\w\s,\-]+)"
        seniority_match = re.search(seniority_pattern, text, re.IGNORECASE)
        if seniority_match:
            job_data['seniority_level'] = seniority_match.group(1).strip()
        
        return job_data
    
    def _parse_company_details(self, text: str) -> Dict[str, Any]:
        """Parse company details from extracted text.
        
        Args:
            text: Extracted text from the company PDF
            
        Returns:
            Dictionary with structured company data
        """
        # Initialize company data structure
        company_data = {
            'name': '',
            'website': '',
            'industry': '',
            'company_size': '',
            'headquarters': '',
            'type': '',
            'founded': '',
            'specialties': [],
            'description': '',
        }
        
        # Extract company name
        name_pattern = r"([\w\s,\-\&\.]+)(?:\son LinkedIn)"
        name_match = re.search(name_pattern, text)
        if name_match:
            company_data['name'] = name_match.group(1).strip()
        
        # Extract website
        website_pattern = r"(?:Website|Homepage)\s*(?:\:|\s)\s*(https?://[\w\.-]+)"
        website_match = re.search(website_pattern, text, re.IGNORECASE)
        if website_match:
            company_data['website'] = website_match.group(1).strip()
        
        # Extract industry
        industry_pattern = r"(?:Industry)\s*(?:\:|\s)\s*([\w\s,\-\&]+)"
        industry_match = re.search(industry_pattern, text, re.IGNORECASE)
        if industry_match:
            company_data['industry'] = industry_match.group(1).strip()
        
        # Extract company size
        size_pattern = r"(?:Company size|Employees)\s*(?:\:|\s)\s*([\w\s,\-\&]+)"
        size_match = re.search(size_pattern, text, re.IGNORECASE)
        if size_match:
            company_data['company_size'] = size_match.group(1).strip()
        
        # Extract headquarters
        hq_pattern = r"(?:Headquarters|Location)\s*(?:\:|\s)\s*([\w\s,\-\&]+)"
        hq_match = re.search(hq_pattern, text, re.IGNORECASE)
        if hq_match:
            company_data['headquarters'] = hq_match.group(1).strip()
        
        # Extract description
        desc_pattern = r"(?:About|Overview)\s*(?:\:|\n)([\s\S]+?)(?:Specialties|Founded|$)"
        desc_match = re.search(desc_pattern, text, re.IGNORECASE)
        if desc_match:
            company_data['description'] = desc_match.group(1).strip()
        
        # Extract specialties
        spec_pattern = r"(?:Specialties)\s*(?:\:|\n)([\s\S]+?)(?:Website|Industry|$)"
        spec_match = re.search(spec_pattern, text, re.IGNORECASE)
        if spec_match:
            specialties_text = spec_match.group(1).strip()
            # Split by commas, bullets, or newlines
            company_data['specialties'] = [
                item.strip() 
                for item in re.split(r',|•|\n-|\n\*', specialties_text) 
                if item.strip()
            ]
        
        return company_data
    
    def combine_data(self, job_data: Dict[str, Any], company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine job and company data into a single structure.
        
        Args:
            job_data: Parsed job data
            company_data: Parsed company data
            
        Returns:
            Combined data dictionary
        """
        combined_data = {
            "job": job_data,
            "company": company_data
        }
        
        # If we have company data but no company name in job data, use the company name
        if not job_data.get('company') and company_data.get('name'):
            combined_data["job"]["company"] = company_data["name"]
        
        # If we have company industry but no job industry, use the company industry
        if not job_data.get('industry') and company_data.get('industry'):
            combined_data["job"]["industry"] = company_data["industry"]
        
        return combined_data 