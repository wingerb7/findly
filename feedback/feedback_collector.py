"""
Feedback Collector - User feedback collection and analysis system
Collects, stores, and analyzes user feedback to improve search performance.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of user feedback"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"

class FeedbackCategory(Enum):
    """Categories for feedback analysis"""
    PRICE = "price"
    RELEVANCE = "relevance"
    SPEED = "speed"
    UI_UX = "ui_ux"
    CONTENT = "content"
    OTHER = "other"

@dataclass
class FeedbackData:
    """Feedback data structure"""
    feedback_id: str
    query_id: str
    search_query: str
    feedback_type: FeedbackType
    feedback_category: FeedbackCategory
    feedback_text: str
    user_rating: Optional[int] = None
    suggested_improvement: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

@dataclass
class FeedbackAnalysis:
    """Analysis results for feedback"""
    total_feedback: int
    positive_ratio: float
    negative_ratio: float
    avg_rating: float
    top_categories: List[Dict[str, Any]]
    trending_issues: List[str]
    improvement_suggestions: List[str]
    satisfaction_score: float

class FeedbackCollector:
    """Main feedback collection and analysis system"""
    
    def __init__(self, db_path: str = "search_knowledge_base.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize feedback database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create feedback table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id TEXT PRIMARY KEY,
                        query_id TEXT NOT NULL,
                        search_query TEXT NOT NULL,
                        feedback_type TEXT NOT NULL,
                        feedback_category TEXT NOT NULL,
                        feedback_text TEXT NOT NULL,
                        user_rating INTEGER,
                        suggested_improvement TEXT,
                        user_agent TEXT,
                        ip_address TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT,
                        FOREIGN KEY (query_id) REFERENCES benchmark_history (query_id)
                    )
                """)
                
                # Create feedback_analysis table for aggregated insights
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        analysis_date DATE NOT NULL,
                        total_feedback INTEGER,
                        positive_ratio REAL,
                        negative_ratio REAL,
                        avg_rating REAL,
                        satisfaction_score REAL,
                        top_categories TEXT,
                        trending_issues TEXT,
                        improvement_suggestions TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_query_id ON feedback(query_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(feedback_category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)")
                
                conn.commit()
                logger.info("Feedback database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing feedback database: {e}")
            raise
    
    def collect_feedback(self, feedback_data: FeedbackData) -> bool:
        """Collect and store user feedback"""
        try:
            # Generate feedback ID if not provided
            if not feedback_data.feedback_id:
                feedback_data.feedback_id = str(uuid.uuid4())
            
            # Set timestamp if not provided
            if not feedback_data.timestamp:
                feedback_data.timestamp = datetime.now()
            
            # Anonymize sensitive data
            if feedback_data.ip_address:
                feedback_data.ip_address = self._anonymize_ip(feedback_data.ip_address)
            
            if feedback_data.user_agent:
                feedback_data.user_agent = self._sanitize_user_agent(feedback_data.user_agent)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO feedback (
                        feedback_id, query_id, search_query, feedback_type, 
                        feedback_category, feedback_text, user_rating, 
                        suggested_improvement, user_agent, ip_address, 
                        timestamp, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feedback_data.feedback_id,
                    feedback_data.query_id,
                    feedback_data.search_query,
                    feedback_data.feedback_type.value,
                    feedback_data.feedback_category.value,
                    feedback_data.feedback_text,
                    feedback_data.user_rating,
                    feedback_data.suggested_improvement,
                    feedback_data.user_agent,
                    feedback_data.ip_address,
                    feedback_data.timestamp.isoformat(),
                    json.dumps(feedback_data.metadata) if feedback_data.metadata else None
                ))
                
                conn.commit()
                logger.info(f"Feedback collected successfully: {feedback_data.feedback_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}")
            return False
    
    def get_feedback_by_query(self, query_id: str) -> List[FeedbackData]:
        """Retrieve feedback for a specific query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM feedback WHERE query_id = ? ORDER BY timestamp DESC
                """, (query_id,))
                
                rows = cursor.fetchall()
                feedback_list = []
                
                for row in rows:
                    feedback_data = FeedbackData(
                        feedback_id=row[0],
                        query_id=row[1],
                        search_query=row[2],
                        feedback_type=FeedbackType(row[3]),
                        feedback_category=FeedbackCategory(row[4]),
                        feedback_text=row[5],
                        user_rating=row[6],
                        suggested_improvement=row[7],
                        user_agent=row[8],
                        ip_address=row[9],
                        timestamp=datetime.fromisoformat(row[10]) if row[10] else None,
                        metadata=json.loads(row[11]) if row[11] else None
                    )
                    feedback_list.append(feedback_data)
                
                return feedback_list
                
        except Exception as e:
            logger.error(f"Error retrieving feedback: {e}")
            return []
    
    def analyze_feedback(self, days: int = 30) -> FeedbackAnalysis:
        """Analyze feedback patterns and trends"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total feedback count
                cursor.execute("""
                    SELECT COUNT(*) FROM feedback WHERE timestamp >= ?
                """, (cutoff_date.isoformat(),))
                total_feedback = cursor.fetchone()[0]
                
                if total_feedback == 0:
                    return FeedbackAnalysis(
                        total_feedback=0,
                        positive_ratio=0.0,
                        negative_ratio=0.0,
                        avg_rating=0.0,
                        top_categories=[],
                        trending_issues=[],
                        improvement_suggestions=[],
                        satisfaction_score=0.0
                    )
                
                # Get feedback type distribution
                cursor.execute("""
                    SELECT feedback_type, COUNT(*) FROM feedback 
                    WHERE timestamp >= ? GROUP BY feedback_type
                """, (cutoff_date.isoformat(),))
                type_counts = dict(cursor.fetchall())
                
                positive_count = type_counts.get(FeedbackType.POSITIVE.value, 0)
                negative_count = type_counts.get(FeedbackType.NEGATIVE.value, 0)
                
                positive_ratio = positive_count / total_feedback
                negative_ratio = negative_count / total_feedback
                
                # Get average rating
                cursor.execute("""
                    SELECT AVG(user_rating) FROM feedback 
                    WHERE timestamp >= ? AND user_rating IS NOT NULL
                """, (cutoff_date.isoformat(),))
                avg_rating = cursor.fetchone()[0] or 0.0
                
                # Get top categories
                cursor.execute("""
                    SELECT feedback_category, COUNT(*) as count 
                    FROM feedback WHERE timestamp >= ? 
                    GROUP BY feedback_category 
                    ORDER BY count DESC LIMIT 5
                """, (cutoff_date.isoformat(),))
                top_categories = [
                    {"category": row[0], "count": row[1], "percentage": row[1]/total_feedback*100}
                    for row in cursor.fetchall()
                ]
                
                # Get trending issues (negative feedback patterns)
                cursor.execute("""
                    SELECT feedback_text, COUNT(*) as count 
                    FROM feedback 
                    WHERE timestamp >= ? AND feedback_type = ? 
                    GROUP BY LOWER(feedback_text) 
                    ORDER BY count DESC LIMIT 10
                """, (cutoff_date.isoformat(), FeedbackType.NEGATIVE.value))
                trending_issues = [row[0] for row in cursor.fetchall()]
                
                # Get improvement suggestions
                cursor.execute("""
                    SELECT suggested_improvement, COUNT(*) as count 
                    FROM feedback 
                    WHERE timestamp >= ? AND suggested_improvement IS NOT NULL 
                    GROUP BY LOWER(suggested_improvement) 
                    ORDER BY count DESC LIMIT 10
                """, (cutoff_date.isoformat(),))
                improvement_suggestions = [row[0] for row in cursor.fetchall()]
                
                # Calculate satisfaction score (weighted average)
                satisfaction_score = (positive_ratio * 0.6) + (avg_rating / 5 * 0.4)
                
                return FeedbackAnalysis(
                    total_feedback=total_feedback,
                    positive_ratio=positive_ratio,
                    negative_ratio=negative_ratio,
                    avg_rating=avg_rating,
                    top_categories=top_categories,
                    trending_issues=trending_issues,
                    improvement_suggestions=improvement_suggestions,
                    satisfaction_score=satisfaction_score
                )
                
        except Exception as e:
            logger.error(f"Error analyzing feedback: {e}")
            return FeedbackAnalysis(
                total_feedback=0,
                positive_ratio=0.0,
                negative_ratio=0.0,
                avg_rating=0.0,
                top_categories=[],
                trending_issues=[],
                improvement_suggestions=[],
                satisfaction_score=0.0
            )
    
    def store_analysis(self, analysis: FeedbackAnalysis) -> bool:
        """Store feedback analysis results"""
        try:
            analysis_id = str(uuid.uuid4())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO feedback_analysis (
                        analysis_id, analysis_date, total_feedback, positive_ratio,
                        negative_ratio, avg_rating, satisfaction_score, top_categories,
                        trending_issues, improvement_suggestions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    datetime.now().date().isoformat(),
                    analysis.total_feedback,
                    analysis.positive_ratio,
                    analysis.negative_ratio,
                    analysis.avg_rating,
                    analysis.satisfaction_score,
                    json.dumps(analysis.top_categories),
                    json.dumps(analysis.trending_issues),
                    json.dumps(analysis.improvement_suggestions)
                ))
                
                conn.commit()
                logger.info(f"Feedback analysis stored: {analysis_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
            return False
    
    def get_improvement_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on feedback"""
        try:
            analysis = self.analyze_feedback(days=30)
            recommendations = []
            
            # Low satisfaction score
            if analysis.satisfaction_score < 0.6:
                recommendations.append("⚠️ User satisfaction is low - review search relevance and result quality")
            
            # High negative feedback ratio
            if analysis.negative_ratio > 0.3:
                recommendations.append("🔧 High negative feedback - investigate common issues and implement fixes")
            
            # Price-related issues
            price_issues = [cat for cat in analysis.top_categories if cat["category"] == FeedbackCategory.PRICE.value]
            if price_issues and price_issues[0]["percentage"] > 20:
                recommendations.append("💰 Price-related feedback is high - review price filtering and range detection")
            
            # Speed issues
            speed_issues = [cat for cat in analysis.top_categories if cat["category"] == FeedbackCategory.SPEED.value]
            if speed_issues and speed_issues[0]["percentage"] > 15:
                recommendations.append("⚡ Speed-related feedback - optimize search performance and caching")
            
            # Add specific suggestions from users
            if analysis.improvement_suggestions:
                recommendations.extend([
                    f"💡 User suggestion: {suggestion}" 
                    for suggestion in analysis.improvement_suggestions[:3]
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _anonymize_ip(self, ip_address: str) -> str:
        """Anonymize IP address for privacy"""
        if not ip_address:
            return None
        
        # Simple anonymization - keep only first two octets
        parts = ip_address.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        return ip_address
    
    def _sanitize_user_agent(self, user_agent: str) -> str:
        """Sanitize user agent string"""
        if not user_agent:
            return None
        
        # Remove potentially sensitive information
        sensitive_terms = ['password', 'token', 'key', 'secret']
        sanitized = user_agent.lower()
        
        for term in sensitive_terms:
            if term in sanitized:
                return "sanitized_user_agent"
        
        return user_agent[:200]  # Limit length
    
    def export_feedback_report(self, days: int = 30) -> Dict[str, Any]:
        """Export comprehensive feedback report"""
        try:
            analysis = self.analyze_feedback(days)
            
            report = {
                "report_date": datetime.now().isoformat(),
                "analysis_period_days": days,
                "summary": {
                    "total_feedback": analysis.total_feedback,
                    "satisfaction_score": analysis.satisfaction_score,
                    "positive_ratio": analysis.positive_ratio,
                    "negative_ratio": analysis.negative_ratio,
                    "avg_rating": analysis.avg_rating
                },
                "categories": analysis.top_categories,
                "trending_issues": analysis.trending_issues,
                "improvement_suggestions": analysis.improvement_suggestions,
                "recommendations": self.get_improvement_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error exporting feedback report: {e}")
            return {"error": str(e)}

# Global instance
feedback_collector = FeedbackCollector() 