#!/usr/bin/env python3
"""
Performance Dashboard

A Streamlit dashboard for visualizing search performance metrics, trends, and insights.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_base_builder import KnowledgeBaseBuilder
from benchmarks.continuous_benchmark import ContinuousBenchmarker

# Page configuration
st.set_page_config(
    page_title="Findly Search Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .success-card {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

class PerformanceDashboard:
    """Main dashboard class for search performance visualization."""
    
    def __init__(self, db_path: str = "search_knowledge_base.db"):
        self.db_path = db_path
        self.knowledge_builder = KnowledgeBaseBuilder(db_path)
        self.continuous_benchmarker = ContinuousBenchmarker(db_path=db_path)
    
    def load_benchmark_data(self, days: int = 7) -> pd.DataFrame:
        """Load benchmark data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        timestamp,
                        query,
                        score,
                        response_time,
                        result_count,
                        detected_intents,
                        complexity_score,
                        cache_hit,
                        price_filter_applied,
                        fallback_used,
                        avg_price_top5,
                        price_coherence,
                        diversity_score,
                        category_coverage,
                        conversion_potential,
                        primary_intent,
                        semantic_relevance,
                        contextual_relevance,
                        user_intent_alignment
                    FROM benchmark_history 
                    WHERE timestamp >= DATE('now', '-{} days')
                    ORDER BY timestamp DESC
                """.format(days)
                
                df = pd.read_sql_query(query, conn)
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Parse JSON columns
                if 'detected_intents' in df.columns:
                    df['detected_intents'] = df['detected_intents'].apply(
                        lambda x: json.loads(x) if x else {}
                    )
                
                return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def load_store_profiles(self) -> List[Dict]:
        """Load store profiles from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM store_profiles ORDER BY last_updated DESC"
                df = pd.read_sql_query(query, conn)
                return df.to_dict('records')
        except Exception as e:
            st.error(f"Error loading store profiles: {e}")
            return []
    
    def render_header(self):
        """Render dashboard header."""
        st.markdown('<h1 class="main-header">📊 Findly Search Performance Dashboard</h1>', unsafe_allow_html=True)
        
        # Sidebar filters
        st.sidebar.header("🔧 Dashboard Controls")
        
        # Date range selector
        days = st.sidebar.selectbox(
            "Time Period",
            [1, 3, 7, 14, 30],
            index=2,
            format_func=lambda x: f"Last {x} days"
        )
        
        # Store selector
        store_profiles = self.load_store_profiles()
        if store_profiles:
            store_ids = [profile['store_id'] for profile in store_profiles]
            selected_store = st.sidebar.selectbox("Store", store_ids)
        else:
            selected_store = None
        
        return days, selected_store
    
    def render_overview_metrics(self, df: pd.DataFrame):
        """Render overview metrics cards."""
        st.header("📈 Overview Metrics")
        
        if df.empty:
            st.warning("No data available for the selected period")
            return
        
        # Calculate metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_score = df['score'].mean()
            st.metric(
                label="Average Relevance Score",
                value=f"{avg_score:.3f}",
                delta=f"{avg_score - 0.7:.3f}" if avg_score > 0.7 else f"{avg_score - 0.7:.3f}"
            )
        
        with col2:
            avg_response_time = df['response_time'].mean()
            st.metric(
                label="Average Response Time",
                value=f"{avg_response_time:.3f}s",
                delta=f"{0.3 - avg_response_time:.3f}s" if avg_response_time < 0.3 else f"{0.3 - avg_response_time:.3f}s"
            )
        
        with col3:
            total_queries = len(df)
            st.metric(
                label="Total Queries",
                value=total_queries,
                delta=None
            )
        
        with col4:
            cache_hit_rate = df['cache_hit'].mean() * 100
            st.metric(
                label="Cache Hit Rate",
                value=f"{cache_hit_rate:.1f}%",
                delta=f"{cache_hit_rate - 60:.1f}%" if cache_hit_rate > 60 else f"{cache_hit_rate - 60:.1f}%"
            )
    
    def render_trend_charts(self, df: pd.DataFrame):
        """Render trend charts."""
        st.header("📊 Performance Trends")
        
        if df.empty:
            st.warning("No data available for trend analysis")
            return
        
        # Prepare data for charts
        df_daily = df.groupby(df['timestamp'].dt.date).agg({
            'score': 'mean',
            'response_time': 'mean',
            'result_count': 'mean',
            'price_coherence': 'mean',
            'diversity_score': 'mean'
        }).reset_index()
        
        df_daily['timestamp'] = pd.to_datetime(df_daily['timestamp'])
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Relevance Score Trend', 'Response Time Trend', 
                          'Price Coherence Trend', 'Diversity Score Trend'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Relevance Score Trend
        fig.add_trace(
            go.Scatter(x=df_daily['timestamp'], y=df_daily['score'], 
                      mode='lines+markers', name='Relevance Score'),
            row=1, col=1
        )
        
        # Response Time Trend
        fig.add_trace(
            go.Scatter(x=df_daily['timestamp'], y=df_daily['response_time'], 
                      mode='lines+markers', name='Response Time'),
            row=1, col=2
        )
        
        # Price Coherence Trend
        fig.add_trace(
            go.Scatter(x=df_daily['timestamp'], y=df_daily['price_coherence'], 
                      mode='lines+markers', name='Price Coherence'),
            row=2, col=1
        )
        
        # Diversity Score Trend
        fig.add_trace(
            go.Scatter(x=df_daily['timestamp'], y=df_daily['diversity_score'], 
                      mode='lines+markers', name='Diversity Score'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_intent_analysis(self, df: pd.DataFrame):
        """Render intent analysis charts."""
        st.header("🧠 Query Intent Analysis")
        
        if df.empty:
            st.warning("No data available for intent analysis")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Primary Intent Distribution
            if 'primary_intent' in df.columns:
                intent_counts = df['primary_intent'].value_counts()
                fig = px.pie(
                    values=intent_counts.values,
                    names=intent_counts.index,
                    title="Primary Intent Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Intent Performance
            if 'primary_intent' in df.columns:
                intent_performance = df.groupby('primary_intent')['score'].agg(['mean', 'count']).reset_index()
                intent_performance = intent_performance[intent_performance['count'] >= 3]  # Min 3 queries
                
                fig = px.bar(
                    intent_performance,
                    x='primary_intent',
                    y='mean',
                    title="Average Score by Intent Type",
                    labels={'mean': 'Average Score', 'primary_intent': 'Intent Type'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_quality_metrics(self, df: pd.DataFrame):
        """Render quality metrics analysis."""
        st.header("🎯 Quality Metrics")
        
        if df.empty:
            st.warning("No data available for quality analysis")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Relevance Scoring Comparison
            relevance_cols = ['score', 'semantic_relevance', 'contextual_relevance', 'user_intent_alignment']
            available_cols = [col for col in relevance_cols if col in df.columns]
            
            if available_cols:
                relevance_data = df[available_cols].mean()
                fig = px.bar(
                    x=relevance_data.index,
                    y=relevance_data.values,
                    title="Average Relevance Scores by Type",
                    labels={'x': 'Score Type', 'y': 'Average Score'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Performance Distribution
            fig = px.histogram(
                df,
                x='score',
                nbins=20,
                title="Score Distribution",
                labels={'score': 'Relevance Score', 'count': 'Number of Queries'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_worst_performing_queries(self, df: pd.DataFrame):
        """Render worst performing queries analysis."""
        st.header("🔴 Worst Performing Queries")
        
        if df.empty:
            st.warning("No data available for query analysis")
            return
        
        # Get worst performing queries
        worst_queries = df.nsmallest(10, 'score')[['query', 'score', 'response_time', 'result_count']]
        
        st.dataframe(
            worst_queries,
            column_config={
                "query": "Query",
                "score": st.column_config.NumberColumn("Score", format="%.3f"),
                "response_time": st.column_config.NumberColumn("Response Time (s)", format="%.3f"),
                "result_count": "Result Count"
            },
            hide_index=True
        )
    
    def render_filter_analysis(self, df: pd.DataFrame):
        """Render filter usage analysis."""
        st.header("🔍 Filter Usage Analysis")
        
        if df.empty:
            st.warning("No data available for filter analysis")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filter Usage Rates
            filter_metrics = {
                'Cache Hit Rate': df['cache_hit'].mean() * 100,
                'Price Filter Usage': df['price_filter_applied'].mean() * 100,
                'Fallback Usage': df['fallback_used'].mean() * 100
            }
            
            fig = px.bar(
                x=list(filter_metrics.keys()),
                y=list(filter_metrics.values()),
                title="Filter Usage Rates (%)",
                labels={'x': 'Filter Type', 'y': 'Usage Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Filter Performance Impact
            if 'price_filter_applied' in df.columns:
                filter_performance = df.groupby('price_filter_applied')['score'].agg(['mean', 'count']).reset_index()
                filter_performance['price_filter_applied'] = filter_performance['price_filter_applied'].map({True: 'Applied', False: 'Not Applied'})
                
                fig = px.bar(
                    filter_performance,
                    x='price_filter_applied',
                    y='mean',
                    title="Average Score by Price Filter Usage",
                    labels={'mean': 'Average Score', 'price_filter_applied': 'Price Filter'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_alerts_and_recommendations(self, df: pd.DataFrame):
        """Render alerts and recommendations."""
        st.header("🚨 Alerts & Recommendations")
        
        if df.empty:
            st.warning("No data available for analysis")
            return
        
        alerts = []
        recommendations = []
        
        # Check for performance issues
        avg_score = df['score'].mean()
        avg_response_time = df['response_time'].mean()
        cache_hit_rate = df['cache_hit'].mean()
        
        if avg_score < 0.6:
            alerts.append({
                "type": "warning",
                "title": "Low Average Relevance Score",
                "message": f"Average score is {avg_score:.3f}, below the target of 0.7"
            })
            recommendations.append("Consider improving search relevance algorithms")
        
        if avg_response_time > 0.5:
            alerts.append({
                "type": "warning",
                "title": "High Response Time",
                "message": f"Average response time is {avg_response_time:.3f}s, above the target of 0.3s"
            })
            recommendations.append("Optimize search performance and caching")
        
        if cache_hit_rate < 0.5:
            alerts.append({
                "type": "info",
                "title": "Low Cache Hit Rate",
                "message": f"Cache hit rate is {cache_hit_rate:.1%}, consider improving caching strategy"
            })
            recommendations.append("Implement better caching strategies")
        
        # Display alerts
        for alert in alerts:
            if alert["type"] == "warning":
                st.warning(f"**{alert['title']}**: {alert['message']}")
            else:
                st.info(f"**{alert['title']}**: {alert['message']}")
        
        # Display recommendations
        if recommendations:
            st.subheader("💡 Recommendations")
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
    
    def run_dashboard(self):
        """Run the main dashboard."""
        # Render header and get filters
        days, selected_store = self.render_header()
        
        # Load data
        df = self.load_benchmark_data(days)
        
        # Filter by store if selected
        if selected_store and not df.empty:
            # Note: This would need store_id column in the data
            pass
        
        # Render dashboard sections
        self.render_overview_metrics(df)
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Trends", "🧠 Intent Analysis", "🎯 Quality Metrics", 
            "🔴 Worst Queries", "🔍 Filter Analysis", "🚨 Alerts"
        ])
        
        with tab1:
            self.render_trend_charts(df)
        
        with tab2:
            self.render_intent_analysis(df)
        
        with tab3:
            self.render_quality_metrics(df)
        
        with tab4:
            self.render_worst_performing_queries(df)
        
        with tab5:
            self.render_filter_analysis(df)
        
        with tab6:
            self.render_alerts_and_recommendations(df)

def main():
    """Main function to run the dashboard."""
    st.title("Findly Search Performance Dashboard")
    
    # Initialize dashboard
    dashboard = PerformanceDashboard()
    
    # Run dashboard
    dashboard.run_dashboard()

if __name__ == "__main__":
    main() 