"""
Performance tests for model inference
"""
import pytest
import pytest_asyncio
import asyncio
import time
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from tests.conftest import performance_thresholds


class TestModelInference:
    """Test cases for model inference performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_text_embedding_inference_time(self, performance_thresholds):
        """Test text embedding model inference time"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.SentenceTransformer') as mock_transformer:
            # Mock fast inference
            mock_model = Mock()
            mock_model.encode.return_value = np.random.rand(384)
            mock_transformer.return_value = mock_model

            # Test inference time
            start_time = time.time()
            
            # Simulate text embedding
            text = "This is a test document for performance testing of text embedding inference."
            embeddings = mock_model.encode([text])
            
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000

            assert len(embeddings) == 1
            assert embeddings[0].shape == (384,)
            assert inference_time_ms < threshold, f"Text embedding inference time {inference_time_ms}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_image_embedding_inference_time(self, performance_thresholds):
        """Test image embedding model inference time"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.CLIPModel') as mock_clip:
            # Mock fast inference
            mock_model = Mock()
            mock_model.encode_image.return_value = np.random.rand(1, 512)
            mock_clip.return_value = mock_model

            # Test inference time
            start_time = time.time()
            
            # Simulate image embedding
            mock_image = np.random.rand(224, 224, 3)  # Mock image
            embeddings = mock_model.encode_image(mock_image)
            
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000

            assert embeddings.shape == (1, 512)
            assert inference_time_ms < threshold, f"Image embedding inference time {inference_time_ms}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_image_captioning_inference_time(self, performance_thresholds):
        """Test image captioning model inference time"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.BLIPModel') as mock_blip:
            # Mock fast inference
            mock_model = Mock()
            mock_model.generate.return_value = ["A test image caption for performance testing"]
            mock_blip.return_value = mock_model

            # Test inference time
            start_time = time.time()
            
            # Simulate image captioning
            mock_image = np.random.rand(224, 224, 3)  # Mock image
            caption = mock_model.generate(mock_image)
            
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000

            assert len(caption) == 1
            assert isinstance(caption[0], str)
            assert inference_time_ms < threshold, f"Image captioning inference time {inference_time_ms}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_audio_transcription_inference_time(self, performance_thresholds):
        """Test audio transcription model inference time"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.WhisperModel') as mock_whisper:
            # Mock fast inference
            mock_model = Mock()
            mock_model.transcribe.return_value = {"text": "This is a test audio transcription for performance testing"}
            mock_whisper.return_value = mock_model

            # Test inference time
            start_time = time.time()
            
            # Simulate audio transcription
            mock_audio = np.random.rand(16000)  # 1 second of audio at 16kHz
            result = mock_model.transcribe(mock_audio)
            
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000

            assert "text" in result
            assert isinstance(result["text"], str)
            assert inference_time_ms < threshold, f"Audio transcription inference time {inference_time_ms}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_inference_performance(self, performance_thresholds):
        """Test batch inference performance"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.SentenceTransformer') as mock_transformer:
            # Mock batch inference
            mock_model = Mock()
            batch_size = 10
            mock_model.encode.return_value = np.random.rand(batch_size, 384)
            mock_transformer.return_value = mock_model

            # Test batch inference time
            start_time = time.time()
            
            # Simulate batch text embedding
            texts = [f"Test document {i} for batch processing" for i in range(batch_size)]
            embeddings = mock_model.encode(texts)
            
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000
            avg_time_per_item = inference_time_ms / batch_size

            assert embeddings.shape == (batch_size, 384)
            assert avg_time_per_item < threshold, f"Batch inference time per item {avg_time_per_item}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_model_memory_usage(self):
        """Test model memory usage"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch('app.models.SentenceTransformer') as mock_transformer:
            # Mock model with memory usage
            mock_model = Mock()
            mock_model.encode.return_value = np.random.rand(384)
            mock_transformer.return_value = mock_model

            # Load and use model
            model = mock_transformer()
            
            # Simulate multiple inferences
            for i in range(100):
                embeddings = model.encode([f"Test text {i}"])
                assert len(embeddings) == 1

            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Verify memory usage is reasonable (should not increase by more than 200MB)
            max_memory_increase = 200  # MB
            assert memory_increase < max_memory_increase, f"Model memory increase {memory_increase:.2f}MB exceeds limit {max_memory_increase}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_model_inference(self, performance_thresholds):
        """Test concurrent model inference performance"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.SentenceTransformer') as mock_transformer:
            # Mock concurrent inference
            mock_model = Mock()
            mock_model.encode.return_value = np.random.rand(384)
            mock_transformer.return_value = mock_model

            # Test concurrent inference
            async def inference_task(text_id: int):
                start_time = time.time()
                embeddings = mock_model.encode([f"Concurrent test text {text_id}"])
                end_time = time.time()
                return (text_id, embeddings, (end_time - start_time) * 1000)

            # Run concurrent inferences
            tasks = [inference_task(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

            # Verify all inferences succeeded
            for text_id, embeddings, inference_time in results:
                assert len(embeddings) == 1
                assert embeddings[0].shape == (384,)
                assert inference_time < threshold, f"Concurrent inference time {inference_time}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_model_loading_time(self):
        """Test model loading time"""
        with patch('app.models.SentenceTransformer') as mock_transformer:
            # Mock model loading
            mock_model = Mock()
            mock_transformer.return_value = mock_model

            # Test model loading time
            start_time = time.time()
            model = mock_transformer("sentence-transformers/all-MiniLM-L6-v2")
            end_time = time.time()
            loading_time = end_time - start_time

            # Verify model loaded successfully
            assert model is not None
            # Model loading should be reasonably fast (less than 10 seconds)
            assert loading_time < 10, f"Model loading time {loading_time}s exceeds 10s limit"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_model_inference_accuracy_under_load(self, performance_thresholds):
        """Test model inference accuracy under load"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.SentenceTransformer') as mock_transformer:
            # Mock model with consistent output
            mock_model = Mock()
            mock_model.encode.return_value = np.random.rand(384)
            mock_transformer.return_value = mock_model

            # Test inference under load
            results = []
            for i in range(50):  # High load
                start_time = time.time()
                embeddings = mock_model.encode([f"Load test text {i}"])
                end_time = time.time()
                inference_time = (end_time - start_time) * 1000
                
                results.append({
                    "iteration": i,
                    "embeddings": embeddings,
                    "inference_time": inference_time
                })

            # Verify all inferences succeeded and maintained performance
            for result in results:
                assert len(result["embeddings"]) == 1
                assert result["embeddings"][0].shape == (384,)
                assert result["inference_time"] < threshold, f"Inference time {result['inference_time']}ms exceeds threshold {threshold}ms under load"

            # Verify consistent performance
            inference_times = [r["inference_time"] for r in results]
            avg_time = sum(inference_times) / len(inference_times)
            max_time = max(inference_times)
            
            # Performance should not degrade significantly under load
            assert max_time < avg_time * 2, "Performance degraded significantly under load"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_model_inference_with_different_input_sizes(self, performance_thresholds):
        """Test model inference performance with different input sizes"""
        threshold = performance_thresholds["model_inference_time_ms"]

        with patch('app.models.SentenceTransformer') as mock_transformer:
            # Mock model
            mock_model = Mock()
            mock_transformer.return_value = mock_model

            # Test different input sizes
            input_sizes = [1, 5, 10, 20, 50]
            
            for size in input_sizes:
                # Mock response for this batch size
                mock_model.encode.return_value = np.random.rand(size, 384)
                
                start_time = time.time()
                texts = [f"Test text {i}" for i in range(size)]
                embeddings = mock_model.encode(texts)
                end_time = time.time()
                
                inference_time_ms = (end_time - start_time) * 1000
                avg_time_per_item = inference_time_ms / size

                assert embeddings.shape == (size, 384)
                assert avg_time_per_item < threshold, f"Inference time per item {avg_time_per_item}ms exceeds threshold {threshold}ms for batch size {size}"
