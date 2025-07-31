"""
Unit tests for fixed price intent extraction functionality.
Tests the enhanced price intent detection with fallback logic.
"""

import pytest
from price_intent import (
    extract_price_intent, 
    clean_query_from_price_intent, 
    format_price_message,
    validate_price_range,
    get_price_category
)


class TestPriceIntentExtraction:
    """Test price intent extraction with various query formats."""
    
    def test_budget_words_different_forms(self):
        """Test that budget words in different forms are recognized."""
        test_cases = [
            ("goedkoop jas", None, 75, "budget"),
            ("goedkope jas geel", None, 75, "budget"),
            ("goedkopere schoenen", None, 75, "budget"),
            ("goedkoopste producten", None, 75, "budget"),
            ("cheap shoes", None, 75, "budget"),
            ("cheaper options", None, 75, "budget"),
            ("budget friendly", None, 75, "budget"),
            ("voordelige kleding", None, 75, "budget"),
            ("affordable items", None, 75, "budget"),
        ]
        
        for query, expected_min, expected_max, expected_pattern in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            assert min_price == expected_min, f"Failed for query: {query}"
            assert max_price == expected_max, f"Failed for query: {query}"
            assert metadata["pattern_type"] == expected_pattern, f"Failed for query: {query}"
            assert metadata["confidence"] > 0.0, f"Confidence should be > 0 for query: {query}"
    
    def test_premium_words_different_forms(self):
        """Test that premium words in different forms are recognized."""
        test_cases = [
            ("duur product", 200, None, "premium"),
            ("dure kleding", 200, None, "premium"),
            ("duurdere items", 200, None, "premium"),
            ("duurste producten", 200, None, "premium"),
            ("expensive shoes", 200, None, "premium"),
            ("luxe accessoires", 200, None, "premium"),
            ("premium quality", 200, None, "premium"),
            ("exclusief items", 200, None, "premium"),
            ("high-end products", 200, None, "premium"),
        ]
        
        for query, expected_min, expected_max, expected_pattern in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            assert min_price == expected_min, f"Failed for query: {query}"
            assert max_price == expected_max, f"Failed for query: {query}"
            assert metadata["pattern_type"] == expected_pattern, f"Failed for query: {query}"
            assert metadata["confidence"] > 0.0, f"Confidence should be > 0 for query: {query}"
    
    def test_exact_price_ranges(self):
        """Test exact price range extraction."""
        test_cases = [
            ("onder 50 euro", None, 50.0, "below"),
            ("below 100 euro", None, 100.0, "below"),
            ("boven 200 euro", 200.0, None, "above"),
            ("above 150 euro", 150.0, None, "above"),
            ("tussen 50 en 100 euro", 50.0, 100.0, "range"),
            ("between 75 and 125 euro", 75.0, 125.0, "range"),
            ("50 tot 100 euro", 50.0, 100.0, "range"),
            ("75 to 125 euro", 75.0, 125.0, "range"),
        ]
        
        for query, expected_min, expected_max, expected_pattern in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            assert min_price == expected_min, f"Failed for query: {query}"
            assert max_price == expected_max, f"Failed for query: {query}"
            assert metadata["pattern_type"] == expected_pattern, f"Failed for query: {query}"
    
    def test_approximate_price_patterns(self):
        """Test approximate price pattern extraction."""
        test_cases = [
            ("rond 100 euro", 80.0, 120.0, "approximate"),
            ("around 150 euro", 120.0, 180.0, "approximate"),
            ("ongeveer 200 euro", 160.0, 240.0, "approximate"),
            ("approximately 75 euro", 60.0, 90.0, "approximate"),
        ]
        
        for query, expected_min, expected_max, expected_pattern in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            assert abs(min_price - expected_min) < 0.1, f"Failed for query: {query}"
            assert abs(max_price - expected_max) < 0.1, f"Failed for query: {query}"
            assert metadata["pattern_type"] == expected_pattern, f"Failed for query: {query}"
    
    def test_exact_price_patterns(self):
        """Test exact price pattern extraction."""
        test_cases = [
            ("100 euro", 90.0, 110.0, "exact"),
            ("75 eur", 67.5, 82.5, "exact"),
        ]
        
        for query, expected_min, expected_max, expected_pattern in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            if expected_min is not None:
                assert abs(min_price - expected_min) < 0.1, f"Failed for query: {query}"
            else:
                assert min_price is None, f"Failed for query: {query}"
            if expected_max is not None:
                assert abs(max_price - expected_max) < 0.1, f"Failed for query: {query}"
            else:
                assert max_price is None, f"Failed for query: {query}"
            assert metadata["pattern_type"] == expected_pattern, f"Failed for query: {query}"
    
    def test_fallback_budget_detection(self):
        """Test fallback budget word detection when patterns don't match."""
        # Test cases that should trigger fallback (words not in main patterns)
        test_cases = [
            ("betaalbare schoenen", None, 75, "budget_fallback"),
            ("economical items", None, 75, "budget_fallback"),
            ("inexpensive products", None, 75, "budget_fallback"),
        ]
        
        for query, expected_min, expected_max, expected_pattern in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            assert min_price == expected_min, f"Failed for query: {query}"
            assert max_price == expected_max, f"Failed for query: {query}"
            assert metadata["pattern_type"] == expected_pattern, f"Failed for query: {query}"
            assert metadata["confidence"] >= 0.8, f"Fallback should have high confidence for query: {query}"
    
    def test_no_price_intent(self):
        """Test queries without price intent."""
        test_cases = [
            "rode schoenen",
            "katoenen shirt",
            "wollen trui",
            "leer tas",
            "",
            "   ",
        ]
        
        for query in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            assert min_price is None, f"Should be None for query: {query}"
            assert max_price is None, f"Should be None for query: {query}"
            assert metadata["confidence"] == 0.0, f"Confidence should be 0 for query: {query}"
    
    def test_price_range_validation(self):
        """Test automatic price range validation and swapping."""
        # Test case where min > max should be swapped
        min_price, max_price, metadata = extract_price_intent("tussen 100 en 50 euro")
        assert min_price == 50.0, "Min and max should be swapped"
        assert max_price == 100.0, "Min and max should be swapped"
        assert metadata["pattern_type"] == "range"


class TestQueryCleaning:
    """Test query cleaning functionality."""
    
    def test_clean_budget_words(self):
        """Test cleaning of budget words from queries."""
        test_cases = [
            ("goedkope jas geel", "jas geel"),
            ("cheap shoes red", "shoes red"),
            ("budget friendly items", "friendly items"),
            ("voordelige kleding", "kleding"),
        ]
        
        for original, expected in test_cases:
            cleaned = clean_query_from_price_intent(original)
            assert cleaned == expected, f"Failed for: {original} -> {cleaned}"
    
    def test_clean_premium_words(self):
        """Test cleaning of premium words from queries."""
        test_cases = [
            ("dure kleding", "kleding"),
            ("expensive shoes", "shoes"),
            ("luxe accessoires", "accessoires"),
            ("premium quality", "quality"),
        ]
        
        for original, expected in test_cases:
            cleaned = clean_query_from_price_intent(original)
            assert cleaned == expected, f"Failed for: {original} -> {cleaned}"
    
    def test_clean_price_ranges(self):
        """Test cleaning of price ranges from queries."""
        test_cases = [
            ("schoenen onder 50 euro", "schoenen"),
            ("shoes between 75 and 125", "shoes"),
            ("kleding rond 100 euro", "kleding"),
        ]
        
        for original, expected in test_cases:
            cleaned = clean_query_from_price_intent(original)
            assert cleaned == expected, f"Failed for: {original} -> {cleaned}"
    
    def test_clean_empty_result(self):
        """Test that empty cleaned queries return original."""
        test_cases = [
            "goedkoop",
            "duur",
            "onder 50 euro",
        ]
        
        for query in test_cases:
            cleaned = clean_query_from_price_intent(query)
            assert cleaned == query, f"Should return original for: {query}"


class TestPriceMessageFormatting:
    """Test price message formatting functionality."""
    
    def test_format_budget_message(self):
        """Test formatting of budget price messages."""
        min_price, max_price, metadata = extract_price_intent("goedkope jas")
        message = format_price_message(min_price, max_price, metadata)
        assert "tot €75.00" in message
        assert "vertrouwen" in message
    
    def test_format_premium_message(self):
        """Test formatting of premium price messages."""
        min_price, max_price, metadata = extract_price_intent("dure kleding")
        message = format_price_message(min_price, max_price, metadata)
        assert "vanaf €200.00" in message
        assert "vertrouwen" in message
    
    def test_format_range_message(self):
        """Test formatting of price range messages."""
        min_price, max_price, metadata = extract_price_intent("tussen 50 en 100 euro")
        message = format_price_message(min_price, max_price, metadata)
        assert "tussen €50.00 en €100.00" in message
    
    def test_format_no_price_message(self):
        """Test formatting when no price intent is found."""
        message = format_price_message(None, None)
        assert "Geen prijsfilter toegepast" in message


class TestPriceValidation:
    """Test price validation functionality."""
    
    def test_valid_price_ranges(self):
        """Test valid price range validation."""
        assert validate_price_range(50, 100) == True
        assert validate_price_range(None, 100) == True
        assert validate_price_range(50, None) == True
        assert validate_price_range(None, None) == True
    
    def test_invalid_price_ranges(self):
        """Test invalid price range validation."""
        assert validate_price_range(-10, 100) == False
        assert validate_price_range(50, -20) == False
        assert validate_price_range(100, 50) == False  # min > max


class TestPriceCategorization:
    """Test price categorization functionality."""
    
    def test_price_categories(self):
        """Test price categorization into budget, midden, premium."""
        assert get_price_category(25) == "budget"
        assert get_price_category(75) == "midden"
        assert get_price_category(250) == "premium"
    
    def test_price_category_boundaries(self):
        """Test price category boundary conditions."""
        assert get_price_category(49.99) == "budget"
        assert get_price_category(50) == "midden"
        assert get_price_category(199.99) == "midden"
        assert get_price_category(200) == "premium"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_special_characters(self):
        """Test handling of special characters in queries."""
        min_price, max_price, metadata = extract_price_intent("goedkope jas €50")
        assert max_price == 75  # Should still detect "goedkope"
    
    def test_numbers_in_query(self):
        """Test handling of numbers that are not prices."""
        min_price, max_price, metadata = extract_price_intent("jas maat 42 goedkoop")
        assert max_price == 75  # Should detect "goedkoop"
    
    def test_mixed_language(self):
        """Test handling of mixed language queries."""
        min_price, max_price, metadata = extract_price_intent("cheap jas goedkoop")
        assert max_price == 75  # Should detect both "cheap" and "goedkoop"
    
    def test_case_insensitive(self):
        """Test case insensitive matching."""
        test_cases = [
            ("GOEDKOPE jas", None, 75),
            ("Cheap SHOES", None, 75),
            ("DURE kleding", 200, None),
            ("Expensive ITEMS", 200, None),
        ]
        
        for query, expected_min, expected_max in test_cases:
            min_price, max_price, metadata = extract_price_intent(query)
            assert min_price == expected_min, f"Failed for query: {query}"
            assert max_price == expected_max, f"Failed for query: {query}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 