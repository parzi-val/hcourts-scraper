import requests
from bs4 import BeautifulSoup
import re
import json
import time
import logging
from datetime import datetime
from captcha_solver import CaptchaSolver

class ECourtsHCSCraper:
    def __init__(self, district_court_url):
        self.base_url = district_court_url
        self.session = requests.Session()
        self.state_map = {}
        self.bench_map = {}
        self.case_type_map = {}
        self.captcha_url = ""
        self.captcha_solver = CaptchaSolver()
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup comprehensive logging for the scraper"""
        from logging_config import setup_logging
        
        # Setup logging with default configuration
        self.logger = setup_logging(log_level='INFO', log_to_file=True, log_to_console=True)
        
        self.logger.info("=" * 60)
        self.logger.info("ECourts High Court Scraper Initialized")
        self.logger.info(f"Base URL: {self.base_url}")
        self.logger.info("=" * 60)

    def _fetch_page_content(self, url, method='GET', headers=None, data=None):
        self.logger.debug(f"Making {method} request to: {url}")
        if data:
            self.logger.debug(f"Request data: {data}")
        
        try:
            if method == 'POST':
                response = self.session.post(url, data=data, headers=headers, timeout=15)
            else:
                response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            return response
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def initialize_session(self):
        self.logger.info("=" * 40)
        self.logger.info("INITIALIZING SESSION AND SCRAPING STATE LIST")
        self.logger.info("=" * 40)
        
        main_url = f"{self.base_url}/hcservices/main.php"
        self.logger.info(f"Accessing main portal: {main_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = self._fetch_page_content(main_url, headers=headers)
        if not response:
            self.logger.error("Failed to fetch main portal page")
            return False

        self.logger.info("Successfully fetched main portal page")
        self.logger.debug(f"Page content length: {len(response.text)} characters")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        state_select = soup.find('select', {'name': 'sess_state_code'})
        
        if state_select:
            self.logger.info("Found state selection dropdown")
            state_count = 0
            for option in state_select.find_all('option'):
                if option.text.strip() and 'value' in option.attrs:
                    state_name = option.text.strip()
                    state_code = option['value']
                    self.state_map[state_name] = state_code
                    state_count += 1
                    self.logger.debug(f"Found state: '{state_name}' -> Code: {state_code}")
            
            self.logger.info(f"Successfully scraped {state_count} states/courts")
            self.logger.info("Available states/courts:")
            for state_name, state_code in self.state_map.items():
                self.logger.info(f"  - {state_name} (Code: {state_code})")
        else:
            self.logger.error("Failed to find state select element")
            return False
        
        self.logger.info("Session initialization completed successfully")
        return True

    def get_bench_list(self, state_code):
        self.logger.info("=" * 40)
        self.logger.info(f"FETCHING BENCH LIST FOR STATE CODE: {state_code}")
        self.logger.info("=" * 40)
        
        url = f"{self.base_url}/hcservices/cases_qry/index_qry.php"
        self.logger.info(f"Requesting bench list from: {url}")
        
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': f"{self.base_url}/",
            'Origin': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        payload = {
            'action_code': 'fillHCBench',
            'state_code': state_code,
            'appFlag': 'web'
        }
        
        self.logger.debug(f"Request payload: {payload}")
        
        response = self._fetch_page_content(url, method='POST', headers=headers, data=payload)
        if not response:
            self.logger.error("Failed to fetch bench list")
            return False
            
        self.logger.debug(f"Raw bench list response: {response.text}")
        
        self.bench_map = self._parse_delimited_string(response.text)
        
        self.logger.info(f"Successfully parsed {len(self.bench_map)} benches")
        self.logger.info("Available benches:")
        for bench_name, bench_code in self.bench_map.items():
            self.logger.info(f"  - {bench_name} (Code: {bench_code})")
        
        return self.bench_map

    def get_case_types(self, state_code, court_code):
        self.logger.info("=" * 40)
        self.logger.info(f"FETCHING CASE TYPES FOR STATE CODE: {state_code}, COURT CODE: {court_code}")
        self.logger.info("=" * 40)
        
        url = f"{self.base_url}/hcservices/cases_qry/index_qry.php?action_code=fillCaseType"
        self.logger.info(f"Requesting case types from: {url}")
        
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': f"{self.base_url}/",
            'Origin': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        payload = {
            'court_code': court_code,
            'state_code': state_code
        }
        
        self.logger.debug(f"Request payload: {payload}")
        
        response = self._fetch_page_content(url, method='POST', headers=headers, data=payload)
        if not response:
            self.logger.error("Failed to fetch case types")
            return False
            
        self.logger.debug(f"Raw case types response: {response.text}")
        
        self.case_type_map = self._parse_delimited_string(response.text)
        
        self.logger.info(f"Successfully parsed {len(self.case_type_map)} case types")
        self.logger.info("Available case types:")
        for case_type_name, case_type_code in self.case_type_map.items():
            self.logger.info(f"  - {case_type_name} (Code: {case_type_code})")
        
        return self.case_type_map

    def get_captcha_image(self):
        self.logger.info("=" * 40)
        self.logger.info("FETCHING CAPTCHA IMAGE")
        self.logger.info("=" * 40)
        
        url = f"{self.base_url}/hcservices/securimage/securimage_show.php"
        self.logger.info(f"Requesting captcha from: {url}")
        
        headers = {
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Referer': f"{self.base_url}/",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        
        response = self._fetch_page_content(url, headers=headers)
        if response:
            self.logger.info(f"Successfully fetched captcha image ({len(response.content)} bytes)")
            return response.content
        
        self.logger.error("Failed to fetch captcha image")
        return None

    def search_records(self, search_params):
        self.logger.info("=" * 40)
        self.logger.info("PERFORMING INITIAL SEARCH")
        self.logger.info("=" * 40)
        
        url = f"{self.base_url}/hcservices/cases_qry/index_qry.php?action_code=showRecords"
        self.logger.info(f"Searching records at: {url}")
        
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': f"{self.base_url}/",
            'Origin': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        
        self.logger.info("Search parameters:")
        for key, value in search_params.items():
            if key != 'captcha':  # Don't log captcha for security
                self.logger.info(f"  - {key}: {value}")
            else:
                self.logger.info(f"  - {key}: [HIDDEN]")
        
        response = self._fetch_page_content(url, method='POST', headers=headers, data=search_params)
        if not response:
            self.logger.error("Search request failed")
            return False
            
        self.logger.info(f"Search completed successfully. Response length: {len(response.text)} characters")
        self.logger.debug(f"Search response preview: {response.text[:500]}...")
        
        # Log the response type and structure
        try:
            import json
            search_data = json.loads(response.text)
            self.logger.info(f"Search response is valid JSON with keys: {list(search_data.keys())}")
            if 'con' in search_data:
                self.logger.info(f"Found {len(search_data['con'])} cases in response")
                if search_data['con']:
                    case_info = json.loads(search_data['con'][0])
                    self.logger.info(f"First case CINO: {case_info.get('cino')}")
                    self.logger.info(f"First case number: {case_info.get('case_no2')}")
        except json.JSONDecodeError:
            self.logger.warning("Search response is not valid JSON")
        
        return response.text

    def get_case_history(self, cino, case_no, court_code, state_code, court_complex_code):
        self.logger.info("=" * 40)
        self.logger.info("FETCHING FINAL CASE HISTORY")
        self.logger.info("=" * 40)
        
        url = f"{self.base_url}/hcservices/cases_qry/o_civil_case_history.php"
        self.logger.info(f"Requesting case history from: {url}")
        
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': f"{self.base_url}/",
            'Origin': self.base_url,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        payload = {
            'court_code': court_code,
            'state_code': state_code,
            'court_complex_code': court_complex_code,
            'case_no': case_no,
            'cino': cino,
            'appFlag': 'web'
        }
        
        self.logger.info("Case history parameters:")
        for key, value in payload.items():
            self.logger.info(f"  - {key}: {value}")
        
        response = self._fetch_page_content(url, method='POST', headers=headers, data=payload)
        if not response:
            self.logger.error("Failed to fetch case history")
            return False
            
        self.logger.info(f"Successfully fetched case history. Response length: {len(response.text)} characters")
        self.logger.debug(f"Case history preview: {response.text[:500]}...")
        
        # Check for error messages in the response
        if "THERE IS AN SQL ERROR" in response.text or "Error" in response.text:
            self.logger.error("Case history request returned an error")
            self.logger.error(f"Response preview: {response.text[:1000]}...")
        
        return response.text

    def _parse_delimited_string(self, text):
        self.logger.debug(f"Parsing delimited string: {text}")
        
        # Remove BOM characters from the text
        text = text.replace('\ufeff', '')
        
        parsed_data = {}
        pairs = text.split('#')
        self.logger.debug(f"Found {len(pairs)} pairs to parse")
        
        for i, pair in enumerate(pairs):
            if '~' in pair:
                key, value = pair.split('~', 1)
                # Clean BOM characters from both key and value
                key = key.strip().replace('\ufeff', '')
                value = value.strip().replace('\ufeff', '')
                parsed_data[value] = key
                self.logger.debug(f"Pair {i+1}: '{value}' -> '{key}'")
            else:
                self.logger.debug(f"Pair {i+1}: Skipping invalid format '{pair}'")
        
        self.logger.debug(f"Parsed {len(parsed_data)} valid entries")
        return parsed_data

    def _parse_search_results(self, html_content):
        self.logger.info("=" * 40)
        self.logger.info("PARSING SEARCH RESULTS")
        self.logger.info("=" * 40)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        rows = soup.find_all('tr')
        
        self.logger.info(f"Found {len(rows)} table rows")
        
        if not rows:
            self.logger.warning("No table rows found in search results")
            return None
            
        for i, row in enumerate(rows[1:], 1):  # Skip header row
            cells = row.find_all('td')
            if len(cells) >= 5:
                result = {
                    'sr_no': cells[0].text.strip(),
                    'case_info': cells[1].text.strip(),
                    'petitioner': cells[2].text.strip(),
                    'cino': cells[3].text.strip(),
                    'view_link': cells[4].find('a')['href'] if cells[4].find('a') else None
                }
                results.append(result)
                self.logger.debug(f"Row {i}: {result}")
            else:
                self.logger.debug(f"Row {i}: Skipping row with {len(cells)} cells (expected 5+)")
        
        self.logger.info(f"Successfully parsed {len(results)} search results")
        return results
