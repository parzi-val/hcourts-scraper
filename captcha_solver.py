import google.generativeai as genai
import base64
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class CaptchaSolver:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CAPTCHA solver with Gemini API
        
        Args:
            api_key: Google Gemini API key. If None, will try to get from environment variable
        """
        self.api_key = api_key or os.getenv('GOOGLE_GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Google Gemini API key is required. Set GOOGLE_GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def solve_captcha(self, image_bytes: bytes) -> Optional[str]:
        """
        Solve CAPTCHA using Gemini Vision API
        
        Args:
            image_bytes: CAPTCHA image as bytes
            
        Returns:
            Solved CAPTCHA text or None if failed
        """
        try:
            # Convert bytes to base64 for Gemini
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Create prompt for CAPTCHA solving
            prompt = """
            This is a CAPTCHA image. Please read the text characters in the image and return ONLY the text, nothing else.
            
            Rules:
            1. Return only the alphanumeric characters you see
            2. Ignore any background noise or distortions
            3. If you can't read it clearly, make your best guess
            4. Return the text in a single line without spaces
            5. Only return the text, no explanations or additional text
            
            What text do you see in this CAPTCHA?
            """
            
            # Create image part for Gemini
            image_part = {
                "mime_type": "image/png",
                "data": image_base64
            }
            
            # Generate response
            response = self.model.generate_content([prompt, image_part])
            
            if response.text:
                # Clean the response - remove any extra text and keep only alphanumeric
                captcha_text = ''.join(c for c in response.text.strip() if c.isalnum())
                print(f"CAPTCHA SOLVED: {captcha_text}")
                return captcha_text if captcha_text else None
            else:
                return None
                
        except Exception as e:
            print(f"Error solving CAPTCHA with Gemini: {e}")
            return None
    
    def solve_captcha_with_fallback(self, image_bytes: bytes) -> tuple[Optional[str], bool]:
        """
        Solve CAPTCHA with fallback information
        
        Args:
            image_bytes: CAPTCHA image as bytes
            
        Returns:
            Tuple of (solved_text, was_auto_solved)
        """
        solved_text = self.solve_captcha(image_bytes)
        return solved_text, solved_text is not None 