"""
Fuzzy search utilities for spell correction and typo tolerance.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class FuzzySearch:
    """Fuzzy search and spell correction utilities."""
    
    def __init__(self):
        # Common Dutch fashion terms and their variations
        self.fashion_synonyms = {
            # Product types
            "schoen": ["schoenen", "schoen", "schoentje", "schoentjes"],
            "schoenen": ["schoen", "schoenen", "schoentje", "schoentjes"],
            "jas": ["jas", "jassen", "jacket", "coat", "blazer"],
            "jassen": ["jas", "jassen", "jacket", "coat", "blazer"],
            "shirt": ["shirt", "shirts", "t-shirt", "tshirt", "top", "blouse"],
            "shirts": ["shirt", "shirts", "t-shirt", "tshirt", "top", "blouse"],
            "broek": ["broek", "broeken", "pants", "trousers", "jeans"],
            "broeken": ["broek", "broeken", "pants", "trousers", "jeans"],
            "jurk": ["jurk", "jurken", "dress", "dresses"],
            "jurken": ["jurk", "jurken", "dress", "dresses"],
            "accessoire": ["accessoire", "accessoires", "accessory", "accessories"],
            "accessoires": ["accessoire", "accessoires", "accessory", "accessories"],
            
            # Materials
            "leder": ["leder", "lederen", "leer", "leather"],
            "lederen": ["leder", "lederen", "leer", "leather"],
            "katoen": ["katoen", "cotton"],
            "wol": ["wol", "wollen", "wool"],
            "wollen": ["wol", "wollen", "wool"],
            "zijde": ["zijde", "zijden", "silk"],
            "zijden": ["zijde", "zijden", "silk"],
            "denim": ["denim", "spijkerstof"],
            "spijkerstof": ["denim", "spijkerstof"],
            "polyester": ["polyester", "poly"],
            "linnen": ["linnen", "linen"],
            "synthetisch": ["synthetisch", "synthetic"],
            
            # Price terms
            "goedkoop": ["goedkoop", "goedkope", "betaalbaar", "betaalbare", "voordelig", "voordelige", "economisch", "economische"],
            "goedkope": ["goedkoop", "goedkope", "betaalbaar", "betaalbare", "voordelig", "voordelige", "economisch", "economische"],
            "duur": ["duur", "dure", "exclusief", "exclusieve", "premium", "luxe", "luxueus"],
            "dure": ["duur", "dure", "exclusief", "exclusieve", "premium", "luxe", "luxueus"],
            "betaalbaar": ["goedkoop", "goedkope", "betaalbaar", "betaalbare", "voordelig", "voordelige"],
            "betaalbare": ["goedkoop", "goedkope", "betaalbaar", "betaalbare", "voordelig", "voordelige"],
            
            # Colors
            "zwart": ["zwart", "zwarte", "black"],
            "zwarte": ["zwart", "zwarte", "black"],
            "wit": ["wit", "witte", "white"],
            "witte": ["wit", "witte", "white"],
            "blauw": ["blauw", "blauwe", "blue"],
            "blauwe": ["blauw", "blauwe", "blue"],
            "rood": ["rood", "rode", "red"],
            "rode": ["rood", "rode", "red"],
            "groen": ["groen", "groene", "green"],
            "groene": ["groen", "groene", "green"],
            "geel": ["geel", "gele", "yellow"],
            "gele": ["geel", "gele", "yellow"],
            "paars": ["paars", "paarse", "purple"],
            "paarse": ["paars", "paarse", "purple"],
            "grijs": ["grijs", "grijze", "gray", "grey"],
            "grijze": ["grijs", "grijze", "gray", "grey"],
            "bruin": ["bruin", "bruine", "brown"],
            "bruine": ["bruin", "bruine", "brown"],
            "beige": ["beige", "beige"],
            "roze": ["roze", "pink"],
            "oranje": ["oranje", "orange"],
            
            # Seasons
            "zomer": ["zomer", "zomerse", "summer"],
            "zomerse": ["zomer", "zomerse", "summer"],
            "winter": ["winter", "winterse", "winter"],
            "winterse": ["winter", "winterse", "winter"],
            "lente": ["lente", "lentese", "spring"],
            "lentese": ["lente", "lentese", "spring"],
            "herfst": ["herfst", "herfstse", "autumn", "fall"],
            "herfstse": ["herfst", "herfstse", "autumn", "fall"],
            
            # Styles
            "casual": ["casual", "casuele", "informeel", "informele"],
            "casuele": ["casual", "casuele", "informeel", "informele"],
            "formeel": ["formeel", "formele", "elegant", "elegante"],
            "formele": ["formeel", "formele", "elegant", "elegante"],
            "sport": ["sport", "sportief", "sportieve", "athletic"],
            "sportief": ["sport", "sportief", "sportieve", "athletic"],
            "sportieve": ["sport", "sportief", "sportieve", "athletic"],
            
            # Sizes
            "klein": ["klein", "kleine", "s", "xs"],
            "kleine": ["klein", "kleine", "s", "xs"],
            "medium": ["medium", "m", "middel"],
            "middel": ["medium", "m", "middel"],
            "groot": ["groot", "grote", "l", "xl"],
            "grote": ["groot", "grote", "l", "xl"],
        }
        
        # Common typos and corrections
        self.typo_corrections = {
            "schoen": "schoenen",
            "jas": "jassen", 
            "shirt": "shirts",
            "broek": "broeken",
            "jurk": "jurken",
            "accessoire": "accessoires",
            "leder": "lederen",
            "wol": "wollen",
            "zijde": "zijden",
            "goedkoop": "goedkope",
            "duur": "dure",
            "betaalbaar": "betaalbare",
            "zwart": "zwarte",
            "wit": "witte",
            "blauw": "blauwe",
            "rood": "rode",
            "groen": "groene",
            "geel": "gele",
            "paars": "paarse",
            "grijs": "grijze",
            "bruin": "bruine",
            "zomer": "zomerse",
            "winter": "winterse",
            "lente": "lentese",
            "herfst": "herfstse",
            "casual": "casuele",
            "formeel": "formele",
            "sportief": "sportieve",
            "klein": "kleine",
            "groot": "grote",
        }
    
    def correct_query(self, query: str) -> Tuple[str, List[str]]:
        """
        Correct common typos and suggest alternatives.
        
        Args:
            query: Original search query
            
        Returns:
            Tuple of (corrected_query, suggestions)
        """
        if not query or len(query.strip()) < 2:
            return query, []
        
        original_query = query.lower().strip()
        words = original_query.split()
        corrected_words = []
        suggestions = []
        
        for word in words:
            # Check for exact synonyms
            if word in self.fashion_synonyms:
                corrected_words.append(word)
                suggestions.extend(self.fashion_synonyms[word][:3])  # Top 3 suggestions
                continue
            
            # Check for typo corrections
            if word in self.typo_corrections:
                corrected_word = self.typo_corrections[word]
                corrected_words.append(corrected_word)
                suggestions.append(corrected_word)
                continue
            
            # Check for fuzzy matches
            best_match = self._find_fuzzy_match(word)
            if best_match and best_match[1] > 0.8:  # High confidence threshold
                corrected_words.append(best_match[0])
                suggestions.append(best_match[0])
            else:
                corrected_words.append(word)
        
        corrected_query = " ".join(corrected_words)
        
        # Add query-level suggestions
        query_suggestions = self._generate_query_suggestions(original_query)
        suggestions.extend(query_suggestions)
        
        # Remove duplicates and limit
        suggestions = list(set(suggestions))[:5]
        
        return corrected_query, suggestions
    
    def _find_fuzzy_match(self, word: str) -> Optional[Tuple[str, float]]:
        """Find the best fuzzy match for a word."""
        best_match = None
        best_score = 0.0
        
        for correct_word in self.fashion_synonyms.keys():
            score = SequenceMatcher(None, word, correct_word).ratio()
            if score > best_score and score > 0.7:  # Minimum threshold
                best_score = score
                best_match = (correct_word, score)
        
        return best_match
    
    def _generate_query_suggestions(self, query: str) -> List[str]:
        """Generate query-level suggestions."""
        suggestions = []
        
        # Common query patterns
        if "goedkoop" in query or "goedkope" in query:
            suggestions.extend(["goedkope schoenen", "goedkope jas", "goedkope shirt"])
        
        if "duur" in query or "dure" in query:
            suggestions.extend(["dure schoenen", "dure jas", "exclusieve accessoires"])
        
        if "winter" in query:
            suggestions.extend(["winter jas", "winter schoenen", "winter accessoires"])
        
        if "zomer" in query:
            suggestions.extend(["zomer kleding", "zomer schoenen", "zomer jas"])
        
        if "casual" in query:
            suggestions.extend(["casual schoenen", "casual shirt", "casual broek"])
        
        if "sport" in query:
            suggestions.extend(["sport schoenen", "sport kleding", "sport jas"])
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word."""
        return self.fashion_synonyms.get(word.lower(), [])
    
    def expand_query(self, query: str) -> str:
        """Expand query with synonyms for better matching."""
        words = query.lower().split()
        expanded_words = []
        
        for word in words:
            synonyms = self.get_synonyms(word)
            if synonyms:
                # Add original word and top 2 synonyms
                expanded_words.append(word)
                expanded_words.extend(synonyms[:2])
            else:
                expanded_words.append(word)
        
        return " ".join(expanded_words)
    
    def calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries."""
        return SequenceMatcher(None, query1.lower(), query2.lower()).ratio()
    
    def is_typo(self, word: str) -> bool:
        """Check if a word is likely a typo."""
        return word in self.typo_corrections
    
    def get_correction(self, word: str) -> Optional[str]:
        """Get the correction for a typo."""
        return self.typo_corrections.get(word) 