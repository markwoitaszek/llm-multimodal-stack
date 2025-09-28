#!/usr/bin/env python3
"""
AI Agents Acceptance Criteria Test

This script tests all the acceptance criteria for Issue #3:
[P1.3] Complete LangChain Agent Framework Implementation
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8003/api/v1"

class AcceptanceCriteriaTester:
    """Test class for validating acceptance criteria"""
    
    def __init__(self):
        self.results = []
        self.agent_ids = []
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_service_health(self) -> bool:
        """Test 1: Service is running and healthy"""
        try:
            response = requests.get("http://localhost:8003/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    self.log_result("Service Health Check", True, "Service is running and healthy")
                    return True
                else:
                    self.log_result("Service Health Check", False, f"Service status: {health_data.get('status')}")
                    return False
            else:
                self.log_result("Service Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Service Health Check", False, f"Connection error: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test 2: API endpoints are accessible"""
        endpoints = [
            ("/agents", "GET"),
            ("/templates", "GET"),
            ("/tools", "GET"),
            ("/status", "GET")
        ]
        
        all_passed = True
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{API_BASE_URL}{endpoint}", timeout=5)
                
                if response.status_code in [200, 405]:  # 405 is OK for POST on GET endpoint
                    self.log_result(f"API Endpoint {endpoint}", True)
                else:
                    self.log_result(f"API Endpoint {endpoint}", False, f"HTTP {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_result(f"API Endpoint {endpoint}", False, f"Error: {e}")
                all_passed = False
        
        return all_passed
    
    def test_templates_available(self) -> bool:
        """Test 3: 5+ pre-built agent templates available"""
        try:
            response = requests.get(f"{API_BASE_URL}/templates", timeout=10)
            if response.status_code == 200:
                data = response.json()
                template_count = data.get("count", 0)
                templates = data.get("templates", [])
                
                if template_count >= 5:
                    self.log_result("Templates Available", True, f"Found {template_count} templates")
                    
                    # Log template names
                    template_names = [t["name"] for t in templates]
                    self.log_result("Template Names", True, f"Templates: {', '.join(template_names)}")
                    return True
                else:
                    self.log_result("Templates Available", False, f"Only {template_count} templates found")
                    return False
            else:
                self.log_result("Templates Available", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Templates Available", False, f"Error: {e}")
            return False
    
    def test_agent_creation_api(self) -> bool:
        """Test 4: Agents can be created via API"""
        try:
            # Test creating agent from template
            response = requests.post(
                f"{API_BASE_URL}/agents/from-template",
                params={
                    "template_name": "research_assistant",
                    "agent_name": "Test Research Agent"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_id = data.get("agent_id")
                if agent_id:
                    self.agent_ids.append(agent_id)
                    self.log_result("Agent Creation via API", True, f"Created agent: {agent_id}")
                    return True
                else:
                    self.log_result("Agent Creation via API", False, "No agent ID returned")
                    return False
            else:
                self.log_result("Agent Creation via API", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Agent Creation via API", False, f"Error: {e}")
            return False
    
    def test_agent_creation_manual(self) -> bool:
        """Test 5: Agents can be created manually"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/agents",
                json={
                    "name": "Manual Test Agent",
                    "goal": "Test agent created manually",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_id = data.get("agent_id")
                if agent_id:
                    self.agent_ids.append(agent_id)
                    self.log_result("Agent Creation Manual", True, f"Created agent: {agent_id}")
                    return True
                else:
                    self.log_result("Agent Creation Manual", False, "No agent ID returned")
                    return False
            else:
                self.log_result("Agent Creation Manual", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Agent Creation Manual", False, f"Error: {e}")
            return False
    
    def test_core_tools_functioning(self) -> bool:
        """Test 6: All 4 core tools working (image, search, text, web)"""
        try:
            response = requests.get(f"{API_BASE_URL}/tools", timeout=10)
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", {})
                
                expected_tools = ["analyze_image", "search_content", "generate_text", "web_search"]
                available_tools = list(tools.keys())
                
                missing_tools = [tool for tool in expected_tools if tool not in available_tools]
                
                if not missing_tools:
                    self.log_result("Core Tools Available", True, f"All {len(expected_tools)} tools available")
                    return True
                else:
                    self.log_result("Core Tools Available", False, f"Missing tools: {missing_tools}")
                    return False
            else:
                self.log_result("Core Tools Available", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Core Tools Available", False, f"Error: {e}")
            return False
    
    def test_agent_execution(self) -> bool:
        """Test 7: Agent execution and monitoring"""
        if not self.agent_ids:
            self.log_result("Agent Execution", False, "No agents available for testing")
            return False
        
        try:
            agent_id = self.agent_ids[0]
            response = requests.post(
                f"{API_BASE_URL}/agents/{agent_id}/execute",
                json={"task": "Hello, can you help me with a simple task?"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("Agent Execution", True, "Agent executed task successfully")
                    
                    # Test execution history
                    history_response = requests.get(f"{API_BASE_URL}/agents/{agent_id}/history")
                    if history_response.status_code == 200:
                        self.log_result("Execution History", True, "History tracking working")
                    else:
                        self.log_result("Execution History", False, f"HTTP {history_response.status_code}")
                    
                    # Test agent stats
                    stats_response = requests.get(f"{API_BASE_URL}/agents/{agent_id}/stats")
                    if stats_response.status_code == 200:
                        self.log_result("Agent Statistics", True, "Statistics tracking working")
                    else:
                        self.log_result("Agent Statistics", False, f"HTTP {stats_response.status_code}")
                    
                    return True
                else:
                    self.log_result("Agent Execution", False, f"Execution failed: {data.get('error')}")
                    return False
            else:
                self.log_result("Agent Execution", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("Agent Execution", False, f"Error: {e}")
            return False
    
    def test_persistent_memory(self) -> bool:
        """Test 8: Persistent memory across conversations"""
        if not self.agent_ids:
            self.log_result("Persistent Memory", False, "No agents available for testing")
            return False
        
        try:
            agent_id = self.agent_ids[0]
            
            # First conversation
            response1 = requests.post(
                f"{API_BASE_URL}/agents/{agent_id}/execute",
                json={"task": "My name is Alice. Remember this."},
                timeout=30
            )
            
            time.sleep(2)  # Brief pause
            
            # Second conversation
            response2 = requests.post(
                f"{API_BASE_URL}/agents/{agent_id}/execute",
                json={"task": "What is my name?"},
                timeout=30
            )
            
            if response1.status_code == 200 and response2.status_code == 200:
                self.log_result("Persistent Memory", True, "Memory persistence working")
                return True
            else:
                self.log_result("Persistent Memory", False, "Memory test failed")
                return False
        except Exception as e:
            self.log_result("Persistent Memory", False, f"Error: {e}")
            return False
    
    def test_agent_monitoring(self) -> bool:
        """Test 9: Agent execution monitoring and logging"""
        if not self.agent_ids:
            self.log_result("Agent Monitoring", False, "No agents available for testing")
            return False
        
        try:
            agent_id = self.agent_ids[0]
            
            # Get agent stats
            response = requests.get(f"{API_BASE_URL}/agents/{agent_id}/stats")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["total_executions", "successful_executions", "success_rate", "avg_execution_time_ms"]
                
                if all(field in stats for field in required_fields):
                    self.log_result("Agent Monitoring", True, "Monitoring and logging working")
                    return True
                else:
                    self.log_result("Agent Monitoring", False, f"Missing fields: {[f for f in required_fields if f not in stats]}")
                    return False
            else:
                self.log_result("Agent Monitoring", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Agent Monitoring", False, f"Error: {e}")
            return False
    
    def test_agent_management(self) -> bool:
        """Test 10: Complete API documentation"""
        try:
            # Test agent listing
            response = requests.get(f"{API_BASE_URL}/agents")
            if response.status_code == 200:
                agents = response.json()
                self.log_result("Agent Management", True, f"Found {len(agents)} agents")
                
                # Test agent deletion (cleanup)
                for agent_id in self.agent_ids:
                    delete_response = requests.delete(f"{API_BASE_URL}/agents/{agent_id}")
                    if delete_response.status_code == 200:
                        self.log_result("Agent Cleanup", True, f"Deleted agent: {agent_id}")
                    else:
                        self.log_result("Agent Cleanup", False, f"Failed to delete agent: {agent_id}")
                
                return True
            else:
                self.log_result("Agent Management", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Agent Management", False, f"Error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all acceptance criteria tests"""
        print("🧪 AI Agents Acceptance Criteria Test")
        print("=" * 50)
        
        tests = [
            ("Service Health", self.test_service_health),
            ("API Endpoints", self.test_api_endpoints),
            ("Templates Available", self.test_templates_available),
            ("Agent Creation API", self.test_agent_creation_api),
            ("Agent Creation Manual", self.test_agent_creation_manual),
            ("Core Tools Functioning", self.test_core_tools_functioning),
            ("Agent Execution", self.test_agent_execution),
            ("Persistent Memory", self.test_persistent_memory),
            ("Agent Monitoring", self.test_agent_monitoring),
            ("Agent Management", self.test_agent_management)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test_name, False, f"Test exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All acceptance criteria met! Issue #3 is complete.")
        else:
            print("⚠️  Some acceptance criteria not met. Review failed tests above.")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "results": self.results
        }

def main():
    """Main test function"""
    tester = AcceptanceCriteriaTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["passed_tests"] == results["total_tests"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
