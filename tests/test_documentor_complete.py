#!/usr/bin/env python3
"""
Complete Test Suite for DocuMentor
Tests all functionality after documentation is loaded
"""
import requests
import json
import time
import os
from datetime import datetime

API_BASE = "http://localhost:8000"

class DocuMentorTester:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def log_result(self, test_name, success, details="", response_time=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.1f}s)" if response_time else ""
        print(f"{status} | {test_name}{time_info}")
        if details:
            print(f"     {details}")
    
    def test_api_connection(self):
        """Test basic API connectivity"""
        print("\n🔗 Testing API Connection")
        print("-" * 30)
        
        try:
            start = time.time()
            response = requests.get(f"{API_BASE}/docs", timeout=10)
            response_time = time.time() - start
            
            if response.status_code == 200:
                self.log_result("API Connection", True, "FastAPI docs accessible", response_time)
                return True
            else:
                self.log_result("API Connection", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Connection", False, f"Connection error: {e}")
            return False
    
    def test_system_stats(self):
        """Test system statistics"""
        print("\n📊 Testing System Stats")
        print("-" * 30)
        
        try:
            start = time.time()
            response = requests.get(f"{API_BASE}/stats", timeout=10)
            response_time = time.time() - start
            
            if response.status_code == 200:
                stats = response.json()
                
                # Check different possible field names
                total_chunks = stats.get('total_chunks', stats.get('total_documents', 0))
                sources = stats.get('sources', {})
                status = stats.get('status', 'unknown')
                
                self.log_result("Get System Stats", True, 
                              f"Status: {status}, Chunks: {total_chunks}, Sources: {len(sources)}", 
                              response_time)
                
                print(f"     API Version: {stats.get('api_version', 'N/A')}")
                print(f"     Total Chunks: {total_chunks}")
                print(f"     Sources: {list(sources.keys()) if sources else 'None'}")
                
                return stats
            else:
                self.log_result("Get System Stats", False, f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log_result("Get System Stats", False, str(e))
            return None
    
    def test_document_search(self):
        """Test document search functionality"""
        print("\n🔍 Testing Document Search")
        print("-" * 30)
        
        test_queries = [
            ("Django models", "Should find Django documentation"),
            ("Python functions", "Should find Python documentation"),
            ("React components", "Should find React documentation"),
            ("Database queries", "Should find database documentation"),
            ("Docker containers", "Should find Docker documentation")
        ]
        
        search_results = []
        
        for query, description in test_queries:
            try:
                start = time.time()
                response = requests.post(f"{API_BASE}/search", 
                    json={"query": query, "k": 5}, 
                    timeout=15
                )
                response_time = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    result_count = data.get('total_found', len(data.get('results', [])))
                    
                    self.log_result(f"Search: {query}", True, 
                                  f"{result_count} results found", response_time)
                    
                    search_results.append({
                        'query': query,
                        'count': result_count,
                        'results': data.get('results', [])
                    })
                    
                    # Show top result if available
                    if data.get('results') and len(data['results']) > 0:
                        top_result = data['results'][0]
                        metadata = top_result.get('metadata', {})
                        source = metadata.get('source', 'Unknown')
                        title = metadata.get('title', 'No title')[:40]
                        print(f"     Top result: [{source}] {title}...")
                        
                else:
                    self.log_result(f"Search: {query}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Search: {query}", False, str(e))
        
        return search_results
    
    def test_ai_qa(self):
        """Test AI question answering"""
        print("\n🤖 Testing AI Question Answering")
        print("-" * 30)
        
        test_questions = [
            {
                'question': "How do I create a Django model with foreign keys?",
                'expected_topics': ['Django', 'models', 'foreign key'],
                'timeout': 120
            },
            {
                'question': "What are React hooks and how do I use useState?",
                'expected_topics': ['React', 'hooks', 'useState'],
                'timeout': 120
            },
            {
                'question': "How to handle exceptions in Python?",
                'expected_topics': ['Python', 'exceptions', 'try'],
                'timeout': 90
            }
        ]
        
        qa_results = []
        
        for test_case in test_questions:
            question = test_case['question']
            timeout = test_case['timeout']
            
            print(f"\n   Question: {question}")
            print(f"   ⏳ Waiting for Gemma 3 response (timeout: {timeout}s)...")
            
            try:
                start = time.time()
                response = requests.post(f"{API_BASE}/ask", 
                    json={
                        "question": question,
                        "k": 5,
                        "temperature": 0.1
                    }, 
                    timeout=timeout
                )
                response_time = time.time() - start
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '')
                    sources = data.get('sources', [])
                    confidence = data.get('confidence', 0)
                    
                    # Evaluate answer quality
                    has_answer = len(answer) > 100
                    uses_sources = len(sources) > 0
                    
                    quality_score = 0
                    quality_notes = []
                    
                    if has_answer:
                        quality_score += 40
                        quality_notes.append("substantial answer")
                    
                    if uses_sources:
                        quality_score += 30
                        quality_notes.append(f"{len(sources)} sources")
                    
                    # Check if expected topics are mentioned
                    answer_lower = answer.lower()
                    expected_topics = test_case['expected_topics']
                    topics_found = [topic for topic in expected_topics 
                                  if topic.lower() in answer_lower]
                    
                    if topics_found:
                        quality_score += 30
                        quality_notes.append(f"mentions {topics_found}")
                    
                    success = quality_score >= 50
                    details = f"Quality: {quality_score}% ({', '.join(quality_notes)})"
                    
                    self.log_result(f"AI Q&A: {question[:30]}...", success, details, response_time)
                    
                    # Show answer preview
                    preview = answer[:200] + "..." if len(answer) > 200 else answer
                    print(f"     Answer preview: {preview}")
                    
                    qa_results.append({
                        'question': question,
                        'answer': answer,
                        'sources': len(sources),
                        'response_time': response_time,
                        'quality_score': quality_score
                    })
                    
                else:
                    self.log_result(f"AI Q&A: {question[:30]}...", False, 
                                  f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.log_result(f"AI Q&A: {question[:30]}...", False, 
                              f"Timeout after {timeout}s")
            except Exception as e:
                self.log_result(f"AI Q&A: {question[:30]}...", False, str(e))
        
        return qa_results
    
    def test_document_upload(self):
        """Test document upload functionality"""
        print("\n📤 Testing Document Upload")
        print("-" * 30)
        
        # Create test document
        test_content = """# Test Document - PowerShell Guide

PowerShell is a cross-platform task automation solution made up of a command-line shell, 
a scripting language, and a configuration management framework.

## Key Features

### Object-Oriented
PowerShell is built on the .NET Common Language Runtime (CLR), and accepts and returns .NET objects.

### Extensible
PowerShell can be extended through functions, classes, scripts, and modules.

### Cross-Platform  
PowerShell runs on Windows, Linux, and macOS.

## Basic Commands

- `Get-Process`: Lists running processes
- `Get-Service`: Lists system services  
- `Get-ChildItem`: Lists files and folders
- `Set-Location`: Changes directory

This document tests the upload functionality of DocuMentor.
"""
        
        test_file = "test_powershell_doc.md"
        
        try:
            # Save test file
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Upload file
            start = time.time()
            with open(test_file, 'rb') as f:
                files = {'file': (test_file, f, 'text/markdown')}
                response = requests.post(f"{API_BASE}/upload", files=files, timeout=30)
            
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                chunks_created = data.get('chunks_created', 0)
                message = data.get('message', 'Upload successful')
                
                self.log_result("Document Upload", True, 
                              f"{chunks_created} chunks created: {message}", response_time)
            else:
                self.log_result("Document Upload", False, f"HTTP {response.status_code}")
            
            # Clean up
            os.remove(test_file)
            
        except Exception as e:
            self.log_result("Document Upload", False, str(e))
            try:
                os.remove(test_file)
            except:
                pass
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📋 DocuMentor Test Report")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        total_time = time.time() - self.start_time
        
        print(f"\n📊 Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print(f"   ⏱️ Total Time: {total_time:.1f}s")
        
        # Performance analysis
        response_times = [r['response_time'] for r in self.results if r['response_time']]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            print(f"\n⚡ Performance:")
            print(f"   Average Response: {avg_response:.1f}s")
            print(f"   Slowest Response: {max_response:.1f}s")
        
        # Recommendations
        print(f"\n🎯 Assessment:")
        if success_rate >= 90:
            print("   🌟 Excellent! DocuMentor is working very well.")
        elif success_rate >= 70:
            print("   👍 Good performance with minor issues to address.")
        elif success_rate >= 50:
            print("   ⚠️ Moderate performance. Several issues need attention.")
        else:
            print("   🚨 Multiple issues found. Requires troubleshooting.")
        
        # Failed tests
        failed_results = [r for r in self.results if not r['success']]
        if failed_results:
            print(f"\n❌ Failed Tests:")
            for result in failed_results:
                print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n📝 Next Steps:")
        print("   1. Address any failed tests above")
        print("   2. Test with your own questions and documents")
        print("   3. Monitor performance over extended use")
        print("   4. Consider GPU acceleration for faster responses")
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'total_time': total_time
            },
            'results': self.results
        }
        
        with open('documentor_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: documentor_test_report.json")

def main():
    """Run complete test suite"""
    print("🧪 DocuMentor Complete Test Suite")
    print("Testing all functionality after documentation loading...")
    
    tester = DocuMentorTester()
    
    # Run all tests
    if not tester.test_api_connection():
        print("\n❌ Cannot connect to API. Make sure the server is running:")
        print("   python api_server.py")
        return
    
    tester.test_system_stats()
    tester.test_document_search()
    tester.test_ai_qa()
    tester.test_document_upload()
    
    # Generate final report
    tester.generate_report()

if __name__ == "__main__":
    main()
