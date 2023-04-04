import dns.resolver
from fastapi import FastAPI
import re
from email_validator import validate_email, EmailSyntaxError, EmailNotValidError
import smtplib


app = FastAPI()

@app.get('/')
def index():
    return {'message': 'welcome to email validation service'}

@app.get('/check-temp-email')
async def check_temp_email(email: str):
    temp_domains = ['guerrillamail','mitigado','lyft','finews.biz','afia.pro','brand-app.biz','clout.wiki', 'mailinator', 'sharklasers', 'getnada', 'temp-mail', 'tempmail','cyclesat','10minutemail', 'temp-mail','yopmail','mailcatch','jetable','throwawaymail','fakeinbox','sharklasers','guerrillamailblock','guerrillamail','guerrillamail','spamgourmet','mailsucker','getairmail','mailnesia','dispostable','maildrop','mailnesia','emlses','trashmail','mailinator',
    'binkmail',
    'guerrillamail',
    'guerrillamail',
    'guerrillamail',
    'spam4',
    'trashmail',
    'gettempmail',
    'incognitomail',
    'tempmailgen',
    'tempmailo',
    'trashmail'
    'trashmail',
    'mailnesia',
    'mytemp',
    'temp-mail',
    'throwawaymail',
    'trash-mail',
    'yopmail',
    'grr',
    'inboxalias',
    'getonemail',
    'tempmail',
    'yopmail',
    'yopmail',
    'mintemail',
    'easytrashmail',
    'trashmail',
    '33mail',
    'anonymousemail',
    'discard',
    'dispostable',
    'dodgeit',
    'emailfake',
    'emailondeck',
    'emlhub',
    'fakeinbox',
    'fakemailgenerator',
    'guerrillamail',
    'guerrillamail',
    'mailinator2',
    'mohmal',
    'mytrashmail',
    'one-time',
    'owlymail',
    'recyclemail',
    'sendtrash',
    'spamgourmet',
    'spaml',
    'tempemail',
    'tempemail',
    'tempmail',
    'tempmail',
    'tempmail2',
    'tempmailer',
    'tempomail',
    'throwawaymailclub',
    'trash-me',
    'vasya',
    '20mail',
    'fghmail',
    'gtrcincc',
    'guerillamail',
    'guerillamail',
    'guerillamail',
    'guerillamail',
    'guerillamailblock',
    'guerrillamail',
    'guerrillamail',
    'guerrillamail',
    'guerrillamail',
    'guerrillamail',
    'guerrillamail',
    'guerrillamailblock',
    'h8s',
    'harakirimail',
    'hartbot',
    'ihateyoualot',
    'inbax',
    'inbox',
    'inboxalias',
    'inboxclean',
    'inboxproxy',
    'incognitomail',
    'jetable',
    'jetable',
    'jetable',
    'jetable',
    'jnxjn',
    'kasmail',
    'keemail',
    'killmail',
    'klzlk',
    'kulturbetrieb',
    'mail',
    'zimages',
    'mail4trash',
    'mailcatch',
    'maileater',
    'mailexpire',
    'mailinator',
    'mailinator',
    'mailinator',
    'mailnesia',
    'mailsucker',
    'mailtemp',
    'mailzilla',
    'mytrashmail',
    'netmails',
    'nomail.xl.cx',
    'nospam.ze.tc',
    'onewaymail',
    'pjjkp',
    'plhk',
    'pookmail',
    'privacy',
    'proxymail',
    'qq',
    'quickinbox',
    'rejectmail',
    'rtrtr',
    'safetymail',
    'scootmail',
    'sharklasers',
    'shiftmail',
    'shieldedmail',
    'shortmail',
    'smailpro',
    'sneakemail',
    'snkmail',
    'sogetthis',
    'soodonims',
    'spam4',
    'spamavert',
    'spambob',
    'spambog',
    'spambog',
    'spambog',
    'spambox',
    'spambox',
    'irishspringrealty',
    'spamcannon',
    'spamcannon',
    'spamcorptastic',
    'spamcowboy',
    'spamcowboy',
    'spamcowboy',
    'spamday',
    'spamex',
    'spamfree24',
    'spamfree24',
    'spamfree24',
    'spamfree24',
    'spamfree24',
    'spamfree24',
    'spamgourmet',
    'spamherelots',
    'spamhereplease',
    'spamhole',
    'spamify',
    'spaml']

    local, domain = email.split('@')

    # Check if the domain is a temporary email domain
    for temp_domain in temp_domains:
        if temp_domain in domain:
            return {"temp_email": True}

    # Check if the local part contains a common temporary email username pattern
    temp_usernames = ['temp', 'test', 'demo', 'trial']
    for temp_username in temp_usernames:
        if temp_username in local.lower():
            return {"temp_email": True}

    return {"temp_email": False}

@app.get('/check-valid-email')
def check_valid_email(email: str):
    try:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_regex, email) and  validate_email(email):
            return {"email": email,  "valid": True }
        else:
            return {"email": email, "valid": False, "error": "Invalid email syntax."}
    except EmailSyntaxError:
        return {"email": email, "valid": False, "error": "Invalid email syntax."}
    except EmailNotValidError:
        return {"email": email, "valid": False, "error": "Invalid email."}

@app.get("/check-email-mx-records")
def check_email_mx_records(email: str):
    domain = email.split("@")[1]
    try:
        mx_records = dns.resolver.query(domain, 'MX')
        return { "message": "MX records exists.", "status":True}
    except dns.resolver.NXDOMAIN:
        return {"message": "Domain does not exist.", "status":False}
    except dns.resolver.NoAnswer:
        return {"message": "No valid mail server found for the domain.", "status":False}

# @app.post("/check-email-account-exists")
# def check_email_account_exists(email: str):
#     try:
#         # Call the Mailgun email validation API
#         response = requests.get(
#             f"https://api.mailgun.net/v4/address/validate",
#             auth=("api", "your_mailgun_api_key"),
#             params={"address": email},
#         )

#         # Check if the email address exists and is valid
#         if response.ok and response.json()["result"] == "deliverable":
#             return {"message": "Email address exists."}
#         else:
#             return {"message": "Email address does not exist."}

#     except requests.exceptions.RequestException as e:
#         # If the request fails, an error message is returned
#         return {"message": f"Request failed: {e}"}

@app.get("/validate-email-by-service")
def validate_email_by_service(email: str):
    try:
        # Define the regular expression pattern for service emails
        pattern = r"^(no-reply|no-spam|no_reply|no_spam|support|info|admin|billing|sales|help|contact|customerservice|feedback|newsletter|marketing|media|press|privacy|security|service|subscribe|unsubscribe|webmaster)\@"
        

        # Use the re module to match the pattern against the email address
        if re.match(pattern, email):
            return {"status":200, "message": "Email address is from a service.", "service": 1}
        else:
            return {"status":200, "message": "Email address is not from a service.", "service": 0}

    except Exception as e:
        # If an error occurs, an error message is returned
        return {"status":400, "message": f"Error: {e}"}

@app.get("/check-free-email")
def check_free_email(email: str):
    try:
        # Validate the email address
        is_valid = validate_email(email)

        # Check if the email address belongs to a free email provider
        domain = re.search("@[\w.]+", email).group()[1:]
        free_mail_providers = ['gmail.com', 'yahoo.com', 'outlook.com', 'aol.com', 'protonmail.com', 'icloud.com', 'mail.com', 'zoho.com', 'yandex.com', 'gmx.com', 'hotmail.com', 'live.com', 'outlook.in', 'rediffmail.com', 'tutanota.com', 'fastmail.com', 'mail.ru', 'tutanota.de', 'hushmail.com', 'startmail.com', 'disroot.org', '10minutemail.com', 'mailinator.com', 'guerrillamail.com', 'temp-mail.org', 'hide-my-email.com', 'cock.li', 'protonmail.ch', 'swissmail.org', 'posteo.de', 'tutamail.com', 'tutanota.it', 'tutanota.at', 'tutanota.eu', 'tutanota.nl', 'tutanota.fr', 'tutanota.es', 'tutanota.org', 'tutanota.io', 'tutamail.com', 'inbox.lv', 'inbox.lt', 'mail.ee', 'seznam.cz', 'azet.sk', 'post.sk', 'pobox.com', 'mailnesia.com', 'sharklasers.com', 'mytemp.email', 'eclipso.eu', 'tutamail.it', 'tutanota.no', 'tutanota.se', 'tutanota.com.au', 'zoho.eu', 'yopmail.com', 'trashmail.com', 'spikemail.com', 'tempmail.space', 'tempr.email', 'fakeinbox.com', 'fake-mail.net', 'mail.tm', 'secure-mail.biz', 'smailpro.com', 'mymail-in.com', 'jetable.org', 'trashmailer.com', 'torbox.ch', 'mailforspam.com', 'maildrop.cc', 'msgsafe.io', 'inboxkitten.com', 'deadaddress.com', 'enigmail.net', 'vivaldi.net', 'runbox.com', 'tutanota.uk', 'tutanota.us', 'tutanota.be', 'tutanota.me', 'tutanota.es', 'tutanota.de', 'tutanota.fi', 'tutanota.pl', 'tutanota.ru', 'tutanota.jp', 'tutanota.cn', 'tutanota.in', 'tutanota.co', 'tutamail.de', 'tutamail.net', 'protonmail.com.au', 'protonmail.at', 'protonmail.ch', 'protonmail.cz', 'protonmail.de', 'protonmail.dk', 'protonmail.es', 'protonmail.fi', 'protonmail.fr', 'protonmail.gr', 'protonmail.hu', 'protonmail.is', 'protonmail.it', 'protonmail.li', 'protonmail.lt', 'protonmail.lu', 'protonmail.nl', 'protonmail.no', 'protonmail.pl', 'protonmail.pt', 'protonmail.ro', 'protonmail.se', 'protonmail.si', 'protonmail.uk', 'protonmail.us', 'protonmail.xyz', 'tutamail.ch', 'tutamail.com.ar', 'tutamail.com.br', 'tutamail.com.cn', 'tutamail.com.mx', 'tutamail.com.tw', 'tutamail.com.ua', 'tutamail.com.vn', 'tutamail.co.za', 'tutamail.de','tutamail.fr', 'tutamail.in', 'tutamail.io', 'tutamail.jp', 'tutamail.kr', 'tutamail.net', 'tutamail.nl', 'tutamail.ru', 'tutamail.sg', 'tutamail.tw', 'tutamail.us', 'tutamail.xyz', 'tutanota.cl', 'tutanota.co.il', 'tutanota.com.co', 'tutanota.com.sg', 'tutanota.com.tr', 'tutanota.com.ua', 'tutanota.com.ve', 'tutanota.dk', 'tutanota.ec']

        is_free = domain in free_mail_providers

        # Return the validation result and whether it's from a free email provider or not
        return {"status":200, "is_free_email": is_free, "is_valid": is_valid}

    except Exception as e:
        # If an error occurs, an error message is returned
        return {"status":400, "message": f"Error: {e}"}