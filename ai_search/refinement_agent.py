"""
Conversational Refinements Agent - AI-powered search refinement suggestions
Provides context-aware refinement suggestions after search results to improve user experience.
"""

import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefinementType(Enum):
    """Types of refinement suggestions"""
    PRICE = "price"
    STYLE = "style"
    BRAND = "brand"
    COLOR = "color"
    SIZE = "size"
    CATEGORY = "category"
    OCCASION = "occasion"
    SEASON = "season"
    MATERIAL = "material"
    FEATURE = "feature"

class RefinementPriority(Enum):
    """Priority levels for refinements"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RefinementSuggestion:
    """Individual refinement suggestion"""
    refinement_id: str
    type: RefinementType
    title: str
    description: str
    action: str
    confidence: float
    priority: RefinementPriority
    metadata: Dict[str, Any] = None

@dataclass
class RefinementContext:
    """Context for generating refinements"""
    search_query: str
    result_count: int
    avg_price: float
    price_range: Dict[str, float]
    categories: List[str]
    brands: List[str]
    colors: List[str]
    materials: List[str]
    user_behavior: Dict[str, Any] = None
    search_history: List[str] = None

@dataclass
class RefinementResponse:
    """Complete refinement response"""
    query_id: str
    search_query: str
    refinements: List[RefinementSuggestion]
    total_refinements: int
    primary_refinement: Optional[RefinementSuggestion]
    confidence_score: float
    generated_at: datetime
    metadata: Dict[str, Any] = None

class ConversationalRefinementAgent:
    """AI-powered refinement suggestion agent"""
    
    def __init__(self):
        self.refinement_templates = self._load_refinement_templates()
        self.context_patterns = self._load_context_patterns()
        self.behavior_weights = {
            "price_sensitive": 0.8,
            "brand_conscious": 0.6,
            "style_focused": 0.7,
            "budget_conscious": 0.9
        }
    
    def _load_refinement_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load refinement suggestion templates"""
        return {
            "price": [
                {
                    "title": "Toon goedkopere opties",
                    "description": "Vind vergelijkbare producten voor minder geld",
                    "action": "filter_price_lower",
                    "confidence_base": 0.8
                },
                {
                    "title": "Toon premium opties",
                    "description": "Ontdek hoogwaardige producten in hogere prijsklasse",
                    "action": "filter_price_higher",
                    "confidence_base": 0.6
                },
                {
                    "title": "Vergelijk prijzen",
                    "description": "Zie prijsverschillen tussen vergelijkbare producten",
                    "action": "compare_prices",
                    "confidence_base": 0.7
                }
            ],
            "style": [
                {
                    "title": "Toon sportieve varianten",
                    "description": "Ontdek sportieve en casual stijlen",
                    "action": "filter_style_sporty",
                    "confidence_base": 0.7
                },
                {
                    "title": "Toon elegante opties",
                    "description": "Vind formele en elegante stijlen",
                    "action": "filter_style_elegant",
                    "confidence_base": 0.6
                },
                {
                    "title": "Toon streetwear",
                    "description": "Ontdek moderne streetwear en urban stijlen",
                    "action": "filter_style_streetwear",
                    "confidence_base": 0.5
                }
            ],
            "brand": [
                {
                    "title": "Vergelijk met {brand}",
                    "description": "Zie alternatieven van andere merken",
                    "action": "compare_brands",
                    "confidence_base": 0.8
                },
                {
                    "title": "Toon meer {brand} producten",
                    "description": "Ontdek het volledige assortiment van dit merk",
                    "action": "filter_brand",
                    "confidence_base": 0.9
                }
            ],
            "color": [
                {
                    "title": "Toon meer kleuren",
                    "description": "Ontdek dit product in andere kleuren",
                    "action": "filter_colors",
                    "confidence_base": 0.8
                },
                {
                    "title": "Toon {color} varianten",
                    "description": "Vind vergelijkbare producten in {color}",
                    "action": "filter_color_specific",
                    "confidence_base": 0.7
                }
            ],
            "category": [
                {
                    "title": "Vergelijkbare categorieën",
                    "description": "Ontdek gerelateerde productcategorieën",
                    "action": "explore_categories",
                    "confidence_base": 0.6
                },
                {
                    "title": "Toon {category} producten",
                    "description": "Vind meer producten in deze categorie",
                    "action": "filter_category",
                    "confidence_base": 0.8
                }
            ],
            "occasion": [
                {
                    "title": "Perfect voor {occasion}",
                    "description": "Vind producten specifiek voor {occasion}",
                    "action": "filter_occasion",
                    "confidence_base": 0.7
                },
                {
                    "title": "Toon formele opties",
                    "description": "Ontdek formele en zakelijke stijlen",
                    "action": "filter_occasion_formal",
                    "confidence_base": 0.6
                }
            ]
        }
    
    def _load_context_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load context analysis patterns"""
        return {
            "price_sensitive": {
                "keywords": ["goedkoop", "betaalbaar", "korting", "sale", "budget"],
                "price_threshold": 50.0,
                "weight": 0.8
            },
            "brand_conscious": {
                "keywords": ["merk", "brand", "exclusief", "premium", "designer"],
                "weight": 0.6
            },
            "style_focused": {
                "keywords": ["stijl", "style", "trendy", "fashion", "mode"],
                "weight": 0.7
            },
            "budget_conscious": {
                "keywords": ["duur", "prijzig", "kostbaar", "luxe"],
                "price_threshold": 100.0,
                "weight": 0.9
            }
        }
    
    def generate_refinements(self, context: RefinementContext) -> RefinementResponse:
        """Generate context-aware refinement suggestions"""
        try:
            query_id = str(uuid.uuid4())
            refinements = []
            
            # Analyze context and user behavior
            behavior_analysis = self._analyze_user_behavior(context)
            context_score = self._calculate_context_score(context)
            
            # Generate refinements based on context
            refinements.extend(self._generate_price_refinements(context, behavior_analysis))
            refinements.extend(self._generate_style_refinements(context, behavior_analysis))
            refinements.extend(self._generate_brand_refinements(context))
            refinements.extend(self._generate_color_refinements(context))
            refinements.extend(self._generate_category_refinements(context))
            refinements.extend(self._generate_occasion_refinements(context))
            
            # Sort by confidence and priority
            refinements.sort(key=lambda x: (x.confidence, x.priority.value), reverse=True)
            
            # Limit to top refinements
            top_refinements = refinements[:5]
            
            # Calculate overall confidence
            confidence_score = sum(r.confidence for r in top_refinements) / len(top_refinements) if top_refinements else 0.0
            
            # Determine primary refinement
            primary_refinement = top_refinements[0] if top_refinements else None
            
            return RefinementResponse(
                query_id=query_id,
                search_query=context.search_query,
                refinements=top_refinements,
                total_refinements=len(top_refinements),
                primary_refinement=primary_refinement,
                confidence_score=confidence_score,
                generated_at=datetime.now(),
                metadata={
                    "behavior_analysis": behavior_analysis,
                    "context_score": context_score,
                    "total_generated": len(refinements)
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating refinements: {e}")
            return self._create_fallback_refinements(context)
    
    def _analyze_user_behavior(self, context: RefinementContext) -> Dict[str, float]:
        """Analyze user behavior patterns"""
        behavior_scores = {}
        query_lower = context.search_query.lower()
        
        for pattern_name, pattern_data in self.context_patterns.items():
            score = 0.0
            
            # Check keywords
            for keyword in pattern_data["keywords"]:
                if keyword in query_lower:
                    score += pattern_data["weight"]
            
            # Check price sensitivity
            if "price_threshold" in pattern_data:
                if context.avg_price > pattern_data["price_threshold"]:
                    score += pattern_data["weight"] * 0.5
            
            behavior_scores[pattern_name] = min(score, 1.0)
        
        return behavior_scores
    
    def _calculate_context_score(self, context: RefinementContext) -> float:
        """Calculate overall context relevance score"""
        score = 0.0
        
        # Result count factor
        if context.result_count > 0:
            score += min(context.result_count / 10.0, 0.3)
        
        # Price range factor
        if context.price_range:
            price_range = context.price_range.get("max", 0) - context.price_range.get("min", 0)
            if price_range > 0:
                score += min(price_range / 100.0, 0.2)
        
        # Diversity factors
        if context.categories:
            score += min(len(context.categories) / 5.0, 0.2)
        
        if context.brands:
            score += min(len(context.brands) / 3.0, 0.15)
        
        if context.colors:
            score += min(len(context.colors) / 5.0, 0.15)
        
        return min(score, 1.0)
    
    def _generate_price_refinements(self, context: RefinementContext, behavior: Dict[str, float]) -> List[RefinementSuggestion]:
        """Generate price-related refinements"""
        refinements = []
        
        # Check if price-sensitive behavior detected
        price_sensitive = behavior.get("price_sensitive", 0) > 0.5 or behavior.get("budget_conscious", 0) > 0.5
        
        if price_sensitive and context.avg_price > 50:
            # Suggest cheaper options
            template = self.refinement_templates["price"][0]
            refinements.append(RefinementSuggestion(
                refinement_id=str(uuid.uuid4()),
                type=RefinementType.PRICE,
                title=template["title"],
                description=template["description"],
                action=template["action"],
                confidence=template["confidence_base"] * 1.2,  # Boost for price sensitivity
                priority=RefinementPriority.HIGH,
                metadata={"price_sensitive": True, "current_avg_price": context.avg_price}
            ))
        
        # Suggest price comparison if multiple brands
        if len(context.brands) > 1:
            template = self.refinement_templates["price"][2]
            refinements.append(RefinementSuggestion(
                refinement_id=str(uuid.uuid4()),
                type=RefinementType.PRICE,
                title=template["title"],
                description=template["description"],
                action=template["action"],
                confidence=template["confidence_base"],
                priority=RefinementPriority.MEDIUM,
                metadata={"brand_count": len(context.brands)}
            ))
        
        return refinements
    
    def _generate_style_refinements(self, context: RefinementContext, behavior: Dict[str, float]) -> List[RefinementSuggestion]:
        """Generate style-related refinements"""
        refinements = []
        
        # Check if style-focused behavior detected
        style_focused = behavior.get("style_focused", 0) > 0.5
        
        if style_focused:
            # Suggest style variations
            for template in self.refinement_templates["style"]:
                refinements.append(RefinementSuggestion(
                    refinement_id=str(uuid.uuid4()),
                    type=RefinementType.STYLE,
                    title=template["title"],
                    description=template["description"],
                    action=template["action"],
                    confidence=template["confidence_base"] * 1.1,
                    priority=RefinementPriority.MEDIUM,
                    metadata={"style_focused": True}
                ))
        
        return refinements
    
    def _generate_brand_refinements(self, context: RefinementContext) -> List[RefinementSuggestion]:
        """Generate brand-related refinements"""
        refinements = []
        
        if context.brands:
            # Suggest brand comparison
            if len(context.brands) > 1:
                template = self.refinement_templates["brand"][0]
                for brand in context.brands[:2]:  # Top 2 brands
                    refinements.append(RefinementSuggestion(
                        refinement_id=str(uuid.uuid4()),
                        type=RefinementType.BRAND,
                        title=template["title"].format(brand=brand),
                        description=template["description"],
                        action=template["action"],
                        confidence=template["confidence_base"],
                        priority=RefinementPriority.MEDIUM,
                        metadata={"brand": brand}
                    ))
            
            # Suggest more products from top brand
            if context.brands:
                template = self.refinement_templates["brand"][1]
                top_brand = context.brands[0]
                refinements.append(RefinementSuggestion(
                    refinement_id=str(uuid.uuid4()),
                    type=RefinementType.BRAND,
                    title=template["title"].format(brand=top_brand),
                    description=template["description"],
                    action=template["action"],
                    confidence=template["confidence_base"],
                    priority=RefinementPriority.MEDIUM,
                    metadata={"brand": top_brand}
                ))
        
        return refinements
    
    def _generate_color_refinements(self, context: RefinementContext) -> List[RefinementSuggestion]:
        """Generate color-related refinements"""
        refinements = []
        
        if context.colors:
            # Suggest more colors
            template = self.refinement_templates["color"][0]
            refinements.append(RefinementSuggestion(
                refinement_id=str(uuid.uuid4()),
                type=RefinementType.COLOR,
                title=template["title"],
                description=template["description"],
                action=template["action"],
                confidence=template["confidence_base"],
                priority=RefinementPriority.MEDIUM,
                metadata={"available_colors": context.colors}
            ))
            
            # Suggest specific color variants
            if len(context.colors) > 1:
                template = self.refinement_templates["color"][1]
                for color in context.colors[:3]:  # Top 3 colors
                    refinements.append(RefinementSuggestion(
                        refinement_id=str(uuid.uuid4()),
                        type=RefinementType.COLOR,
                        title=template["title"].format(color=color),
                        description=template["description"].format(color=color),
                        action=template["action"],
                        confidence=template["confidence_base"] * 0.8,
                        priority=RefinementPriority.LOW,
                        metadata={"color": color}
                    ))
        
        return refinements
    
    def _generate_category_refinements(self, context: RefinementContext) -> List[RefinementSuggestion]:
        """Generate category-related refinements"""
        refinements = []
        
        if context.categories:
            # Suggest category exploration
            template = self.refinement_templates["category"][0]
            refinements.append(RefinementSuggestion(
                refinement_id=str(uuid.uuid4()),
                type=RefinementType.CATEGORY,
                title=template["title"],
                description=template["description"],
                action=template["action"],
                confidence=template["confidence_base"],
                priority=RefinementPriority.MEDIUM,
                metadata={"categories": context.categories}
            ))
            
            # Suggest specific category
            if context.categories:
                template = self.refinement_templates["category"][1]
                top_category = context.categories[0]
                refinements.append(RefinementSuggestion(
                    refinement_id=str(uuid.uuid4()),
                    type=RefinementType.CATEGORY,
                    title=template["title"].format(category=top_category),
                    description=template["description"],
                    action=template["action"],
                    confidence=template["confidence_base"],
                    priority=RefinementPriority.MEDIUM,
                    metadata={"category": top_category}
                ))
        
        return refinements
    
    def _generate_occasion_refinements(self, context: RefinementContext) -> List[RefinementSuggestion]:
        """Generate occasion-related refinements"""
        refinements = []
        
        # Analyze query for occasions
        query_lower = context.search_query.lower()
        occasions = {
            "bruiloft": "wedding",
            "feest": "party", 
            "werk": "work",
            "sport": "sport",
            "casual": "casual",
            "formele": "formal"
        }
        
        detected_occasions = []
        for dutch, english in occasions.items():
            if dutch in query_lower:
                detected_occasions.append(english)
        
        if detected_occasions:
            template = self.refinement_templates["occasion"][0]
            for occasion in detected_occasions:
                refinements.append(RefinementSuggestion(
                    refinement_id=str(uuid.uuid4()),
                    type=RefinementType.OCCASION,
                    title=template["title"].format(occasion=occasion),
                    description=template["description"].format(occasion=occasion),
                    action=template["action"],
                    confidence=template["confidence_base"],
                    priority=RefinementPriority.MEDIUM,
                    metadata={"occasion": occasion}
                ))
        
        return refinements
    
    def _create_fallback_refinements(self, context: RefinementContext) -> RefinementResponse:
        """Create fallback refinements when generation fails"""
        fallback_refinements = [
            RefinementSuggestion(
                refinement_id=str(uuid.uuid4()),
                type=RefinementType.CATEGORY,
                title="Ontdek meer categorieën",
                description="Vind gerelateerde productcategorieën",
                action="explore_categories",
                confidence=0.5,
                priority=RefinementPriority.MEDIUM
            ),
            RefinementSuggestion(
                refinement_id=str(uuid.uuid4()),
                type=RefinementType.STYLE,
                title="Toon verschillende stijlen",
                description="Ontdek verschillende stijlvarianten",
                action="filter_styles",
                confidence=0.4,
                priority=RefinementPriority.LOW
            )
        ]
        
        return RefinementResponse(
            query_id=str(uuid.uuid4()),
            search_query=context.search_query,
            refinements=fallback_refinements,
            total_refinements=len(fallback_refinements),
            primary_refinement=fallback_refinements[0],
            confidence_score=0.45,
            generated_at=datetime.now(),
            metadata={"fallback": True, "error": "Generation failed"}
        )
    
    def get_refinement_statistics(self) -> Dict[str, Any]:
        """Get refinement generation statistics"""
        return {
            "total_templates": sum(len(templates) for templates in self.refinement_templates.values()),
            "refinement_types": len(RefinementType),
            "context_patterns": len(self.context_patterns),
            "behavior_weights": self.behavior_weights
        }

# Global instance
refinement_agent = ConversationalRefinementAgent() 