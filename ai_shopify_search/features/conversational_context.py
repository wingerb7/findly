"""
Conversational Context Manager - Manages ongoing search conversations
Enables users to refine searches with natural language like "nee, duurder" or "meer blauw"
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SESSION_TTL = 3600  # 1 hour
DEFAULT_USER_SESSION_TTL = 86400  # 24 hours
DEFAULT_MAX_HISTORY = 10
DEFAULT_MAX_PRICE = 1000
DEFAULT_PRICE_MODIFIER = 0.2  # 20%
DEFAULT_LIMIT = 25
DEFAULT_MAX_LIMIT = 100
DEFAULT_MIN_LIMIT = 10

# Price modification factors
PRICE_INCREASE_FACTOR = 1.2
PRICE_DECREASE_FACTOR = 0.8

# Error Messages
ERROR_INTERPRETING_QUERY = "Error interpreting conversational query: {error}"
ERROR_APPLYING_MODIFICATION = "Error applying conversational modification: {error}"
ERROR_CLEANUP_SESSIONS = "Error cleaning up expired sessions: {error}"

# Logging Context Keys
LOG_CONTEXT_SESSION_ID = "session_id"
LOG_CONTEXT_USER_ID = "user_id"
LOG_CONTEXT_ACTION = "action"

class ConversationAction(Enum):
    """Types of conversation actions"""
    PRICE_UP = "price_up"
    PRICE_DOWN = "price_down"
    COLOR_CHANGE = "color_change"
    STYLE_CHANGE = "style_change"
    BRAND_CHANGE = "brand_change"
    CATEGORY_CHANGE = "category_change"
    QUANTITY_MORE = "quantity_more"
    QUANTITY_LESS = "quantity_less"
    MATERIAL_CHANGE = "material_change"
    GENERAL_REFINE = "general_refine"

@dataclass
class ConversationState:
    """Current state of a conversation"""
    session_id: str
    user_id: Optional[str] = None
    current_query: str = ""
    previous_query: str = ""
    current_filters: Dict[str, Any] = None
    previous_filters: Dict[str, Any] = None
    search_history: List[Dict[str, Any]] = None
    refinement_history: List[Dict[str, Any]] = None
    created_at: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.current_filters is None:
            self.current_filters = {}
        if self.previous_filters is None:
            self.previous_filters = {}
        if self.search_history is None:
            self.search_history = []
        if self.refinement_history is None:
            self.refinement_history = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()

class ConversationalContextManager:
    """Manages conversational search context using Redis"""
    
    def __init__(self, redis_client):
        """
        Initialize conversational context manager.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.session_ttl = DEFAULT_SESSION_TTL
        self.max_history = DEFAULT_MAX_HISTORY
    
    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"conversation:{session_id}"
    
    def _get_user_key(self, user_id: str) -> str:
        """Get Redis key for user sessions"""
        return f"user_conversations:{user_id}"
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        state = ConversationState(session_id=session_id, user_id=user_id)
        
        # Store in Redis
        session_key = self._get_session_key(session_id)
        self.redis.setex(
            session_key,
            self.session_ttl,
            json.dumps(asdict(state), default=str)
        )
        
        # Link to user if provided
        if user_id:
            user_key = self._get_user_key(user_id)
            self.redis.sadd(user_key, session_id)
            self.redis.expire(user_key, DEFAULT_USER_SESSION_TTL)  # 24 hours
        
        logger.info(f"Created conversation session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get conversation session state"""
        try:
            session_key = self._get_session_key(session_id)
            data = self.redis.get(session_key)
            
            if not data:
                return None
            
            state_dict = json.loads(data)
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in state_dict:
                state_dict['created_at'] = datetime.fromisoformat(state_dict['created_at'])
            if 'last_updated' in state_dict:
                state_dict['last_updated'] = datetime.fromisoformat(state_dict['last_updated'])
            
            return ConversationState(**state_dict)
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, **updates) -> bool:
        """Update conversation session state"""
        try:
            state = self.get_session(session_id)
            if not state:
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            
            # Update timestamp
            state.last_updated = datetime.now()
            
            # Store back to Redis
            session_key = self._get_session_key(session_id)
            self.redis.setex(
                session_key,
                self.session_ttl,
                json.dumps(asdict(state), default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def add_search_to_history(self, session_id: str, search_data: Dict[str, Any]) -> bool:
        """Add search result to conversation history"""
        try:
            state = self.get_session(session_id)
            if not state:
                return False
            
            # Add to history
            search_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": search_data.get("query", ""),
                "result_count": search_data.get("result_count", 0),
                "filters": search_data.get("filters", {}),
                "refinements": search_data.get("refinements", [])
            }
            
            state.search_history.append(search_entry)
            
            # Keep only recent history
            if len(state.search_history) > self.max_history:
                state.search_history = state.search_history[-self.max_history:]
            
            # Update session
            return self.update_session(
                session_id,
                search_history=state.search_history,
                current_query=search_data.get("query", ""),
                previous_query=state.current_query,
                current_filters=search_data.get("filters", {}),
                previous_filters=state.current_filters
            )
            
        except Exception as e:
            logger.error(f"Error adding search to history: {e}")
            return False
    
    def add_refinement_to_history(self, session_id: str, refinement_data: Dict[str, Any]) -> bool:
        """Add refinement action to conversation history"""
        try:
            state = self.get_session(session_id)
            if not state:
                return False
            
            # Add to refinement history
            refinement_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": refinement_data.get("action", ""),
                "refinement_id": refinement_data.get("refinement_id", ""),
                "user_feedback": refinement_data.get("user_feedback", ""),
                "applied_filters": refinement_data.get("applied_filters", {})
            }
            
            state.refinement_history.append(refinement_entry)
            
            # Keep only recent history
            if len(state.refinement_history) > self.max_history:
                state.refinement_history = state.refinement_history[-self.max_history:]
            
            # Update session
            return self.update_session(
                session_id,
                refinement_history=state.refinement_history
            )
            
        except Exception as e:
            logger.error(f"Error adding refinement to history: {e}")
            return False
    
    def _detect_price_modification(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """
        Detect price-related modifications in user input.
        
        Args:
            user_input_lower: Lowercase user input
            
        Returns:
            Price modification data or None
        """
        if any(word in user_input_lower for word in ["duurder", "hoger", "boven", "meer geld"]):
            return {
                "action": ConversationAction.PRICE_UP.value,
                "modification": "increase_price"
            }
        elif any(word in user_input_lower for word in ["goedkoper", "lager", "onder", "minder geld"]):
            return {
                "action": ConversationAction.PRICE_DOWN.value,
                "modification": "decrease_price"
            }
        return None
    
    def _detect_color_modification(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """
        Detect color-related modifications in user input.
        
        Args:
            user_input_lower: Lowercase user input
            
        Returns:
            Color modification data or None
        """
        colors = ["rood", "blauw", "groen", "geel", "zwart", "wit", "grijs", "bruin", "paars", "oranje"]
        for color in colors:
            if color in user_input_lower:
                return {
                    "action": ConversationAction.COLOR_CHANGE.value,
                    "modification": "set_color",
                    "color": color
                }
        return None
    
    def _detect_quantity_modification(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """
        Detect quantity-related modifications in user input.
        
        Args:
            user_input_lower: Lowercase user input
            
        Returns:
            Quantity modification data or None
        """
        if any(word in user_input_lower for word in ["meer", "extra", "meer resultaten"]):
            return {
                "action": ConversationAction.QUANTITY_MORE.value,
                "modification": "increase_limit"
            }
        elif any(word in user_input_lower for word in ["minder", "weinig", "minder resultaten"]):
            return {
                "action": ConversationAction.QUANTITY_LESS.value,
                "modification": "decrease_limit"
            }
        return None
    
    def _detect_style_modification(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """
        Detect style-related modifications in user input.
        
        Args:
            user_input_lower: Lowercase user input
            
        Returns:
            Style modification data or None
        """
        styles = ["sportief", "casual", "elegant", "formeel", "streetwear", "minimalistisch"]
        for style in styles:
            if style in user_input_lower:
                return {
                    "action": ConversationAction.STYLE_CHANGE.value,
                    "modification": "set_style",
                    "style": style
                }
        return None
    
    def _detect_brand_modification(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """
        Detect brand-related modifications in user input.
        
        Args:
            user_input_lower: Lowercase user input
            
        Returns:
            Brand modification data or None
        """
        brands = ["nike", "adidas", "puma", "reebok", "zara", "h&m", "mango"]
        for brand in brands:
            if brand in user_input_lower:
                return {
                    "action": ConversationAction.BRAND_CHANGE.value,
                    "modification": "set_brand",
                    "brand": brand
                }
        return None
    
    def _detect_general_refinement(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """
        Detect general refinement modifications in user input.
        
        Args:
            user_input_lower: Lowercase user input
            
        Returns:
            General refinement data or None
        """
        if any(word in user_input_lower for word in ["nee", "niet", "anders", "iets anders"]):
            return {
                "action": ConversationAction.GENERAL_REFINE.value,
                "modification": "general_refine"
            }
        return None
    
    def interpret_conversational_query(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Interpret conversational input like 'nee, duurder' or 'meer blauw'"""
        try:
            state = self.get_session(session_id)
            if not state:
                return {"action": "new_search", "query": user_input}
            
            user_input_lower = user_input.lower().strip()
            
            # Detect price modification
            price_mod = self._detect_price_modification(user_input_lower)
            if price_mod:
                return price_mod
            
            # Detect color modification
            color_mod = self._detect_color_modification(user_input_lower)
            if color_mod:
                return color_mod
            
            # Detect quantity modification
            quantity_mod = self._detect_quantity_modification(user_input_lower)
            if quantity_mod:
                return quantity_mod
            
            # Detect style modification
            style_mod = self._detect_style_modification(user_input_lower)
            if style_mod:
                return style_mod
            
            # Detect brand modification
            brand_mod = self._detect_brand_modification(user_input_lower)
            if brand_mod:
                return brand_mod
            
            # Detect general refinement
            general_refine = self._detect_general_refinement(user_input_lower)
            if general_refine:
                return general_refine
            
            # Default: treat as new search
            return {
                "action": "new_search",
                "query": user_input,
                "current_filters": state.current_filters
            }
            
        except Exception as e:
            logger.error(f"Error interpreting conversational query: {e}")
            return {"action": "new_search", "query": user_input}
    
    def _apply_price_modification(self, new_filters: Dict[str, Any], modification: Dict[str, Any]) -> None:
        """
        Apply price modification to filters.
        
        Args:
            new_filters: Filters to modify
            modification: Modification data
        """
        if modification.get("modification") == "increase_price":
            current_max = new_filters.get("max_price", DEFAULT_MAX_PRICE)
            new_filters["max_price"] = int(current_max * PRICE_INCREASE_FACTOR)
            new_filters["price_modified"] = True
        elif modification.get("modification") == "decrease_price":
            current_max = new_filters.get("max_price", DEFAULT_MAX_PRICE)
            new_filters["max_price"] = int(current_max * PRICE_DECREASE_FACTOR)
            new_filters["price_modified"] = True
    
    def _apply_color_modification(self, new_filters: Dict[str, Any], modification: Dict[str, Any]) -> None:
        """
        Apply color modification to filters.
        
        Args:
            new_filters: Filters to modify
            modification: Modification data
        """
        if modification.get("modification") == "set_color":
            new_filters["color"] = modification.get("color")
            new_filters["color_modified"] = True
    
    def _apply_style_modification(self, new_filters: Dict[str, Any], modification: Dict[str, Any]) -> None:
        """
        Apply style modification to filters.
        
        Args:
            new_filters: Filters to modify
            modification: Modification data
        """
        if modification.get("modification") == "set_style":
            new_filters["style"] = modification.get("style")
            new_filters["style_modified"] = True
    
    def _apply_brand_modification(self, new_filters: Dict[str, Any], modification: Dict[str, Any]) -> None:
        """
        Apply brand modification to filters.
        
        Args:
            new_filters: Filters to modify
            modification: Modification data
        """
        if modification.get("modification") == "set_brand":
            new_filters["brand"] = modification.get("brand")
            new_filters["brand_modified"] = True
    
    def _apply_quantity_modification(self, new_filters: Dict[str, Any], modification: Dict[str, Any]) -> None:
        """
        Apply quantity modification to filters.
        
        Args:
            new_filters: Filters to modify
            modification: Modification data
        """
        if modification.get("modification") == "increase_limit":
            current_limit = new_filters.get("limit", DEFAULT_LIMIT)
            new_filters["limit"] = min(current_limit * 2, DEFAULT_MAX_LIMIT)
            new_filters["limit_modified"] = True
        elif modification.get("modification") == "decrease_limit":
            current_limit = new_filters.get("limit", DEFAULT_LIMIT)
            new_filters["limit"] = max(current_limit // 2, DEFAULT_MIN_LIMIT)
            new_filters["limit_modified"] = True
    
    def apply_conversational_modification(self, current_filters: Dict[str, Any], modification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply conversational modification to current filters.
        
        Args:
            current_filters: Current filter state
            modification: Modification to apply
            
        Returns:
            Modified filters
        """
        try:
            new_filters = current_filters.copy()
            
            # Apply price modification
            self._apply_price_modification(new_filters, modification)
            
            # Apply color modification
            self._apply_color_modification(new_filters, modification)
            
            # Apply style modification
            self._apply_style_modification(new_filters, modification)
            
            # Apply brand modification
            self._apply_brand_modification(new_filters, modification)
            
            # Apply quantity modification
            self._apply_quantity_modification(new_filters, modification)
            
            return new_filters
            
        except Exception as e:
            logger.error(ERROR_APPLYING_MODIFICATION.format(error=str(e)))
            return current_filters
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (called periodically)"""
        try:
            # This would be implemented with Redis SCAN for production
            # For now, we rely on Redis TTL
            return 0
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0 

# Global instance
conversational_context_manager = ConversationalContextManager(None)

# TODO: Future Improvements and Recommendations
"""
TODO: Future Improvements and Recommendations

## 🔄 Module Opsplitsing
- [ ] Split into separate modules:
  - `conversation_state.py` - Conversation state management
  - `conversation_actions.py` - Conversation action definitions
  - `query_interpreter.py` - Query interpretation logic
  - `filter_modifier.py` - Filter modification logic
  - `session_manager.py` - Session management and Redis operations
  - `conversation_orchestrator.py` - Main conversation orchestration

## 🗑️ Functies voor Verwijdering
- [ ] `cleanup_expired_sessions()` - Consider moving to a dedicated cleanup service
- [ ] `get_session()` - Consider moving to a dedicated session service
- [ ] `update_session()` - Consider moving to a dedicated session service
- [ ] `add_search_to_history()` - Consider moving to a dedicated history service

## ⚡ Performance Optimalisaties
- [ ] Implement caching for frequently accessed sessions
- [ ] Add batch processing for multiple session operations
- [ ] Implement parallel processing for query interpretation
- [ ] Optimize Redis operations for large datasets
- [ ] Add indexing for frequently accessed patterns

## 🏗️ Architectuur Verbeteringen
- [ ] Implement proper dependency injection
- [ ] Add configuration management for different environments
- [ ] Implement proper error recovery mechanisms
- [ ] Add comprehensive unit and integration tests
- [ ] Implement proper logging strategy with structured logging

## 🔧 Code Verbeteringen
- [ ] Add type hints for all methods
- [ ] Implement proper error handling with custom exceptions
- [ ] Add comprehensive docstrings for all methods
- [ ] Implement proper validation for input parameters
- [ ] Add proper constants for all magic numbers

## 📊 Monitoring en Observability
- [ ] Add comprehensive metrics collection
- [ ] Implement proper distributed tracing
- [ ] Add health checks for the service
- [ ] Implement proper alerting mechanisms
- [ ] Add performance monitoring

## 🔒 Security Verbeteringen
- [ ] Implement proper authentication and authorization
- [ ] Add input validation and sanitization
- [ ] Implement proper secrets management
- [ ] Add audit logging for sensitive operations
- [ ] Implement proper data encryption

## 🧪 Testing Verbeteringen
- [ ] Add unit tests for all helper methods
- [ ] Implement integration tests for session management
- [ ] Add performance tests for large datasets
- [ ] Implement proper mocking strategies
- [ ] Add end-to-end tests for complete conversation flow

## 📚 Documentatie Verbeteringen
- [ ] Add comprehensive API documentation
- [ ] Implement proper code examples
- [ ] Add troubleshooting guides
- [ ] Implement proper changelog management
- [ ] Add architecture decision records (ADRs)

## 🎯 Specifieke Verbeteringen
- [ ] Refactor large query interpretation methods into smaller, more focused ones
- [ ] Implement proper error handling for session operations
- [ ] Add retry mechanisms for failed operations
- [ ] Implement proper caching strategies
- [ ] Add support for different output formats
- [ ] Implement proper progress tracking
- [ ] Add support for custom conversation patterns
- [ ] Implement proper result aggregation
- [ ] Add support for different data sources
- [ ] Implement proper result validation
- [ ] Add support for real-time conversation updates
- [ ] Implement proper data versioning
- [ ] Add support for conversation comparison
- [ ] Implement proper data export functionality
- [ ] Add support for conversation templates
- [ ] Implement proper A/B testing for conversation patterns
- [ ] Add support for personalized conversations
- [ ] Implement proper feedback collection
- [ ] Add support for conversation analytics
- [ ] Implement proper conversation ranking
""" 