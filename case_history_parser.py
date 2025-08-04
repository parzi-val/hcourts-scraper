import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import json

class CaseHistoryParser:
    """Parser for case history HTML from eCourts High Court Services"""
    
    def __init__(self, html_content: str):
        self.html_content = html_content
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.parsed_data = {}
        
        # Check for error messages
        self.has_error = self._check_for_errors()
        
    def parse_all(self) -> Dict[str, Any]:
        """Parse all sections of the case history"""
        self.parsed_data = {
            'case_details': self._parse_case_details(),
            'case_status': self._parse_case_status(),
            'parties': self._parse_parties(),
            'acts': self._parse_acts(),
            'categories': self._parse_categories(),
            'subordinate_court': self._parse_subordinate_court(),
            'fir_details': self._parse_fir_details(),
            'ia_details': self._parse_ia_details(),
            'hearing_history': self._parse_hearing_history(),
            'orders': self._parse_orders(),
            'objections': self._parse_objections()
        }
        return self.parsed_data
    
    def _check_for_errors(self) -> bool:
        """Check if the HTML contains error messages"""
        error_indicators = [
            "THERE IS AN SQL ERROR",
            "Error",
            "error",
            "SQL ERROR",
            "Database Error",
            "Server Error"
        ]
        
        text_content = self.soup.get_text().lower()
        for indicator in error_indicators:
            if indicator.lower() in text_content:
                return True
        return False
    
    def get_error_message(self) -> str:
        """Get the error message if present"""
        if not self.has_error:
            return ""
        
        # Look for error messages in the HTML
        error_elements = self.soup.find_all(['h1', 'h2', 'h3', 'div', 'span'], 
                                          string=lambda text: text and any(err in text.upper() for err in ['ERROR', 'SQL']))
        
        if error_elements:
            return error_elements[0].get_text(strip=True)
        
        return "Unknown error occurred"
    
    def has_case_data(self) -> bool:
        """Check if the HTML contains actual case data"""
        # Look for common case data indicators
        case_indicators = [
            'case_details_table',
            'table_r',
            'Petitioner_Advocate_table',
            'Respondent_Advocate_table',
            'act_table',
            'history_table',
            'order_table',
            'FIR_details_table'
        ]
        
        for indicator in case_indicators:
            if self.soup.find(class_=indicator) or self.soup.find(id=indicator):
                return True
        
        # Also check for common case-related text
        text_content = self.soup.get_text().lower()
        case_text_indicators = [
            'filing number',
            'registration number',
            'petitioner',
            'respondent',
            'hearing date',
            'order'
        ]
        
        for indicator in case_text_indicators:
            if indicator in text_content:
                return True
        
        return False
    
    def _parse_case_details(self) -> Dict[str, str]:
        """Parse the case details table"""
        details = {}
        case_details_table = self.soup.find('table', class_='case_details_table')
        if not case_details_table:
            return details
            
        rows = case_details_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                # Extract labels and values
                labels = []
                values = []
                
                for i, cell in enumerate(cells):
                    if i % 2 == 0:  # Label cells (even indices)
                        label_elem = cell.find('label')
                        if label_elem:
                            labels.append(label_elem.get_text(strip=True))
                    else:  # Value cells (odd indices)
                        values.append(cell.get_text(strip=True))
                
                # Pair labels with values
                for label, value in zip(labels, values):
                    if label and value:
                        details[label] = value
        
        # Also extract CNR number from the special row
        cnr_row = case_details_table.find('tr', style=lambda x: x and 'color:#df3527' in x)
        if cnr_row:
            cnr_cell = cnr_row.find('td', colspan='3')
            if cnr_cell:
                cnr_text = cnr_cell.get_text(strip=True)
                if 'CNR Number' in cnr_text:
                    # Extract CNR number using regex
                    cnr_match = re.search(r'([A-Z]{2}HC\d+-\d+-\d+)', cnr_text)
                    if cnr_match:
                        details['CNR Number'] = cnr_match.group(1)
        
        return details
    
    def _parse_case_status(self) -> Dict[str, str]:
        """Parse the case status table"""
        status = {}
        status_table = self.soup.find('table', class_='table_r')
        if not status_table:
            return status
            
        rows = status_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label_elem = cells[0].find('label')
                value_elem = cells[1].find('strong') or cells[1]
                
                if label_elem and value_elem:
                    label = label_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    if label and value:
                        status[label] = value
        
        return status
    
    def _parse_parties(self) -> Dict[str, List[Dict[str, str]]]:
        """Parse petitioner and respondent information"""
        parties = {'petitioners': [], 'respondents': []}
        
        # Parse Petitioner and Advocate section
        petitioner_section = self.soup.find('span', class_='Petitioner_Advocate_table')
        if petitioner_section:
            petitioner_text = petitioner_section.get_text()
            parties['petitioners'] = self._parse_party_text_improved(petitioner_text)
        
        # Parse Respondent and Advocate section
        respondent_section = self.soup.find('span', class_='Respondent_Advocate_table')
        if respondent_section:
            respondent_text = respondent_section.get_text()
            parties['respondents'] = self._parse_party_text_improved(respondent_text)
        
        return parties
    
    def _parse_party_text_improved(self, text: str) -> List[Dict[str, str]]:
        """Improved party text parsing"""
        parties = []
        
        # Clean up the text first
        text = text.replace('&nbsp;', ' ')
        
        # Split by numbered entries
        party_entries = re.split(r'\d+\)', text)
        if len(party_entries) <= 1:
            return parties
        
        # Process each party entry
        for i, entry in enumerate(party_entries[1:], 1):  # Skip first empty entry
            entry = entry.strip()
            if not entry:
                continue
                
            # Extract party name (first line)
            lines = entry.split('\n')
            party_name = lines[0].strip()
            
            # Clean up party name
            party_name = re.sub(r'Advocate-[^,\n]*', '', party_name).strip()
            party_name = re.sub(r'\s+', ' ', party_name).strip()
            
            party = {'name': party_name}
            
            # Look for advocate information
            advocate_match = re.search(r'Advocate-([^,\n]+)', entry)
            if advocate_match:
                party['advocate'] = advocate_match.group(1).strip()
            
            # Look for additional details
            details = []
            for line in lines[1:]:  # Skip the first line (name)
                line = line.strip()
                if line and not line.startswith('Advocate-'):
                    details.append(line)
            
            if details:
                party['details'] = details
            
            parties.append(party)
        
        return parties
    
    def _parse_party_text(self, text: str) -> List[Dict[str, str]]:
        """Parse party text into structured data"""
        parties = []
        lines = text.split('\n')
        current_party = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new party (starts with number)
            if re.match(r'^\d+\)', line):
                if current_party:
                    parties.append(current_party)
                # Extract party name after the number
                party_name = line.split(')', 1)[1].strip()
                current_party = {'name': party_name}
            elif 'Advocate-' in line:
                # Extract advocate name
                advocate_name = line.split('Advocate-', 1)[1].strip()
                current_party['advocate'] = advocate_name
            elif current_party and (line.startswith('   ') or line.startswith('&nbsp;&nbsp;&nbsp;&nbsp;')):
                # Additional party info
                if 'details' not in current_party:
                    current_party['details'] = []
                current_party['details'].append(line.strip())
            elif current_party and re.match(r'^\d+\)', line):
                # Another party in the same section
                if current_party:
                    parties.append(current_party)
                party_name = line.split(')', 1)[1].strip()
                current_party = {'name': party_name}
        
        if current_party:
            parties.append(current_party)
        
        return parties
    
    def _parse_acts(self) -> List[Dict[str, str]]:
        """Parse the Acts table"""
        acts = []
        acts_table = self.soup.find('table', id='act_table')
        if not acts_table:
            return acts
            
        rows = acts_table.find_all('tr')[1:]  # Skip header
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                act = {
                    'act': cells[0].get_text(strip=True),
                    'section': cells[1].get_text(strip=True)
                }
                acts.append(act)
        
        return acts
    
    def _parse_categories(self) -> Dict[str, str]:
        """Parse the Category Details table"""
        categories = {}
        category_table = self.soup.find('table', id='subject_table')
        if not category_table:
            return categories
            
        rows = category_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if label and value:
                    categories[label] = value
        
        return categories
    
    def _parse_subordinate_court(self) -> Dict[str, str]:
        """Parse the Subordinate Court Information"""
        court_info = {}
        court_section = self.soup.find('span', class_='Lower_court_table')
        if not court_section:
            return court_info
            
        text = court_section.get_text()
        
        # Extract key-value pairs using regex
        patterns = [
            r'Court Number and Name\s*:\s*([^:]+)',
            r'Case Number and Year\s*:\s*([^:]+)',
            r'Case Decision Date\s*:\s*:\s*([^:]+)',
            r'state\s*:\s*([^:]+)',
            r'District\s*:\s*([^:]+)'
        ]
        
        keys = [
            'Court Number and Name',
            'Case Number and Year', 
            'Case Decision Date',
            'State',
            'District'
        ]
        
        for pattern, key in zip(patterns, keys):
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                court_info[key] = value
        
        return court_info
    
    def _parse_fir_details(self) -> Dict[str, str]:
        """Parse the FIR Details section"""
        fir_info = {}
        fir_section = self.soup.find('span', class_='FIR_details_table')
        if not fir_section:
            return fir_info
            
        # Parse each line separately to avoid concatenation issues
        lines = fir_section.get_text().split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                # Split on first colon
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    # Clean up extra whitespace and remove any trailing text
                    value = re.sub(r'\s+', ' ', value).strip()
                    # Remove any trailing text that might be part of the next field
                    value = re.sub(r'\s+[A-Za-z\s]+$', '', value).strip()
                    fir_info[key] = value
        
        return fir_info
    
    def _parse_ia_details(self) -> List[Dict[str, str]]:
        """Parse the IA Details table"""
        ia_details = []
        ia_table = self.soup.find('table', class_='IAheading')
        if not ia_table:
            return ia_details
            
        rows = ia_table.find_all('tr')[1:]  # Skip header
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                ia = {
                    'ia_number': cells[0].get_text(strip=True),
                    'party': cells[1].get_text(strip=True),
                    'filing_date': cells[2].get_text(strip=True),
                    'next_date': cells[3].get_text(strip=True),
                    'status': cells[4].get_text(strip=True)
                }
                ia_details.append(ia)
        
        return ia_details
    
    def _parse_hearing_history(self) -> List[Dict[str, str]]:
        """Parse the History of Case Hearing table"""
        history = []
        history_table = self.soup.find('table', class_='history_table')
        if not history_table:
            return history
            
        rows = history_table.find_all('tr')[1:]  # Skip header
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                # Skip rows that look like order table headers
                first_cell = cells[0].get_text(strip=True)
                if first_cell in ['Order Number', '1', '2', '3']:
                    continue
                    
                hearing = {
                    'cause_list_type': cells[0].get_text(strip=True),
                    'judge': cells[1].get_text(strip=True),
                    'business_date': cells[2].get_text(strip=True),
                    'hearing_date': cells[3].get_text(strip=True),
                    'purpose': cells[4].get_text(strip=True)
                }
                history.append(hearing)
        
        return history
    
    def _parse_orders(self) -> List[Dict[str, str]]:
        """Parse the Orders table"""
        orders = []
        orders_table = self.soup.find('table', class_='order_table')
        if not orders_table:
            return orders
            
        rows = orders_table.find_all('tr')[1:]  # Skip header
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                order = {
                    'order_number': cells[0].get_text(strip=True),
                    'order_on': cells[1].get_text(strip=True),
                    'judge': cells[2].get_text(strip=True),
                    'order_date': cells[3].get_text(strip=True),
                    'order_details': cells[4].get_text(strip=True)
                }
                
                # Extract PDF link if available
                pdf_link = cells[4].find('a')
                if pdf_link and 'href' in pdf_link.attrs:
                    order['pdf_url'] = pdf_link['href']
                
                orders.append(order)
        
        return orders
    
    def _parse_objections(self) -> List[Dict[str, str]]:
        """Parse the Objection table"""
        objections = []
        objection_table = self.soup.find('table', class_='obj_table')
        if not objection_table:
            return objections
            
        rows = objection_table.find_all('tr')[1:]  # Skip header
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:
                objection = {
                    'sr_no': cells[0].get_text(strip=True),
                    'scrutiny_date': cells[1].get_text(strip=True),
                    'objection': cells[2].get_text(strip=True),
                    'compliance_date': cells[3].get_text(strip=True),
                    'receipt_date': cells[4].get_text(strip=True)
                }
                objections.append(objection)
        
        return objections
    
    def get_structured_data(self) -> Dict[str, Any]:
        """Get the complete structured data"""
        return self.parse_all()
    
    def save_to_json(self, filename: str = 'parsed_case_history.json'):
        """Save parsed data to JSON file"""
        data = self.get_structured_data()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Parsed case history saved to '{filename}'")
    
    def print_summary(self):
        """Print a summary of the parsed data"""
        data = self.get_structured_data()
        
        print("\n" + "=" * 80)
        print("CASE HISTORY PARSING SUMMARY")
        print("=" * 80)
        
        # Check for errors first
        if self.has_error:
            print(f"\n❌ ERROR DETECTED:")
            print(f"  {self.get_error_message()}")
            print("\nThis indicates the case history request failed on the server side.")
            print("Possible causes:")
            print("  - Invalid case parameters (CINO, case number, etc.)")
            print("  - Server-side database issues")
            print("  - Session timeout or authentication issues")
            print("  - Network connectivity problems")
            return
        
        # Check if we have actual case data
        if not self.has_case_data():
            print(f"\n⚠️  NO CASE DATA FOUND:")
            print("The HTML doesn't contain expected case data tables.")
            print("This could mean:")
            print("  - The case doesn't exist in the database")
            print("  - The case parameters are incorrect")
            print("  - The server returned an empty response")
            print("  - The HTML structure is different than expected")
            return
        
        # Case Details
        if data['case_details']:
            print("\n📋 CASE DETAILS:")
            for key, value in data['case_details'].items():
                print(f"  {key}: {value}")
        
        # Case Status
        if data['case_status']:
            print("\n📊 CASE STATUS:")
            for key, value in data['case_status'].items():
                print(f"  {key}: {value}")
        
        # Parties
        if data['parties']['petitioners']:
            print(f"\n👥 PETITIONERS ({len(data['parties']['petitioners'])}):")
            for i, petitioner in enumerate(data['parties']['petitioners'], 1):
                print(f"  {i}. {petitioner.get('name', 'N/A')}")
                if 'advocate' in petitioner:
                    print(f"     Advocate: {petitioner['advocate']}")
        
        if data['parties']['respondents']:
            print(f"\n👥 RESPONDENTS ({len(data['parties']['respondents'])}):")
            for i, respondent in enumerate(data['parties']['respondents'], 1):
                print(f"  {i}. {respondent.get('name', 'N/A')}")
                if 'advocate' in respondent:
                    print(f"     Advocate: {respondent['advocate']}")
        
        # Acts
        if data['acts']:
            print(f"\n📜 ACTS ({len(data['acts'])}):")
            for act in data['acts']:
                print(f"  {act['act']} - Section {act['section']}")
        
        # FIR Details
        if data['fir_details']:
            print(f"\n🚨 FIR DETAILS:")
            for key, value in data['fir_details'].items():
                print(f"  {key}: {value}")
        
        # Hearing History
        if data['hearing_history']:
            print(f"\n📅 HEARING HISTORY ({len(data['hearing_history'])} entries):")
            for hearing in data['hearing_history'][:3]:  # Show first 3
                print(f"  {hearing['hearing_date']}: {hearing['purpose']} (Judge: {hearing['judge']})")
            if len(data['hearing_history']) > 3:
                print(f"  ... and {len(data['hearing_history']) - 3} more entries")
        
        # Orders
        if data['orders']:
            print(f"\n📄 ORDERS ({len(data['orders'])}):")
            for order in data['orders']:
                print(f"  Order {order['order_number']}: {order['order_on']} ({order['order_date']})")
        
        # Objections
        if data['objections']:
            print(f"\n⚠️ OBJECTIONS ({len(data['objections'])}):")
            for objection in data['objections']:
                print(f"  {objection['objection']} (Date: {objection['scrutiny_date']})")
        
        print("\n" + "=" * 80) 