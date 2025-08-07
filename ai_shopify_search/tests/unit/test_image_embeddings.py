#!/usr/bin/env python3
"""
Unit tests for image embedding functionality.

Tests OpenCLIP integration, embedding generation, and combination logic.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import torch

# Import the functions to test
from core.embeddings import (
    generate_image_embedding,
    combine_embeddings,
    generate_embedding,
    get_clip_model,
    load_image_from_url_or_path
)


class TestImageEmbeddings:
    """Test suite for image embedding functionality."""
    
    @pytest.fixture
    def sample_image_embedding(self):
        """Sample image embedding for testing."""
        return [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # 500 dimensions
    
    @pytest.fixture
    def sample_text_embedding(self):
        """Sample text embedding for testing."""
        return [0.2, 0.3, 0.4, 0.5, 0.6] * 100  # 500 dimensions
    
    @pytest.fixture
    def mock_image(self):
        """Mock PIL Image for testing."""
        image = Mock(spec=Image.Image)
        image.mode = 'RGB'
        image.convert.return_value = image
        return image
    
    @pytest.fixture
    def mock_clip_model(self):
        """Mock OpenCLIP model for testing."""
        model = Mock()
        preprocess = Mock()
        
        # Mock the model.encode_image method
        mock_features = torch.tensor([[0.1, 0.2, 0.3, 0.4, 0.5] * 100])  # 500 dimensions
        model.encode_image.return_value = mock_features
        
        return model, preprocess
    
    def test_load_image_from_url(self, mock_image):
        """Test loading image from URL."""
        with patch('requests.get') as mock_get, \
             patch('PIL.Image.open') as mock_open:
            
            # Mock response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = b'fake_image_data'
            mock_get.return_value = mock_response
            
            # Mock PIL Image
            mock_open.return_value = mock_image
            
            # Test
            result = load_image_from_url_or_path("https://example.com/image.jpg")
            
            # Assertions
            assert result == mock_image
            mock_get.assert_called_once_with("https://example.com/image.jpg", timeout=10)
            mock_open.assert_called_once()
    
    def test_load_image_from_path(self, mock_image):
        """Test loading image from local path."""
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = mock_image
            
            result = load_image_from_url_or_path("/path/to/image.jpg")
            
            assert result == mock_image
            mock_open.assert_called_once_with("/path/to/image.jpg")
    
    def test_load_image_converts_to_rgb(self, mock_image):
        """Test that non-RGB images are converted to RGB."""
        # Create mock image that's not RGB
        mock_image.mode = 'RGBA'
        
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = mock_image
            
            result = load_image_from_url_or_path("/path/to/image.jpg")
            
            assert result == mock_image
            mock_image.convert.assert_called_once_with('RGB')
    
    @patch('core.embeddings.get_clip_model')
    @patch('core.embeddings.load_image_from_url_or_path')
    def test_generate_image_embedding(self, mock_load_image, mock_get_model, 
                                    mock_clip_model, mock_image):
        """Test image embedding generation."""
        # Setup mocks
        mock_load_image.return_value = mock_image
        mock_get_model.return_value = mock_clip_model
        model, preprocess = mock_clip_model
        
        # Mock preprocess
        mock_tensor = torch.tensor([[0.1, 0.2, 0.3, 0.4, 0.5] * 100])
        preprocess.return_value = mock_tensor
        
        # Test
        result = generate_image_embedding("https://example.com/image.jpg")
        
        # Assertions
        assert isinstance(result, list)
        assert len(result) == 500  # 500 dimensions
        assert all(isinstance(x, float) for x in result)
        
        # Check that functions were called
        mock_load_image.assert_called_once_with("https://example.com/image.jpg")
        mock_get_model.assert_called_once()
        preprocess.assert_called_once_with(mock_image)
        model.encode_image.assert_called_once()
    
    def test_combine_embeddings_fashion_category(self, sample_text_embedding, sample_image_embedding):
        """Test embedding combination for fashion category."""
        result = combine_embeddings(sample_text_embedding, sample_image_embedding, "fashion")
        
        assert isinstance(result, list)
        assert len(result) == 500
        assert all(isinstance(x, float) for x in result)
        
        # Check normalization
        result_array = np.array(result)
        norm = np.linalg.norm(result_array)
        assert abs(norm - 1.0) < 0.01
    
    def test_combine_embeddings_electronics_category(self, sample_text_embedding, sample_image_embedding):
        """Test embedding combination for electronics category."""
        result = combine_embeddings(sample_text_embedding, sample_image_embedding, "electronics")
        
        assert isinstance(result, list)
        assert len(result) == 500
        assert all(isinstance(x, float) for x in result)
        
        # Check normalization
        result_array = np.array(result)
        norm = np.linalg.norm(result_array)
        assert abs(norm - 1.0) < 0.01
    
    def test_combine_embeddings_general_category(self, sample_text_embedding, sample_image_embedding):
        """Test embedding combination for general category."""
        result = combine_embeddings(sample_text_embedding, sample_image_embedding, "general")
        
        assert isinstance(result, list)
        assert len(result) == 500
        assert all(isinstance(x, float) for x in result)
        
        # Check normalization
        result_array = np.array(result)
        norm = np.linalg.norm(result_array)
        assert abs(norm - 1.0) < 0.01
    
    def test_combine_embeddings_no_category(self, sample_text_embedding, sample_image_embedding):
        """Test embedding combination without category."""
        result = combine_embeddings(sample_text_embedding, sample_image_embedding)
        
        assert isinstance(result, list)
        assert len(result) == 500
        assert all(isinstance(x, float) for x in result)
        
        # Check normalization
        result_array = np.array(result)
        norm = np.linalg.norm(result_array)
        assert abs(norm - 1.0) < 0.01
    
    def test_combine_embeddings_different_dimensions(self):
        """Test combining embeddings with different dimensions."""
        text_emb = [0.1, 0.2, 0.3]  # 3 dimensions
        image_emb = [0.4, 0.5, 0.6, 0.7, 0.8]  # 5 dimensions
        
        result = combine_embeddings(text_emb, image_emb)
        
        assert isinstance(result, list)
        assert len(result) == 5  # Should pad to max dimension
        assert all(isinstance(x, float) for x in result)
    
    @patch('core.embeddings.generate_embedding_cached')
    @patch('core.embeddings.generate_image_embedding')
    def test_generate_embedding_with_image_url(self, mock_gen_image, mock_gen_text,
                                             sample_text_embedding, sample_image_embedding):
        """Test generate_embedding with image URL."""
        # Setup mocks
        mock_gen_text.return_value = sample_text_embedding
        mock_gen_image.return_value = sample_image_embedding
        
        # Mock combine_embeddings
        with patch('core.embeddings.combine_embeddings') as mock_combine:
            mock_combine.return_value = [0.5] * 500
            
            result = generate_embedding(
                title="Test Product",
                description="Test description",
                category="fashion",
                image_url="https://example.com/image.jpg"
            )
            
            # Assertions
            assert result == [0.5] * 500
            mock_gen_text.assert_called_once()
            mock_gen_image.assert_called_once_with("https://example.com/image.jpg")
            mock_combine.assert_called_once()
    
    @patch('core.embeddings.generate_embedding_cached')
    def test_generate_embedding_without_image_url(self, mock_gen_text, sample_text_embedding):
        """Test generate_embedding without image URL."""
        mock_gen_text.return_value = sample_text_embedding
        
        result = generate_embedding(
            title="Test Product",
            description="Test description",
            category="fashion"
        )
        
        assert result == sample_text_embedding
        mock_gen_text.assert_called_once()
    
    @patch('core.embeddings.generate_embedding_cached')
    @patch('core.embeddings.generate_image_embedding')
    def test_generate_embedding_image_failure_fallback(self, mock_gen_image, mock_gen_text,
                                                     sample_text_embedding):
        """Test that generate_embedding falls back to text-only when image fails."""
        mock_gen_text.return_value = sample_text_embedding
        mock_gen_image.side_effect = Exception("Image processing failed")
        
        result = generate_embedding(
            title="Test Product",
            description="Test description",
            category="fashion",
            image_url="https://example.com/image.jpg"
        )
        
        assert result == sample_text_embedding
        mock_gen_text.assert_called_once()
        mock_gen_image.assert_called_once()
    
    def test_get_clip_model_caching(self):
        """Test that get_clip_model uses caching."""
        with patch('open_clip.create_model_and_transforms') as mock_create:
            mock_create.return_value = (Mock(), Mock(), Mock())
            
            # Call twice
            result1 = get_clip_model()
            result2 = get_clip_model()
            
            # Should only call create_model_and_transforms once due to caching
            mock_create.assert_called_once()
            assert result1 == result2
    
    def test_embedding_normalization(self, sample_text_embedding, sample_image_embedding):
        """Test that combined embeddings are properly normalized."""
        result = combine_embeddings(sample_text_embedding, sample_image_embedding, "fashion")
        
        result_array = np.array(result)
        norm = np.linalg.norm(result_array)
        
        # Should be normalized to unit length
        assert abs(norm - 1.0) < 0.01
    
    def test_embedding_weights_by_category(self):
        """Test that different categories use different weights."""
        text_emb = [1.0, 0.0, 0.0]  # Unit vector in x direction
        image_emb = [0.0, 1.0, 0.0]  # Unit vector in y direction
        
        # Fashion should give more weight to image
        fashion_result = combine_embeddings(text_emb, image_emb, "fashion")
        fashion_array = np.array(fashion_result)
        
        # Electronics should give more balanced weight
        electronics_result = combine_embeddings(text_emb, image_emb, "electronics")
        electronics_array = np.array(electronics_result)
        
        # The results should be different due to different weights
        assert not np.allclose(fashion_array, electronics_array)


class TestImageEmbeddingEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_image_embedding(self):
        """Test handling of empty image embedding."""
        text_emb = [0.1, 0.2, 0.3]
        image_emb = []
        
        with pytest.raises(ValueError):
            combine_embeddings(text_emb, image_emb)
    
    def test_empty_text_embedding(self):
        """Test handling of empty text embedding."""
        text_emb = []
        image_emb = [0.1, 0.2, 0.3]
        
        with pytest.raises(ValueError):
            combine_embeddings(text_emb, image_emb)
    
    def test_zero_embeddings(self):
        """Test handling of zero embeddings."""
        text_emb = [0.0, 0.0, 0.0]
        image_emb = [0.0, 0.0, 0.0]
        
        result = combine_embeddings(text_emb, image_emb)
        
        # Should handle gracefully and return normalized result
        assert isinstance(result, list)
        assert len(result) == 3
    
    def test_invalid_image_url(self):
        """Test handling of invalid image URL."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):
                load_image_from_url_or_path("https://invalid-url.com/image.jpg")
    
    def test_invalid_image_path(self):
        """Test handling of invalid image path."""
        with patch('PIL.Image.open') as mock_open:
            mock_open.side_effect = FileNotFoundError("Image not found")
            
            with pytest.raises(FileNotFoundError):
                load_image_from_url_or_path("/invalid/path/image.jpg")


if __name__ == "__main__":
    pytest.main([__file__]) 