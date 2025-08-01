#!/usr/bin/env python3
"""
Knowledge Base Service for building and managing AI knowledge bases.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from features.knowledge_base_builder import KnowledgeBaseBuilder
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Knowledge Base Builder not available - feature disabled")
    KnowledgeBaseBuilder = None

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """Service for building and managing AI knowledge bases."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get absolute path from project root
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(project_root, "data", "databases", "findly_consolidated.db")
        else:
            self.db_path = db_path
        self.knowledge_builder = None
        
        try:
            if KnowledgeBaseBuilder is not None:
                self.knowledge_builder = KnowledgeBaseBuilder(self.db_path)
                logger.info("Knowledge Base Service initialized successfully")
            else:
                logger.warning("Knowledge Base Builder not available - feature disabled")
        except Exception as e:
            logger.warning(f"Knowledge Base Service initialization failed: {e}")
    
    async def build_knowledge_base_async(self, store_id: str = None) -> Dict[str, Any]:
        """Build knowledge base for a specific store or all stores."""
        if not self.knowledge_builder:
            return {"error": "Knowledge Base Builder not available"}
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.knowledge_builder.build_knowledge_base,
                store_id
            )
            
            return {
                "success": True,
                "store_id": store_id,
                "knowledge_base_size": len(result) if isinstance(result, list) else 0,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to build knowledge base: {e}")
            return {"error": str(e)}
    
    async def get_store_insights_async(self, store_id: str) -> Dict[str, Any]:
        """Get insights for a specific store."""
        if not self.knowledge_builder:
            return {"error": "Knowledge Base Builder not available"}
        
        try:
            loop = asyncio.get_event_loop()
            insights = await loop.run_in_executor(
                None,
                self.knowledge_builder.get_store_insights,
                store_id
            )
            
            return {
                "success": True,
                "store_id": store_id,
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get store insights: {e}")
            return {"error": str(e)}
    
    async def update_knowledge_base_async(self, store_id: str = None) -> Dict[str, Any]:
        """Update knowledge base with new data."""
        if not self.knowledge_builder:
            return {"error": "Knowledge Base Builder not available"}
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.knowledge_builder.update_knowledge_base,
                store_id
            )
            
            return {
                "success": True,
                "store_id": store_id,
                "updated": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to update knowledge base: {e}")
            return {"error": str(e)}
    
    def is_available(self) -> bool:
        """Check if knowledge base service is available."""
        return self.knowledge_builder is not None 