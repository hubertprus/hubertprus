#!/usr/bin/env python3
"""
Backend API Testing for AI Money Maker - AI Infrastructure Integration Endpoints
Testing new endpoints: /api/jobs/create, /api/jobs/webhook, /api/jobs/bulk-create, /api/jobs/auto-execute
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://ai-money-agent-4.preview.emergentagent.com/api"

def test_api_endpoint(method, endpoint, data=None, headers=None):
    """Helper function to test API endpoints"""
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        
        print(f"\n{'='*60}")
        print(f"Testing: {method.upper()} {endpoint}")
        print(f"URL: {url}")
        if data:
            print(f"Request Data: {json.dumps(data, indent=2)}")
        print(f"Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            return response.status_code, response_json
        except:
            print(f"Response Text: {response.text}")
            return response.status_code, response.text
            
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"ERROR Testing: {method.upper()} {endpoint}")
        print(f"Error: {str(e)}")
        return None, str(e)

def main():
    print("🚀 Starting AI Infrastructure Integration Endpoints Testing")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Test results tracking
    test_results = []
    
    # ========================================
    # Test 1: Create job with valid data
    # ========================================
    print("\n" + "="*80)
    print("TEST 1: POST /api/jobs/create - Create single job with valid data")
    print("="*80)
    
    valid_job_data = {
        "title": "AI Infrastructure Test: Social Media Campaign",
        "description": "Create engaging social media posts for a new tech startup launch",
        "job_type": "social_media",
        "word_count": 400,
        "price_gbp": 35.00
    }
    
    status, response = test_api_endpoint("POST", "/jobs/create", valid_job_data)
    
    if status == 200 and isinstance(response, dict) and response.get("success"):
        print("✅ TEST 1 PASSED: Job created successfully")
        job_id_1 = response.get("job_id")
        test_results.append(("Create job with valid data", "PASSED", f"Job ID: {job_id_1}"))
    else:
        print("❌ TEST 1 FAILED: Job creation failed")
        test_results.append(("Create job with valid data", "FAILED", f"Status: {status}, Response: {response}"))
    
    # ========================================
    # Test 2: Create job with missing fields
    # ========================================
    print("\n" + "="*80)
    print("TEST 2: POST /api/jobs/create - Create job with missing fields (should fail)")
    print("="*80)
    
    invalid_job_data = {
        "title": "Incomplete Job",
        # Missing description, job_type, word_count, price_gbp
    }
    
    status, response = test_api_endpoint("POST", "/jobs/create", invalid_job_data)
    
    if status == 500:
        print("✅ TEST 2 PASSED: Job creation properly failed with missing fields")
        test_results.append(("Create job with missing fields", "PASSED", "Properly rejected invalid data"))
    else:
        print("❌ TEST 2 FAILED: Job creation should have failed")
        test_results.append(("Create job with missing fields", "FAILED", f"Status: {status}, should be 500"))
    
    # ========================================
    # Test 3: Webhook with full metadata
    # ========================================
    print("\n" + "="*80)
    print("TEST 3: POST /api/jobs/webhook - Webhook with full metadata")
    print("="*80)
    
    webhook_full_data = {
        "title": "AI Infrastructure Webhook: Blog Post Creation",
        "description": "Write a comprehensive blog post about AI trends in 2024",
        "job_type": "blog_post",
        "word_count": 800,
        "price_gbp": 45.00,
        "external_id": "EXT_12345",
        "metadata": {
            "source_system": "AI_Infrastructure_v2",
            "priority": "high",
            "client_id": "CLIENT_789",
            "campaign_id": "CAMP_456"
        }
    }
    
    status, response = test_api_endpoint("POST", "/jobs/webhook", webhook_full_data)
    
    if status == 200 and isinstance(response, dict) and response.get("success"):
        print("✅ TEST 3 PASSED: Webhook with full metadata accepted")
        job_id_2 = response.get("job_id")
        test_results.append(("Webhook with full metadata", "PASSED", f"Job ID: {job_id_2}"))
    else:
        print("❌ TEST 3 FAILED: Webhook with full metadata failed")
        test_results.append(("Webhook with full metadata", "FAILED", f"Status: {status}, Response: {response}"))
    
    # ========================================
    # Test 4: Webhook with minimal required fields
    # ========================================
    print("\n" + "="*80)
    print("TEST 4: POST /api/jobs/webhook - Webhook with minimal required fields")
    print("="*80)
    
    webhook_minimal_data = {
        "title": "Minimal Webhook Job: Product Description",
        "description": "Create a product description for eco-friendly packaging"
        # Using defaults for job_type, word_count, price_gbp
    }
    
    status, response = test_api_endpoint("POST", "/jobs/webhook", webhook_minimal_data)
    
    if status == 200 and isinstance(response, dict) and response.get("success"):
        print("✅ TEST 4 PASSED: Webhook with minimal fields accepted")
        job_id_3 = response.get("job_id")
        test_results.append(("Webhook with minimal fields", "PASSED", f"Job ID: {job_id_3}"))
    else:
        print("❌ TEST 4 FAILED: Webhook with minimal fields failed")
        test_results.append(("Webhook with minimal fields", "FAILED", f"Status: {status}, Response: {response}"))
    
    # ========================================
    # Test 5: Bulk create with 3 jobs
    # ========================================
    print("\n" + "="*80)
    print("TEST 5: POST /api/jobs/bulk-create - Create 3 jobs at once")
    print("="*80)
    
    bulk_jobs_data = [
        {
            "title": "Bulk Job 1: Email Marketing Campaign",
            "description": "Create email marketing content for holiday sales",
            "job_type": "email_marketing",
            "word_count": 300,
            "price_gbp": 22.00
        },
        {
            "title": "Bulk Job 2: Product Review Article",
            "description": "Write a detailed review of the latest smartphone",
            "job_type": "article",
            "word_count": 600,
            "price_gbp": 38.00
        },
        {
            "title": "Bulk Job 3: Website Copy",
            "description": "Create compelling website copy for a fitness app",
            "job_type": "website_copy",
            "word_count": 450,
            "price_gbp": 28.00
        }
    ]
    
    status, response = test_api_endpoint("POST", "/jobs/bulk-create", bulk_jobs_data)
    
    if status == 200 and isinstance(response, dict) and response.get("success"):
        job_ids = response.get("job_ids", [])
        if len(job_ids) == 3:
            print("✅ TEST 5 PASSED: Bulk create with 3 jobs successful")
            test_results.append(("Bulk create 3 jobs", "PASSED", f"Created {len(job_ids)} jobs"))
        else:
            print(f"❌ TEST 5 FAILED: Expected 3 job IDs, got {len(job_ids)}")
            test_results.append(("Bulk create 3 jobs", "FAILED", f"Expected 3 jobs, got {len(job_ids)}"))
    else:
        print("❌ TEST 5 FAILED: Bulk create failed")
        test_results.append(("Bulk create 3 jobs", "FAILED", f"Status: {status}, Response: {response}"))
    
    # ========================================
    # Test 6: Check available jobs list
    # ========================================
    print("\n" + "="*80)
    print("TEST 6: GET /api/jobs/available - Check available jobs list")
    print("="*80)
    
    status, response = test_api_endpoint("GET", "/jobs/available")
    
    if status == 200 and isinstance(response, list):
        available_count = len(response)
        print(f"✅ TEST 6 PASSED: Found {available_count} available jobs")
        
        # Show some job details
        for i, job in enumerate(response[:3]):  # Show first 3 jobs
            print(f"  Job {i+1}: {job.get('title', 'N/A')} - £{job.get('price_gbp', 0)}")
        
        test_results.append(("Check available jobs", "PASSED", f"{available_count} jobs available"))
    else:
        print("❌ TEST 6 FAILED: Could not retrieve available jobs")
        test_results.append(("Check available jobs", "FAILED", f"Status: {status}, Response: {response}"))
    
    # ========================================
    # Test 7: Auto-execute all available jobs
    # ========================================
    print("\n" + "="*80)
    print("TEST 7: POST /api/jobs/auto-execute - Auto-execute all available jobs")
    print("="*80)
    
    status, response = test_api_endpoint("POST", "/jobs/auto-execute")
    
    if status == 200 and isinstance(response, dict) and response.get("success"):
        jobs_executed = response.get("jobs_executed", 0)
        total_earnings = response.get("total_earnings_gbp", 0)
        errors = response.get("errors", [])
        
        if jobs_executed > 0:
            print(f"✅ TEST 7 PASSED: Auto-executed {jobs_executed} jobs, earned £{total_earnings}")
            if errors:
                print(f"⚠️  Some jobs had errors: {len(errors)} errors")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"    Error: {error}")
            test_results.append(("Auto-execute jobs", "PASSED", f"Executed {jobs_executed} jobs, £{total_earnings} earned"))
        else:
            print("✅ TEST 7 PASSED: No jobs available to execute")
            test_results.append(("Auto-execute jobs", "PASSED", "No jobs available to execute"))
    else:
        print("❌ TEST 7 FAILED: Auto-execute failed")
        test_results.append(("Auto-execute jobs", "FAILED", f"Status: {status}, Response: {response}"))
    
    # ========================================
    # Test 8: Verify stats after auto-execution
    # ========================================
    print("\n" + "="*80)
    print("TEST 8: GET /api/stats - Verify stats after auto-execution")
    print("="*80)
    
    status, response = test_api_endpoint("GET", "/stats")
    
    if status == 200 and isinstance(response, dict):
        total_earnings = response.get("total_earnings_gbp", 0)
        jobs_completed = response.get("jobs_completed", 0)
        jobs_available = response.get("jobs_available", 0)
        
        print(f"✅ TEST 8 PASSED: Stats retrieved successfully")
        print(f"  Total Earnings: £{total_earnings}")
        print(f"  Jobs Completed: {jobs_completed}")
        print(f"  Jobs Available: {jobs_available}")
        
        test_results.append(("Verify stats", "PASSED", f"£{total_earnings} total, {jobs_completed} completed, {jobs_available} available"))
    else:
        print("❌ TEST 8 FAILED: Could not retrieve stats")
        test_results.append(("Verify stats", "FAILED", f"Status: {status}, Response: {response}"))
    
    # ========================================
    # FINAL TEST SUMMARY
    # ========================================
    print("\n" + "="*80)
    print("🏁 FINAL TEST SUMMARY - AI Infrastructure Integration Endpoints")
    print("="*80)
    
    passed_tests = 0
    failed_tests = 0
    
    for test_name, result, details in test_results:
        status_icon = "✅" if result == "PASSED" else "❌"
        print(f"{status_icon} {test_name}: {result}")
        print(f"   Details: {details}")
        
        if result == "PASSED":
            passed_tests += 1
        else:
            failed_tests += 1
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    print(f"   📈 Success Rate: {(passed_tests/(passed_tests+failed_tests)*100):.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! AI Infrastructure Integration endpoints are working correctly.")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Please review the failed tests above.")
    
    return passed_tests, failed_tests

if __name__ == "__main__":
    main()