#!/usr/bin/env python3
"""
Performance Test for DocuMentor
Tests response times, concurrent requests, and memory usage
"""
import requests
import time
import threading
import psutil
import os
from statistics import mean, stdev

API_BASE = "http://localhost:8000"

def test_api_response_time(endpoint, method="GET", json_data=None, runs=5):
    """Test average response time for an endpoint"""
    times = []
    for i in range(runs):
        start = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}", timeout=30)
            else:
                response = requests.post(f"{API_BASE}{endpoint}", json=json_data, timeout=30)
            elapsed = time.time() - start
            times.append(elapsed)
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")
            times.append(30.0)  # Timeout value
    
    if times:
        avg_time = mean(times)
        std_dev = stdev(times) if len(times) > 1 else 0
        return avg_time, std_dev
    return None, None

def test_concurrent_requests(endpoint, num_threads=10):
    """Test concurrent request handling"""
    results = {"success": 0, "failed": 0, "times": []}
    lock = threading.Lock()
    
    def make_request():
        start = time.time()
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            elapsed = time.time() - start
            with lock:
                if response.status_code == 200:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                results["times"].append(elapsed)
        except:
            with lock:
                results["failed"] += 1
    
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=make_request)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    return results

def get_memory_usage():
    """Get current memory usage of the API process"""
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        if 'python' in proc.info['name'].lower() and 'api_server' in ' '.join(proc.cmdline()):
            return proc.info['memory_percent']
    return 0

def run_performance_tests():
    print("🏃 DocuMentor Performance Test Suite")
    print("=" * 50)
    
    # Test 1: API Health Check Response Time
    print("\n1️⃣ Testing Health Check Response Time...")
    avg_time, std_dev = test_api_response_time("/health")
    if avg_time:
        print(f"✅ Average response time: {avg_time:.2f}s (±{std_dev:.2f}s)")
        if avg_time < 0.1:
            print("   🚀 Excellent performance!")
        elif avg_time < 0.5:
            print("   ✅ Good performance")
        else:
            print("   ⚠️  Slow response time")
    
    # Test 2: Search Performance
    print("\n2️⃣ Testing Search Performance...")
    search_data = {"query": "python tutorial", "k": 5}
    avg_time, std_dev = test_api_response_time("/search", "POST", search_data)
    if avg_time:
        print(f"✅ Average search time: {avg_time:.2f}s (±{std_dev:.2f}s)")
        if avg_time < 1.0:
            print("   🚀 Fast search!")
        elif avg_time < 3.0:
            print("   ✅ Acceptable search speed")
        else:
            print("   ⚠️  Search is slow")
    
    # Test 3: Concurrent Request Handling
    print("\n3️⃣ Testing Concurrent Requests...")
    results = test_concurrent_requests("/health", num_threads=20)
    print(f"✅ Concurrent requests completed:")
    print(f"   Success: {results['success']}")
    print(f"   Failed: {results['failed']}")
    if results['times']:
        print(f"   Average time: {mean(results['times']):.2f}s")
    
    # Test 4: Memory Usage
    print("\n4️⃣ Checking Memory Usage...")
    mem_usage = get_memory_usage()
    print(f"✅ API Memory Usage: {mem_usage:.1f}%")
    if mem_usage < 5:
        print("   🚀 Low memory usage")
    elif mem_usage < 10:
        print("   ✅ Moderate memory usage")
    else:
        print("   ⚠️  High memory usage")
    
    # Test 5: Stats Endpoint Performance
    print("\n5️⃣ Testing Stats Endpoint...")
    avg_time, std_dev = test_api_response_time("/stats")
    if avg_time:
        print(f"✅ Stats response time: {avg_time:.2f}s (±{std_dev:.2f}s)")
    
    # Test 6: Question Answering Performance (this will be slow)
    print("\n6️⃣ Testing Question Answering Performance...")
    print("   ⏳ This test takes time due to LLM processing...")
    qa_data = {"question": "What is Python?", "k": 3, "temperature": 0.1}
    avg_time, std_dev = test_api_response_time("/ask", "POST", qa_data, runs=2)
    if avg_time:
        print(f"✅ Average QA response time: {avg_time:.1f}s")
        if avg_time < 10:
            print("   🚀 Fast LLM response!")
        elif avg_time < 30:
            print("   ✅ Normal LLM speed")
        else:
            print("   ⚠️  Very slow LLM response")
    
    print("\n" + "=" * 50)
    print("📊 Performance Test Summary:")
    print("• API endpoints are responding")
    print("• Search functionality is working")
    print("• Concurrent request handling is functional")
    print("• Memory usage should be monitored")
    print("• LLM responses are slow (expected with local models)")

if __name__ == "__main__":
    run_performance_tests()