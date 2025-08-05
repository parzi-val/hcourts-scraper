from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from scraper_class import ECourtsHCSCraper
from case_history_parser import CaseHistoryParser
import base64
from io import BytesIO
import json
import os

app = FastAPI(title="High Courts Case Scraper")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Global scraper instance
scraper = None

class SearchRequest(BaseModel):
    state: str
    bench: str
    case_type: str
    case_no: str
    year: str
    captcha_value: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/states")
async def get_states():
    """Get all available states"""
    global scraper
    try:
        if not scraper:
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
        
        states = list(scraper.state_map.keys())
        return {"success": True, "states": states}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching states: {str(e)}")

@app.post("/api/benches")
async def get_benches(request: Request):
    """Get benches for a specific state"""
    global scraper
    try:
        data = await request.json()
        state_name = data.get("state")
        
        if not state_name:
            raise HTTPException(status_code=400, detail="State name required")
        
        if not scraper:
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
        
        # Find state code
        state_code = None
        for name, code in scraper.state_map.items():
            if state_name.lower() in name.lower():
                state_code = code
                break
        
        if not state_code:
            raise HTTPException(status_code=400, detail="State not found")
        
        # Get benches
        if not scraper.get_bench_list(state_code):
            raise HTTPException(status_code=500, detail="Failed to fetch benches")
        
        benches = list(scraper.bench_map.keys())
        return {"success": True, "benches": benches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching benches: {str(e)}")

@app.post("/api/case-types")
async def get_case_types(request: Request):
    """Get case types for a specific state and bench"""
    global scraper
    try:
        data = await request.json()
        state_name = data.get("state")
        bench_name = data.get("bench")
        
        if not state_name or not bench_name:
            raise HTTPException(status_code=400, detail="State and bench required")
        
        if not scraper:
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
        
        # Find state code
        state_code = None
        for name, code in scraper.state_map.items():
            if state_name.lower() in name.lower():
                state_code = code
                break
        
        if not state_code:
            raise HTTPException(status_code=400, detail="State not found")
        
        # Get benches
        if not scraper.get_bench_list(state_code):
            raise HTTPException(status_code=500, detail="Failed to fetch benches")
        
        # Find bench code
        bench_code = None
        for name, code in scraper.bench_map.items():
            if bench_name.lower() in name.lower():
                bench_code = code
                break
        
        if not bench_code:
            raise HTTPException(status_code=400, detail="Bench not found")
        
        # Get case types
        if not scraper.get_case_types(state_code, bench_code):
            raise HTTPException(status_code=500, detail="Failed to fetch case types")
        
        case_types = list(scraper.case_type_map.keys())
        return {"success": True, "case_types": case_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching case types: {str(e)}")

@app.get("/api/captcha")
async def get_captcha():
    """Get CAPTCHA image"""
    global scraper
    try:
        if not scraper:
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
        
        captcha_image = scraper.get_captcha_image()
        if not captcha_image:
            raise HTTPException(status_code=500, detail="Failed to fetch CAPTCHA")
        
        # Convert to base64
        captcha_base64 = base64.b64encode(captcha_image).decode('utf-8')
        return {"success": True, "captcha_image": f"data:image/png;base64,{captcha_base64}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching CAPTCHA: {str(e)}")

@app.post("/api/search")
async def search_case(request: Request):
    """Search for cases"""
    global scraper
    try:
        data = await request.json()
        state_name = data.get("state")
        bench_name = data.get("bench")
        case_type = data.get("case_type")
        case_no = data.get("case_no")
        year = data.get("year")
        captcha_value = data.get("captcha_value")
        
        if not all([state_name, bench_name, case_type, case_no, year, captcha_value]):
            raise HTTPException(status_code=400, detail="All fields are required")
        
        if not scraper:
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
        
        # Find state code
        state_code = None
        for name, code in scraper.state_map.items():
            if state_name.lower() in name.lower():
                state_code = code
                break
        
        if not state_code:
            raise HTTPException(status_code=400, detail="State not found")
        
        # Get benches
        if not scraper.get_bench_list(state_code):
            raise HTTPException(status_code=500, detail="Failed to fetch benches")
        
        # Find bench code
        bench_code = None
        for name, code in scraper.bench_map.items():
            if bench_name.lower() in name.lower():
                bench_code = code
                break
        
        if not bench_code:
            raise HTTPException(status_code=400, detail="Bench not found")
        
        # Get case types
        if not scraper.get_case_types(state_code, bench_code):
            raise HTTPException(status_code=500, detail="Failed to fetch case types")
        
        # Find case type code
        case_type_code = None
        for name, code in scraper.case_type_map.items():
            if case_type.lower() in name.lower():
                case_type_code = code
                break
        
        if not case_type_code:
            # Try to use the case_type directly as a code
            case_type_code = case_type
            print(f"Using case_type directly as code: {case_type_code}")
        
        print(f"Selected case type code: {case_type_code}")
        print(f"Available case types: {list(scraper.case_type_map.keys())[:5]}...")  # Show first 5 for debugging
        
        # Prepare search parameters
        search_params = {
            'court_code': bench_code,
            'state_code': state_code,
            'court_complex_code': bench_code,
            'caseStatusSearchType': 'CScaseNumber',
            'captcha': captcha_value,
            'case_type': case_type_code,
            'case_no': case_no,
            'rgyear': year,
            'caseNoType': 'new',
            'displayOldCaseNo': 'NO'
        }
        
        # Perform search
        search_results = scraper.search_records(search_params)
        if not search_results:
            raise HTTPException(status_code=404, detail="No search results found")
        
        # Parse results
        try:
            # Remove BOM if present
            if search_results.startswith('\ufeff'):
                search_results = search_results[1:]
            
            # Debug: Print the actual response
            print(f"Search response: {search_results[:500]}...")
            
            outer_json = json.loads(search_results)
            if "Invalid Captcha" in outer_json.get("con", [""])[0]:
                raise HTTPException(status_code=400, detail="Invalid CAPTCHA")
            
            case_list = json.loads(outer_json["con"][0])
            if isinstance(case_list, list):
                results = case_list
            else:
                results = [case_list] if case_list else []
            
            # Add missing fields that the frontend expects
            for result in results:
                # Add court_code and state_code if not present
                if 'court_code' not in result:
                    result['court_code'] = bench_code
                if 'state_code' not in result:
                    result['state_code'] = state_code
                if 'court_complex_code' not in result:
                    result['court_complex_code'] = bench_code
                
                # Map case_no2 to case_no if case_no is not present
                if 'case_no' not in result and 'case_no2' in result:
                    result['case_no'] = str(result['case_no2'])
                
                # Add petitioner and respondent fields if not present
                if 'petitioner' not in result and 'pet_name' in result:
                    result['petitioner'] = result['pet_name']
                if 'respondent' not in result and 'res_name' in result:
                    result['respondent'] = result['res_name']
                
                # Add filing_date if not present
                if 'filing_date' not in result and 'case_year' in result:
                    result['filing_date'] = str(result['case_year'])
            
            return {"success": True, "results": results}
        except json.JSONDecodeError as e:
            # Log the actual response for debugging
            print(f"JSON Parse Error: {e}")
            print(f"Response preview: {search_results[:500]}...")
            
            # Check if it's an HTML error page
            if "<html" in search_results.lower() or "<!doctype" in search_results.lower():
                raise HTTPException(status_code=500, detail="Server returned HTML instead of JSON. Check search parameters.")
            
            raise HTTPException(status_code=500, detail="Failed to parse search results")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during search: {str(e)}")

@app.post("/api/case-details")
async def get_case_details(request: Request):
    """Get detailed case information"""
    global scraper
    try:
        data = await request.json()
        selected_case = data.get("case")
        
        if not selected_case:
            raise HTTPException(status_code=400, detail="Case data required")
        
        if not scraper:
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
        
        # Debug: Print the selected case data
        print(f"Selected case data: {selected_case}")
        
        # Extract the required parameters from the case data
        cino = selected_case.get('cino')
        case_no = selected_case.get('case_no')  # This is their internal case_no
        case_no2 = selected_case.get('case_no2')  # This is the original case number
        court_code = selected_case.get('court_code', '1')  # Default to 1 if not present
        state_code = selected_case.get('state_code', '29')  # Default to 29 if not present
        court_complex_code = selected_case.get('court_complex_code', court_code)
        
        print(f"Extracted parameters:")
        print(f"  - CINO: {cino}")
        print(f"  - Case No: {case_no}")
        print(f"  - Case No2: {case_no2}")
        print(f"  - Court Code: {court_code}")
        print(f"  - State Code: {state_code}")
        print(f"  - Court Complex Code: {court_complex_code}")
        
        if not cino or not case_no:
            raise HTTPException(status_code=400, detail="Missing required case parameters (CINO or case_no)")
        
        # Get case history
        case_history_html = scraper.get_case_history(
            cino=cino,
            case_no=case_no,
            court_code=court_code,
            state_code=state_code,
            court_complex_code=court_complex_code
        )
        
        if not case_history_html:
            raise HTTPException(status_code=500, detail="Failed to fetch case history")
        
        # Parse case history
        parser = CaseHistoryParser(case_history_html)
        parsed_data = parser.get_structured_data()
        
        # Update PDF URLs to use our proxy endpoint
        if parsed_data.get('orders'):
            for order in parsed_data['orders']:
                if order.get('pdf_url'):
                    # Extract the filename from the original URL
                    original_url = order['pdf_url']
                    print(f"Processing PDF URL: {original_url}")
                    
                    if 'filename=' in original_url:
                        filename = original_url.split('filename=')[1].split('&')[0]
                        print(f"Extracted filename: {filename}")
                        
                        # Ensure original_url is the relative path
                        if original_url.startswith('http'):
                            # Extract just the path part
                            from urllib.parse import urlparse
                            parsed = urlparse(original_url)
                            original_url = parsed.path + '?' + parsed.query
                            print(f"Extracted relative path: {original_url}")
                        
                        # Create our proxy URL
                        proxy_url = f"/api/pdf-proxy?filename={filename}&original_url={original_url}"
                        print(f"Created proxy URL: {proxy_url}")
                        order['pdf_url'] = proxy_url
        
        return {"success": True, "case_data": parsed_data}
        
    except Exception as e:
        print(f"Error in case details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching case details: {str(e)}")

@app.get("/api/pdf-proxy")
async def pdf_proxy(filename: str, original_url: str):
    """Proxy PDF requests to handle session cookies"""
    global scraper
    
    print(f"PDF Proxy Debug:")
    print(f"  - filename: {filename}")
    print(f"  - original_url: {original_url}")
    
    try:
        if not scraper:
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
        
        # URL decode the original_url first
        from urllib.parse import unquote
        original_url = unquote(original_url)
        print(f"  - decoded original_url: {original_url}")
        
        # Check if original_url contains our proxy endpoint (which means it's wrong)
        if '/api/pdf-proxy' in original_url:
            print(f"  - ERROR: original_url contains /api/pdf-proxy, this is wrong!")
            # Try to extract the actual PDF URL from the query parameters
            if 'original_url=' in original_url:
                # Extract everything after original_url= until the end
                import re
                full_match = re.search(r'original_url=(.+)', original_url)
                if full_match:
                    actual_url = unquote(full_match.group(1))
                    print(f"  - extracted full actual_url: {actual_url}")
                    original_url = actual_url
                else:
                    raise HTTPException(status_code=400, detail="Could not extract PDF URL from proxy URL")
            else:
                raise HTTPException(status_code=400, detail="Invalid proxy URL format")
        
        # Ensure original_url is the correct PDF path
        if not original_url.startswith('/cases/display_pdf.php'):
            if original_url.startswith('cases/display_pdf.php'):
                original_url = '/' + original_url
            else:
                print(f"  - ERROR: Invalid PDF URL format: {original_url}")
                raise HTTPException(status_code=400, detail="Invalid PDF URL format")
        
        # Construct the full PDF URL
        full_url = f"https://hcservices.ecourts.gov.in/hcservices{original_url}"
        print(f"  - full_url: {full_url}")
        
        # Fetch the PDF with session cookies
        response = scraper._fetch_page_content(full_url)
        
        if not response or response.status_code != 200:
            print(f"  - ERROR: PDF fetch failed - status: {response.status_code if response else 'No response'}")
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Check if the response is actually a PDF or HTML error page
        content_type = response.headers.get('content-type', '')
        print(f"  - Response content-type: {content_type}")
        
        # Check first few bytes to see if it's PDF or HTML
        first_bytes = response.content[:20]
        print(f"  - First 20 bytes: {first_bytes}")
        
        if b'%PDF' in first_bytes:
            print(f"  - SUCCESS: Valid PDF content detected")
        elif b'<!doctype' in first_bytes.lower() or b'<html' in first_bytes.lower():
            print(f"  - ERROR: Server returned HTML instead of PDF")
            print(f"  - HTML content preview: {response.content[:200]}")
            raise HTTPException(status_code=404, detail="PDF not available - server returned HTML error page")
        else:
            print(f"  - WARNING: Unknown content type, proceeding anyway")
            print(f"  - Content preview: {response.content[:200]}")
        
        print(f"  - SUCCESS: PDF fetched successfully")
        
        # Return the PDF content
        from fastapi.responses import Response
        return Response(
            content=response.content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={filename}.pdf",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except Exception as e:
        print(f"  - ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching PDF: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 