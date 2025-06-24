#!/usr/bin/env python3
"""
Generate a CSV summary of all created AVID vulnerabilities.
"""

import json
import csv
from pathlib import Path


def main():
    """Generate CSV summary of vulnerabilities."""
    vuln_dir = Path("vulnerabilities/2025")
    output_file = "atlas_vulnerabilities_summary.csv"
    
    vulnerabilities = []
    
    # Process all JSON files
    for json_file in sorted(vuln_dir.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            reports = data.get('reports', [{}])
            atlas_id = reports[0].get('report_id', '').replace('ATLAS-', '')
            
            problemtype = data.get('problemtype', {})
            desc_data = problemtype.get('description', {})
            problem_desc = desc_data.get('value', 'Unknown')
            
            affects = data.get('affects', {})
            target_system = affects.get('deployer', ['Unknown'])[0]
            
            desc_value = data.get('description', {}).get('value', '')
            atlas_url = f"https://atlas.mitre.org/studies/{atlas_id}"
            
            vuln = {
                'AVID_ID': data.get('metadata', {}).get('vuln_id', 'Unknown'),
                'ATLAS_ID': atlas_id,
                'Name': problem_desc,
                'Target_System': target_system,
                'Published_Date': data.get('published_date', 'Unknown'),
                'Atlas_URL': atlas_url,
                'Description_Length': len(desc_value),
                'References_Count': len(data.get('references', []))
            }
            vulnerabilities.append(vuln)
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'AVID_ID', 'ATLAS_ID', 'Name', 'Target_System', 'Published_Date',
            'Atlas_URL', 'Description_Length', 'References_Count'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for vuln in vulnerabilities:
            writer.writerow(vuln)
    
    print(f"✅ CSV summary created: {output_file}")
    print(f"📊 Total vulnerabilities: {len(vulnerabilities)}")
    print(f"📁 Files processed: {len(list(vuln_dir.glob('*.json')))}")


if __name__ == "__main__":
    main()
