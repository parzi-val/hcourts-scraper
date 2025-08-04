#!/usr/bin/env python3
"""
Test script to get a proper case history with correct parameters
"""

from scraper_class import ECourtsHCSCraper
from case_history_parser import CaseHistoryParser
import json

def test_proper_case():
    """Test with a known working case"""
    
    print("=" * 80)
    print("TESTING PROPER CASE HISTORY")
    print("=" * 80)
    
    # Initialize scraper
    BASE_URL = "https://hcservices.ecourts.gov.in"
    scraper = ECourtsHCSCraper(BASE_URL)
    
    if not scraper.initialize_session():
        print("❌ Failed to initialize session")
        return
    
    print("✅ Session initialized")
    
    # Find Calcutta High Court
    target_states = ["Calcutta High Court", "High Court at Calcutta", "High Court of Calcutta"]
    state_code = None
    for state_name in target_states:
        if state_name in scraper.state_map:
            state_code = scraper.state_map[state_name]
            break
    
    if not state_code:
        print("❌ Calcutta High Court not found")
        return
    
    print(f"✅ Found Calcutta High Court (Code: {state_code})")
    
    # Get bench list and find Circuit Bench at Jalpaiguri
    bench_map = scraper.get_bench_list(state_code)
    if not bench_map:
        print("❌ Failed to get bench list")
        return
    
    target_bench = "Circuit Bench At Jalpaiguri"
    court_code = None
    for bench_name, bench_code in bench_map.items():
        if target_bench in bench_name:
            court_code = bench_code
            break
    
    if not court_code:
        print(f"❌ Circuit Bench At Jalpaiguri not found")
        return
    
    court_complex_code = court_code  # Same as court_code
    case_type = '58'   # CRM(DB)(BAIL APPLICATIONS A THE PRE CONVICTION STAGE WHERE SENTENCE MAY EXCEED IMPRISONMENT)
    case_no = '123'
    rgyear = '2024'
    
    print(f"✅ Using parameters:")
    print(f"  - State: Calcutta High Court (Code: {state_code})")
    print(f"  - Bench: Circuit Bench at Jalpaiguri (Code: {court_code})")
    print(f"  - Case Type: CRM(DB)(BAIL APPLICATIONS A THE PRE CONVICTION STAGE WHERE SENTENCE MAY EXCEED IMPRISONMENT) (Code: {case_type})")
    print(f"  - Case Number: {case_no}")
    print(f"  - Year: {rgyear}")
    
    # Get CAPTCHA
    print("\n📷 Getting CAPTCHA...")
    captcha_image_data = scraper.get_captcha_image()
    if not captcha_image_data:
        print("❌ Failed to get CAPTCHA")
        return
    
    print("✅ CAPTCHA image received")
    captcha_value = input("Please enter the CAPTCHA code: ").strip()
    if not captcha_value:
        print("❌ No CAPTCHA entered")
        return
    
    # Search for the case
    print("\n🔍 Searching for case...")
    search_params = {
        'court_code': court_code,
        'state_code': state_code,
        'court_complex_code': court_complex_code,
        'caseStatusSearchType': 'CScaseNumber',
        'captcha': captcha_value,
        'case_type': case_type,
        'case_no': case_no,
        'rgyear': rgyear,
        'caseNoType': 'new',
        'displayOldCaseNo': 'NO'
    }
    
    search_results = scraper.search_records(search_params)
    if not search_results:
        print("❌ Search failed")
        return
    
    print("✅ Search successful")
    
    # Parse search results
    import json
    if search_results.startswith('\ufeff'):
        search_results = search_results[1:]
    
    try:
        outer_json = json.loads(search_results)
        if "Invalid Captcha" in outer_json.get("con", [""])[0]:
            print("❌ Invalid CAPTCHA")
            return
        
        case_list = json.loads(outer_json["con"][0])
        if not case_list:
            print("❌ No search results")
            return
        
        case_data = case_list[0] if isinstance(case_list, list) else case_list
        cino = case_data.get('cino')
        case_no = case_data.get('case_no')
        
        print(f"✅ Found case:")
        print(f"  - CINO: {cino}")
        print(f"  - Case Number: {case_no}")
        
        # Get case history
        print("\n📄 Getting case history...")
        case_history_html = scraper.get_case_history(cino, case_no, court_code, state_code, court_complex_code)
        
        if not case_history_html:
            print("❌ Failed to get case history")
            return
        
        # Save and parse
        with open('proper_case_history.html', 'w', encoding='utf-8') as f:
            f.write(case_history_html)
        print("✅ Case history saved to 'proper_case_history.html'")
        
        # Parse the case history
        parser = CaseHistoryParser(case_history_html)
        parser.print_summary()
        parser.save_to_json('proper_parsed_case_history.json')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Search results: {search_results[:500]}")

if __name__ == "__main__":
    test_proper_case() 