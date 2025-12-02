#!/usr/bin/env python3
"""
Test script for Scan History API endpoints.
Demonstrates complete audit trail functionality.
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "1"  # test@example.com with 100 credits

def test_scan_with_history():
    """Test complete flow: scan → history → detail"""
    
    print("="*70)
    print("SCAN HISTORY API TEST")
    print("="*70)
    
    # 1. Check initial credits
    print("\n[1] Checking initial credits...")
    response = requests.get(
        f"{BASE_URL}/credits",
        headers={"X-User-Id": USER_ID}
    )
    credits_before = response.json()
    print(f"    Credits before: {credits_before['credits_balance']}")
    
    # 2. Initiate a scan
    print("\n[2] Initiating DNS scan for google.com...")
    response = requests.post(
        f"{BASE_URL}/scan",
        headers={
            "X-User-Id": USER_ID,
            "Content-Type": "application/json"
        },
        json={
            "target": "google.com",
            "type": "dns"
        }
    )
    
    if response.status_code == 200:
        scan_data = response.json()
        task_id = scan_data["task_id"]
        print(f"    ✓ Scan initiated: {task_id}")
        print(f"    ✓ Credits remaining: {scan_data['credits_remaining']}")
        print(f"    ✓ Cost: {scan_data['cost']} credits")
    else:
        print(f"    ✗ Failed: {response.status_code}")
        print(f"    {response.text}")
        return
    
    # 3. Wait for scan to complete
    print("\n[3] Waiting for scan to complete...")
    for i in range(30):
        time.sleep(1)
        response = requests.get(
            f"{BASE_URL}/scan/{task_id}",
            headers={"X-User-Id": USER_ID}
        )
        status_data = response.json()
        
        if status_data["status"] in ["SUCCESS", "FAILURE"]:
            print(f"    ✓ Scan completed with status: {status_data['status']}")
            break
        else:
            print(f"    ⏳ Status: {status_data['status']}", end="\r")
    
    # 4. Get scan history list
    print("\n[4] Fetching scan history (last 5 scans)...")
    response = requests.get(
        f"{BASE_URL}/history?page=1&limit=5",
        headers={"X-User-Id": USER_ID}
    )
    
    if response.status_code == 200:
        history_data = response.json()
        print(f"    ✓ Total scans in history: {history_data['total']}")
        print(f"    ✓ Current page: {history_data['page']}/{history_data['pages']}")
        print(f"\n    Recent scans:")
        for scan in history_data["scans"][:3]:
            print(f"      - {scan['id'][:8]}... | {scan['target']:20s} | {scan['status']:10s} | {scan['scan_type']}")
    else:
        print(f"    ✗ Failed: {response.status_code}")
    
    # 5. Get detailed scan result
    print("\n[5] Fetching complete scan details...")
    scan_id = history_data["scans"][0]["id"]
    response = requests.get(
        f"{BASE_URL}/history/{scan_id}",
        headers={"X-User-Id": USER_ID}
    )
    
    if response.status_code == 200:
        detail = response.json()
        print(f"    ✓ Scan ID: {detail['id']}")
        print(f"    ✓ Target: {detail['target']}")
        print(f"    ✓ Type: {detail['scan_type']}")
        print(f"    ✓ Status: {detail['status']}")
        print(f"    ✓ Performed: {detail['performed_at']}")
        print(f"    ✓ Client IP: {detail.get('client_ip', 'N/A')}")
        print(f"    ✓ Credits charged: {detail['credits_charged']}")
        
        if detail.get('result_snapshot'):
            result = detail['result_snapshot']
            print(f"    ✓ Result available: {result.get('success', 'N/A')}")
            if 'data' in result:
                data_size = len(json.dumps(result['data']))
                print(f"    ✓ Result data size: {data_size} bytes")
    else:
        print(f"    ✗ Failed: {response.status_code}")
    
    # 6. Get statistics
    print("\n[6] Fetching scan statistics...")
    response = requests.get(
        f"{BASE_URL}/history/stats/summary",
        headers={"X-User-Id": USER_ID}
    )
    
    if response.status_code == 200:
        stats = response.json()
        print(f"    ✓ Total scans: {stats['total_scans']}")
        print(f"    ✓ Successful: {stats.get('success', 0)}")
        print(f"    ✓ Failed: {stats.get('failed', 0)}")
        print(f"    ✓ Pending: {stats.get('pending', 0)}")
        print(f"    ✓ Total credits spent: {stats['total_credits_spent']}")
    else:
        print(f"    ✗ Failed: {response.status_code}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETED")
    print("="*70)


if __name__ == "__main__":
    try:
        test_scan_with_history()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API at http://localhost:8000")
        print("   Make sure the backend is running with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
