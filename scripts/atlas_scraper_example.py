#!/usr/bin/env python3
"""
Example usage of the MITRE ATLAS scraper.

This demonstrates how to use the atlas_scraper.py script to generate
vulnerability files from MITRE ATLAS case studies.
"""

import subprocess
import sys


def main():
    """Run example usage of the ATLAS scraper."""
    
    print("🚀 MITRE ATLAS Case Study Scraper Example")
    print("=" * 50)
    
    # Example 1: Dry run to see what would be created
    print("\n1. Dry run - See what vulnerabilities would be created:")
    result = subprocess.run([
        sys.executable, "scripts/atlas_scraper.py",
        "--dry-run", "--no-git"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        # Show key statistics
        for line in lines:
            if ("Found" in line and
                    ("case studies" in line or "vulnerability" in line)):
                print(f"  📊 {line}")
            elif "DRY RUN" in line:
                print(f"  📄 {line}")
    else:
        print(f"  ❌ Error: {result.stderr}")
        return
    
    # Example 2: Show how to run with actual file creation
    print("\n2. To create actual vulnerability files:")
    print("   python scripts/atlas_scraper.py --output-dir "
          "./vulnerabilities/2025")
    
    # Example 3: Show how to run with existing AVID database
    print("\n3. To use an existing local AVID database:")
    print("   python scripts/atlas_scraper.py --avid-db-path /path/to/avid-db")
    
    # Example 4: Show how to skip git operations
    print("\n4. To skip automatic git branch creation:")
    print("   python scripts/atlas_scraper.py --no-git")
    
    print("\n✅ Example completed! Check the script output above.")
    print("\n📚 For more options, run:")
    print("   python scripts/atlas_scraper.py --help")


if __name__ == "__main__":
    main()
