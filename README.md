# TrustMail API - Email Validation & Intelligence Platform

A comprehensive REST API for email validation, fraud prevention, and deliverability intelligence. Built for developers who need reliable email verification, AI-powered analysis, and email campaign management.

## 🚀 Quick Start

**Base URL:** `https://your-api-domain.com`

**Authentication:** Include your API key in the request headers:
```
X-RapidAPI-Key: YOUR_API_KEY
X-RapidAPI-Host: your-api-host.rapidapi.com
```

## 📚 API Endpoints

### Email Validation

#### 1. Validate Email Syntax (Single)

Check if an email address has valid syntax.

**Endpoint:** `GET /validate/syntax`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email` | string | Yes | Email address to validate |

**Example Request:**
```bash
curl -X GET "https://your-api-domain.com/validate/syntax?email=user@example.com" \
  -H "X-RapidAPI-Key: YOUR_API_KEY"
```

**Example Response:**
```json
{
  "email": "user@example.com",
  "is_valid_syntax": true,
  "error_message": null
}
```

**Error Response:**
```json
{
  "email": "invalid-email",
  "is_valid_syntax": false,
  "error_message": "Invalid email format"
}
```

---

#### 2. Validate Email Syntax (Bulk - File Upload)

Validate multiple emails from a file (TXT, CSV, or XLSX).

**Endpoint:** `POST /validate/syntax-bulk`

**Request:** Multipart form data

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | File containing email addresses (max 10,000 emails) |

**Supported File Formats:**
- `.txt` - One email per line
- `.csv` - First column contains emails
- `.xlsx` / `.xls` - First column contains emails

**Example Request:**
```bash
curl -X POST "https://your-api-domain.com/validate/syntax-bulk" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -F "file=@emails.txt"
```

**Example Response:**
```json
[
  {
    "email": "user1@example.com",
    "is_valid_syntax": true,
    "error_message": null
  },
  {
    "email": "invalid-email",
    "is_valid_syntax": false,
    "error_message": "Invalid email format"
  }
]
```

---

#### 3. Validate Email Syntax (Bulk - JSON)

Validate multiple emails from JSON body.

**Endpoint:** `POST /validate/syntax-bulk-json`

**Request Body:**
```json
{
  "emails": [
    "user1@example.com",
    "user2@example.com",
    "invalid-email"
  ]
}
```

**Limits:**
- Maximum 1,000 emails per request

**Example Request:**
```bash
curl -X POST "https://your-api-domain.com/validate/syntax-bulk-json" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["user1@example.com", "user2@example.com"]
  }'
```

---

#### 4. Comprehensive Email Validation (Inbox Status)

Perform comprehensive email validation with AI-powered analysis. This is the most detailed validation endpoint.

**Endpoint:** `GET /validate/inbox-status`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | string | Yes | - | Email address to validate |
| `skip_smtp` | boolean | No | `true` | Skip SMTP checking for faster results (3-5s vs 10-15s) |

**What This Endpoint Checks:**
- ✅ Email syntax validation
- ✅ Disposable email detection (4,500+ domains)
- ✅ Suspicious TLD detection
- ✅ Well-known email provider detection
- ✅ Paid email domain detection
- ✅ Role-based email detection
- ✅ Domain typo detection (AI-powered)
- ✅ Gibberish/bot detection (AI-powered)
- ✅ Demographic inference (name & gender)
- ✅ HTTP status verification
- ✅ MX record validation
- ✅ SMTP deliverability (optional)
- ✅ Catch-all domain detection (optional)
- ✅ Confidence scoring (0.0 - 1.0)

**Example Request:**
```bash
curl -X GET "https://your-api-domain.com/validate/inbox-status?email=user@example.com&skip_smtp=true" \
  -H "X-RapidAPI-Key: YOUR_API_KEY"
```

**Example Response:**
```json
{
  "email": "user@example.com",
  "is_valid_syntax": true,
  "is_disposable": false,
  "has_mx_records": true,
  "is_deliverable_smtp": true,
  "is_catch_all_domain": false,
  "is_role_based": false,
  "is_paid_domain": false,
  "confidence_score": 0.95,
  "details": {
    "syntax": "Valid",
    "role_based": "No",
    "tld_check": "OK: Standard TLD",
    "disposable_list": "OK: Permanent email domain",
    "paid_domain": "No: Free or unknown domain",
    "typo_check": {
      "has_typo": false,
      "suggestion": null,
      "confidence": 0
    },
    "bot_check": {
      "is_gibberish": false
    },
    "demographics": {
      "likely_name": "User",
      "likely_gender": "mostly_male",
      "confidence": "medium"
    },
    "http_status": "Website accessible (HTTPS/HTTP with valid response)",
    "mx_records": "Found 5 MX record(s)",
    "smtp": "Skipped for faster response (use skip_smtp=false to enable)",
    "catch_all": "Unknown (skipped for faster response)"
  }
}
```

**Response Fields Explained:**

| Field | Type | Description |
|-------|------|-------------|
| `is_valid_syntax` | boolean | Whether email format is valid |
| `is_disposable` | boolean | Whether domain is disposable/temporary |
| `has_mx_records` | boolean | Whether domain has MX records |
| `is_deliverable_smtp` | boolean | Whether email can receive messages (if SMTP check enabled) |
| `is_catch_all_domain` | boolean | Whether domain accepts any email address |
| `is_role_based` | boolean | Whether email is role-based (admin, support, etc.) |
| `is_paid_domain` | boolean | Whether domain is a paid email provider |
| `confidence_score` | float | Overall confidence (0.0 = low, 1.0 = high) |

**Performance:**
- With `skip_smtp=true`: 3-5 seconds
- With `skip_smtp=false`: 10-15 seconds

---

#### 5. Bulk Email Validation (Inbox Status)

Validate multiple emails with comprehensive checks.

**Endpoint:** `POST /validate/inbox-status-bulk`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip_smtp` | boolean | No | `true` | Skip SMTP checking for faster results |

**Request Body:**
```json
{
  "emails": [
    "user1@example.com",
    "user2@example.com",
    "admin@company.com"
  ]
}
```

**Limits:**
- Maximum 100 emails per request

**Example Request:**
```bash
curl -X POST "https://your-api-domain.com/validate/inbox-status-bulk?skip_smtp=true" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["user1@example.com", "user2@example.com"]
  }'
```

**Example Response:**
```json
{
  "total": 2,
  "valid_count": 2,
  "invalid_count": 0,
  "results": [
    {
      "email": "user1@example.com",
      "is_valid_syntax": true,
      "is_disposable": false,
      "has_mx_records": true,
      "is_deliverable_smtp": true,
      "is_catch_all_domain": false,
      "is_role_based": false,
      "is_paid_domain": false,
      "confidence_score": 0.95,
      "details": {...}
    },
    {
      "email": "user2@example.com",
      "is_valid_syntax": true,
      "is_disposable": false,
      "has_mx_records": true,
      "is_deliverable_smtp": true,
      "is_catch_all_domain": false,
      "is_role_based": false,
      "is_paid_domain": false,
      "confidence_score": 0.92,
      "details": {...}
    }
  ]
}
```

---

### Email Generation

#### 6. Generate Fake Email Addresses

Generate realistic fake email addresses for testing purposes.

**Endpoint:** `GET /generate/fake-email`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `count` | integer | No | 1 | Number of emails to generate (1-1000) |
| `domain` | string | No | - | Specific domain to use (e.g., "example.com") |
| `format` | string | No | "random" | Email format pattern (see formats below) |
| `include_job_title` | boolean | No | true | Include job title in response |
| `include_company` | boolean | No | true | Include company name in response |
| `include_names` | boolean | No | true | Include first and last names |
| `include_number` | boolean | No | false | Add random numbers to emails |
| `locale` | string | No | "en_US" | Locale for name generation (en_US, de_DE, fr_FR, es_ES, etc.) |

**Email Formats:**
- `first.last` - john.doe@example.com
- `first_last` - john_doe@example.com
- `firstlast` - johndoe@example.com
- `first-last` - john-doe@example.com
- `flast` - jdoe@example.com
- `firstl` - johnd@example.com
- `f.last` - j.doe@example.com
- `first.last.number` - john.doe.123@example.com
- `firstnumber` - john123@example.com
- `lastfirst` - doejohn@example.com
- `last.first` - doe.john@example.com
- `lastnumber` - doe123@example.com
- `random` - Random format for each email

**Example Request:**
```bash
curl -X GET "https://your-api-domain.com/generate/fake-email?count=5&format=random&locale=en_US" \
  -H "X-RapidAPI-Key: YOUR_API_KEY"
```

**Example Response:**
```json
[
  {
    "email": "john.doe@techcorp.com",
    "first_name": "John",
    "last_name": "Doe",
    "job_title": "Software Engineer",
    "company": "Tech Corp",
    "domain": "techcorp.com",
    "format": "first.last"
  },
  {
    "email": "jane_smith@innovate.io",
    "first_name": "Jane",
    "last_name": "Smith",
    "job_title": "Product Manager",
    "company": "Innovate Inc",
    "domain": "innovate.io",
    "format": "first_last"
  }
]
```

---

### Email Campaigns

#### 7. Send Email Campaign

Send email campaigns to unlimited recipients with advanced features.

**Endpoint:** `POST /communication/send-email`

**Request Body:**
```json
{
  "from_email": "sender@example.com",
  "from_name": "John Doe",
  "emails": [
    {
      "to_email": "recipient1@example.com",
      "subject": "Welcome to Our Service",
      "html_body": "<h1>Welcome!</h1><p>Thank you for joining.</p>",
      "text_body": "Welcome! Thank you for joining."
    },
    {
      "to_email": "recipient2@example.com",
      "subject": "Welcome to Our Service",
      "html_body": "<h1>Welcome!</h1><p>Thank you for joining.</p>",
      "text_body": "Welcome! Thank you for joining."
    }
  ],
  "batch_size": 50,
  "delay_between_batches": 1.0,
  "max_retries": 3,
  "concurrent_connections": 5
}
```

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `from_email` | string | Yes | - | Sender email address |
| `from_name` | string | No | - | Sender display name |
| `emails` | array | Yes | - | Array of email objects (unlimited) |
| `batch_size` | integer | No | 50 | Emails per batch (1-1000) |
| `delay_between_batches` | float | No | 1.0 | Delay in seconds between batches (0-60) |
| `max_retries` | integer | No | 3 | Max retry attempts per email (0-10) |
| `concurrent_connections` | integer | No | 5 | Concurrent SMTP connections (1-20) |

**Email Object:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to_email` | string | Yes | Recipient email address |
| `subject` | string | Yes | Email subject (max 200 chars) |
| `html_body` | string | Yes | HTML email content |
| `text_body` | string | No | Plain text email content (fallback if HTML not supported) |

**Example Request:**
```bash
curl -X POST "https://your-api-domain.com/communication/send-email" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from_email": "sender@example.com",
    "from_name": "John Doe",
    "emails": [
      {
        "to_email": "recipient@example.com",
        "subject": "Test Email",
        "html_body": "<h1>Hello</h1><p>This is a test.</p>",
        "text_body": "Hello\nThis is a test."
      }
    ]
  }'
```

**Example Response:**
```json
{
  "message": "Email campaign processing completed.",
  "total_emails": 100,
  "sent_count": 98,
  "failed_count": 2,
  "success_rate": "98.00%",
  "batches_processed": 2,
  "failed_details": [
    {
      "email": "invalid@example.com",
      "error": "SMTP error: Connection timeout"
    }
  ]
}
```

**Note:** SMTP configuration required. Set environment variables:
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`

---

## 💻 Code Examples

### Python

```python
import requests

# Set your API key
headers = {
    "X-RapidAPI-Key": "YOUR_API_KEY",
    "X-RapidAPI-Host": "your-api-host.rapidapi.com"
}

# Validate single email
response = requests.get(
    "https://your-api-domain.com/validate/inbox-status",
    params={"email": "user@example.com", "skip_smtp": True},
    headers=headers
)
print(response.json())

# Generate fake emails
response = requests.get(
    "https://your-api-domain.com/generate/fake-email",
    params={"count": 10, "format": "random", "locale": "en_US"},
    headers=headers
)
print(response.json())

# Bulk validation
response = requests.post(
    "https://your-api-domain.com/validate/inbox-status-bulk",
    json={"emails": ["user1@example.com", "user2@example.com"]},
    params={"skip_smtp": True},
    headers=headers
)
print(response.json())
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const headers = {
  'X-RapidAPI-Key': 'YOUR_API_KEY',
  'X-RapidAPI-Host': 'your-api-host.rapidapi.com'
};

// Validate single email
axios.get('https://your-api-domain.com/validate/inbox-status', {
  params: { email: 'user@example.com', skip_smtp: true },
  headers: headers
})
.then(response => console.log(response.data))
.catch(error => console.error(error));

// Generate fake emails
axios.get('https://your-api-domain.com/generate/fake-email', {
  params: { count: 10, format: 'random' },
  headers: headers
})
.then(response => console.log(response.data))
.catch(error => console.error(error));

// Bulk validation
axios.post('https://your-api-domain.com/validate/inbox-status-bulk', {
  emails: ['user1@example.com', 'user2@example.com']
}, {
  params: { skip_smtp: true },
  headers: headers
})
.then(response => console.log(response.data))
.catch(error => console.error(error));
```

### PHP

```php
<?php
$apiKey = 'YOUR_API_KEY';
$baseUrl = 'https://your-api-domain.com';

// Validate single email
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $baseUrl . '/validate/inbox-status?email=user@example.com&skip_smtp=true');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-RapidAPI-Key: ' . $apiKey,
    'X-RapidAPI-Host: your-api-host.rapidapi.com'
]);
$response = curl_exec($ch);
curl_close($ch);
echo $response;
?>
```

### cURL

```bash
# Validate email
curl -X GET "https://your-api-domain.com/validate/inbox-status?email=user@example.com&skip_smtp=true" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "X-RapidAPI-Host: your-api-host.rapidapi.com"

# Generate fake emails
curl -X GET "https://your-api-domain.com/generate/fake-email?count=5&format=random" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "X-RapidAPI-Host: your-api-host.rapidapi.com"

# Bulk validation
curl -X POST "https://your-api-domain.com/validate/inbox-status-bulk?skip_smtp=true" \
  -H "X-RapidAPI-Key: YOUR_API_KEY" \
  -H "X-RapidAPI-Host: your-api-host.rapidapi.com" \
  -H "Content-Type: application/json" \
  -d '{"emails": ["user1@example.com", "user2@example.com"]}'
```

---

## 📊 Response Times

| Endpoint | Average Response Time |
|----------|---------------------|
| Syntax Validation | < 10ms |
| Well-Known Domains | < 50ms |
| Unknown Domains (skip_smtp=true) | 3-5 seconds |
| Unknown Domains (skip_smtp=false) | 10-15 seconds |
| Bulk Validation (100 emails) | 30-60 seconds |
| Email Generation | < 100ms |

---

## 🔍 Understanding Confidence Scores

The `confidence_score` (0.0 - 1.0) indicates how reliable an email address is:

- **0.9 - 1.0**: Very High - Well-known provider, valid MX, deliverable
- **0.7 - 0.9**: High - Valid domain, MX records, likely deliverable
- **0.5 - 0.7**: Medium - Valid format, but uncertain deliverability
- **0.3 - 0.5**: Low - Suspicious or uncertain
- **0.0 - 0.3**: Very Low - Invalid, disposable, or no MX records

**Factors affecting confidence:**
- ✅ Valid syntax (+0.15)
- ✅ Not disposable (+0.15)
- ✅ Has MX records (+0.20)
- ✅ SMTP deliverable (+0.30)
- ✅ Not catch-all (+0.10)
- ✅ Personal email (not role-based) (+0.05)
- ✅ Paid domain (+0.05)

---

## ⚠️ Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Request successful
- **400 Bad Request**: Invalid parameters or request body
- **422 Unprocessable Entity**: Invalid email format
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

**Error Response Format:**
```json
{
  "detail": "Error message description"
}
```

---

## 📝 Rate Limits

Rate limits may apply based on your subscription tier. Check your RapidAPI dashboard for current limits.

**Recommended Practices:**
- Use `skip_smtp=true` for faster responses when SMTP validation isn't critical
- Batch requests when possible (use bulk endpoints)
- Implement retry logic with exponential backoff
- Cache results for frequently validated emails

---

## 🔒 Security & Privacy

- All requests should use HTTPS
- API keys should be kept secure and never exposed in client-side code
- Email addresses are processed securely and not stored
- No sensitive data is logged

---

## 📞 Support

For API support, issues, or questions:
- Check the API documentation at `/docs` endpoint
- Contact support through RapidAPI platform
- Review error messages for troubleshooting

---

**Last Updated:** 2025
