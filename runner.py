from scraper_class import ECourtsHCSCraper
import os
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import logging
import json

def run_test_flow():
    """
    Simulates the full scraping process to confirm the flow works.
    """
    # --- 1. CONFIGURATION ---
    # The base URL for the High Court services portal.
    BASE_URL = "https://hcservices.ecourts.gov.in"
    
    print("=" * 80)
    print("HIGH COURTS SCRAPER - TEST FLOW")
    print("=" * 80)
    
    # --- 2. INITIALIZE SCRAPER AND SESSION ---
    print("\nStep 1: Initializing scraper session...")
    scraper = ECourtsHCSCraper(BASE_URL)
    
    if not scraper.initialize_session():
        print("❌ Failed to initialize session. Exiting.")
        return
    
    print("✅ Session initialized successfully. State list scraped.")
    
    # --- 3. SIMULATE USER CHOOSING A HIGH COURT ---
    print("\nStep 2: Simulating user selection of High Court...")
    # Try to find Calcutta High Court
    target_states = [
        "Calcutta High Court",
        "High Court at Calcutta",
        "High Court of Calcutta"
    ]
    
    selected_state = None
    selected_state_code = None
    
    for state_name in target_states:
        if state_name in scraper.state_map:
            selected_state = state_name
            selected_state_code = scraper.state_map[state_name]
            break
    
    if not selected_state:
        print("❌ Target state not found. Available states:")
        for state_name, state_code in scraper.state_map.items():
            print(f"  - {state_name} (Code: {state_code})")
        return
    
    print(f"✅ Selected High Court: {selected_state} (Code: {selected_state_code})")
    
    # --- 4. FETCH BENCH LIST ---
    print(f"\nStep 3: Fetching bench list for {selected_state}...")
    bench_map = scraper.get_bench_list(selected_state_code)
    if not bench_map:
        print("❌ Failed to get bench list. Exiting.")
        return
    
    print(f"✅ Successfully fetched {len(bench_map)} benches")
    
    # Find Circuit Bench at Jalpaiguri
    target_bench = "Circuit Bench At Jalpaiguri"
    court_code = None
    for bench_name, bench_code in bench_map.items():
        if target_bench in bench_name:
            court_code = bench_code
            break
    
    if not court_code:
        print(f"❌ Target bench '{target_bench}' not found. Available benches:")
        for bench_name, bench_code in bench_map.items():
            print(f"  - {bench_name} (Code: {bench_code})")
        return
    
    print(f"✅ Selected Bench: {target_bench} (Code: {court_code})")
        
    # --- 5. FETCH CASE TYPES ---
    print(f"\nStep 4: Fetching case types for court code {court_code}...")
    case_types = scraper.get_case_types(selected_state_code, court_code)
    if not case_types:
        print("❌ Failed to get case types. Exiting.")
        return

    print(f"✅ Successfully fetched {len(case_types)} case types")
    print("Bench and Case Type lists fetched successfully.")

    # --- 6. SOLVE CAPTCHA (AUTOMATIC) ---
    print("\nStep 5: Fetching and solving CAPTCHA automatically...")
    captcha_image_data = scraper.get_captcha_image()
    if not captcha_image_data:
        print("❌ Failed to get CAPTCHA image. Exiting.")
        return
        
    captcha_value, was_auto_solved = scraper.captcha_solver.solve_captcha_with_fallback(captcha_image_data)
    
    if not captcha_value:
        print("❌ Failed to solve CAPTCHA. Exiting.")
        return

    print(f"✅ CAPTCHA solved automatically: {captcha_value}")

    # --- 7. PERFORM FINAL SEARCH ---
    print("\nStep 6: Performing the final search...")
    # Use the specified case parameters
    case_type_name = "CRM(DB)(BAIL APPLICATIONS A THE PRE CONVICTION STAGE WHERE SENTENCE MAY EXCEED IMPRISONMENT)-58"
    case_type_code = case_types.get(case_type_name)
    case_no = '123'
    rgyear = '2024'
    
    if not case_type_code:
        print(f"❌ Case type '{case_type_name}' not found. Available case types:")
        for case_type, code in list(case_types.items())[:10]:  # Show first 10
            print(f"  - {case_type} (Code: {code})")
        return
    
    print(f"✅ Using case type: {case_type_name} (Code: {case_type_code})")
    print(f"✅ Using case number: {case_no}")
    print(f"✅ Using year: {rgyear}")
    
    search_params = {
        'court_code': court_code,
        'state_code': selected_state_code,
        'court_complex_code': court_code, # This is the same as court_code
        'caseStatusSearchType': 'CScaseNumber',
        'captcha': captcha_value,
        'case_type': case_type_code,
        'case_no': case_no,
        'rgyear': rgyear,
        'caseNoType': 'new',
        'displayOldCaseNo': 'NO'
    }
    
    search_results_html = scraper.search_records(search_params)
    
    if not search_results_html:
        print("❌ Search failed. Check CAPTCHA and try again.")
        return
        
    print("✅ Search successful. Parsing intermediate results...")
    
    # --- 8. PARSE SEARCH RESULTS AND GET CINO ---
    print("\nStep 7: Parsing search results...")
    
    # The search results are returned as double-encoded JSON
    try:
        # Handle UTF-8 BOM
        if search_results_html.startswith('\ufeff'):
            search_results_html = search_results_html[1:]  # Remove BOM
        
        print("✅ Parsing double-encoded JSON response")
        
        # First parse: Get the outer JSON structure
        outer_json = json.loads(search_results_html)
        
        # Check for invalid captcha
        if "Invalid Captcha" in outer_json.get("con", [""])[0]:
            print("❌ Invalid CAPTCHA. Please try again.")
            return
        
        # Second parse: Get the actual case data from the "con" field
        case_list = json.loads(outer_json["con"][0])
        
        # Check if we have multiple results or single result
        if isinstance(case_list, list) and len(case_list) > 1:
            print(f"✅ Found {len(case_list)} search results. Using the first one for demo.")
            print("Note: In production, you would show a table for user selection.")
            case_data = case_list[0]
        elif isinstance(case_list, list) and len(case_list) == 1:
            print("✅ Found single search result.")
            case_data = case_list[0]
        else:
            print("❌ No search results found.")
            return
        
        print("✅ Successfully parsed double-encoded JSON")
        
        # Extract required parameters from the parsed case data
        cino = case_data.get('cino')
        case_no = case_data.get('case_no')  # Use their internal case_no mapping
        case_year = case_data.get('case_year')
        petitioner = case_data.get('pet_name')
        respondent = case_data.get('res_name')
        
        print(f"✅ Extracted case information:")
        print(f"  - CINO: {cino}")
        print(f"  - Case Number: {case_no}")
        print(f"  - Case Year: {case_year}")
        print(f"  - Petitioner: {petitioner}")
        print(f"  - Respondent: {respondent}")
        
        if not cino or not case_no:
            print("❌ Failed to extract CINO or case number from search results. Exiting.")
            return
            
        # court_complex_code is the same as court_code
        court_complex_code = court_code
        print(f"  - Court Complex Code: {court_complex_code}")
        
        # Save the clean parsed data for debugging (optional)
        with open('search_results_html.json', 'w') as f: 
            json.dump(case_data, f, indent=2)
            
    except Exception as e:
        print("❌ Failed to parse search results. Exiting.")
        print(f"Error: {e}")
        print("Search results preview:")
        print(search_results_html[:500])
        return
        
    # --- 9. FETCH FINAL CASE HISTORY ---
    print("\nStep 8: Fetching final case history...")
    case_history_html = scraper.get_case_history(cino, case_no, court_code, selected_state_code, court_complex_code)
    
    if not case_history_html:
        print("❌ Failed to get final case history. Exiting.")
        return

    # Save the case history HTML for analysis
    with open('case_history.html', 'w', encoding='utf-8') as f:
        f.write(case_history_html)
    print("✅ Case history HTML saved to 'case_history.html'")

    # Parse the case history HTML
    print("\nStep 9: Parsing case history...")
    from case_history_parser import CaseHistoryParser
    
    parser = CaseHistoryParser(case_history_html)
    parser.print_summary()
    parser.save_to_json()

    print("\n" + "=" * 80)
    print("✅ Test flow completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        from scraper_class import ECourtsHCSCraper
    except ImportError:
        print("❌ Error: Could not import ECourtsHCSCraper class. Make sure it's in a file named `scraper_class.py`.")
        exit()
        
    run_test_flow()