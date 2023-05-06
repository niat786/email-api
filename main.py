import dns.resolver
from fastapi import FastAPI, File, UploadFile
import re, csv, os, shutil, uuid, zipfile, openpyxl, io
from email_validator import validate_email, EmailSyntaxError, EmailNotValidError
import smtplib, requests
from faker import Faker

app = FastAPI()
fake = Faker()


@app.get("/")
def index():
    return {"message": "welcome to email validation service"}


@app.post("/check-temp-email")
async def check_temp_email(email: str):
    temp_domains = [
        "guerrillamail",
        "mitigado",
        "lyft",
        "finews.biz",
        "afia.pro",
        "brand-app.biz",
        "clout.wiki",
        "mailinator",
        "sharklasers",
        "getnada",
        "temp-mail",
        "tempmail",
        "cyclesat",
        "10minutemail",
        "temp-mail",
        "yopmail",
        "mailcatch",
        "jetable",
        "throwawaymail",
        "fakeinbox",
        "sharklasers",
        "guerrillamailblock",
        "guerrillamail",
        "guerrillamail",
        "spamgourmet",
        "mailsucker",
        "getairmail",
        "mailnesia",
        "dispostable",
        "maildrop",
        "mailnesia",
        "emlses",
        "trashmail",
        "mailinator",
        "binkmail",
        "guerrillamail",
        "guerrillamail",
        "guerrillamail",
        "spam4",
        "trashmail",
        "gettempmail",
        "incognitomail",
        "tempmailgen",
        "tempmailo",
        "trashmail" "trashmail",
        "mailnesia",
        "mytemp",
        "temp-mail",
        "throwawaymail",
        "trash-mail",
        "yopmail",
        "grr",
        "inboxalias",
        "getonemail",
        "tempmail",
        "yopmail",
        "yopmail",
        "mintemail",
        "easytrashmail",
        "trashmail",
        "33mail",
        "anonymousemail",
        "discard",
        "dispostable",
        "dodgeit",
        "emailfake",
        "emailondeck",
        "emlhub",
        "fakeinbox",
        "fakemailgenerator",
        "guerrillamail",
        "guerrillamail",
        "mailinator2",
        "mohmal",
        "mytrashmail",
        "one-time",
        "owlymail",
        "recyclemail",
        "sendtrash",
        "spamgourmet",
        "spaml",
        "tempemail",
        "tempemail",
        "tempmail",
        "tempmail",
        "tempmail2",
        "tempmailer",
        "tempomail",
        "throwawaymailclub",
        "trash-me",
        "vasya",
        "20mail",
        "fghmail",
        "gtrcincc",
        "guerillamail",
        "guerillamail",
        "guerillamail",
        "guerillamail",
        "guerillamailblock",
        "guerrillamail",
        "guerrillamail",
        "guerrillamail",
        "guerrillamail",
        "guerrillamail",
        "guerrillamail",
        "guerrillamailblock",
        "h8s",
        "harakirimail",
        "hartbot",
        "ihateyoualot",
        "inbax",
        "inbox",
        "inboxalias",
        "inboxclean",
        "inboxproxy",
        "incognitomail",
        "jetable",
        "jetable",
        "jetable",
        "jetable",
        "jnxjn",
        "kasmail",
        "keemail",
        "killmail",
        "klzlk",
        "kulturbetrieb",
        "zimages",
        "mail4trash",
        "mailcatch",
        "maileater",
        "mailexpire",
        "mailinator",
        "mailinator",
        "mailinator",
        "mailnesia",
        "mailsucker",
        "mailtemp",
        "mailzilla",
        "mytrashmail",
        "netmails",
        "nomail.xl.cx",
        "nospam.ze.tc",
        "onewaymail",
        "pjjkp",
        "plhk",
        "pookmail",
        "privacy",
        "proxymail",
        "qq",
        "quickinbox",
        "rejectmail",
        "rtrtr",
        "safetymail",
        "scootmail",
        "sharklasers",
        "shiftmail",
        "shieldedmail",
        "shortmail",
        "smailpro",
        "sneakemail",
        "snkmail",
        "sogetthis",
        "soodonims",
        "spam4",
        "spamavert",
        "spambob",
        "spambog",
        "spambog",
        "spambog",
        "spambox",
        "spambox",
        "irishspringrealty",
        "spamcannon",
        "spamcannon",
        "spamcorptastic",
        "spamcowboy",
        "spamcowboy",
        "spamcowboy",
        "spamday",
        "spamex",
        "spamfree24",
        "spamfree24",
        "spamfree24",
        "spamfree24",
        "spamfree24",
        "spamfree24",
        "spamgourmet",
        "spamherelots",
        "spamhereplease",
        "spamhole",
        "spamify",
        "spaml",
    ]
    temp_mail_pattern = "^(?i)([a-z0-9._%+-]+@(?:10mail\.org|20mail\.eu|20mail\.it|33mail\.com|anonymail\.info|bcaoo\.com|bccto\.me|brefmail\.com|burnermail\.io|byom\.de|clrmail\.net|coepoe\.com|cool.fr\.nf|correo\.plus|cosmorph\.com|cust.in|dayrep\.com|deadaddress\.com|discard\.email|discardmail\.com|disposableemailaddresses\.com|dispostable\.com|dodgeit\.com|dump-email\.info|dumpmail\.de|email-fake\.com|emailfake\.com|emailondeck\.com|emailsensei\.com|emailtemporanea\.org|emailtemporario\.com\.br|emailthe\.de|emlhub\.com|fakeinbox\.com|fakemail\.net|fast-mail\.org|filzmail\.com|fivemail\.net|fleckens\.hu|getonemail\.com|gettempmail\.com|giantmail\.dk|guerrillamail\.biz|guerrillamail\.com|guerrillamail\.de|guerrillamail\.net|guerrillamail\.org|hatespam\.org|hidemail\.de|hmamail\.com|hochsitze\.com|hotpop\.com|ieh-mail\.de|imails\.info|incognitomail\.org|inbox\.lv|inbox\.lt|inbox\.ru|incognitomail\.com|instant-mail\.org|ipoo\.org|irish2me\.com|jetable\.org|jnxjn\.com|jourrapide\.com|kasmail\.com|keepmymail\.com|killmail\.net|klzlk\.com|koszmail\.pl|kurzepost\.de|letthemeatspam\.com|link2mail\.net|litedrop\.com|mail4trash\.com|mail666\.in|maildrop\.cc|maileater\.net|mailexpire\.com|mailimate\.com|mailinater\.com|mailinator\.com|mailinator2\.com|mailismagic\.com|mailme24\.com|mailnesia\.com|mailnull\.com|mailshell\.com|mailsiphon\.com|mailtemp\.de|mailtemporaire\.com|mailtome\.de|mailtrash\.net|mailzilla\.org|mega.zik.dj|meinspamschutz\.de|meltmail\.com|mierdamail\.com|ministry-of-silly-walks\.de|mintemail\.com|mohmal\.com|moncourrier\.fr\.n|mt2014\.com|mx0\.mailslite\.com|mytempemail\.com|nepwk\.com|no-spam\.at|no-spam\.ch|no-spam\.info|no-spam\.it|no-spam\.jp|no-spam\.nl|noblepioneer\.com|nomail\.2nn\.ru|nomail\.xyz|nospamfor\.us|nospamthanks\.info|notmailinator\.com|nowhere\.org|nurfuerspam\.de|objectmail\.com|obobbo\."
    local, domain = email.split("@")
    if domain in temp_mail_pattern:
        return {"email": email, "temp_email": True}

    # Check if the local part contains a common temporary email username pattern
    temp_usernames = [
        "temp",
        "test",
        "demo",
        "trial",
        "sample",
        "debug",
        "prototype",
        "experiment",
        "sandbox",
        "beta",
        "guest",
        "fakeuser",
        "user",
        "fake_user",
        "junk",
        "disposable",
        "anonymous",
        "user123",
        "example",
        "trash",
    ]
    for temp_username in temp_usernames:
        if temp_username in local.lower():
            return {"email": email, "temp_email": True}

    # Check if the domain is a temporary email domain
    for temp_domain in temp_domains:
        if temp_domain in domain:
            return {"email": email, "email": email, "temp_email": True}

    # check if a domain is live
    split_email = email.split("@")

    try:
        response = requests.get(f"https://{split_email[1]}")

        if response.status_code in range(200, 300):
            return {"email": email, "temp_email": False}
        else:
            return {"email": email, "email": email, "temp_email": True}
    except requests.exceptions.RequestException as e:
        return {"email": email, "email": email, "temp_email": True}

    return {"email": email, "temp_email": False}


@app.post("/check-valid-email")
def check_valid_email(email: str):
    try:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.match(email_regex, email) and validate_email(email):
            return {"email": email, "valid": True}
        else:
            return {"email": email, "valid": False, "error": "Invalid email syntax."}
    except EmailSyntaxError:
        return {"email": email, "valid": False, "error": "Invalid email syntax."}
    except EmailNotValidError:
        return {"email": email, "valid": False, "error": "Invalid email."}


@app.post("/check-email-mx-records")
def check_email_mx_records(email: str):
    domain = email.split("@")[1]
    try:
        mx_records = dns.resolver.query(domain, "MX")
        # Validate the email address
        mx_data = validate_email(email)
        return {"message": "MX records exists.", "status": True, "mx_data": mx_data}
    except dns.resolver.NXDOMAIN:
        return {"message": "Domain does not exist.", "status": False}
    except dns.resolver.NoAnswer:
        return {
            "message": "No valid mail server found for the domain.",
            "status": False,
        }


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


@app.post("/validate-email-by-service")
def validate_email_by_service(email: str):
    try:
        # Define the regular expression pattern for service emails
        pattern = r"^(no-reply|no-spam|no_reply|no_spam|support|info|admin|billing|sales|help|contact|customerservice|feedback|newsletter|marketing|media|press|privacy|security|service|subscribe|unsubscribe|webmaster)\@"

        # Use the re module to match the pattern against the email address
        if re.match(pattern, email):
            return {
                "status": 200,
                "message": "Email address is from a service.",
                "service": 1,
            }
        else:
            return {
                "status": 200,
                "message": "Email address is not from a service.",
                "service": 0,
            }

    except Exception as e:
        # If an error occurs, an error message is returned
        return {"status": 400, "message": f"Error: {e}"}


@app.post("/check-free-email")
def check_free_email(email: str):
    try:
        # Validate the email address
        is_valid = validate_email(email)

        # Check if the email address belongs to a free email provider
        domain = re.search("@[\w.]+", email).group()[1:]
        free_mail_providers = [
            "gmail.com",
            "yahoo.com",
            "outlook.com",
            "aol.com",
            "protonmail.com",
            "icloud.com",
            "mail.com",
            "zoho.com",
            "yandex.com",
            "gmx.com",
            "hotmail.com",
            "live.com",
            "outlook.in",
            "rediffmail.com",
            "tutanota.com",
            "fastmail.com",
            "mail.ru",
            "tutanota.de",
            "hushmail.com",
            "startmail.com",
            "disroot.org",
            "10minutemail.com",
            "mailinator.com",
            "guerrillamail.com",
            "temp-mail.org",
            "hide-my-email.com",
            "cock.li",
            "protonmail.ch",
            "swissmail.org",
            "posteo.de",
            "tutamail.com",
            "tutanota.it",
            "tutanota.at",
            "tutanota.eu",
            "tutanota.nl",
            "tutanota.fr",
            "tutanota.es",
            "tutanota.org",
            "tutanota.io",
            "tutamail.com",
            "inbox.lv",
            "inbox.lt",
            "mail.ee",
            "seznam.cz",
            "azet.sk",
            "post.sk",
            "pobox.com",
            "mailnesia.com",
            "sharklasers.com",
            "mytemp.email",
            "eclipso.eu",
            "tutamail.it",
            "tutanota.no",
            "tutanota.se",
            "tutanota.com.au",
            "zoho.eu",
            "yopmail.com",
            "trashmail.com",
            "spikemail.com",
            "tempmail.space",
            "tempr.email",
            "fakeinbox.com",
            "fake-mail.net",
            "mail.tm",
            "secure-mail.biz",
            "smailpro.com",
            "mymail-in.com",
            "jetable.org",
            "trashmailer.com",
            "torbox.ch",
            "mailforspam.com",
            "maildrop.cc",
            "msgsafe.io",
            "inboxkitten.com",
            "deadaddress.com",
            "enigmail.net",
            "vivaldi.net",
            "runbox.com",
            "tutanota.uk",
            "tutanota.us",
            "tutanota.be",
            "tutanota.me",
            "tutanota.es",
            "tutanota.de",
            "tutanota.fi",
            "tutanota.pl",
            "tutanota.ru",
            "tutanota.jp",
            "tutanota.cn",
            "tutanota.in",
            "tutanota.co",
            "tutamail.de",
            "tutamail.net",
            "protonmail.com.au",
            "protonmail.at",
            "protonmail.ch",
            "protonmail.cz",
            "protonmail.de",
            "protonmail.dk",
            "protonmail.es",
            "protonmail.fi",
            "protonmail.fr",
            "protonmail.gr",
            "protonmail.hu",
            "protonmail.is",
            "protonmail.it",
            "protonmail.li",
            "protonmail.lt",
            "protonmail.lu",
            "protonmail.nl",
            "protonmail.no",
            "protonmail.pl",
            "protonmail.pt",
            "protonmail.ro",
            "protonmail.se",
            "protonmail.si",
            "protonmail.uk",
            "protonmail.us",
            "protonmail.xyz",
            "tutamail.ch",
            "tutamail.com.ar",
            "tutamail.com.br",
            "tutamail.com.cn",
            "tutamail.com.mx",
            "tutamail.com.tw",
            "tutamail.com.ua",
            "tutamail.com.vn",
            "tutamail.co.za",
            "tutamail.de",
            "tutamail.fr",
            "tutamail.in",
            "tutamail.io",
            "tutamail.jp",
            "tutamail.kr",
            "tutamail.net",
            "tutamail.nl",
            "tutamail.ru",
            "tutamail.sg",
            "tutamail.tw",
            "tutamail.us",
            "tutamail.xyz",
            "tutanota.cl",
            "tutanota.co.il",
            "tutanota.com.co",
            "tutanota.com.sg",
            "tutanota.com.tr",
            "tutanota.com.ua",
            "tutanota.com.ve",
            "tutanota.dk",
            "tutanota.ec",
        ]

        is_free = domain in free_mail_providers

        # Return the validation result and whether it's from a free email provider or not
        return {"status": 200, "is_free_email": is_free, "is_valid": is_valid}

    except Exception as e:
        # If an error occurs, an error message is returned
        return {"status": 400, "message": f"Error: {e}"}


# generate fake emails
@app.get("/fake_email")
async def generate_fake_business_email():
    first_name = fake.first_name()
    last_name = fake.last_name()
    job_title = fake.job()
    email_domain = fake.domain_name()
    email = "{}.{}@{}".format(first_name.lower(), last_name.lower(), email_domain)
    return {"email": email, "job_title": job_title}


# file emails vaildate in bulk
@app.post("/bulk_email_syntax_check")
async def validate_emails(file: UploadFile = File(...), column_name: str = "Emails"):
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    valid_emails = []
    invalid_emails = []
    emails = []
    emails_limit = 999
    valid_emails_count = 0
    invalid_emails_count = 0

    try:
        if file.filename.endswith(".txt"):
            txt_data = await file.read()
            txt_text = txt_data.decode("utf-8-sig")
            emails = txt_text.split("\n")
            for i, email in enumerate(emails):
                if re.match(email_pattern, email):
                    valid_emails.append(email)
                    valid_emails_count = valid_emails_count + 1
                else:
                    invalid_emails.append(email)
                    invalid_emails_count = invalid_emails_count + 1

                if i >= emails_limit:
                    break

        elif file.filename.endswith(".csv"):
            csv_data = await file.read()
            csv_text = csv_data.decode("utf-8-sig")
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            email_col = column_name  # change to the name of the email column
            for i, row in enumerate(csv_reader):
                email = row[email_col]
                if re.match(email_pattern, email):
                    valid_emails.append(email)
                    valid_emails_count = valid_emails_count + 1

                else:
                    invalid_emails.append(email)
                    invalid_emails_count = invalid_emails_count + 1

                if i >= emails_limit:
                    break

        elif file.filename.endswith(".xlsx"):
            excel_data = await file.read()
            workbook = openpyxl.load_workbook(excel_data)
            worksheet = workbook.active
            for i, row in enumerate(worksheet.iter_rows(values_only=True)):
                email = row[0]  # assuming email is in the first column
                if re.match(email_pattern, email):
                    valid_emails.append(email)
                    valid_emails_count = valid_emails_count + 1
                else:
                    invalid_emails.append(email)
                    invalid_emails_count = invalid_emails_count + 1
                if i >= emails_limit:
                    break
        else:
            return {
                "status": 400,
                "message": "Invalid file type. Please upload a TXT or CSV file.",
            }
    except:
        return {"status": 400, "message": "File is corrupt or not supported"}

    return {
        "status": 200,
        "valid_emails_count": valid_emails_count,
        "invalid_emails_count": invalid_emails_count,
        "valid_emails": valid_emails,
        "invalid_emails": invalid_emails,
    }
