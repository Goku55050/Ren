from flask import Flask, request, jsonify
import requests
from faker import Faker
import random
import string
import json
import time
import logging
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
fake = Faker()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get port from environment variable for Render
port = int(os.environ.get("PORT", 5000))

# Rate limiting
request_tracker = {}
RATE_LIMIT = 30  # requests per minute
RATE_WINDOW = 60  # seconds

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time.time()
        
        # Clean old requests
        if client_ip in request_tracker:
            request_tracker[client_ip] = [
                t for t in request_tracker[client_ip] 
                if current_time - t < RATE_WINDOW
            ]
        
        # Check rate limit
        if len(request_tracker.get(client_ip, [])) >= RATE_LIMIT:
            return jsonify({
                "error": "Rate limit exceeded",
                "message": f"Maximum {RATE_LIMIT} requests per minute",
                "developer": "Basic Coders | @SajagOG"
            }), 429
        
        # Track request
        if client_ip not in request_tracker:
            request_tracker[client_ip] = []
        request_tracker[client_ip].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

def gen_pass():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(12))

def create_session():
    session = requests.Session()
    session.headers.update({
        "accept": "*/*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://darkosint.in",
        "referer": "https://darkosint.in/",
        "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    })
    return session

def signup_user(session):
    try:
        name = fake.first_name() + " " + fake.last_name()
        email = fake.first_name().lower() + str(random.randint(1000, 9999)) + "@gmail.com"
        password = gen_pass()
        payload = {
            "action": "signup",
            "name": name,
            "email": email,
            "password": password
        }
        
        response = session.post(
            "https://darkosint.in/api/auth.php",
            data=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"User signed up: {email}")
            return True
        return False
    except Exception as e:
        logger.error(f"Signup error: {e}")
        return False

def extract_clean(resp):
    try:
        raw = resp.text
        parsed = json.loads(raw)
        
        # Check response structure
        if "data" not in parsed or "result" not in parsed["data"]:
            return {
                "error": "Invalid API response",
                "developer": "Basic Coders | @SajagOG"
            }
        
        # Try different response formats
        try:
            results = parsed["data"]["result"]["result"]
        except:
            results = parsed["data"]["result"]
        
        if not results or len(results) == 0:
            return {
                "error": "No records found",
                "developer": "Basic Coders | @SajagOG"
            }
        
        row = results[0]
        
        # Build response
        response = {
            "name": row.get("name", "").strip(),
            "father_name": row.get("father_name", "").strip(),
            "address": row.get("address", "").replace("!", ", ").strip(),
            "mobile": row.get("mobile", "").strip(),
            "aadhaar": row.get("id_number", "").strip(),
            "email": row.get("email", "").strip(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success",
            "developer": "Basic Coders | @SajagOG",
            "source": "darkosint.in"
        }
        
        # Add optional fields
        optional_fields = ["dob", "gender", "pincode", "state", "district"]
        for field in optional_fields:
            if field in row and row[field]:
                response[field] = row[field]
        
        return response
        
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON response",
            "developer": "Basic Coders | @SajagOG"
        }
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return {
            "error": f"Data extraction failed: {str(e)}",
            "developer": "Basic Coders | @SajagOG"
        }

def perform_lookup(session, lookup_type, query):
    try:
        payload = {"type": lookup_type, "query": query}
        resp = session.post(
            "https://darkosint.in/api/lookup.php",
            data=payload,
            timeout=15
        )
        
        if resp.status_code == 200:
            return extract_clean(resp)
        return {
            "error": f"API returned status {resp.status_code}",
            "developer": "Basic Coders | @SajagOG"
        }
    except requests.Timeout:
        return {
            "error": "Request timeout",
            "developer": "Basic Coders | @SajagOG"
        }
    except requests.RequestException as e:
        return {
            "error": f"Network error: {str(e)}",
            "developer": "Basic Coders | @SajagOG"
        }

@app.route('/')
def home():
    return jsonify({
        "message": "DarkOSINT API - Indian Data Lookup Service",
        "version": "2.0",
        "developer": "Basic Coders | @SajagOG",
        "endpoints": {
            "/num": "Lookup by phone number - GET /num?number=9876543210",
            "/aadhar": "Lookup by Aadhaar number - GET /aadhar?aadhar=123456789012",
            "/health": "Health check endpoint",
            "/docs": "API documentation"
        },
        "rate_limit": f"{RATE_LIMIT} requests per minute",
        "note": "For educational purposes only. Use responsibly."
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DarkOSINT API",
        "uptime": "100%"
    })

@app.route('/docs')
def docs():
    return jsonify({
        "api_name": "DarkOSINT Data Lookup API",
        "description": "Lookup Indian citizen data by phone number or Aadhaar",
        "base_url": "https://your-render-app.onrender.com",
        "authentication": "None required",
        "rate_limits": f"{RATE_LIMIT} requests per minute per IP",
        "endpoints": [
            {
                "path": "/num",
                "method": "GET",
                "description": "Lookup by phone number",
                "parameters": "number (10 digits)",
                "example": "/num?number=9876543210"
            },
            {
                "path": "/aadhar",
                "method": "GET",
                "description": "Lookup by Aadhaar number",
                "parameters": "aadhar (12 digits)",
                "example": "/aadhar?aadhar=123456789012"
            }
        ],
        "response_format": {
            "success": {
                "name": "string",
                "father_name": "string",
                "address": "string",
                "mobile": "string",
                "aadhaar": "string",
                "email": "string",
                "status": "success",
                "developer": "Basic Coders | @SajagOG"
            },
            "error": {
                "error": "string",
                "developer": "Basic Coders | @SajagOG"
            }
        },
        "disclaimer": "This API is for educational purposes only. Respect privacy and follow all applicable laws."
    })

@app.route('/num')
@rate_limit
def lookup_num():
    """Lookup by phone number"""
    number = request.args.get("number")
    
    if not number:
        return jsonify({
            "error": "Missing parameter",
            "required": "?number=9876543210",
            "example": "/num?number=9876543210",
            "developer": "Basic Coders | @SajagOG"
        }), 400
    
    # Clean and validate number
    number = ''.join(filter(str.isdigit, number))
    if len(number) != 10:
        return jsonify({
            "error": "Invalid phone number",
            "message": "Must be exactly 10 digits",
            "developer": "Basic Coders | @SajagOG"
        }), 400
    
    try:
        session = create_session()
        
        # Create user session
        if not signup_user(session):
            # Retry once
            session = create_session()
            signup_user(session)
        
        result = perform_lookup(session, "mobile", number)
        
        # Log successful lookup
        if "error" not in result:
            logger.info(f"Successful phone lookup: {number}")
        else:
            logger.warning(f"Failed phone lookup: {number} - {result.get('error')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Phone lookup error: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "developer": "Basic Coders | @SajagOG"
        }), 500

@app.route('/aadhar')
@rate_limit
def lookup_aadhar():
    """Lookup by Aadhaar number"""
    aadhar = request.args.get("aadhar")
    
    if not aadhar:
        return jsonify({
            "error": "Missing parameter",
            "required": "?aadhar=123456789012",
            "example": "/aadhar?aadhar=123456789012",
            "developer": "Basic Coders | @SajagOG"
        }), 400
    
    # Clean and validate Aadhaar
    aadhar = ''.join(filter(str.isdigit, aadhar))
    if len(aadhar) != 12:
        return jsonify({
            "error": "Invalid Aadhaar number",
            "message": "Must be exactly 12 digits",
            "developer": "Basic Coders | @SajagOG"
        }), 400
    
    try:
        session = create_session()
        
        # Create user session
        if not signup_user(session):
            # Retry once
            session = create_session()
            signup_user(session)
        
        result = perform_lookup(session, "aadhaar", aadhar)
        
        # Log successful lookup
        if "error" not in result:
            logger.info(f"Successful Aadhaar lookup: {aadhar[:4]}****{aadhar[-4:]}")
        else:
            logger.warning(f"Failed Aadhaar lookup - {result.get('error')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Aadhaar lookup error: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "developer": "Basic Coders | @SajagOG"
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/num", "/aadhar", "/health", "/docs"],
        "developer": "Basic Coders | @SajagOG"
    }), 404

@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({
        "error": "Rate limit exceeded",
        "message": f"Maximum {RATE_LIMIT} requests per minute",
        "retry_after": "60 seconds",
        "developer": "Basic Coders | @SajagOG"
    }), 429

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "Please try again later",
        "developer": "Basic Coders | @SajagOG"
    }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 DarkOSINT API Server Starting...")
    print(f"🌐 Port: {port}")
    print("👨‍💻 Developer: Basic Coders | @SajagOG")
    print("📌 Version: 2.0")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
