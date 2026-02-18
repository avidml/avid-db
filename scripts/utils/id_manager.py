"""
ID Manager for AVID database.

Handles generation and tracking of AVID Report and Vulnerability IDs.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, Dict


class IDManager:
    """
    Manages AVID ID generation with session tracking.
    
    Tracks IDs assigned during a session to avoid duplicates when
    processing multiple items before files are written to disk.
    """
    
    def __init__(self):
        """Initialize the ID manager with empty tracking."""
        self._report_counters: Dict[int, int] = {}
        self._vuln_counters: Dict[int, int] = {}
    
    def get_next_report_id(self, year: Optional[int] = None) -> str:
        """
        Generate the next available AVID Report ID for a given year.
        
        Tracks IDs within the session to avoid duplicates.
        
        Args:
            year: Year for the report ID. Defaults to current year.
            
        Returns:
            Next available report ID in format AVID-YYYY-R####
        """
        if year is None:
            year = datetime.now().year
        
        # Initialize counter for this year if not exists
        if year not in self._report_counters:
            self._report_counters[year] = self._scan_max_report_number(year)
        
        # Increment and return
        self._report_counters[year] += 1
        return f"AVID-{year}-R{self._report_counters[year]:04d}"
    
    def get_next_vuln_id(self, year: Optional[int] = None) -> str:
        """
        Generate the next available AVID Vulnerability ID for a given year.
        
        Tracks IDs within the session to avoid duplicates.
        
        Args:
            year: Year for the vulnerability ID. Defaults to current year.
            
        Returns:
            Next available vulnerability ID in format AVID-YYYY-V###
        """
        if year is None:
            year = datetime.now().year
        
        # Initialize counter for this year if not exists
        if year not in self._vuln_counters:
            self._vuln_counters[year] = self._scan_max_vuln_number(year)
        
        # Increment and return
        self._vuln_counters[year] += 1
        return f"AVID-{year}-V{self._vuln_counters[year]:03d}"
    
    def _scan_max_report_number(self, year: int) -> int:
        """Scan filesystem for maximum report number for a given year."""
        script_dir = Path(__file__).parent.parent
        reports_dir = script_dir.parent / "reports"
        
        pattern = re.compile(rf"AVID-{year}-R(\d+)")
        max_number = 0
        
        # Scan year directory
        year_dir = reports_dir / str(year)
        if year_dir.exists():
            for file_path in year_dir.glob("AVID-*.json"):
                match = pattern.match(file_path.stem)
                if match:
                    number = int(match.group(1))
                    max_number = max(max_number, number)
        
        # Scan review directory
        review_dir = reports_dir / "review"
        if review_dir.exists():
            for file_path in review_dir.glob("AVID-*.json"):
                match = pattern.match(file_path.stem)
                if match:
                    number = int(match.group(1))
                    max_number = max(max_number, number)
        
        return max_number
    
    def _scan_max_vuln_number(self, year: int) -> int:
        """Scan filesystem for maximum vulnerability number for a year."""
        script_dir = Path(__file__).parent.parent
        vulns_dir = script_dir.parent / "vulnerabilities"
        
        pattern = re.compile(rf"AVID-{year}-V(\d+)")
        max_number = 0
        
        # Scan year directory
        year_dir = vulns_dir / str(year)
        if year_dir.exists():
            for file_path in year_dir.glob("AVID-*.json"):
                match = pattern.match(file_path.stem)
                if match:
                    number = int(match.group(1))
                    max_number = max(max_number, number)
        
        return max_number


def get_next_report_id(year: Optional[int] = None) -> str:
    """
    Generate the next available AVID Report ID for a given year.
    
    Scans the reports directory to find the highest existing report number
    and returns the next sequential ID.
    
    Args:
        year: Year for the report ID. Defaults to current year.
        
    Returns:
        Next available report ID in format AVID-YYYY-R####
    """
    if year is None:
        year = datetime.now().year
    
    # Get the avid-db reports directory
    script_dir = Path(__file__).parent.parent
    reports_dir = script_dir.parent / "reports"
    
    # Pattern to match report IDs: AVID-YYYY-R####
    pattern = re.compile(rf"AVID-{year}-R(\d+)")
    
    max_number = 0
    
    # Scan year directory
    year_dir = reports_dir / str(year)
    if year_dir.exists():
        for file_path in year_dir.glob("AVID-*.json"):
            match = pattern.match(file_path.stem)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
    
    # Scan review directory
    review_dir = reports_dir / "review"
    if review_dir.exists():
        for file_path in review_dir.glob("AVID-*.json"):
            match = pattern.match(file_path.stem)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
    
    # Return next ID
    next_number = max_number + 1
    return f"AVID-{year}-R{next_number:04d}"


def get_next_vuln_id(year: Optional[int] = None) -> str:
    """
    Generate the next available AVID Vulnerability ID for a given year.
    
    Scans the vulnerabilities directory to find the highest existing
    vulnerability number and returns the next sequential ID.
    
    Args:
        year: Year for the vulnerability ID. Defaults to current year.
        
    Returns:
        Next available vulnerability ID in format AVID-YYYY-V###
    """
    if year is None:
        year = datetime.now().year
    
    # Get the avid-db vulnerabilities directory
    script_dir = Path(__file__).parent.parent
    vulns_dir = script_dir.parent / "vulnerabilities"
    
    # Pattern to match vulnerability IDs: AVID-YYYY-V###
    pattern = re.compile(rf"AVID-{year}-V(\d+)")
    
    max_number = 0
    
    # Scan year directory
    year_dir = vulns_dir / str(year)
    if year_dir.exists():
        for file_path in year_dir.glob("AVID-*.json"):
            match = pattern.match(file_path.stem)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
    
    # Return next ID
    next_number = max_number + 1
    return f"AVID-{year}-V{next_number:03d}"


def parse_avid_id(avid_id: str) -> Tuple[int, str, int]:
    """
    Parse an AVID ID into its components.
    
    Args:
        avid_id: AVID ID string (e.g., 'AVID-2025-R0001' or 'AVID-2025-V001')
        
    Returns:
        Tuple of (year, type, number) where type is 'R' or 'V'
        
    Raises:
        ValueError: If the ID format is invalid
    """
    pattern = re.compile(r"AVID-(\d{4})-([RV])(\d+)")
    match = pattern.match(avid_id)
    
    if not match:
        raise ValueError(f"Invalid AVID ID format: {avid_id}")
    
    year = int(match.group(1))
    type_char = match.group(2)
    number = int(match.group(3))
    
    return year, type_char, number


def validate_avid_id(avid_id: str) -> bool:
    """
    Validate an AVID ID format.
    
    Args:
        avid_id: AVID ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        parse_avid_id(avid_id)
        return True
    except ValueError:
        return False
