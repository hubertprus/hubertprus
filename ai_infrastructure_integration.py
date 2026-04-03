#!/usr/bin/env python3
"""
AI Money Maker - Przykładowy skrypt integracji z infrastrukturą AI

Ten skrypt pokazuje jak zintegrować własną infrastrukturę AI
z systemem AI Money Maker do automatycznego przyjmowania i wykonywania zleceń.
"""

import requests
import time
from typing import List, Dict

# Konfiguracja
API_URL = "https://ai-money-agent-4.preview.emergentagent.com"
# API_URL = "http://localhost:8001"  # Dla local development

class AIMoneyMakerClient:
    """Klient do komunikacji z AI Money Maker API"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        
    def create_job(self, title: str, description: str, job_type: str, 
                   word_count: int, price_gbp: float) -> Dict:
        """Tworzy pojedyncze zlecenie"""
        endpoint = f"{self.api_url}/api/jobs/create"
        
        payload = {
            "title": title,
            "description": description,
            "job_type": job_type,
            "word_count": word_count,
            "price_gbp": price_gbp
        }
        
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    def send_webhook(self, job_data: Dict) -> Dict:
        """Wysyła zlecenie przez webhook"""
        endpoint = f"{self.api_url}/api/jobs/webhook"
        
        response = requests.post(endpoint, json=job_data)
        response.raise_for_status()
        return response.json()
    
    def bulk_create_jobs(self, jobs: List[Dict]) -> Dict:
        """Tworzy wiele zleceń jednocześnie"""
        endpoint = f"{self.api_url}/api/jobs/bulk-create"
        
        response = requests.post(endpoint, json=jobs)
        response.raise_for_status()
        return response.json()
    
    def auto_execute_jobs(self) -> Dict:
        """Automatycznie wykonuje wszystkie dostępne zlecenia"""
        endpoint = f"{self.api_url}/api/jobs/auto-execute"
        
        response = requests.post(endpoint)
        response.raise_for_status()
        return response.json()
    
    def get_available_jobs(self) -> List[Dict]:
        """Pobiera listę dostępnych zleceń"""
        endpoint = f"{self.api_url}/api/jobs/available"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    
    def get_balance(self) -> Dict:
        """Pobiera informacje o saldzie"""
        endpoint = f"{self.api_url}/api/balance"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict:
        """Pobiera statystyki"""
        endpoint = f"{self.api_url}/api/stats"
        
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()


def example_1_single_job():
    """Przykład 1: Tworzenie pojedynczego zlecenia"""
    print("\n=== Przykład 1: Pojedyncze zlecenie ===")
    
    client = AIMoneyMakerClient(API_URL)
    
    result = client.create_job(
        title="Blog Post: Cybersecurity Tips 2026",
        description="Write comprehensive 650-word blog post about cybersecurity tips for businesses in 2026",
        job_type="blog_post",
        word_count=650,
        price_gbp=34.00
    )
    
    print(f"✓ Zlecenie utworzone!")
    print(f"  Job ID: {result['job_id']}")
    print(f"  Tytuł: {result['job']['title']}")
    print(f"  Cena: £{result['job']['price_gbp']}")


def example_2_webhook():
    """Przykład 2: Wysyłanie zlecenia przez webhook"""
    print("\n=== Przykład 2: Webhook ===")
    
    client = AIMoneyMakerClient(API_URL)
    
    job_data = {
        "title": "Product Description: AI Assistant Device",
        "description": "Create compelling 250-word product description for AI-powered personal assistant device",
        "job_type": "product_description",
        "word_count": 250,
        "price_gbp": 18.00,
        "external_id": "PROD-AI-001",
        "metadata": {
            "client": "TechStartup Inc",
            "priority": "high",
            "deadline": "2026-04-15"
        }
    }
    
    result = client.send_webhook(job_data)
    
    print(f"✓ Zlecenie wysłane przez webhook!")
    print(f"  Job ID: {result['job_id']}")


def example_3_bulk_import():
    """Przykład 3: Bulk import zleceń"""
    print("\n=== Przykład 3: Bulk Import ===")
    
    client = AIMoneyMakerClient(API_URL)
    
    jobs = [
        {
            "title": "Email Series: Customer Onboarding",
            "description": "Create 3-email onboarding series for new customers",
            "job_type": "email_marketing",
            "word_count": 450,
            "price_gbp": 27.00
        },
        {
            "title": "Social Media: Weekly Content Calendar",
            "description": "Write 7 social media posts for weekly content calendar",
            "job_type": "social_media",
            "word_count": 700,
            "price_gbp": 35.00
        },
        {
            "title": "Article: Remote Work Best Practices",
            "description": "Write informative 800-word article about remote work best practices",
            "job_type": "article",
            "word_count": 800,
            "price_gbp": 42.00
        }
    ]
    
    result = client.bulk_create_jobs(jobs)
    
    print(f"✓ Utworzono {len(result['job_ids'])} zleceń!")
    for i, job_id in enumerate(result['job_ids'], 1):
        print(f"  {i}. Job ID: {job_id}")


def example_4_auto_execute():
    """Przykład 4: Automatyczne wykonywanie zleceń"""
    print("\n=== Przykład 4: Auto-Execute ===")
    
    client = AIMoneyMakerClient(API_URL)
    
    # Sprawdź dostępne zlecenia
    available = client.get_available_jobs()
    print(f"Dostępnych zleceń: {len(available)}")
    
    if len(available) > 0:
        print("\nWykonuję zlecenia...")
        result = client.auto_execute_jobs()
        
        print(f"\n✓ Wykonano {result['jobs_executed']} zleceń!")
        print(f"  Zarobiono: £{result['total_earnings_gbp']}")
        
        if result.get('errors'):
            print(f"  Błędy: {len(result['errors'])}")
    else:
        print("Brak dostępnych zleceń do wykonania.")


def example_5_monitoring():
    """Przykład 5: Monitoring i statystyki"""
    print("\n=== Przykład 5: Monitoring ===")
    
    client = AIMoneyMakerClient(API_URL)
    
    # Pobierz balance
    balance = client.get_balance()
    print("\nSaldo:")
    print(f"  Łącznie zarobione: £{balance['total_earnings']}")
    print(f"  Wypłacono: £{balance['total_withdrawn']}")
    print(f"  Dostępne: £{balance['available_balance']}")
    print(f"  Można wypłacić: {'Tak' if balance['can_withdraw'] else 'Nie'}")
    
    # Pobierz statystyki
    stats = client.get_stats()
    print("\nStatystyki:")
    print(f"  Wykonanych zleceń: {stats['jobs_completed']}")
    print(f"  Dostępnych zleceń: {stats['jobs_available']}")
    print(f"  Zarobki dzisiaj: £{stats['today_earnings']}")
    print(f"  Zarobki w tym tygodniu: £{stats['this_week_earnings']}")


def example_6_automated_workflow():
    """Przykład 6: Zautomatyzowany workflow"""
    print("\n=== Przykład 6: Zautomatyzowany Workflow ===")
    
    client = AIMoneyMakerClient(API_URL)
    
    print("1. Tworzenie nowych zleceń...")
    jobs = [
        {
            "title": "Landing Page Copy: SaaS Product",
            "description": "Write compelling landing page copy for new SaaS product",
            "job_type": "general",
            "word_count": 400,
            "price_gbp": 30.00
        },
        {
            "title": "Blog Post: AI Ethics",
            "description": "Write thought-provoking 600-word blog post about AI ethics",
            "job_type": "blog_post",
            "word_count": 600,
            "price_gbp": 32.00
        }
    ]
    
    create_result = client.bulk_create_jobs(jobs)
    print(f"   ✓ Utworzono {len(create_result['job_ids'])} zleceń")
    
    print("\n2. Czekam 2 sekundy...")
    time.sleep(2)
    
    print("\n3. Wykonuję zlecenia automatycznie...")
    execute_result = client.auto_execute_jobs()
    print(f"   ✓ Wykonano {execute_result['jobs_executed']} zleceń")
    print(f"   ✓ Zarobiono £{execute_result['total_earnings_gbp']}")
    
    print("\n4. Sprawdzam zaktualizowane saldo...")
    balance = client.get_balance()
    print(f"   ✓ Dostępne saldo: £{balance['available_balance']}")


def main():
    """Main function - uruchamia wszystkie przykłady"""
    print("=" * 60)
    print("AI Money Maker - Przykłady integracji z infrastrukturą AI")
    print("=" * 60)
    
    try:
        # Uruchom wszystkie przykłady
        example_1_single_job()
        time.sleep(1)
        
        example_2_webhook()
        time.sleep(1)
        
        example_3_bulk_import()
        time.sleep(1)
        
        example_5_monitoring()
        time.sleep(1)
        
        # Uncomment to run auto-execute examples
        # example_4_auto_execute()
        # example_6_automated_workflow()
        
        print("\n" + "=" * 60)
        print("✓ Wszystkie przykłady wykonane pomyślnie!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Błąd: {e}")


if __name__ == "__main__":
    main()
