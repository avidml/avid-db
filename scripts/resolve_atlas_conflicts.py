#!/usr/bin/env python3
"""
Script to resolve conflicts between newly created ATLAS vulnerability files
and existing vulnerability files that already cover the same case studies.

This script will:
1. Identify conflicting case studies
2. Delete duplicate vulnerability files from 2025/
3. Update existing vulnerability files with latest ATLAS data if needed
"""

import json
import re
from pathlib import Path
from typing import Dict, Set
from avidtools.connectors.atlas import import_case_study, convert_case_study


class ConflictResolver:
    """Resolves conflicts between new and existing ATLAS vulnerability files."""
    
    def __init__(self, avid_db_path: str = "/home/smajumdar/avidml/avid-db"):
        self.avid_db_path = Path(avid_db_path)
        self.vuln_dir = self.avid_db_path / "vulnerabilities"
        self.existing_mappings: Dict[str, str] = {}  # CS_ID -> existing_file_path
        self.new_files_dir = self.vuln_dir / "2025"
        
    def find_existing_case_studies(self) -> Dict[str, str]:
        """Find all existing case study mappings in older vulnerability files."""
        case_study_pattern = re.compile(r'AML\.CS\d+', re.IGNORECASE)
        mappings = {}
        
        for year in ["2022", "2023"]:
            year_dir = self.vuln_dir / year
            if not year_dir.exists():
                continue
                
            for vuln_file in year_dir.glob("*.json"):
                try:
                    with open(vuln_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = case_study_pattern.findall(content)
                        for match in matches:
                            cs_id = match.upper()
                            if cs_id not in mappings:
                                mappings[cs_id] = str(vuln_file)
                                print(f"Found existing: {cs_id} -> {vuln_file.name}")
                except Exception as e:
                    print(f"Warning: Could not read {vuln_file}: {e}")
        
        return mappings
    
    def find_new_case_studies(self) -> Dict[str, str]:
        """Find all new case study mappings in 2025 vulnerability files."""
        case_study_pattern = re.compile(r'AML\.CS\d+', re.IGNORECASE)
        mappings = {}
        
        if not self.new_files_dir.exists():
            return mappings
            
        for vuln_file in self.new_files_dir.glob("*.json"):
            try:
                with open(vuln_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = case_study_pattern.findall(content)
                    for match in matches:
                        cs_id = match.upper()
                        if cs_id not in mappings:
                            mappings[cs_id] = str(vuln_file)
                            print(f"Found new: {cs_id} -> {vuln_file.name}")
            except Exception as e:
                print(f"Warning: Could not read {vuln_file}: {e}")
        
        return mappings
    
    def find_conflicts(self, existing: Dict[str, str], new: Dict[str, str]) -> Set[str]:
        """Find case studies that exist in both existing and new files."""
        conflicts = set(existing.keys()) & set(new.keys())
        print(f"Found {len(conflicts)} conflicts: {sorted(conflicts)}")
        return conflicts
    
    def remove_duplicate_files(self, conflicts: Set[str], new_mappings: Dict[str, str]):
        """Remove duplicate vulnerability files for conflicting case studies."""
        removed_files = []
        
        for cs_id in conflicts:
            if cs_id in new_mappings:
                file_path = Path(new_mappings[cs_id])
                if file_path.exists():
                    print(f"Removing duplicate file: {file_path}")
                    file_path.unlink()
                    removed_files.append(str(file_path))
        
        return removed_files
    
    def update_existing_file_with_latest_data(self, cs_id: str, existing_file: str):
        """Update existing vulnerability file with latest ATLAS data."""
        try:
            print(f"Updating {existing_file} with latest data for {cs_id}")
            
            # Load existing vulnerability
            with open(existing_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # Get latest ATLAS data
            case_study_data = import_case_study(cs_id)
            latest_report = convert_case_study(case_study_data)
            
            # Update the description and other fields if needed
            if 'description' in latest_report:
                existing_data['description'] = latest_report['description']
            
            # Update last_modified_date
            from datetime import date
            existing_data['last_modified_date'] = str(date.today())
            
            # Write back to file
            with open(existing_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            print(f"Successfully updated {existing_file}")
            
        except Exception as e:
            print(f"Error updating {existing_file} for {cs_id}: {e}")
    
    def get_unique_case_studies(self, new_mappings: Dict[str, str], conflicts: Set[str]) -> Dict[str, str]:
        """Get case studies that are truly new (not in existing files)."""
        unique = {cs_id: file_path for cs_id, file_path in new_mappings.items() 
                 if cs_id not in conflicts}
        print(f"Found {len(unique)} unique new case studies: {sorted(unique.keys())}")
        return unique
    
    def resolve_conflicts(self, dry_run: bool = False):
        """Main method to resolve all conflicts."""
        print("=== ATLAS Vulnerability Conflict Resolution ===")
        
        # Find existing and new case studies
        existing_mappings = self.find_existing_case_studies()
        new_mappings = self.find_new_case_studies()
        
        # Find conflicts
        conflicts = self.find_conflicts(existing_mappings, new_mappings)
        
        if not conflicts:
            print("No conflicts found!")
            return
        
        if dry_run:
            print("\n[DRY RUN] Actions that would be taken:")
            print(f"- Remove {len(conflicts)} duplicate files from 2025/")
            print(f"- Update {len(conflicts)} existing files with latest ATLAS data")
            return
        
        # Remove duplicate files
        print("\n=== Removing Duplicate Files ===")
        removed_files = self.remove_duplicate_files(conflicts, new_mappings)
        
        # Update existing files with latest data
        print("\n=== Updating Existing Files ===")
        for cs_id in conflicts:
            if cs_id in existing_mappings:
                self.update_existing_file_with_latest_data(cs_id, existing_mappings[cs_id])
        
        # Show final status
        unique_new = self.get_unique_case_studies(new_mappings, conflicts)
        
        print(f"\n=== Summary ===")
        print(f"- Removed {len(removed_files)} duplicate files")
        print(f"- Updated {len(conflicts)} existing files")
        print(f"- Kept {len(unique_new)} truly new vulnerability files")
        print(f"- Unique new case studies: {sorted(unique_new.keys())}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Resolve conflicts between new and existing ATLAS vulnerability files"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--avid-db-path", default="/home/smajumdar/avidml/avid-db",
        help="Path to AVID database repository"
    )
    
    args = parser.parse_args()
    
    resolver = ConflictResolver(args.avid_db_path)
    resolver.resolve_conflicts(args.dry_run)


if __name__ == "__main__":
    main()
