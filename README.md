# High Courts Scraper

A Python scraper for extracting case information from Indian High Court websites using the eCourts portal.

## Features

- **Comprehensive Logging**: Detailed logging system that shows exactly what data is being scraped
- **Multi-level Logging**: Console output for quick overview, detailed file logs for debugging
- **State/Court Discovery**: Automatically discovers available states and courts
- **Bench and Case Type Mapping**: Fetches and maps available benches and case types
- **CAPTCHA Handling**: Manual CAPTCHA solving with image display
- **Case History Extraction**: Complete case history retrieval

## Improved Logging System

The scraper now includes a comprehensive logging system that provides detailed visibility into the scraping process:

### Log Levels
- **INFO**: General progress and important data (default console output)
- **DEBUG**: Detailed technical information (file logs only)
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

### Log Output
- **Console**: Clean, formatted output with emojis and progress indicators
- **File**: Detailed logs with timestamps saved in `logs/` directory

### What Gets Logged
- All HTTP requests and responses
- Scraped data (states, courts, benches, case types)
- Search parameters and results
- Error conditions and debugging information
- Response content previews

## Usage

### Basic Usage
```bash
python runner.py
```

### Logging Configuration
You can modify the logging behavior by editing `logging_config.py`:

```python
# In scraper_class.py, modify the _setup_logging method:
self.logger = setup_logging(
    log_level='DEBUG',      # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    log_to_file=True,       # Save logs to file
    log_to_console=True     # Show logs in console
)
```

## File Structure

```
highcourts-scraper/
├── runner.py              # Main execution script
├── scraper_class.py       # Core scraper class with logging
├── logging_config.py      # Logging configuration
├── README.md             # This file
└── logs/                 # Log files directory (created automatically)
    └── scraper_log_YYYYMMDD_HHMMSS.log
```

## Example Output

When you run the scraper, you'll see detailed output like:

```
================================================================================
HIGH COURTS SCRAPER - TEST FLOW
================================================================================

Step 1: Initializing scraper session...
INFO: ========================================
INFO: INITIALIZING SESSION AND SCRAPING STATE LIST
INFO: ========================================
INFO: Accessing main portal: https://hcservices.ecourts.gov.in/hcservices/main.php
INFO: Successfully fetched main portal page
INFO: Found state selection dropdown
INFO: Successfully scraped 25 states/courts
INFO: Available states/courts:
INFO:   - High Court for State of Telangana (Code: 29)
INFO:   - High Court of Karnataka (Code: 19)
INFO:   - High Court of Kerala (Code: 21)
...

✅ Session initialized successfully. State list scraped.

Step 2: Simulating user selection of High Court...
✅ Selected High Court: High Court for State of Telangana (Code: 29)

Step 3: Fetching bench list for High Court for State of Telangana...
INFO: ========================================
INFO: FETCHING BENCH LIST FOR STATE CODE: 29
INFO: ========================================
INFO: Requesting bench list from: https://hcservices.ecourts.gov.in/hcservices/cases_qry/index_qry.php
INFO: Successfully parsed 3 benches
INFO: Available benches:
INFO:   - Principal Bench at Hyderabad (Code: 1)
INFO:   - Circuit Bench at Warangal (Code: 2)
INFO:   - Circuit Bench at Karimnagar (Code: 3)

✅ Successfully fetched 3 benches
```

## Troubleshooting

### Common Issues

1. **State not found**: The scraper will show all available states when the target state isn't found
2. **CAPTCHA issues**: Check the logs for CAPTCHA-related errors
3. **Network errors**: Detailed HTTP request/response logging helps identify connectivity issues

### Debug Mode

To enable debug logging, modify the logging configuration:

```python
# In scraper_class.py
self.logger = setup_logging(log_level='DEBUG', log_to_file=True, log_to_console=False)
```

This will show detailed technical information in the log files while keeping console output clean.

## Log Files

Log files are automatically created in the `logs/` directory with timestamps:
- `scraper_log_20241201_143022.log` (format: YYYYMMDD_HHMMSS)

These files contain:
- Complete HTTP request/response details
- Raw data parsing information
- Error stack traces
- Debug information for troubleshooting

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `PIL` (Pillow): Image handling for CAPTCHA
- `logging`: Built-in Python logging (no additional install needed) 