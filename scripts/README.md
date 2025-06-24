# MITRE ATLAS Case Study Scraper

This directory contains scripts for scraping MITRE ATLAS case studies and generating AVID vulnerability files.

## Files

- `atlas_scraper.py` - Main scraper script that processes ATLAS case studies
- `atlas_scraper_example.py` - Example usage and demonstration script

## Requirements

The scraper requires the following Python packages:
- `requests` - For HTTP requests to GitHub API
- `avidtools` - This package (for ATLAS connector and data models)

Additional packages for development:
- `beautifulsoup4` - For HTML parsing (if needed)

## Installation

```bash
# Install required packages
pip install requests beautifulsoup4

# Or install all development dependencies
pip install -e .[dev]
```

## Usage

### Basic Usage

```bash
# Dry run to see what would be created
python scripts/atlas_scraper.py --dry-run

# Create vulnerability files in default location (./vulnerabilities/2025)
python scripts/atlas_scraper.py

# Create files in custom directory
python scripts/atlas_scraper.py --output-dir /path/to/output

# Use existing local AVID database instead of cloning
python scripts/atlas_scraper.py --avid-db-path /path/to/avid-db

# Skip automatic git branch creation
python scripts/atlas_scraper.py --no-git
```

### Command Line Options

- `--dry-run` - Show what would be created without actually creating files
- `--output-dir` - Directory to create new vulnerability files (default: ./vulnerabilities/2025)
- `--avid-db-path` - Path to local avid-db repository (if not provided, will clone temporarily)
- `--no-git` - Don't create git branch and commit

### Example Output

```
Found 32 total case studies: ['AML.CS0000', 'AML.CS0001', ...]
Found 29 new case studies: ['AML.CS0003', 'AML.CS0004', ...]
Processing case study: AML.CS0003
Successfully created vulnerability AVID-2025-V0003 for AML.CS0003
...
Created vulnerability file: vulnerabilities/2025/AVID-2025-V0003.json
```

## How It Works

1. **Discovery**: The script fetches all available case studies from the MITRE ATLAS GitHub repository
2. **Filtering**: It checks the existing AVID database to identify case studies that haven't been processed yet
3. **Conversion**: For each new case study, it:
   - Downloads the case study YAML from ATLAS
   - Converts it to an AVID Report using the `avidtools.connectors.atlas` module
   - Creates a Vulnerability object and ingests the report data
   - Generates a unique vulnerability ID (AVID-2025-VXXXX)
4. **Output**: Saves each vulnerability as a JSON file in the specified directory
5. **Git Integration**: Optionally creates a git branch and commits the new files

## File Format

Generated vulnerability files follow the AVID vulnerability schema:

```json
{
  "data_type": "AVID",
  "data_version": "0.2",
  "metadata": {
    "vuln_id": "AVID-2025-V0001"
  },
  "affects": {
    "developer": [],
    "deployer": ["Target System"],
    "artifacts": [...]
  },
  "problemtype": {
    "classof": "ATLAS Case Study",
    "type": "Advisory",
    "description": {...}
  },
  "references": [...],
  "description": {...},
  "reports": [...]
}
```

## Integration with AVID Database

The script is designed to work with the [AVID Database](https://github.com/avidml/avid-db):

1. **Duplicate Detection**: Checks existing vulnerabilities to avoid duplicates
2. **File Organization**: Creates files in the standard AVID database structure
3. **Git Workflow**: Creates branches suitable for pull requests to the AVID database

## Error Handling

The script includes robust error handling:
- Network errors when fetching case studies
- Missing or malformed case study data
- File system errors
- Git operation failures

Failed case studies are logged but don't stop the overall process.

## Contributing

To contribute improvements to the scraper:

1. Ensure all linting passes: `ruff check scripts/`
2. Test with dry run mode first
3. Verify generated vulnerability files are valid
4. Update documentation as needed

## Troubleshooting

### Common Issues

**"No new case studies to process!"**
- All case studies may already exist in the AVID database
- Check the existing case studies list in the output

**Network errors**
- Ensure internet connectivity
- GitHub API rate limiting may apply for large numbers of requests

**Git operation failures**
- Ensure you're in a git repository
- Check file permissions and git configuration

**Case study processing errors**
- Some case studies may have different formats
- The script will continue processing other case studies

### Debug Mode

For debugging, you can add print statements or use Python's debugger:

```bash
python -u scripts/atlas_scraper.py --dry-run  # Unbuffered output
python -m pdb scripts/atlas_scraper.py       # Python debugger
```
