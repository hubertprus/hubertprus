#!/usr/bin/env python3
"""
Backend API Testing for AI Money Maker - Bank Account and Withdrawal Functionality
Tests the new endpoints for balance, bank account management, and withdrawals.
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://ai-money-agent-4.preview.emergentagent.com/api"

def print_test_header(test_name):
    """Print a formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")

def print_result(success, message, details=None):
    """Print test result with formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"   Details: {details}")

def test_balance_endpoint():
    """Test GET /api/balance endpoint"""
    print_test_header("Testing Balance Endpoint")
    
    try:
        response = requests.get(f"{BACKEND_URL}/balance")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['total_earnings', 'total_withdrawn', 'available_balance', 'can_withdraw']
            
            # Check all required fields are present
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print_result(False, "Missing required fields", f"Missing: {missing_fields}")
                return False
            
            # Validate data types
            if not isinstance(data['total_earnings'], (int, float)):
                print_result(False, "total_earnings should be a number", f"Got: {type(data['total_earnings'])}")
                return False
            
            if not isinstance(data['total_withdrawn'], (int, float)):
                print_result(False, "total_withdrawn should be a number", f"Got: {type(data['total_withdrawn'])}")
                return False
            
            if not isinstance(data['available_balance'], (int, float)):
                print_result(False, "available_balance should be a number", f"Got: {type(data['available_balance'])}")
                return False
            
            if not isinstance(data['can_withdraw'], bool):
                print_result(False, "can_withdraw should be a boolean", f"Got: {type(data['can_withdraw'])}")
                return False
            
            # Validate balance calculation
            expected_balance = data['total_earnings'] - data['total_withdrawn']
            if abs(data['available_balance'] - expected_balance) > 0.01:  # Allow for floating point precision
                print_result(False, "Balance calculation incorrect", 
                           f"Expected: {expected_balance}, Got: {data['available_balance']}")
                return False
            
            # Validate can_withdraw logic
            expected_can_withdraw = data['available_balance'] >= 10.0
            if data['can_withdraw'] != expected_can_withdraw:
                print_result(False, "can_withdraw logic incorrect", 
                           f"Expected: {expected_can_withdraw}, Got: {data['can_withdraw']}")
                return False
            
            print_result(True, "Balance endpoint working correctly", 
                        f"Total: £{data['total_earnings']:.2f}, Withdrawn: £{data['total_withdrawn']:.2f}, Available: £{data['available_balance']:.2f}")
            return data
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def test_save_bank_account():
    """Test POST /api/bank-account endpoint"""
    print_test_header("Testing Save Bank Account")
    
    test_account = {
        "account_holder_name": "John Smith",
        "iban": "GB29NWBK60161331926819",
        "swift_bic": "NWBKGB2L",
        "bank_name": "NatWest Bank",
        "country": "GB"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/bank-account",
            headers={"Content-Type": "application/json"},
            json=test_account
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'saved successfully' in data.get('message', ''):
                print_result(True, "Bank account saved successfully", data.get('message'))
                return True
            else:
                print_result(False, "Unexpected response format", str(data))
                return False
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def test_get_bank_account():
    """Test GET /api/bank-account endpoint"""
    print_test_header("Testing Get Bank Account")
    
    try:
        response = requests.get(f"{BACKEND_URL}/bank-account")
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get('has_account'):
                print_result(False, "No bank account found", "Expected account to exist after saving")
                return False
            
            # Check required fields
            required_fields = ['account_holder_name', 'iban', 'masked_iban']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print_result(False, "Missing required fields", f"Missing: {missing_fields}")
                return False
            
            # Validate IBAN masking
            full_iban = data['iban']
            masked_iban = data['masked_iban']
            
            if len(full_iban) > 4:
                expected_masked = "****" + full_iban[-4:]
                if masked_iban != expected_masked:
                    print_result(False, "IBAN masking incorrect", 
                               f"Expected: {expected_masked}, Got: {masked_iban}")
                    return False
            
            print_result(True, "Bank account retrieved successfully", 
                        f"Account holder: {data['account_holder_name']}, Masked IBAN: {masked_iban}")
            return data
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def test_withdrawal_success(amount, balance_data):
    """Test successful withdrawal"""
    print_test_header(f"Testing Successful Withdrawal (£{amount})")
    
    if not balance_data or amount > balance_data['available_balance']:
        print_result(False, "Cannot test withdrawal", f"Insufficient balance for £{amount}")
        return False
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/withdraw",
            headers={"Content-Type": "application/json"},
            json={"amount": amount}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get('success'):
                print_result(False, "Withdrawal not successful", str(data))
                return False
            
            # Check required fields in response
            required_fields = ['message', 'transaction_id', 'new_balance']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print_result(False, "Missing required fields in response", f"Missing: {missing_fields}")
                return False
            
            # Validate new balance calculation
            expected_new_balance = balance_data['available_balance'] - amount
            if abs(data['new_balance'] - expected_new_balance) > 0.01:
                print_result(False, "New balance calculation incorrect", 
                           f"Expected: {expected_new_balance}, Got: {data['new_balance']}")
                return False
            
            print_result(True, f"Withdrawal of £{amount} successful", 
                        f"Transaction ID: {data['transaction_id']}, New balance: £{data['new_balance']:.2f}")
            return data
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def test_withdrawal_minimum_amount():
    """Test withdrawal below minimum amount (should fail)"""
    print_test_header("Testing Withdrawal Below Minimum (£5)")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/withdraw",
            headers={"Content-Type": "application/json"},
            json={"amount": 5.0}
        )
        
        if response.status_code == 400:
            data = response.json()
            if "minimum withdrawal" in data.get('detail', '').lower():
                print_result(True, "Correctly rejected withdrawal below minimum", data.get('detail'))
                return True
            else:
                print_result(False, "Wrong error message", f"Expected minimum withdrawal error, got: {data.get('detail')}")
                return False
        else:
            print_result(False, f"Expected HTTP 400, got {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def test_withdrawal_insufficient_balance(balance_data):
    """Test withdrawal above available balance (should fail)"""
    print_test_header("Testing Withdrawal Above Available Balance")
    
    if not balance_data:
        print_result(False, "Cannot test", "No balance data available")
        return False
    
    # Try to withdraw more than available
    excessive_amount = balance_data['available_balance'] + 100.0
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/withdraw",
            headers={"Content-Type": "application/json"},
            json={"amount": excessive_amount}
        )
        
        if response.status_code == 400:
            data = response.json()
            if "insufficient balance" in data.get('detail', '').lower():
                print_result(True, "Correctly rejected withdrawal above balance", data.get('detail'))
                return True
            else:
                print_result(False, "Wrong error message", f"Expected insufficient balance error, got: {data.get('detail')}")
                return False
        else:
            print_result(False, f"Expected HTTP 400, got {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def test_withdrawal_history():
    """Test GET /api/withdrawals endpoint"""
    print_test_header("Testing Withdrawal History")
    
    try:
        response = requests.get(f"{BACKEND_URL}/withdrawals")
        
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                print_result(False, "Response should be a list", f"Got: {type(data)}")
                return False
            
            if len(data) == 0:
                print_result(True, "No withdrawals in history", "Empty list returned")
                return True
            
            # Check structure of withdrawal records
            for i, withdrawal in enumerate(data):
                required_fields = ['amount', 'status', 'bank_account_last4', 'created_at', 'transaction_id']
                missing_fields = [field for field in required_fields if field not in withdrawal]
                if missing_fields:
                    print_result(False, f"Withdrawal {i} missing fields", f"Missing: {missing_fields}")
                    return False
                
                # Validate data types
                if not isinstance(withdrawal['amount'], (int, float)):
                    print_result(False, f"Withdrawal {i} amount should be number", f"Got: {type(withdrawal['amount'])}")
                    return False
                
                if withdrawal['status'] not in ['pending', 'completed', 'failed']:
                    print_result(False, f"Withdrawal {i} invalid status", f"Got: {withdrawal['status']}")
                    return False
            
            print_result(True, f"Withdrawal history retrieved successfully", f"Found {len(data)} withdrawals")
            return data
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def test_balance_after_withdrawal(initial_balance, withdrawal_amount):
    """Test that balance is correctly updated after withdrawal"""
    print_test_header("Testing Balance Update After Withdrawal")
    
    try:
        response = requests.get(f"{BACKEND_URL}/balance")
        
        if response.status_code == 200:
            data = response.json()
            
            expected_balance = initial_balance['available_balance'] - withdrawal_amount
            actual_balance = data['available_balance']
            
            if abs(actual_balance - expected_balance) > 0.01:
                print_result(False, "Balance not updated correctly", 
                           f"Expected: £{expected_balance:.2f}, Got: £{actual_balance:.2f}")
                return False
            
            print_result(True, "Balance updated correctly after withdrawal", 
                        f"New balance: £{actual_balance:.2f}")
            return data
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Request failed", str(e))
        return False

def main():
    """Run all tests"""
    print("🚀 Starting AI Money Maker Backend Tests - Bank Account & Withdrawal Functionality")
    print(f"Backend URL: {BACKEND_URL}")
    
    test_results = []
    
    # Test 1: Check current balance
    balance_data = test_balance_endpoint()
    test_results.append(("Balance Endpoint", balance_data is not False))
    
    # Test 2: Save bank account
    bank_save_result = test_save_bank_account()
    test_results.append(("Save Bank Account", bank_save_result))
    
    # Test 3: Retrieve bank account and verify masking
    bank_data = test_get_bank_account()
    test_results.append(("Get Bank Account", bank_data is not False))
    
    # Test 4: Test withdrawal validation (minimum amount)
    min_amount_result = test_withdrawal_minimum_amount()
    test_results.append(("Withdrawal Minimum Validation", min_amount_result))
    
    # Test 5: Test withdrawal validation (insufficient balance)
    if balance_data:
        insufficient_balance_result = test_withdrawal_insufficient_balance(balance_data)
        test_results.append(("Withdrawal Insufficient Balance", insufficient_balance_result))
    
    # Test 6: Attempt successful withdrawal (if sufficient balance)
    withdrawal_result = False
    withdrawal_amount = 10.0  # Minimum amount
    if balance_data and balance_data['available_balance'] >= withdrawal_amount:
        withdrawal_result = test_withdrawal_success(withdrawal_amount, balance_data)
        test_results.append(("Successful Withdrawal", withdrawal_result is not False))
        
        # Test 7: Check balance after withdrawal
        if withdrawal_result:
            balance_after_result = test_balance_after_withdrawal(balance_data, withdrawal_amount)
            test_results.append(("Balance After Withdrawal", balance_after_result is not False))
    else:
        print_test_header("Skipping Withdrawal Tests")
        print("⚠️  Insufficient balance for withdrawal testing")
        if balance_data:
            print(f"   Available balance: £{balance_data['available_balance']:.2f}")
            print(f"   Required for test: £{withdrawal_amount:.2f}")
    
    # Test 8: Check withdrawal history
    history_result = test_withdrawal_history()
    test_results.append(("Withdrawal History", history_result is not False))
    
    # Summary
    print_test_header("Test Summary")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bank account and withdrawal functionality is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())