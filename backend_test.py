#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for AI Money Maker
Tests all core job execution and stats endpoints
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend .env
BACKEND_URL = "https://ai-money-agent-4.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            self.passed_tests.append(test_name)
            print(f"✅ {test_name}")
        else:
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}: {details}")
            
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "AI Money Maker API is running" in data.get("message", ""):
                    self.log_test("Root endpoint", True, "API is running", data)
                else:
                    self.log_test("Root endpoint", False, f"Unexpected message: {data}")
            else:
                self.log_test("Root endpoint", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Root endpoint", False, f"Connection error: {str(e)}")
    
    def test_get_available_jobs(self):
        """Test GET /api/jobs/available - should return list of available jobs with GBP prices"""
        try:
            response = requests.get(f"{API_BASE}/jobs/available", timeout=10)
            if response.status_code == 200:
                jobs = response.json()
                
                if not isinstance(jobs, list):
                    self.log_test("GET /api/jobs/available", False, "Response is not a list")
                    return
                
                if len(jobs) == 0:
                    self.log_test("GET /api/jobs/available", False, "No jobs returned")
                    return
                
                # Check job structure and GBP prices
                valid_jobs = True
                job_details = []
                
                for job in jobs:
                    required_fields = ["title", "description", "job_type", "word_count", "price_gbp", "status"]
                    missing_fields = [field for field in required_fields if field not in job]
                    
                    if missing_fields:
                        valid_jobs = False
                        job_details.append(f"Missing fields: {missing_fields}")
                        continue
                    
                    if job["status"] != "available":
                        valid_jobs = False
                        job_details.append(f"Job {job.get('title', 'Unknown')} status is {job['status']}, not 'available'")
                    
                    if not isinstance(job["price_gbp"], (int, float)) or job["price_gbp"] <= 0:
                        valid_jobs = False
                        job_details.append(f"Job {job.get('title', 'Unknown')} has invalid price_gbp: {job['price_gbp']}")
                    
                    job_details.append(f"✓ {job['title']}: £{job['price_gbp']} ({job['word_count']} words)")
                
                if valid_jobs:
                    self.log_test("GET /api/jobs/available", True, f"Found {len(jobs)} valid jobs with GBP prices", job_details)
                else:
                    self.log_test("GET /api/jobs/available", False, f"Invalid job data: {'; '.join(job_details)}")
            else:
                self.log_test("GET /api/jobs/available", False, f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("GET /api/jobs/available", False, f"Error: {str(e)}")
    
    def test_get_job_by_id(self, job_id: str):
        """Test GET /api/jobs/{job_id} - should return specific job details"""
        try:
            response = requests.get(f"{API_BASE}/jobs/{job_id}", timeout=10)
            if response.status_code == 200:
                job = response.json()
                required_fields = ["title", "description", "job_type", "word_count", "price_gbp", "status"]
                missing_fields = [field for field in required_fields if field not in job]
                
                if missing_fields:
                    self.log_test("GET /api/jobs/{job_id}", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("GET /api/jobs/{job_id}", True, f"Job details: {job['title']} - £{job['price_gbp']}", job)
            elif response.status_code == 404:
                self.log_test("GET /api/jobs/{job_id}", False, f"Job not found: {job_id}")
            else:
                self.log_test("GET /api/jobs/{job_id}", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/jobs/{job_id}", False, f"Error: {str(e)}")
    
    def test_execute_job(self, job_id: str):
        """Test POST /api/jobs/execute/{job_id} - AI should generate content using GPT-5.2"""
        try:
            print(f"🔄 Executing job {job_id}... (this may take 30-60 seconds)")
            response = requests.post(f"{API_BASE}/jobs/execute/{job_id}", timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ["success", "message", "earnings_gbp"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_test("POST /api/jobs/execute/{job_id}", False, f"Missing fields: {missing_fields}")
                elif result.get("success") == True:
                    earnings = result.get("earnings_gbp", 0)
                    content_preview = result.get("content_preview", "No preview")
                    self.log_test("POST /api/jobs/execute/{job_id}", True, 
                                f"Job executed successfully. Earned £{earnings}. Content preview: {content_preview[:100]}...", result)
                else:
                    self.log_test("POST /api/jobs/execute/{job_id}", False, f"Job execution failed: {result.get('message', 'Unknown error')}")
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Unknown error")
                if "not available" in error_detail:
                    self.log_test("POST /api/jobs/execute/{job_id}", False, f"Job already executed or not available: {error_detail}")
                else:
                    self.log_test("POST /api/jobs/execute/{job_id}", False, f"Bad request: {error_detail}")
            elif response.status_code == 404:
                self.log_test("POST /api/jobs/execute/{job_id}", False, "Job not found")
            else:
                self.log_test("POST /api/jobs/execute/{job_id}", False, f"Status code: {response.status_code}, Response: {response.text}")
        except requests.exceptions.Timeout:
            self.log_test("POST /api/jobs/execute/{job_id}", False, "Request timeout (>120s) - AI generation may be taking too long")
        except Exception as e:
            self.log_test("POST /api/jobs/execute/{job_id}", False, f"Error: {str(e)}")
    
    def test_get_stats(self):
        """Test GET /api/stats - should show earnings in GBP and job counts"""
        try:
            response = requests.get(f"{API_BASE}/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["total_earnings_gbp", "jobs_completed", "today_earnings", "this_week_earnings"]
                missing_fields = [field for field in required_fields if field not in stats]
                
                if missing_fields:
                    self.log_test("GET /api/stats", False, f"Missing fields: {missing_fields}")
                else:
                    # Validate data types and values
                    valid_stats = True
                    issues = []
                    
                    for field in ["total_earnings_gbp", "today_earnings", "this_week_earnings"]:
                        if not isinstance(stats[field], (int, float)) or stats[field] < 0:
                            valid_stats = False
                            issues.append(f"{field} is invalid: {stats[field]}")
                    
                    if not isinstance(stats["jobs_completed"], int) or stats["jobs_completed"] < 0:
                        valid_stats = False
                        issues.append(f"jobs_completed is invalid: {stats['jobs_completed']}")
                    
                    if valid_stats:
                        stats_summary = f"Total: £{stats['total_earnings_gbp']}, Completed: {stats['jobs_completed']}, Today: £{stats['today_earnings']}, Week: £{stats['this_week_earnings']}"
                        self.log_test("GET /api/stats", True, f"Stats valid: {stats_summary}", stats)
                    else:
                        self.log_test("GET /api/stats", False, f"Invalid stats data: {'; '.join(issues)}")
            else:
                self.log_test("GET /api/stats", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/stats", False, f"Error: {str(e)}")
    
    def test_get_work_history(self):
        """Test GET /api/work/history - should return completed works with job titles and earnings"""
        try:
            response = requests.get(f"{API_BASE}/work/history", timeout=10)
            if response.status_code == 200:
                history = response.json()
                
                if not isinstance(history, list):
                    self.log_test("GET /api/work/history", False, "Response is not a list")
                    return
                
                if len(history) == 0:
                    self.log_test("GET /api/work/history", True, "No completed work history (empty list is valid)")
                    return
                
                # Check work structure
                valid_history = True
                work_details = []
                
                for work in history:
                    required_fields = ["job_id", "job_title", "generated_content", "earnings_gbp", "completed_at"]
                    missing_fields = [field for field in required_fields if field not in work]
                    
                    if missing_fields:
                        valid_history = False
                        work_details.append(f"Missing fields: {missing_fields}")
                        continue
                    
                    if not isinstance(work["earnings_gbp"], (int, float)) or work["earnings_gbp"] <= 0:
                        valid_history = False
                        work_details.append(f"Invalid earnings_gbp: {work['earnings_gbp']}")
                    
                    work_details.append(f"✓ {work['job_title']}: £{work['earnings_gbp']}")
                
                if valid_history:
                    total_earnings = sum(work["earnings_gbp"] for work in history)
                    self.log_test("GET /api/work/history", True, 
                                f"Found {len(history)} completed works, total earnings: £{total_earnings}", work_details)
                else:
                    self.log_test("GET /api/work/history", False, f"Invalid work history data: {'; '.join(work_details)}")
            else:
                self.log_test("GET /api/work/history", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/work/history", False, f"Error: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all priority tests"""
        print("🚀 Starting AI Money Maker Backend API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test 1: Root endpoint
        self.test_root_endpoint()
        
        # Test 2: Get available jobs
        self.test_get_available_jobs()
        
        # Get a job ID for further testing
        job_id = None
        try:
            response = requests.get(f"{API_BASE}/jobs/available", timeout=10)
            if response.status_code == 200:
                jobs = response.json()
                if jobs and len(jobs) > 0:
                    job_id = jobs[0].get("_id")
        except:
            pass
        
        # Test 3: Get job by ID (if we have a job ID)
        if job_id:
            self.test_get_job_by_id(job_id)
        
        # Test 4: Get initial stats
        print("\n📊 Testing stats before job execution...")
        self.test_get_stats()
        
        # Test 5: Get initial work history
        print("\n📋 Testing work history before job execution...")
        self.test_get_work_history()
        
        # Test 6: Execute a job (if we have a job ID)
        if job_id:
            print(f"\n🤖 Testing job execution with GPT-5.2...")
            self.test_execute_job(job_id)
            
            # Wait a moment for database to update
            time.sleep(2)
            
            # Test 7: Get stats after job execution
            print("\n📊 Testing stats after job execution...")
            self.test_get_stats()
            
            # Test 8: Get work history after job execution
            print("\n📋 Testing work history after job execution...")
            self.test_get_work_history()
        else:
            print("⚠️  No job ID available for execution testing")
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\nFailed Tests:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        if self.passed_tests:
            print("\nPassed Tests:")
            for test in self.passed_tests:
                print(f"  - {test}")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
    else:
        print(f"\n⚠️  {len(tester.failed_tests)} test(s) failed. Check details above.")
    
    # Save detailed results
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(tester.test_results, f, indent=2)
    
    print(f"\n📄 Detailed test results saved to: /app/backend_test_results.json")