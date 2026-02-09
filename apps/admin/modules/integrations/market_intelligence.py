
# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False

"""
Market Intelligence Integration Module
=====================================

This module handles market intelligence data processing, analysis,
and visualization for the admin portal.
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


class MarketIntelligenceCenter:
    """Advanced Market Intelligence Center with real-time data analysis"""
    
    def __init__(self):
        """Initialize Market Intelligence Center with comprehensive data sources"""
        self.base_path = Path(__file__).resolve().parents[3]
        self.market_data = {}
        self.job_trends = None
        self.salary_forecasts = {}
        self.emerging_skills = []
        self.industry_growth = {}
        self.load_market_data()
    
    def load_market_data(self):
        """Load comprehensive market intelligence data from multiple sources"""
        try:
            # Load market intelligence from frontend data
            market_file = self.base_path / "frontend" / "market_intelligence.json"
            if market_file.exists():
                with open(market_file, 'r') as f:
                    self.market_data = json.load(f)
            else:
                self.market_data = self.get_default_market_data()
                self.save_market_data()
            
            # Generate dynamic data
            self.job_trends = self.generate_job_market_trends()
            self.salary_forecasts = self.generate_salary_forecasts()
            self.emerging_skills = self.generate_emerging_skills_data()
            self.industry_growth = self.generate_industry_growth_data()
            
        except Exception as e:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            st.error(f"Error loading market data: {str(e)}")
            self.market_data = self.get_default_market_data()
    
    def save_market_data(self):
        """Save market data to file"""
        try:
            market_file = self.base_path / "frontend" / "market_intelligence.json"
            os.makedirs(os.path.dirname(market_file), exist_ok=True)
            with open(market_file, 'w') as f:
                json.dump(self.market_data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving market data: {str(e)}")
    
    def get_default_market_data(self):
        """Default comprehensive market data"""
        return {
            "hot_skills_2025": {
                "AI/ML Engineering": {"growth_rate": 45, "avg_salary": 165000, "demand_score": 98},
                "Cybersecurity Specialist": {"growth_rate": 38, "avg_salary": 145000, "demand_score": 95},
                "Cloud Architecture": {"growth_rate": 42, "avg_salary": 155000, "demand_score": 92},
                "Data Engineering": {"growth_rate": 35, "avg_salary": 140000, "demand_score": 90},
                "DevOps Engineering": {"growth_rate": 32, "avg_salary": 135000, "demand_score": 88},
                "Full Stack Development": {"growth_rate": 28, "avg_salary": 120000, "demand_score": 85},
                "Product Management": {"growth_rate": 25, "avg_salary": 130000, "demand_score": 82},
                "UX/UI Design": {"growth_rate": 22, "avg_salary": 110000, "demand_score": 80}
            },
            "industry_insights": {
                "Technology": {"growth_projection": 28, "hiring_velocity": "Very High", "remote_friendly": 85},
                "Healthcare": {"growth_projection": 22, "hiring_velocity": "High", "remote_friendly": 45},
                "Finance": {"growth_projection": 18, "hiring_velocity": "Moderate", "remote_friendly": 70},
                "Manufacturing": {"growth_projection": 15, "hiring_velocity": "Moderate", "remote_friendly": 25},
                "Education": {"growth_projection": 12, "hiring_velocity": "Stable", "remote_friendly": 60}
            },
            "remote_work_trends": {
                "fully_remote": 35,
                "hybrid": 45,
                "on_site": 20
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def generate_job_market_trends(self):
        """Generate comprehensive job market trends for past 24 months"""
        base_date = datetime.now() - timedelta(days=730)
        trends_data = []
        
        for i in range(24):
            month_date = base_date + timedelta(days=i*30)
            trends_data.append({
                'month': month_date.strftime('%Y-%m'),
                'month_name': month_date.strftime('%B %Y'),
                'Technology': 100 + (i * 3) + random.randint(-5, 8),
                'Healthcare': 100 + (i * 2) + random.randint(-3, 5),
                'Finance': 100 + (i * 1.5) + random.randint(-2, 4),
                'Manufacturing': 100 + (i * 1) + random.randint(-2, 3),
                'Education': 100 + (i * 0.5) + random.randint(-1, 2),
                'total_jobs': 50000 + (i * 2000) + random.randint(-1000, 3000)
            })
        
        return trends_data
    
    def generate_salary_forecasts(self):
        """Generate salary forecasting data for key roles"""
        return {
            'AI/ML Engineer': {
                'current': 165000,
                'forecast_6m': 172000,
                'forecast_12m': 180000,
                'growth_rate': 9.1,
                'confidence': 85
            },
            'DevOps Engineer': {
                'current': 135000,
                'forecast_6m': 140000,
                'forecast_12m': 145000,
                'growth_rate': 7.4,
                'confidence': 80
            },
            'Data Engineer': {
                'current': 140000,
                'forecast_6m': 146000,
                'forecast_12m': 152000,
                'growth_rate': 8.6,
                'confidence': 82
            },
            'Cloud Architect': {
                'current': 155000,
                'forecast_6m': 162000,
                'forecast_12m': 170000,
                'growth_rate': 9.7,
                'confidence': 88
            },
            'Product Manager': {
                'current': 130000,
                'forecast_6m': 135000,
                'forecast_12m': 140000,
                'growth_rate': 7.7,
                'confidence': 75
            }
        }
    
    def generate_emerging_skills_data(self):
        """Generate emerging skills with trend analysis"""
        return [
            {"skill": "Generative AI", "growth_rate": 340, "adoption_rate": 68, "category": "Artificial Intelligence"},
            {"skill": "Kubernetes", "growth_rate": 180, "adoption_rate": 45, "category": "DevOps"},
            {"skill": "Vector Databases", "growth_rate": 220, "adoption_rate": 35, "category": "Data Engineering"},
            {"skill": "Edge Computing", "growth_rate": 150, "adoption_rate": 40, "category": "Cloud Computing"},
            {"skill": "WebAssembly", "growth_rate": 160, "adoption_rate": 25, "category": "Web Development"},
            {"skill": "Quantum Computing", "growth_rate": 120, "adoption_rate": 15, "category": "Advanced Computing"},
            {"skill": "MLOps", "growth_rate": 200, "adoption_rate": 55, "category": "Machine Learning"},
            {"skill": "Blockchain Development", "growth_rate": 90, "adoption_rate": 30, "category": "Distributed Systems"}
        ]
    
    def generate_industry_growth_data(self):
        """Generate industry-specific growth projections"""
        return {
            "Technology": {
                "current_size": 2.8e12,  # $2.8T
                "projected_growth": 0.15,
                "key_drivers": ["AI/ML", "Cloud Computing", "Cybersecurity"],
                "job_creation": 450000,
                "avg_salary_growth": 0.08
            },
            "Healthcare": {
                "current_size": 4.5e12,  # $4.5T
                "projected_growth": 0.12,
                "key_drivers": ["Digital Health", "Telemedicine", "Health Analytics"],
                "job_creation": 320000,
                "avg_salary_growth": 0.06
            },
            "Finance": {
                "current_size": 1.5e12,  # $1.5T
                "projected_growth": 0.08,
                "key_drivers": ["FinTech", "Digital Banking", "Cryptocurrency"],
                "job_creation": 180000,
                "avg_salary_growth": 0.05
            },
            "Manufacturing": {
                "current_size": 2.2e12,  # $2.2T
                "projected_growth": 0.05,
                "key_drivers": ["Industry 4.0", "IoT", "Automation"],
                "job_creation": 120000,
                "avg_salary_growth": 0.04
            }
        }
    
    def display_market_intelligence_dashboard(self):
        """Display comprehensive market intelligence dashboard"""
        st.markdown('<div class="section-header"><h2>📈 Market Intelligence Center</h2></div>', unsafe_allow_html=True)
        
        # Market overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔥 Hottest Skill", "AI/ML Engineering", "+45% growth")
        with col2:
            st.metric("💰 Top Salary", "$165K", "AI/ML Engineer")
        with col3:
            st.metric("🚀 Fastest Growing", "Technology", "+28% projection")
        with col4:
            st.metric("🏠 Remote Work", "80%", "Hybrid + Remote")
        
        # Tabs for different intelligence views
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Hot Skills", "📊 Job Trends", "💵 Salary Forecasts", "🌟 Emerging Skills", "🏭 Industry Growth"])
        
        with tab1:
            self.display_hot_skills_analysis()
        
        with tab2:
            self.display_job_market_trends()
        
        with tab3:
            self.display_salary_forecasting()
        
        with tab4:
            self.display_emerging_skills()
        
        with tab5:
            self.display_industry_growth()
    
    def display_hot_skills_analysis(self):
        """Display hot skills analysis with interactive charts"""
        st.subheader("🎯 Hot Skills for 2025")
        
        # Convert hot skills to DataFrame for better visualization
        skills_data = []
        for skill, data in self.market_data["hot_skills_2025"].items():
            skills_data.append({
                'Skill': skill,
                'Growth Rate (%)': data['growth_rate'],
                'Average Salary ($)': data['avg_salary'],
                'Demand Score': data['demand_score']
            })
        
        df_skills = pd.DataFrame(skills_data)
        
        # Interactive scatter plot
        fig = px.scatter(df_skills, 
                        x='Growth Rate (%)', 
                        y='Average Salary ($)',
                        size='Demand Score',
                        text='Skill',
                        title="Skills Growth vs Salary Matrix",
                        color='Demand Score',
                        color_continuous_scale='Viridis')
        
        fig.update_traces(textposition='top center')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Skills ranking table
        df_skills_sorted = df_skills.sort_values('Demand Score', ascending=False)
        st.subheader("📋 Skills Ranking by Demand Score")
        st.dataframe(df_skills_sorted, use_container_width=True)
    
    def display_job_market_trends(self):
        """Display job market trends with time series analysis"""
        st.subheader("📊 24-Month Job Market Trends")
        
        df_trends = pd.DataFrame(self.job_trends)
        
        # Multi-line chart for industry trends
        fig = go.Figure()
        
        industries = ['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Education']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        for industry, color in zip(industries, colors):
            fig.add_trace(go.Scatter(
                x=df_trends['month_name'],
                y=df_trends[industry],
                mode='lines+markers',
                name=industry,
                line=dict(color=color, width=3),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="Job Market Growth Trends by Industry",
            xaxis_title="Month",
            yaxis_title="Growth Index (Base: 100)",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Total jobs trend
        fig_total = px.area(df_trends, x='month_name', y='total_jobs',
                           title="Total Job Postings Trend",
                           labels={'total_jobs': 'Total Job Postings', 'month_name': 'Month'})
        fig_total.update_layout(height=300)
        st.plotly_chart(fig_total, use_container_width=True)
    
    def display_salary_forecasting(self):
        """Display salary forecasting with predictive analytics"""
        st.subheader("💵 Salary Forecasting & Predictions")
        
        # Salary forecast table
        forecast_data = []
        for role, data in self.salary_forecasts.items():
            forecast_data.append({
                'Role': role,
                'Current Salary': f"${data['current']:,}",
                '6M Forecast': f"${data['forecast_6m']:,}",
                '12M Forecast': f"${data['forecast_12m']:,}",
                'Growth Rate (%)': f"{data['growth_rate']:.1f}%",
                'Confidence': f"{data['confidence']}%"
            })
        
        df_forecast = pd.DataFrame(forecast_data)
        st.dataframe(df_forecast, use_container_width=True)
        
        # Salary progression chart
        fig_salary = go.Figure()
        
        for role, data in self.salary_forecasts.items():
            fig_salary.add_trace(go.Scatter(
                x=['Current', '6 Months', '12 Months'],
                y=[data['current'], data['forecast_6m'], data['forecast_12m']],
                mode='lines+markers',
                name=role,
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        fig_salary.update_layout(
            title="Salary Progression Forecasts",
            xaxis_title="Time Period",
            yaxis_title="Salary ($)",
            height=500
        )
        
        st.plotly_chart(fig_salary, use_container_width=True)
    
    def display_emerging_skills(self):
        """Display emerging skills with trend analysis"""
        st.subheader("🌟 Emerging Skills & Technologies")
        
        df_emerging = pd.DataFrame(self.emerging_skills)
        
        # Bubble chart for emerging skills
        fig_emerging = px.scatter(df_emerging,
                                 x='adoption_rate',
                                 y='growth_rate',
                                 size='growth_rate',
                                 color='category',
                                 text='skill',
                                 title="Emerging Skills: Adoption vs Growth Rate",
                                 labels={'adoption_rate': 'Adoption Rate (%)', 'growth_rate': 'Growth Rate (%)'})
        
        fig_emerging.update_traces(textposition='top center')
        fig_emerging.update_layout(height=500)
        st.plotly_chart(fig_emerging, use_container_width=True)
        
        # Skills by category
        category_stats = df_emerging.groupby('category').agg({
            'growth_rate': 'mean',
            'adoption_rate': 'mean',
            'skill': 'count'
        }).round(1)
        category_stats.columns = ['Avg Growth Rate (%)', 'Avg Adoption Rate (%)', 'Number of Skills']
        
        st.subheader("📊 Skills by Category")
        st.dataframe(category_stats, use_container_width=True)
    
    def display_industry_growth(self):
        """Display industry growth projections and analysis"""
        st.subheader("🏭 Industry Growth Projections")
        
        # Industry overview cards
        for industry, data in self.industry_growth.items():
            with st.expander(f"🏢 {industry} Industry Analysis"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Market Size", f"${data['current_size']/1e12:.1f}T")
                    st.metric("Growth Rate", f"{data['projected_growth']*100:.1f}%")
                
                with col2:
                    st.metric("Job Creation", f"{data['job_creation']:,}")
                    st.metric("Salary Growth", f"{data['avg_salary_growth']*100:.1f}%")
                
                with col3:
                    st.write("**Key Drivers:**")
                    for driver in data['key_drivers']:
                        st.write(f"• {driver}")
        
        # Industry comparison chart
        industries = list(self.industry_growth.keys())
        growth_rates = [data['projected_growth'] * 100 for data in self.industry_growth.values()]
        job_creation = [data['job_creation'] for data in self.industry_growth.values()]
        
        fig_industry = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Industry Growth Rates (%)', 'Job Creation Projections'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        fig_industry.add_trace(
            go.Bar(x=industries, y=growth_rates, name="Growth Rate (%)", marker_color='lightblue'),
            row=1, col=1
        )
        
        fig_industry.add_trace(
            go.Bar(x=industries, y=job_creation, name="Job Creation", marker_color='lightgreen'),
            row=1, col=2
        )
        
        fig_industry.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_industry, use_container_width=True)