#!/usr/bin/env python3
"""
MITRE ATLAS Case Study Scraper

This script scrapes MITRE ATLAS case studies and generates AVID vulnerability
files for any case studies not already covered in the AVID database.

Usage:
    python atlas_scraper.py [--dry-run] [--output-dir OUTPUT_DIR] \\
                            [--avid-db-path AVID_DB_PATH]

Options:
    --dry-run           Show what would be created without actually creating
                        files
    --output-dir        Directory to create new vulnerability files
                        (default: ./vulnerabilities/2025)
    --avid-db-path      Path to local avid-db repository (if not provided,
                        will clone temporarily)
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import List, Set, Optional
import requests

from avidtools.connectors.atlas import import_case_study, convert_case_study
from avidtools.datamodels.vulnerability import (
    Vulnerability, VulnMetadata, ReportSummary
)
from avidtools.datamodels.enums import TypeEnum


class AtlasScraper:
    """Scraper for MITRE ATLAS case studies."""
    
    def __init__(
        self,
        avid_db_path: Optional[str] = None,
        output_dir: str = "./vulnerabilities/2025"
    ):
        self.avid_db_path = avid_db_path
        self.output_dir = Path(output_dir)
        self.temp_dir = None
        self.existing_case_studies: Set[str] = set()
        
    def __enter__(self):
        """Context manager entry."""
        self._setup_avid_db()
        self._load_existing_case_studies()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.temp_dir:
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def _setup_avid_db(self):
        """Setup access to AVID database repository."""
        if self.avid_db_path and Path(self.avid_db_path).exists():
            self.avid_db_path = Path(self.avid_db_path)
            print(f"Using local AVID database at: {self.avid_db_path}")
        else:
            # Clone the repository temporarily
            self.temp_dir = tempfile.mkdtemp()
            temp_path = Path(self.temp_dir) / "avid-db"
            print("Cloning AVID database repository...")
            subprocess.run([
                "git", "clone",
                "https://github.com/avidml/avid-db.git",
                str(temp_path)
            ], check=True, capture_output=True)
            self.avid_db_path = temp_path
            print(f"Cloned AVID database to: {self.avid_db_path}")
    
    def _load_existing_case_studies(self):
        """Load existing case study IDs from AVID database."""
        vuln_dir = self.avid_db_path / "vulnerabilities"
        
        if not vuln_dir.exists():
            print(f"Warning: Vulnerabilities directory not found at "
                  f"{vuln_dir}")
            return
            
        print("Loading existing case studies from AVID database...")
        case_study_pattern = re.compile(
            r'"label":\s*"([^"]*AML\.CS\d+[^"]*)"',
            re.IGNORECASE
        )
        
        for year_dir in vuln_dir.iterdir():
            if year_dir.is_dir():
                for vuln_file in year_dir.glob("*.json"):
                    try:
                        with open(vuln_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            matches = case_study_pattern.findall(content)
                            for match in matches:
                                # Extract AML.CS ID from the match
                                cs_match = re.search(
                                    r'AML\.CS\d+', match, re.IGNORECASE
                                )
                                if cs_match:
                                    cs_id = cs_match.group().upper()
                                    self.existing_case_studies.add(cs_id)
                    except Exception as e:
                        print(f"Warning: Could not read {vuln_file}: {e}")
        
        existing_list = sorted(self.existing_case_studies)
        print(f"Found {len(self.existing_case_studies)} existing case "
              f"studies: {existing_list}")
    
    def scrape_atlas_case_studies(self) -> List[str]:
        """Scrape all case study IDs from MITRE ATLAS GitHub repository."""
        print("Scraping MITRE ATLAS case studies from GitHub...")
        
        case_study_ids = []
        case_study_pattern = re.compile(r'AML\.CS\d+', re.IGNORECASE)
        
        try:
            github_url = (
                "https://api.github.com/repos/mitre-atlas/atlas-data/"
                "contents/data/case-studies"
            )
            github_response = requests.get(github_url)
            github_response.raise_for_status()
            
            files = github_response.json()
            for file_info in files:
                if file_info['name'].endswith('.yaml'):
                    filename = file_info['name'].replace('.yaml', '')
                    if case_study_pattern.match(filename):
                        case_id = filename.upper()
                        if case_id not in case_study_ids:
                            case_study_ids.append(case_id)
                            
        except Exception as e:
            print(f"Error: Could not fetch case studies from GitHub: {e}")
            return []
        
        case_study_ids.sort()
        print(f"Found {len(case_study_ids)} total case studies: "
              f"{case_study_ids}")
        return case_study_ids
    
    def get_new_case_studies(self, all_case_studies: List[str]) -> List[str]:
        """Filter out case studies that already exist in AVID database."""
        new_case_studies = [
            cs for cs in all_case_studies
            if cs not in self.existing_case_studies
        ]
        print(f"Found {len(new_case_studies)} new case studies: "
              f"{new_case_studies}")
        return new_case_studies
    
    def generate_vuln_id(self, case_study_id: str) -> str:
        """Generate a vulnerability ID for a case study."""
        # Extract the number from AML.CS0001 -> 0001
        match = re.search(r'AML\.CS(\d+)', case_study_id, re.IGNORECASE)
        if match:
            cs_number = match.group(1)
            return f"AVID-2025-V{cs_number}"
        else:
            # Fallback - use current year and increment
            return f"AVID-2025-V{case_study_id.replace('AML.CS', '')}"
    
    def create_vulnerability_from_case_study(
        self, case_study_id: str
    ) -> Optional[Vulnerability]:
        """Create a vulnerability object from a case study."""
        try:
            print(f"Processing case study: {case_study_id}")
            
            # Import case study using avidtools connector
            case_study_data = import_case_study(case_study_id)
            
            # Convert to AVID report
            report = convert_case_study(case_study_data)
            
            # Create vulnerability
            vuln_id = self.generate_vuln_id(case_study_id)
            vulnerability = Vulnerability(
                data_version="0.2",
                metadata=VulnMetadata(vuln_id=vuln_id)
            )
            
            # Ingest the report data
            vulnerability.ingest(report)
            
            # Add the report summary
            vulnerability.reports = [ReportSummary(
                report_id=f"ATLAS-{case_study_id}",
                type=TypeEnum.advisory,
                name=case_study_data.get('name', case_study_id)
            )]
            
            # Set published and modified dates
            vulnerability.published_date = date.today()
            vulnerability.last_modified_date = date.today()
            
            # --- NEW: Copy impact.atlas from report if present ---
            if 'impact' in report and isinstance(report['impact'], dict):
                if 'atlas' in report['impact']:
                    if not hasattr(vulnerability, 'impact') or vulnerability.impact is None:
                        vulnerability.impact = {}
                    vulnerability.impact['atlas'] = report['impact']['atlas']
            # --- END NEW ---
            
            print(f"Successfully created vulnerability {vuln_id} for "
                  f"{case_study_id}")
            return vulnerability
            
        except Exception as e:
            print(f"Error processing case study {case_study_id}: {e}")
            return None
    
    def save_vulnerability(
        self, vulnerability: Vulnerability, dry_run: bool = False
    ) -> str:
        """Save vulnerability to JSON file."""
        filename = f"{vulnerability.metadata.vuln_id}.json"
        filepath = self.output_dir / filename
        
        if dry_run:
            print(f"[DRY RUN] Would create: {filepath}")
            return str(filepath)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(vulnerability.model_dump(), f, indent=2, default=str)
        
        print(f"Created vulnerability file: {filepath}")
        return str(filepath)
    
    def create_git_branch_and_commit(
        self, created_files: List[str], dry_run: bool = False
    ):
        """Create a git branch and commit the new vulnerability files."""
        if not created_files:
            print("No files to commit")
            return
            
        branch_name = f"atlas-case-studies-{date.today().strftime('%Y%m%d')}"
        
        if dry_run:
            print(f"[DRY RUN] Would create git branch: {branch_name}")
            print(f"[DRY RUN] Would commit {len(created_files)} files")
            return
        
        try:
            # Change to output directory for git operations
            original_cwd = os.getcwd()
            os.chdir(self.output_dir.parent)
            
            # Create and checkout new branch
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            
            # Add new files
            for file_path in created_files:
                rel_path = os.path.relpath(file_path, self.output_dir.parent)
                subprocess.run(["git", "add", rel_path], check=True)
            
            # Commit
            commit_message = (
                f"Add {len(created_files)} MITRE ATLAS case studies as "
                f"vulnerabilities\n\nAutomatically generated from MITRE "
                f"ATLAS case studies on {date.today()}"
            )
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            print(f"Created git branch '{branch_name}' with "
                  f"{len(created_files)} new vulnerability files")
            print("You can now push this branch and create a pull request")
            
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
        finally:
            os.chdir(original_cwd)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape MITRE ATLAS case studies and generate AVID "
                    "vulnerabilities"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be created without actually creating files"
    )
    parser.add_argument(
        "--output-dir", default="./vulnerabilities/2025",
        help="Directory to create new vulnerability files"
    )
    parser.add_argument(
        "--avid-db-path",
        help="Path to local avid-db repository"
    )
    parser.add_argument(
        "--no-git", action="store_true",
        help="Don't create git branch and commit"
    )
    
    args = parser.parse_args()
    
    try:
        with AtlasScraper(args.avid_db_path, args.output_dir) as scraper:
            # Scrape all case studies
            all_case_studies = scraper.scrape_atlas_case_studies()
            
            # Filter out existing ones
            new_case_studies = scraper.get_new_case_studies(all_case_studies)
            
            if not new_case_studies:
                print("No new case studies to process!")
                return
            
            # Process each new case study
            created_files = []
            for case_study_id in new_case_studies:
                vulnerability = scraper.create_vulnerability_from_case_study(
                    case_study_id
                )
                if vulnerability:
                    filepath = scraper.save_vulnerability(
                        vulnerability, args.dry_run
                    )
                    if not args.dry_run:
                        created_files.append(filepath)
            
            print(f"\nProcessed {len(new_case_studies)} case studies")
            print(f"Successfully created {len(created_files)} vulnerability "
                  f"files")
            
            # Create git branch and commit if requested
            if not args.no_git and created_files:
                scraper.create_git_branch_and_commit(
                    created_files, args.dry_run
                )
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
