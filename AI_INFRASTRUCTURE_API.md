# AI Money Maker - API dla Infrastruktury AI

Dokumentacja API do integracji z zewnętrzną infrastrukturą AI do automatycznego przyjmowania i wykonywania zleceń.

## Base URL
```
https://ai-money-agent-4.preview.emergentagent.com
```

## Endpointy

### 1. Tworzenie pojedynczego zlecenia
**POST** `/api/jobs/create`

Tworzy nowe zlecenie w systemie.

**Request Body:**
```json
{
  "title": "Blog Post: AI in Healthcare",
  "description": "Write a 500-word blog post about AI applications in healthcare",
  "job_type": "blog_post",
  "word_count": 500,
  "price_gbp": 30.00
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job created successfully",
  "job_id": "69d000ca2471d8070521c215",
  "job": {
    "title": "Blog Post: AI in Healthcare",
    "description": "Write a 500-word blog post about AI applications in healthcare",
    "job_type": "blog_post",
    "word_count": 500,
    "price_gbp": 30.0,
    "status": "available",
    "created_at": "2026-04-03T18:02:50.299058+00:00",
    "source": "external_ai_infrastructure",
    "_id": "69d000ca2471d8070521c215"
  }
}
```

---

### 2. Webhook do przyjmowania zleceń
**POST** `/api/jobs/webhook`

Webhook endpoint dla systemów AI do push'owania zleceń.

**Request Body:**
```json
{
  "title": "Product Description: Smart Speaker",
  "description": "Create compelling 200-word product description",
  "job_type": "product_description",
  "word_count": 200,
  "price_gbp": 15.00,
  "external_id": "EXT-12345",
  "metadata": {
    "client": "TechCorp",
    "priority": "high",
    "deadline": "2026-04-10"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job received and queued",
  "job_id": "69d000d02471d8070521c216"
}
```

---

### 3. Bulk tworzenie zleceń
**POST** `/api/jobs/bulk-create`

Tworzy wiele zleceń jednocześnie (batch import).

**Request Body:**
```json
[
  {
    "title": "Email Marketing: Summer Sale",
    "description": "Create email campaign for summer sale",
    "job_type": "email_marketing",
    "word_count": 300,
    "price_gbp": 20.00
  },
  {
    "title": "Social Media: Product Launch",
    "description": "Write 5 social media posts for product launch",
    "job_type": "social_media",
    "word_count": 500,
    "price_gbp": 28.00
  }
]
```

**Response:**
```json
{
  "success": true,
  "message": "2 jobs created successfully",
  "job_ids": [
    "69d000dc2471d8070521c217",
    "69d000dc2471d8070521c218"
  ]
}
```

---

### 4. Auto-wykonywanie zleceń
**POST** `/api/jobs/auto-execute`

Automatycznie wykonuje wszystkie dostępne zlecenia używając AI.

**Request:** Brak body

**Response:**
```json
{
  "success": true,
  "message": "Auto-execution completed",
  "jobs_executed": 5,
  "total_earnings_gbp": 163.00,
  "errors": null
}
```

---

### 5. Lista dostępnych zleceń
**GET** `/api/jobs/available`

Pobiera listę wszystkich dostępnych zleceń.

**Response:**
```json
[
  {
    "_id": "69d000ca2471d8070521c215",
    "title": "Blog Post: AI in Healthcare",
    "description": "Write a 500-word blog post...",
    "job_type": "blog_post",
    "word_count": 500,
    "price_gbp": 30.0,
    "status": "available",
    "source": "external_ai_infrastructure",
    "created_at": "2026-04-03T18:02:50.299058+00:00"
  }
]
```

---

## Typy zleceń (job_type)

- `blog_post` - Posty blogowe
- `product_description` - Opisy produktów
- `social_media` - Posty social media
- `email_marketing` - Kampanie email marketingowe
- `article` - Artykuły
- `general` - Ogólne teksty

---

## Przykładowy kod integracji

### Python - Pojedyncze zlecenie
```python
import requests

API_URL = "https://ai-money-agent-4.preview.emergentagent.com"

def create_job(title, description, job_type, word_count, price_gbp):
    endpoint = f"{API_URL}/api/jobs/create"
    
    payload = {
        "title": title,
        "description": description,
        "job_type": job_type,
        "word_count": word_count,
        "price_gbp": price_gbp
    }
    
    response = requests.post(endpoint, json=payload)
    return response.json()

# Przykład użycia
result = create_job(
    title="Blog Post: Future of AI",
    description="Write engaging 600-word blog post about AI future",
    job_type="blog_post",
    word_count=600,
    price_gbp=32.00
)

print(f"Job created: {result['job_id']}")
```

### Python - Webhook handler
```python
from fastapi import FastAPI, Request

app = FastAPI()

AI_MONEY_MAKER_URL = "https://ai-money-agent-4.preview.emergentagent.com"

@app.post("/send-job-to-ai-money-maker")
async def send_job(request: Request):
    """Wysyła zlecenie do AI Money Maker"""
    job_data = await request.json()
    
    response = requests.post(
        f"{AI_MONEY_MAKER_URL}/api/jobs/webhook",
        json=job_data
    )
    
    return response.json()
```

### Python - Bulk import
```python
def bulk_import_jobs(jobs_list):
    endpoint = f"{API_URL}/api/jobs/bulk-create"
    
    response = requests.post(endpoint, json=jobs_list)
    return response.json()

# Przykład użycia
jobs = [
    {
        "title": "Email: New Product",
        "description": "Email campaign for new product",
        "job_type": "email_marketing",
        "word_count": 300,
        "price_gbp": 22.00
    },
    {
        "title": "Social: Brand Launch",
        "description": "Social media posts for brand launch",
        "job_type": "social_media",
        "word_count": 400,
        "price_gbp": 26.00
    }
]

result = bulk_import_jobs(jobs)
print(f"Created {len(result['job_ids'])} jobs")
```

### Python - Auto-execute
```python
def auto_execute_all_jobs():
    endpoint = f"{API_URL}/api/jobs/auto-execute"
    
    response = requests.post(endpoint)
    return response.json()

# Przykład użycia
result = auto_execute_all_jobs()
print(f"Executed {result['jobs_executed']} jobs")
print(f"Total earnings: £{result['total_earnings_gbp']}")
```

---

## cURL Przykłady

### Tworzenie zlecenia
```bash
curl -X POST https://ai-money-agent-4.preview.emergentagent.com/api/jobs/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Blog Post: AI Trends",
    "description": "Write 500-word blog post about AI trends",
    "job_type": "blog_post",
    "word_count": 500,
    "price_gbp": 28.00
  }'
```

### Webhook
```bash
curl -X POST https://ai-money-agent-4.preview.emergentagent.com/api/jobs/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Description",
    "description": "Write product description",
    "job_type": "product_description",
    "word_count": 250,
    "price_gbp": 18.00,
    "external_id": "EXT-001"
  }'
```

### Auto-execute
```bash
curl -X POST https://ai-money-agent-4.preview.emergentagent.com/api/jobs/auto-execute
```

---

## Automatyzacja z cron

### Linux cron - Auto-execute co godzinę
```bash
# Dodaj do crontab (crontab -e)
0 * * * * curl -X POST https://ai-money-agent-4.preview.emergentagent.com/api/jobs/auto-execute
```

### Node.js - Scheduled job
```javascript
const cron = require('node-cron');
const axios = require('axios');

const API_URL = 'https://ai-money-agent-4.preview.emergentagent.com';

// Auto-execute co 6 godzin
cron.schedule('0 */6 * * *', async () => {
  try {
    const response = await axios.post(`${API_URL}/api/jobs/auto-execute`);
    console.log(`Executed ${response.data.jobs_executed} jobs`);
  } catch (error) {
    console.error('Error:', error);
  }
});
```

---

## Monitoring

### Sprawdzanie balansu
```bash
curl https://ai-money-agent-4.preview.emergentagent.com/api/balance
```

**Response:**
```json
{
  "total_earnings": 293.00,
  "total_withdrawn": 60.00,
  "available_balance": 233.00,
  "can_withdraw": true
}
```

### Statystyki
```bash
curl https://ai-money-agent-4.preview.emergentagent.com/api/stats
```

**Response:**
```json
{
  "total_earnings_gbp": 293.00,
  "jobs_completed": 9,
  "jobs_available": 5,
  "today_earnings": 163.00,
  "this_week_earnings": 293.00
}
```

---

## Bezpieczeństwo

⚠️ **Ważne uwagi:**
1. W produkcji dodaj autoryzację (API keys, JWT tokens)
2. Używaj HTTPS dla wszystkich requestów
3. Waliduj dane wejściowe
4. Rate limiting dla webhooków
5. Monitoring i alerty dla błędów

---

## Support

Pytania? Problemy? 
- Backend: http://localhost:8001 (development)
- Production: https://ai-money-agent-4.preview.emergentagent.com
