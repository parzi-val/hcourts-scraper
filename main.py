from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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
import uuid
from urllib.parse import quote

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
        
        if not all([state_name, bench_name, case_type, case_no, year]):
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

        # --- AUTO-SOLVE CAPTCHA ---
        captcha_image = scraper.get_captcha_image()
        if not captcha_image:
            raise HTTPException(status_code=500, detail="Failed to fetch CAPTCHA image")
        
        captcha_value, was_auto_solved = scraper.captcha_solver.solve_captcha_with_fallback(captcha_image)
        if not captcha_value:
            raise HTTPException(status_code=500, detail="Failed to solve CAPTCHA")
        # --- END AUTO-SOLVE ---
        
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
                    original_url = order['pdf_url']
                    
                    # URL-encode the original URL to ensure it's passed correctly
                    encoded_url = quote(original_url, safe='')
                    
                    # Create our proxy URL with the fully encoded original URL
                    proxy_url = f"/api/pdf-proxy?url={encoded_url}"
                    order['pdf_url'] = proxy_url
        
        return {"success": True, "case_data": parsed_data}
        
    except Exception as e:
        print(f"Error in case details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching case details: {str(e)}")

@app.get("/api/pdf-proxy")
async def pdf_proxy(url: str):
    """Proxy PDF requests to handle session cookies, download and serve statically"""
    global scraper
    from urllib.parse import unquote, urlparse, parse_qs
    
    # Get the logger
    from logging_config import get_logger
    logger = get_logger()

    logger.info("="*40)
    logger.info("PDF PROXY REQUEST RECEIVED")
    logger.info(f"  - Incoming URL parameter: {url}")

    try:
        if not scraper:
            logger.info("Scraper not initialized, creating new instance...")
            scraper = ECourtsHCSCraper("https://hcservices.ecourts.gov.in")
            if not scraper.initialize_session():
                logger.error("Failed to initialize scraper session")
                raise HTTPException(status_code=500, detail="Failed to initialize scraper")
            logger.info("Scraper initialized successfully.")

        # The URL parameter from FastAPI is already decoded, so we use it directly.
        # Any '+' signs in the original URL were preserved by `quote` and decoded by FastAPI.
        original_url = url
        logger.info(f"  - Using URL parameter as received: {original_url}")

        # Ensure the URL starts with a slash
        if not original_url.startswith('/'):
            original_url = '/' + original_url
            logger.info(f"  - Prepended slash to URL: {original_url}")

        # Validate the URL format
        if not original_url.startswith('/cases/display_pdf.php'):
            logger.error(f"Invalid PDF URL format: {original_url}")
            raise HTTPException(status_code=400, detail="Invalid PDF URL format")

        # Extract filename from the original URL for saving the file
        try:
            parsed_original_url = urlparse(original_url)
            query_params = parse_qs(parsed_original_url.query)
            filename = query_params.get('filename', [f"unknown_{uuid.uuid4().hex}"])[0]
            logger.info(f"  - Extracted filename: {filename}")
        except Exception as e:
            logger.error(f"Could not parse filename from URL: {e}")
            filename = f"error_{uuid.uuid4().hex}"

        # Construct the full URL to fetch from the eCourts server
        full_url = f"https://hcservices.ecourts.gov.in/hcservices{original_url}"
        logger.info(f"  - Constructed full URL for fetching: {full_url}")

        # Fetch the PDF with session cookies
        response = scraper._fetch_page_content(full_url)

        if not response:
            logger.error("PDF fetch failed: No response from server.")
            raise HTTPException(status_code=500, detail="Failed to fetch PDF: No response")
            
        logger.info(f"  - Response status code: {response.status_code}")
        logger.info(f"  - Response headers: {dict(response.headers)}")

        if response.status_code != 200:
            logger.error(f"PDF fetch failed with status code {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail="PDF not found on server")

        # Check if the response is actually a PDF or an HTML error page
        content_type = response.headers.get('content-type', '').lower()
        is_pdf = 'application/pdf' in content_type or b'%PDF' in response.content[:10]

        if not is_pdf:
            logger.error("Server returned non-PDF content, likely an error page.")
            logger.debug(f"  - Content-Type: {content_type}")
            logger.debug(f"  - Content preview: {response.content[:200]}")
            raise HTTPException(status_code=404, detail="PDF not available - server returned an error page")

        logger.info("PDF content fetched successfully.")

        # Save PDF to a temporary directory
        temp_dir = 'static/temp_pdfs'
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create a unique filename to avoid conflicts
        unique_id = uuid.uuid4().hex
        temp_filename = f"{filename.replace('/', '_').replace('..', '')}_{unique_id}.pdf"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"PDF saved to temporary file: {temp_path}")

        # Return the static URL to the newly saved PDF
        static_url = f"/static/temp_pdfs/{temp_filename}"
        logger.info(f"Serving PDF from static URL: {static_url}")
        
        # Redirect the user directly to the static PDF file
        return RedirectResponse(url=static_url)

    except HTTPException as he:
        logger.error(f"HTTP Exception in PDF proxy: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"An unexpected error occurred in PDF proxy: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 