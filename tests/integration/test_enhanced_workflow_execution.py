"""
Enhanced integration tests for real workflow execution with actual business logic
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx
import asyncio
import json
import numpy as np
from typing import Dict, Any, List
import tempfile
import os
from PIL import Image
import io
import time

from tests.conftest import test_services, performance_thresholds


class TestEnhancedWorkflowExecution:
    """Enhanced test cases for real workflow execution with actual business logic"""

    @pytest.fixture
    def workflow_test_data(self):
        """Create comprehensive test data for workflow execution"""
        # Create realistic test documents
        documents = {
            "research_paper": """
            Machine Learning in Healthcare: A Comprehensive Review
            
            Abstract: This paper presents a comprehensive review of machine learning applications in healthcare.
            We examine various algorithms including supervised learning, unsupervised learning, and deep learning
            approaches. The paper discusses challenges, opportunities, and future directions in healthcare AI.
            
            Introduction: Healthcare is experiencing a digital transformation with the integration of artificial
            intelligence and machine learning technologies. These technologies have the potential to improve
            patient outcomes, reduce costs, and enhance clinical decision-making processes.
            
            Methods: We conducted a systematic review of machine learning applications in healthcare from 2010 to 2024.
            Our analysis covers diagnostic imaging, drug discovery, personalized medicine, and clinical decision support.
            
            Results: Machine learning has shown significant promise in various healthcare applications. Deep learning
            models have achieved human-level performance in medical image analysis. Natural language processing
            has improved clinical documentation and information extraction.
            
            Conclusion: Machine learning technologies are transforming healthcare delivery. However, challenges
            remain in terms of data privacy, model interpretability, and regulatory approval.
            """,
            
            "technical_guide": """
            Deep Learning Fundamentals: A Technical Guide
            
            Neural Networks: Artificial neural networks are computing systems inspired by biological neural networks.
            They consist of interconnected nodes (neurons) that process information using a connectionist approach.
            
            Backpropagation: Backpropagation is a method used to train neural networks. It calculates the gradient
            of the loss function with respect to the network weights and updates the weights to minimize the loss.
            
            Convolutional Neural Networks: CNNs are particularly effective for image recognition tasks. They use
            convolutional layers to detect local features and pooling layers to reduce spatial dimensions.
            
            Recurrent Neural Networks: RNNs are designed to work with sequential data. They maintain hidden states
            that carry information from previous time steps, making them suitable for natural language processing.
            
            Transformers: Transformer architectures have revolutionized natural language processing. They use
            attention mechanisms to process sequences in parallel, leading to significant performance improvements.
            """,
            
            "business_case": """
            AI Implementation in Enterprise: Business Case Study
            
            Executive Summary: This case study examines the implementation of artificial intelligence solutions
            in a Fortune 500 company. The project resulted in 30% cost reduction and 50% improvement in efficiency.
            
            Problem Statement: The company faced challenges in data processing, customer service, and operational
            efficiency. Manual processes were time-consuming and error-prone, leading to increased costs and
            customer dissatisfaction.
            
            Solution: We implemented a comprehensive AI solution including machine learning models for predictive
            analytics, natural language processing for customer service automation, and computer vision for
            quality control.
            
            Implementation: The project was executed in three phases over 18 months. Phase 1 focused on data
            infrastructure and model development. Phase 2 involved pilot testing and validation. Phase 3
            included full deployment and optimization.
            
            Results: The AI implementation achieved significant business value. Customer satisfaction increased
            by 40%, operational costs decreased by 30%, and processing time was reduced by 60%.
            
            Lessons Learned: Key success factors included executive sponsorship, cross-functional collaboration,
            and iterative development approach. Challenges included data quality issues and change management.
            """
        }
        
        # Create test images
        images = {}
        for name, content in [("research_chart", "red"), ("tech_diagram", "blue"), ("business_graph", "green")]:
            img = Image.new('RGB', (200, 150), color=content)
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG')
            images[name] = img_buffer.getvalue()
        
        return {
            "documents": documents,
            "images": images,
            "queries": [
                "machine learning healthcare applications",
                "deep learning neural networks",
                "AI business implementation case study",
                "artificial intelligence enterprise solutions"
            ]
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comprehensive_research_workflow(self, test_services, workflow_test_data):
        """Test comprehensive research workflow with real document processing and analysis"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Process all documents
            document_ids = {}
            
            for doc_name, doc_content in workflow_test_data["documents"].items():
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": doc_content,
                        "document_name": f"{doc_name}.txt",
                        "metadata": {
                            "source": "research_workflow",
                            "document_type": doc_name,
                            "category": "research_materials"
                        }
                    }
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                document_ids[doc_name] = result["content_id"]
            
            # Step 2: Process images
            image_ids = {}
            
            for img_name, img_data in workflow_test_data["images"].items():
                files = {'file': (f"{img_name}.jpg", img_data, 'image/jpeg')}
                data = {
                    'document_name': f"{img_name}.jpg",
                    'metadata': json.dumps({
                        "source": "research_workflow",
                        "image_type": img_name,
                        "category": "research_visuals"
                    })
                }
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/image",
                    files=files,
                    data=data
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                image_ids[img_name] = result["content_id"]
            
            # Step 3: Create research agent
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Research Analysis Agent",
                    "goal": "Analyze research documents and provide comprehensive insights",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 10,
                    "user_id": "research_workflow_user"
                }
            )
            
            assert agent_response.status_code == 200
            agent_result = agent_response.json()
            agent_id = agent_result["agent_id"]
            
            # Step 4: Execute research analysis workflow
            research_tasks = [
                "Analyze the machine learning applications discussed in the research materials",
                "Compare the technical approaches mentioned in the documents",
                "Summarize the business implications of AI implementation",
                "Identify common themes across all research materials"
            ]
            
            research_results = []
            
            for task in research_tasks:
                execution_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                    json={
                        "task": task,
                        "user_id": "research_workflow_user"
                    }
                )
                
                assert execution_response.status_code == 200
                execution_result = execution_response.json()
                assert execution_result["success"] is True
                research_results.append(execution_result["result"])
            
            # Step 5: Verify research workflow results
            assert len(research_results) == len(research_tasks)
            
            # Each result should contain meaningful analysis
            for result in research_results:
                assert len(result) > 50, "Research results should be substantial"
                assert any(keyword in result.lower() for keyword in 
                          ["machine learning", "artificial intelligence", "neural", "deep learning"])
            
            # Step 6: Test cross-document search and analysis
            cross_search_response = await client.post(
                f"{retrieval_proxy['url']}/api/v1/search",
                json={
                    "query": "machine learning applications healthcare business",
                    "modalities": ["text", "image"],
                    "limit": 20,
                    "score_threshold": 0.3
                }
            )
            
            assert cross_search_response.status_code == 200
            cross_search_result = cross_search_response.json()
            assert cross_search_result["success"] is True
            assert len(cross_search_result["results"]) > 0
            
            # Verify we found content from multiple documents
            found_documents = set()
            for result in cross_search_result["results"]:
                if "metadata" in result and "document_type" in result["metadata"]:
                    found_documents.add(result["metadata"]["document_type"])
            
            assert len(found_documents) > 1, "Should find content from multiple documents"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_workflow(self, test_services, workflow_test_data):
        """Test real multi-agent collaboration with actual task distribution"""
        ai_agents = test_services["ai_agents"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            # Step 1: Create specialized agents
            agents = {
                "researcher": {
                    "name": "Research Specialist Agent",
                    "goal": "Conduct thorough research and gather information",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 15
                },
                "analyst": {
                    "name": "Data Analysis Agent", 
                    "goal": "Analyze data and identify patterns",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 10
                },
                "synthesizer": {
                    "name": "Content Synthesis Agent",
                    "goal": "Synthesize information into coherent reports",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 20
                }
            }
            
            agent_ids = {}
            
            for agent_role, agent_config in agents.items():
                response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents",
                    json={
                        **agent_config,
                        "user_id": "collaboration_workflow_user"
                    }
                )
                
                assert response.status_code == 200
                result = response.json()
                agent_ids[agent_role] = result["agent_id"]
            
            # Step 2: Execute collaborative workflow
            collaboration_results = {}
            
            # Researcher agent: Gather information
            research_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents/{agent_ids['researcher']}/execute",
                json={
                    "task": "Research machine learning applications in healthcare, focusing on diagnostic imaging and drug discovery",
                    "user_id": "collaboration_workflow_user"
                }
            )
            
            assert research_response.status_code == 200
            research_result = research_response.json()
            assert research_result["success"] is True
            collaboration_results["research"] = research_result["result"]
            
            # Analyst agent: Analyze the research
            analysis_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents/{agent_ids['analyst']}/execute",
                json={
                    "task": f"Analyze the following research findings and identify key trends, challenges, and opportunities: {collaboration_results['research'][:500]}",
                    "user_id": "collaboration_workflow_user"
                }
            )
            
            assert analysis_response.status_code == 200
            analysis_result = analysis_response.json()
            assert analysis_result["success"] is True
            collaboration_results["analysis"] = analysis_result["result"]
            
            # Synthesizer agent: Create final report
            synthesis_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents/{agent_ids['synthesizer']}/execute",
                json={
                    "task": f"Create a comprehensive report synthesizing the research findings and analysis. Research: {collaboration_results['research'][:300]} Analysis: {collaboration_results['analysis'][:300]}",
                    "user_id": "collaboration_workflow_user"
                }
            )
            
            assert synthesis_response.status_code == 200
            synthesis_result = synthesis_response.json()
            assert synthesis_result["success"] is True
            collaboration_results["synthesis"] = synthesis_result["result"]
            
            # Step 3: Verify collaboration results
            assert len(collaboration_results) == 3
            
            # Each agent should have contributed meaningful content
            for role, result in collaboration_results.items():
                assert len(result) > 100, f"{role} agent should produce substantial output"
                assert any(keyword in result.lower() for keyword in 
                          ["machine learning", "healthcare", "artificial intelligence"])
            
            # Synthesis should reference both research and analysis
            synthesis_content = collaboration_results["synthesis"].lower()
            assert any(keyword in synthesis_content for keyword in 
                      ["research", "analysis", "findings", "conclusion"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_time_workflow_with_performance_monitoring(self, test_services, workflow_test_data):
        """Test real-time workflow execution with performance monitoring"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Performance monitoring data
            performance_metrics = {
                "processing_times": [],
                "search_times": [],
                "agent_times": [],
                "total_workflow_time": 0
            }
            
            workflow_start = time.time()
            
            # Step 1: Process documents with timing
            document_processing_times = []
            
            for doc_name, doc_content in workflow_test_data["documents"].items():
                step_start = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": doc_content,
                        "document_name": f"perf_test_{doc_name}.txt",
                        "metadata": {"source": "performance_workflow", "document_type": doc_name}
                    }
                )
                
                step_time = time.time() - step_start
                document_processing_times.append(step_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
            
            performance_metrics["processing_times"] = document_processing_times
            
            # Step 2: Search operations with timing
            search_times = []
            
            for query in workflow_test_data["queries"]:
                step_start = time.time()
                
                response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": query,
                        "modalities": ["text"],
                        "limit": 10,
                        "score_threshold": 0.3
                    }
                )
                
                step_time = time.time() - step_start
                search_times.append(step_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                assert len(result["results"]) > 0
            
            performance_metrics["search_times"] = search_times
            
            # Step 3: Agent operations with timing
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Performance Test Agent",
                    "goal": "Execute tasks efficiently and provide performance insights",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 5,
                    "user_id": "performance_workflow_user"
                }
            )
            
            assert agent_response.status_code == 200
            agent_result = agent_response.json()
            agent_id = agent_result["agent_id"]
            
            agent_times = []
            
            for i, query in enumerate(workflow_test_data["queries"]):
                step_start = time.time()
                
                execution_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                    json={
                        "task": f"Analyze the search results for '{query}' and provide insights",
                        "user_id": "performance_workflow_user"
                    }
                )
                
                step_time = time.time() - step_start
                agent_times.append(step_time)
                
                assert execution_response.status_code == 200
                execution_result = execution_response.json()
                assert execution_result["success"] is True
            
            performance_metrics["agent_times"] = agent_times
            performance_metrics["total_workflow_time"] = time.time() - workflow_start
            
            # Step 4: Performance analysis and validation
            avg_processing_time = sum(performance_metrics["processing_times"]) / len(performance_metrics["processing_times"])
            avg_search_time = sum(performance_metrics["search_times"]) / len(performance_metrics["search_times"])
            avg_agent_time = sum(performance_metrics["agent_times"]) / len(performance_metrics["agent_times"])
            
            # Validate performance against thresholds
            assert avg_processing_time < performance_thresholds["text_processing_time"], \
                f"Average processing time {avg_processing_time:.2f}s exceeds threshold {performance_thresholds['text_processing_time']}s"
            
            assert avg_search_time < performance_thresholds["search_response_time"], \
                f"Average search time {avg_search_time:.2f}s exceeds threshold {performance_thresholds['search_response_time']}s"
            
            assert avg_agent_time < performance_thresholds["agent_execution_time"], \
                f"Average agent time {avg_agent_time:.2f}s exceeds threshold {performance_thresholds['agent_execution_time']}s"
            
            # Total workflow should complete within reasonable time
            assert performance_metrics["total_workflow_time"] < 120.0, \
                f"Total workflow time {performance_metrics['total_workflow_time']:.2f}s exceeds 120s limit"
            
            # Performance should be consistent (low variance)
            processing_variance = np.var(performance_metrics["processing_times"])
            search_variance = np.var(performance_metrics["search_times"])
            
            assert processing_variance < 1.0, f"Processing time variance {processing_variance:.2f} too high"
            assert search_variance < 0.5, f"Search time variance {search_variance:.2f} too high"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience_workflow(self, test_services, workflow_test_data):
        """Test error recovery and system resilience in workflow execution"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Test graceful handling of invalid inputs
            error_scenarios = [
                # Empty content
                {
                    "endpoint": f"{multimodal_worker['url']}/api/v1/process/text",
                    "data": {"text": "", "document_name": "empty_test.txt"},
                    "expected_status": [200, 400, 422]
                },
                # Invalid search parameters
                {
                    "endpoint": f"{retrieval_proxy['url']}/api/v1/search",
                    "data": {"query": "", "modalities": ["invalid"], "limit": -1},
                    "expected_status": [200, 400, 422]
                },
                # Malformed JSON
                {
                    "endpoint": f"{multimodal_worker['url']}/api/v1/process/text",
                    "data": "invalid json",
                    "expected_status": [422]
                }
            ]
            
            for scenario in error_scenarios:
                try:
                    if isinstance(scenario["data"], str):
                        response = await client.post(
                            scenario["endpoint"],
                            data=scenario["data"],
                            headers={"Content-Type": "application/json"}
                        )
                    else:
                        response = await client.post(
                            scenario["endpoint"],
                            json=scenario["data"]
                        )
                    
                    assert response.status_code in scenario["expected_status"], \
                        f"Expected status {scenario['expected_status']}, got {response.status_code}"
                
                except Exception as e:
                    # Some errors might be handled at the HTTP client level
                    assert "timeout" in str(e).lower() or "connection" in str(e).lower()
            
            # Step 2: Test recovery from temporary failures
            # Process valid content after errors
            recovery_response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/text",
                json={
                    "text": workflow_test_data["documents"]["research_paper"][:500],
                    "document_name": "recovery_test.txt",
                    "metadata": {"source": "error_recovery_test"}
                }
            )
            
            assert recovery_response.status_code == 200
            recovery_result = recovery_response.json()
            assert recovery_result["success"] is True
            
            # Step 3: Test agent error handling
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Error Recovery Agent",
                    "goal": "Handle errors gracefully and continue processing",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 5,
                    "user_id": "error_recovery_user"
                }
            )
            
            if agent_response.status_code == 200:
                agent_result = agent_response.json()
                agent_id = agent_result["agent_id"]
                
                # Test agent with potentially problematic task
                execution_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                    json={
                        "task": "Search for information about non-existent topic and provide analysis",
                        "user_id": "error_recovery_user"
                    }
                )
                
                # Agent should handle gracefully (either succeed with no results or fail gracefully)
                assert execution_response.status_code in [200, 400, 422, 500]
                
                if execution_response.status_code == 200:
                    execution_result = execution_response.json()
                    # Even if no results found, agent should provide some response
                    assert "result" in execution_result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_flow_integrity_workflow(self, test_services, workflow_test_data):
        """Test data flow integrity and consistency across the entire workflow"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Process documents with specific metadata for tracking
            tracking_metadata = {
                "workflow_id": "data_integrity_test_001",
                "timestamp": "2024-01-01T00:00:00Z",
                "source": "data_integrity_workflow",
                "version": "1.0"
            }
            
            processed_documents = {}
            
            for doc_name, doc_content in workflow_test_data["documents"].items():
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": doc_content,
                        "document_name": f"integrity_test_{doc_name}.txt",
                        "metadata": {
                            **tracking_metadata,
                            "document_type": doc_name,
                            "content_length": len(doc_content)
                        }
                    }
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                processed_documents[doc_name] = {
                    "content_id": result["content_id"],
                    "original_content": doc_content,
                    "metadata": result.get("metadata", {})
                }
            
            # Step 2: Verify data integrity through search
            integrity_checks = []
            
            for doc_name, doc_info in processed_documents.items():
                # Search for specific content from each document
                search_terms = doc_content[:100].split()[:5]  # First 5 words
                query = " ".join(search_terms)
                
                search_response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": query,
                        "modalities": ["text"],
                        "limit": 10,
                        "filters": {
                            "metadata": {
                                "workflow_id": tracking_metadata["workflow_id"],
                                "document_type": doc_name
                            }
                        }
                    }
                )
                
                assert search_response.status_code == 200
                search_result = search_response.json()
                assert search_result["success"] is True
                
                # Verify we found the correct document
                found_document = None
                for result in search_result["results"]:
                    if result["document_id"] == doc_info["content_id"]:
                        found_document = result
                        break
                
                assert found_document is not None, f"Should find document {doc_name} in search results"
                
                # Verify metadata integrity
                if "metadata" in found_document:
                    assert found_document["metadata"]["workflow_id"] == tracking_metadata["workflow_id"]
                    assert found_document["metadata"]["document_type"] == doc_name
                    assert found_document["metadata"]["source"] == tracking_metadata["source"]
                
                integrity_checks.append({
                    "document": doc_name,
                    "found": found_document is not None,
                    "metadata_intact": "metadata" in found_document and 
                                     found_document["metadata"]["workflow_id"] == tracking_metadata["workflow_id"]
                })
            
            # Step 3: Test agent data access integrity
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Data Integrity Agent",
                    "goal": "Verify data integrity and consistency across the system",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 10,
                    "user_id": "data_integrity_user"
                }
            )
            
            assert agent_response.status_code == 200
            agent_result = agent_response.json()
            agent_id = agent_result["agent_id"]
            
            # Agent task to verify data integrity
            integrity_task = f"""
            Verify data integrity for workflow {tracking_metadata['workflow_id']}. 
            Search for documents with workflow_id '{tracking_metadata['workflow_id']}' and 
            verify that all expected documents are found with correct metadata.
            Expected documents: {list(processed_documents.keys())}
            """
            
            execution_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                json={
                    "task": integrity_task,
                    "user_id": "data_integrity_user"
                }
            )
            
            assert execution_response.status_code == 200
            execution_result = execution_response.json()
            assert execution_result["success"] is True
            
            # Step 4: Comprehensive integrity validation
            # All integrity checks should pass
            assert all(check["found"] for check in integrity_checks), \
                "All processed documents should be found in search results"
            
            assert all(check["metadata_intact"] for check in integrity_checks), \
                "All documents should maintain metadata integrity"
            
            # Agent should have found and verified the data
            agent_result_text = execution_result["result"].lower()
            assert any(keyword in agent_result_text for keyword in 
                      ["found", "verified", "integrity", "consistent"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_scalability_workflow(self, test_services, workflow_test_data):
        """Test workflow scalability with multiple concurrent operations"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Concurrent document processing
            processing_tasks = []
            
            for i in range(10):  # Process 10 documents concurrently
                doc_content = f"{workflow_test_data['documents']['research_paper'][:200]} - Batch {i}"
                task = client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": doc_content,
                        "document_name": f"scalability_test_{i}.txt",
                        "metadata": {
                            "source": "scalability_workflow",
                            "batch_id": i,
                            "test_type": "concurrent_processing"
                        }
                    }
                )
                processing_tasks.append(task)
            
            # Execute concurrent processing
            start_time = time.time()
            processing_responses = await asyncio.gather(*processing_tasks, return_exceptions=True)
            processing_time = time.time() - start_time
            
            # Verify processing results
            successful_processing = 0
            for response in processing_responses:
                if not isinstance(response, Exception) and response.status_code == 200:
                    successful_processing += 1
            
            processing_success_rate = successful_processing / len(processing_tasks)
            assert processing_success_rate >= 0.8, \
                f"Processing success rate {processing_success_rate:.2%} below 80% threshold"
            
            # Step 2: Concurrent search operations
            search_tasks = []
            
            for i in range(15):  # 15 concurrent searches
                task = client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": f"machine learning scalability test {i}",
                        "modalities": ["text"],
                        "limit": 5
                    }
                )
                search_tasks.append(task)
            
            # Execute concurrent searches
            start_time = time.time()
            search_responses = await asyncio.gather(*search_tasks, return_exceptions=True)
            search_time = time.time() - start_time
            
            # Verify search results
            successful_searches = 0
            for response in search_responses:
                if not isinstance(response, Exception) and response.status_code == 200:
                    successful_searches += 1
            
            search_success_rate = successful_searches / len(search_tasks)
            assert search_success_rate >= 0.8, \
                f"Search success rate {search_success_rate:.2%} below 80% threshold"
            
            # Step 3: Concurrent agent operations
            agent_tasks = []
            
            # Create multiple agents
            for i in range(3):
                agent_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents",
                    json={
                        "name": f"Scalability Test Agent {i}",
                        "goal": "Handle concurrent operations efficiently",
                        "tools": ["search_content", "generate_text"],
                        "memory_window": 5,
                        "user_id": f"scalability_user_{i}"
                    }
                )
                
                if agent_response.status_code == 200:
                    agent_result = agent_response.json()
                    agent_id = agent_result["agent_id"]
                    
                    # Create concurrent execution tasks for this agent
                    for j in range(2):
                        task = client.post(
                            f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                            json={
                                "task": f"Analyze scalability test data batch {i}-{j}",
                                "user_id": f"scalability_user_{i}"
                            }
                        )
                        agent_tasks.append(task)
            
            # Execute concurrent agent operations
            if agent_tasks:
                start_time = time.time()
                agent_responses = await asyncio.gather(*agent_tasks, return_exceptions=True)
                agent_time = time.time() - start_time
                
                # Verify agent results
                successful_agents = 0
                for response in agent_responses:
                    if not isinstance(response, Exception) and response.status_code == 200:
                        successful_agents += 1
                
                agent_success_rate = successful_agents / len(agent_tasks)
                assert agent_success_rate >= 0.7, \
                    f"Agent success rate {agent_success_rate:.2%} below 70% threshold"
            
            # Step 4: Performance validation
            # Concurrent operations should complete within reasonable time
            assert processing_time < 60.0, \
                f"Concurrent processing took {processing_time:.2f}s, expected < 60s"
            
            assert search_time < 30.0, \
                f"Concurrent searches took {search_time:.2f}s, expected < 30s"
            
            if agent_tasks:
                assert agent_time < 90.0, \
                    f"Concurrent agent operations took {agent_time:.2f}s, expected < 90s"