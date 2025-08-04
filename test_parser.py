#!/usr/bin/env python3
"""
Test script for the Case History Parser
"""

from case_history_parser import CaseHistoryParser
import json

def test_parser():
    """Test the case history parser with the sample HTML"""
    
    print("=" * 80)
    print("TESTING CASE HISTORY PARSER")
    print("=" * 80)
    
    # Read the case history HTML
    try:
        with open('case_history.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        print("✅ Successfully loaded case_history.html")
    except FileNotFoundError:
        print("❌ case_history.html not found. Please run the scraper first.")
        return
    
    # Parse the HTML
    parser = CaseHistoryParser(html_content)
    
    # Get structured data
    data = parser.get_structured_data()
    
    # Print summary
    parser.print_summary()
    
    # Save to JSON
    parser.save_to_json('test_parsed_case_history.json')
    
    # Show some specific data
    print("\n" + "=" * 80)
    print("DETAILED DATA EXAMPLES")
    print("=" * 80)
    
    # Case Details
    if data['case_details']:
        print("\n📋 CASE DETAILS:")
        for key, value in data['case_details'].items():
            print(f"  {key}: {value}")
    
    # CNR Number (if found)
    if 'CNR Number' in data['case_details']:
        print(f"\n🔢 CNR Number: {data['case_details']['CNR Number']}")
    
    # Next Hearing Date
    if data['case_status'] and 'Next Hearing Date' in data['case_status']:
        print(f"\n📅 Next Hearing: {data['case_status']['Next Hearing Date']}")
    
    # Orders with PDF links
    if data['orders']:
        print(f"\n📄 ORDERS WITH PDF LINKS:")
        for order in data['orders']:
            print(f"  Order {order['order_number']}: {order['order_on']}")
            if 'pdf_url' in order:
                print(f"    PDF: {order['pdf_url']}")
    
    # Hearing History
    if data['hearing_history']:
        print(f"\n📅 HEARING HISTORY:")
        for hearing in data['hearing_history'][:3]:  # Show first 3
            print(f"  {hearing['hearing_date']}: {hearing['purpose']}")
    
    print("\n" + "=" * 80)
    print("✅ Parser test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    test_parser() 