# High Courts Scraper

A Python scraper for extracting case information from Indian High Court websites using the eCourts portal.

## Features

- **State/Court Discovery**: Automatically discovers available states and courts
- **Bench and Case Type Mapping**: Fetches and maps available benches and case types
- **CAPTCHA Handling**: Manual CAPTCHA solving with image display
- **Case History Extraction**: Complete case history retrieval with comprehensive parsing
- **FIR Details**: Extracts FIR (First Information Report) details when available
- **Multiple Search Results**: Handles cases with multiple search results
- **Error Detection**: Detects and reports server-side errors and malformed responses

## What It Does

The scraper performs a complete case search flow:

1. **Initialization**: Connects to eCourts portal and scrapes available states/courts
2. **State Selection**: Finds and selects the target High Court (e.g., Calcutta High Court)
3. **Bench Discovery**: Fetches available benches for the selected court (e.g., Circuit Bench at Jalpaiguri)
4. **Case Type Mapping**: Retrieves available case types and their codes
5. **CAPTCHA Handling**: Displays CAPTCHA image for manual solving
6. **Case Search**: Performs search with case parameters (type, number, year)
7. **Result Processing**: Handles single or multiple search results
8. **Case History**: Retrieves and parses complete case history
9. **Data Extraction**: Extracts all case details including FIR information

## Usage

### Basic Usage
```bash
python runner.py
```

### Test with Known Parameters
```bash
python test_proper_case.py
```

### Parse Existing Case History
```bash
python -c "from case_history_parser import CaseHistoryParser; parser = CaseHistoryParser(open('case_history.html', 'r', encoding='utf-8').read()); parser.print_summary()"
```

## File Structure

```
highcourts-scraper/
├── runner.py                    # Main execution script
├── scraper_class.py             # Core scraper class
├── case_history_parser.py       # Comprehensive case history parser
├── test_proper_case.py          # Test script with known working parameters
├── test_parser.py               # Standalone parser test
├── logging_config.py            # Logging configuration
├── README.md                    # This file
├── case_history.html            # Sample case history (generated)
├── parsed_case_history.json     # Parsed output (generated)
└── logs/                        # Log files directory
    └── scraper_log_*.log
```

## Parsed Data Structure

The scraper extracts comprehensive case information:

### Case Details
- Filing Number, Filing Date
- Registration Number, Registration Date
- CNR Number

### Case Status
- First Hearing Date, Decision Date
- Case Status, Nature of Disposal
- Coram, Bench Type, Judicial Branch
- State, District

### Parties
- **Petitioners**: Names and advocates
- **Respondents**: Names and advocates

### Legal Information
- **Acts**: Under which acts and sections
- **Categories**: Case category and sub-category
- **Subordinate Court**: Lower court information

### **FIR Details** (when available)
- State, District, Police Station
- FIR Number, Year

### Case History
- **Hearing History**: Complete hearing timeline
- **Orders**: Order details with PDF links
- **Objections**: Scrutiny objections and compliance

## Example Output

```
================================================================================
CASE HISTORY PARSING SUMMARY
================================================================================

📋 CASE DETAILS:
  Filing Number: CRM(DB) /124/2024
  Filing Date: 28-02-2024
  Registration Number: CRM(DB) /123/2024
  Registration Date: 28-02-2024

📊 CASE STATUS:
  First Hearing Date: 04th March 2024
  Decision Date: 03rd May 2024
  Case Status: CASE DISPOSED
  Coram: HON'BLE JUSTICE SOUMEN SEN , HON'BLE JUSTICE PARTHA SARATHI SEN

👥 PETITIONERS (1):
  1. SANJIT BARMAN
     Advocate: Hillol Saha Podder

👥 RESPONDENTS (1):
  1. THE STATE OF WEST BENGAL

📜 ACTS (1):
  Code of Criminal Procedure, 1973 Act ,1974 - Section U/S439

🚨 FIR DETAILS:
  State: West Bengal
  District: JALPAIGURI
  Police Station: NEW JALPAIGURI
  FIR Number: 955
  Year: 2021

📅 HEARING HISTORY (20 entries):
  04-03-2024: APPLICATION FOR BAIL (Judge: )
  03-05-2024: Disposed (Judge: HON'BLE JUSTICE SOUMEN SEN , HON'BLE JUSTICE PARTHA SARATHI SEN)
  ... and 17 more entries

📄 ORDERS (2):
  Order 1: CRM(DB)/123/2024 (22-04-2024)
  Order 2: CRM(DB)/123/2024 (03-05-2024)
```

## Configuration

### Current Parameters (Calcutta High Court)
- **High Court**: Calcutta High Court
- **Bench**: Circuit Bench at Jalpaiguri
- **Case Type**: CRM(DB)(BAIL APPLICATIONS A THE PRE CONVICTION STAGE WHERE SENTENCE MAY EXCEED IMPRISONMENT) (Code: 58)
- **Case Number**: 123
- **Year**: 2024

To change parameters, edit the values in `runner.py` or `test_proper_case.py`.

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `PIL` (Pillow): Image handling for CAPTCHA
- `logging`: Built-in Python logging

## Installation

```bash
pip install requests beautifulsoup4 Pillow
```

## Troubleshooting

### Common Issues

1. **State not found**: The scraper will show all available states when the target state isn't found
2. **CAPTCHA issues**: Check the logs for CAPTCHA-related errors
3. **Network errors**: Check internet connectivity and server availability
4. **Malformed responses**: The parser handles SQL errors and malformed HTML gracefully

### Error Detection

The scraper detects and reports:
- Server-side SQL errors
- Invalid CAPTCHA responses
- Missing case data
- Malformed HTML responses
- Network connectivity issues 