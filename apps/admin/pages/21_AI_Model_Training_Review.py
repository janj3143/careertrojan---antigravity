"""
AI Model Training & Review Dashboard

This page provides comprehensive admin control over the AI training system:
- Overview of all training scenarios and their performance
- Create and manage training scenarios
- Train models with real IntelliCV data
- Review flagged predictions and provide corrections
- Monitor performance metrics and accuracy
- Control Neural Network, Expert System, and Feedback Loop engines

Created: October 14, 2025
Part of: Backend-Admin Reorientation Project - Phase 2
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
import statistics
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional offline
    BackendTelemetryHelper = None

# Add shared_backend to Python path for backend services
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent / "shared_backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


# Add paths for imports
backend_path = Path(__file__).parent.parent.parent / 'shared_backend'
sys.path.insert(0, str(backend_path))

try:
    from ai_engines.model_trainer import ModelTrainer, TrainingScenario
    from ai_engines.neural_network_engine import NeuralNetworkEngine
    from ai_engines.expert_system_engine import ExpertSystemEngine
    from ai_engines.feedback_loop_engine import FeedbackLoopEngine
    # Import ALL engines from UnifiedIntelliCVAIEngine for complete training
    from services.unified_ai_engine import (
        BayesianInferenceEngine,
        AdvancedNLPEngine,
        FuzzyLogicEngine,
        LLMIntegrationEngine,
        UnifiedIntelliCVAIEngine
    )
except ImportError as e:
    st.error("⚠️ Backend AI services not found. Make sure backend is properly set up.")
    st.stop()

# Page config
st.set_page_config(
    page_title="AI Model Training & Review",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
    }
    .error-card {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #dc3545;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page21_model_training") if BackendTelemetryHelper else None


# Initialize session state for ALL AI engines including FUSION and STATISTICAL
if 'model_trainer' not in st.session_state:
    st.session_state.model_trainer = None
if 'feedback_loop' not in st.session_state:
    st.session_state.feedback_loop = None
# Core engines
if 'expert_system' not in st.session_state:
    st.session_state.expert_system = None
if 'neural_network' not in st.session_state:
    st.session_state.neural_network = None
# Unified AI engines (6 total)
if 'bayesian_engine' not in st.session_state:
    st.session_state.bayesian_engine = None
if 'nlp_engine' not in st.session_state:
    st.session_state.nlp_engine = None
if 'fuzzy_engine' not in st.session_state:
    st.session_state.fuzzy_engine = None
if 'llm_engine' not in st.session_state:
    st.session_state.llm_engine = None
if 'unified_engine' not in st.session_state:
    st.session_state.unified_engine = None
# Statistical Analysis Engine
if 'statistical_engine' not in st.session_state:
    st.session_state.statistical_engine = None


def initialize_engines():
    """Initialize ALL AI engines including FUSION and STATISTICAL ANALYSIS for comprehensive training."""
    try:
        # Initialize Model Trainer
        if st.session_state.model_trainer is None:
            st.session_state.model_trainer = ModelTrainer()

        # Initialize Core AI Engines
        if st.session_state.neural_network is None:
            st.session_state.neural_network = NeuralNetworkEngine()

        if st.session_state.expert_system is None:
            st.session_state.expert_system = ExpertSystemEngine()

        # Initialize Unified AI Engines (from UnifiedIntelliCVAIEngine)
        if st.session_state.bayesian_engine is None:
            st.session_state.bayesian_engine = BayesianInferenceEngine()

        if st.session_state.nlp_engine is None:
            st.session_state.nlp_engine = AdvancedNLPEngine()

        if st.session_state.fuzzy_engine is None:
            st.session_state.fuzzy_engine = FuzzyLogicEngine()

        if st.session_state.llm_engine is None:
            st.session_state.llm_engine = LLMIntegrationEngine()

        if st.session_state.unified_engine is None:
            st.session_state.unified_engine = UnifiedIntelliCVAIEngine()

        # Initialize Statistical Analysis Engine (combines sklearn, scipy, statsmodels)
        if st.session_state.statistical_engine is None:
            try:
                from sklearn import ensemble, linear_model
                from scipy import stats as scipy_stats
                st.session_state.statistical_engine = {
                    'sklearn_available': True,
                    'scipy_available': True,
                    'models': ['RandomForest', 'GradientBoosting', 'LogisticRegression'],
                    'status': 'operational'
                }
                st.success("✅ Statistical Analysis Engine initialized (sklearn + scipy)")
            except ImportError:
                st.session_state.statistical_engine = {'status': 'unavailable'}

        # Initialize Feedback Loop and Register ALL Engines INCLUDING FUSION
        if st.session_state.feedback_loop is None:
            st.session_state.feedback_loop = FeedbackLoopEngine()

            # Register Core Engines
            st.session_state.feedback_loop.register_engine(
                'neural_network',
                st.session_state.neural_network,
                initial_weight=1.0
            )
            st.session_state.feedback_loop.register_engine(
                'expert_system',
                st.session_state.expert_system,
                initial_weight=0.95
            )

            # Register Unified AI Engines (FUSION happens here)
            st.session_state.feedback_loop.register_engine(
                'bayesian_inference',
                st.session_state.bayesian_engine,
                initial_weight=0.90
            )
            st.session_state.feedback_loop.register_engine(
                'advanced_nlp',
                st.session_state.nlp_engine,
                initial_weight=0.85
            )
            st.session_state.feedback_loop.register_engine(
                'fuzzy_logic',
                st.session_state.fuzzy_engine,
                initial_weight=0.80
            )
            st.session_state.feedback_loop.register_engine(
                'llm_integration',
                st.session_state.llm_engine,
                initial_weight=0.75
            )

            # Register FUSION engine (UnifiedAI combines all engines)
            st.session_state.feedback_loop.register_engine(
                'fusion_unified_ai',
                st.session_state.unified_engine,
                initial_weight=0.98  # High weight as it combines all engines
            )

            st.success("✅ Feedback Loop initialized with 7 engines + FUSION + Statistical Analysis")

        return True
    except Exception as e:
        st.error(f"Error initializing engines: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return False


def render_overview_tab():
    """Render the Overview tab."""
    st.header("🎯 AI Training System Overview")

    if not initialize_engines():
        return

    trainer = st.session_state.model_trainer

    # System Status Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_scenarios = len(trainer.scenarios)
        st.metric("Training Scenarios", total_scenarios)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        trained = len([s for s in trainer.scenarios.values() if s.status == 'trained'])
        st.metric("Trained Models", trained)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        pending_reviews = len(trainer.review_queue)
        st.metric("Pending Reviews", pending_reviews)
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        corrections = sum(len(s.corrections_applied) for s in trainer.scenarios.values())
        st.metric("Total Corrections", corrections)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # AI Engines Status - Show ALL 8 Engines (6 Base + Fusion + Statistical)
    st.subheader("🤖 AI Engines Status (8 Active Engines + FUSION)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**Core Engines**")
        st.markdown(f"✅ Neural Network: {'Initialized' if st.session_state.neural_network else 'Not loaded'}")
        st.markdown(f"✅ Expert System: {'Initialized' if st.session_state.expert_system else 'Not loaded'}")

    with col2:
        st.markdown("**Probabilistic & Analysis**")
        st.markdown(f"✅ Bayesian Inference: {'Initialized' if st.session_state.bayesian_engine else 'Not loaded'}")
        st.markdown(f"✅ Advanced NLP: {'Initialized' if st.session_state.nlp_engine else 'Not loaded'}")

    with col3:
        st.markdown("**Advanced Intelligence**")
        st.markdown(f"✅ Fuzzy Logic: {'Initialized' if st.session_state.fuzzy_engine else 'Not loaded'}")
        st.markdown(f"✅ LLM Integration: {'Initialized' if st.session_state.llm_engine else 'Not loaded'}")

    with col4:
        st.markdown("**Fusion & Statistical**")
        st.markdown(f"🔀 Unified AI (Fusion): {'Initialized' if st.session_state.unified_engine else 'Not loaded'}")
        stat_status = st.session_state.statistical_engine.get('status', 'unknown') if st.session_state.statistical_engine else 'Not loaded'
        st.markdown(f"📊 Statistical Analysis: {stat_status.title()}")

    # Feedback Loop Engine Weights
    if st.session_state.feedback_loop:
        st.markdown("**📊 Feedback Loop Engine Weights (Including FUSION)**")
        feedback_weights = {
            'Neural Network': 1.0,
            'Expert System': 0.95,
            'Bayesian Inference': 0.90,
            'Advanced NLP': 0.85,
            'Fuzzy Logic': 0.80,
            'LLM Integration': 0.75,
            'FUSION (UnifiedAI)': 0.98,
            'Statistical Analysis': 0.92
        }
        weights_df = pd.DataFrame(
            list(feedback_weights.items()),
            columns=['Engine', 'Initial Weight']
        )
        st.dataframe(weights_df, use_container_width=True, hide_index=True)

    st.divider()

    # Scenario Status Table
    st.subheader("📊 Training Scenario Status")

    scenario_data = []
    for scenario_id, scenario in trainer.scenarios.items():
        scenario_data.append({
            'Scenario ID': scenario_id,
            'Name': scenario.name,
            'Type': scenario.task_type,
            'Status': scenario.status,
            'Accuracy': f"{scenario.performance_metrics.get('accuracy', 0):.2%}",
            'Confidence': f"{scenario.config.get('confidence_threshold', 0):.2f}",
            'Model Version': scenario.model_version or 'Not trained'
        })

    if scenario_data:
        df = pd.DataFrame(scenario_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No training scenarios found. Create one in the 'Training Scenarios' tab.")

    st.divider()

    # Performance Charts
    st.subheader("📈 Performance Trends")

    col1, col2 = st.columns(2)

    with col1:
        # Accuracy by Scenario
        if scenario_data:
            fig = px.bar(
                df,
                x='Name',
                y='Accuracy',
                title='Accuracy by Scenario',
                color='Status',
                color_discrete_map={
                    'trained': '#28a745',
                    'training': '#ffc107',
                    'pending': '#6c757d',
                    'error': '#dc3545'
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Confidence Thresholds
        if scenario_data:
            fig = px.scatter(
                df,
                x='Name',
                y='Confidence',
                size=[50]*len(df),
                title='Confidence Thresholds',
                color='Type'
            )
            st.plotly_chart(fig, use_container_width=True)


def render_scenarios_tab():
    """Render the Training Scenarios tab."""
    st.header("🎓 Training Scenarios")

    if not initialize_engines():
        return

    trainer = st.session_state.model_trainer

    # Create New Scenario Section
    with st.expander("➕ Create New Training Scenario", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            scenario_id = st.text_input("Scenario ID", placeholder="e.g., custom_classifier_01")
            scenario_name = st.text_input("Scenario Name", placeholder="e.g., Custom Job Title Classifier")
            task_type = st.selectbox(
                "Task Type",
                ["neural_network", "bayesian", "hybrid", "fuzzy_logic"]
            )

        with col2:
            description = st.text_area(
                "Description",
                placeholder="Describe what this scenario will train..."
            )
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.75,
                step=0.05
            )

        if st.button("Create Scenario", type="primary"):
            if scenario_id and scenario_name:
                try:
                    scenario = TrainingScenario(
                        scenario_id=scenario_id,
                        name=scenario_name,
                        description=description,
                        task_type=task_type,
                        config={
                            'confidence_threshold': confidence_threshold,
                            'epochs': 10,
                            'batch_size': 32
                        }
                    )

                    if trainer.add_scenario(scenario):
                        st.success(f"✅ Created scenario: {scenario_name}")
                        st.rerun()
                    else:
                        st.error("Failed to create scenario")
                except Exception as e:
                    st.error(f"Error creating scenario: {e}")
            else:
                st.warning("Please fill in Scenario ID and Name")

    st.divider()

    # Existing Scenarios
    st.subheader("📚 Existing Scenarios")

    for scenario_id, scenario in trainer.scenarios.items():
        with st.expander(f"📊 {scenario.name} ({scenario_id})"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Status:**", scenario.status)
                st.write("**Type:**", scenario.task_type)
                st.write("**Version:**", scenario.model_version or "Not trained")

            with col2:
                st.write("**Accuracy:**", f"{scenario.performance_metrics.get('accuracy', 0):.2%}")
                st.write("**Precision:**", f"{scenario.performance_metrics.get('precision', 0):.2%}")
                st.write("**Recall:**", f"{scenario.performance_metrics.get('recall', 0):.2%}")

            with col3:
                st.write("**Confidence Threshold:**", scenario.config.get('confidence_threshold'))
                st.write("**Epochs:**", scenario.config.get('epochs', 10))
                st.write("**Batch Size:**", scenario.config.get('batch_size', 32))

            st.write("**Description:**", scenario.description)

            # Configuration
            st.write("**Configuration:**")
            st.json(scenario.config)

            # Corrections Applied
            if scenario.corrections_applied:
                st.write(f"**Corrections Applied:** {len(scenario.corrections_applied)}")
                with st.expander("View Corrections"):
                    for correction in scenario.corrections_applied[-10:]:  # Last 10
                        st.write(f"- {correction}")


def render_training_tab():
    """Render the Train Models tab."""
    st.header("🚀 Train Models")

    if not initialize_engines():
        return

    trainer = st.session_state.model_trainer

    # Select Scenario
    scenario_ids = list(trainer.scenarios.keys())

    if not scenario_ids:
        st.warning("No training scenarios available. Create one in the 'Training Scenarios' tab.")
        return

    selected_scenario = st.selectbox(
        "Select Scenario to Train",
        scenario_ids,
        format_func=lambda x: f"{trainer.scenarios[x].name} ({x})"
    )

    scenario = trainer.scenarios[selected_scenario]

    # Training Configuration
    st.subheader("⚙️ Training Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        epochs = st.number_input("Epochs", min_value=1, max_value=100, value=scenario.config.get('epochs', 10))

    with col2:
        batch_size = st.number_input("Batch Size", min_value=1, max_value=256, value=scenario.config.get('batch_size', 32))

    with col3:
        learning_rate = st.number_input("Learning Rate", min_value=0.0001, max_value=1.0, value=0.001, format="%.4f")

    # Training Data Preview
    st.subheader("📁 Training Data")

    try:
        training_data = trainer.load_training_data(selected_scenario)
        st.info(f"✅ Found {len(training_data)} training samples")

        if training_data:
            # Show sample
            with st.expander("Preview Sample Data"):
                st.json(training_data[0])
    except Exception as e:
        st.error(f"Error loading training data: {e}")
        training_data = []

    # Train Button
    st.divider()

    if st.button("🚀 Start Training", type="primary", disabled=len(training_data) == 0):
        with st.spinner(f"Training {scenario.name}..."):
            try:
                # Update config
                scenario.config.update({
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate
                })

                # Train
                result = trainer.train_scenario(selected_scenario)

                if result['status'] == 'success':
                    st.markdown(f"""
                    <div class="success-card">
                        <h3>✅ Training Complete!</h3>
                        <p><strong>Model Version:</strong> {result['model_version']}</p>
                        <p><strong>Accuracy:</strong> {result['metrics'].get('accuracy', 0):.2%}</p>
                        <p><strong>Training Samples:</strong> {result['training_samples']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show metrics
                    st.subheader("📊 Training Metrics")
                    metrics_df = pd.DataFrame([result['metrics']])
                    st.dataframe(metrics_df, use_container_width=True)
                else:
                    st.error(f"Training failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error during training: {e}")

    # Training History
    if scenario.performance_metrics:
        st.divider()
        st.subheader("📈 Training History")

        # Plot training metrics over time (if available)
        st.json(scenario.performance_metrics)


def render_review_tab():
    """Render the Review Queue tab."""
    st.header("🔍 Admin Review Queue")

    if not initialize_engines():
        return

    trainer = st.session_state.model_trainer

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_scenario = st.selectbox(
            "Filter by Scenario",
            ["All"] + list(trainer.scenarios.keys())
        )

    with col2:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "pending", "approved", "rejected"]
        )

    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Timestamp (Newest)", "Timestamp (Oldest)", "Confidence (Low to High)", "Confidence (High to Low)"]
        )

    st.divider()

    # Review Queue
    if not trainer.review_queue:
        st.info("🎉 No items in review queue! All predictions are confident.")
        return

    # Apply filters
    filtered_queue = trainer.review_queue.copy()

    if filter_scenario != "All":
        filtered_queue = [item for item in filtered_queue if item.get('scenario_id') == filter_scenario]

    if filter_status != "All":
        filtered_queue = [item for item in filtered_queue if item.get('status') == filter_status]

    # Sort
    if "Confidence" in sort_by:
        reverse = "High to Low" in sort_by
        filtered_queue.sort(key=lambda x: x.get('confidence', 0), reverse=reverse)
    else:
        reverse = "Newest" in sort_by
        filtered_queue.sort(key=lambda x: x.get('timestamp', ''), reverse=reverse)

    st.subheader(f"📋 Review Items ({len(filtered_queue)})")

    # Display review items
    for idx, item in enumerate(filtered_queue):
        prediction_id = item.get('prediction_id')
        scenario_id = item.get('scenario_id')
        prediction = item.get('prediction')
        confidence = item.get('confidence', 0)
        alternatives = item.get('alternatives', [])
        status = item.get('status', 'pending')
        flagged_reason = item.get('flagged_reason', 'Unknown')

        # Color code by confidence
        if confidence >= 0.7:
            card_class = "warning-card"
        elif confidence >= 0.5:
            card_class = "error-card"
        else:
            card_class = "error-card"

        with st.expander(f"{'✅' if status == 'approved' else '⚠️' if status == 'pending' else '❌'} {prediction_id} - {prediction} (Conf: {confidence:.2%})"):
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("**Scenario:**", scenario_id)
                st.write("**Prediction:**", prediction)
                st.write("**Confidence:**", f"{confidence:.2%}")
                st.write("**Status:**", status)
                st.write("**Flagged Reason:**", flagged_reason)

                if alternatives:
                    st.write("**Alternatives:**")
                    for alt in alternatives[:3]:
                        st.write(f"  - {alt['label']} ({alt['confidence']:.2%})")

            with col2:
                st.write("**Input Data:**")
                st.json(item.get('input_data', {}))

            st.markdown('</div>', unsafe_allow_html=True)

            # Admin Actions
            if status == 'pending':
                st.subheader("Admin Action")

                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    if st.button(f"✅ Approve", key=f"approve_{prediction_id}"):
                        result = trainer.admin_review_prediction(
                            prediction_id=prediction_id,
                            admin_decision='approve',
                            corrected_value=None
                        )
                        if result['status'] == 'success':
                            st.success("Approved!")
                            st.rerun()

                with action_col2:
                    correction = st.text_input(f"Correction for {prediction_id}", key=f"correction_{prediction_id}")
                    if st.button(f"📝 Correct", key=f"correct_{prediction_id}"):
                        if correction:
                            result = trainer.admin_review_prediction(
                                prediction_id=prediction_id,
                                admin_decision='correct',
                                corrected_value=correction
                            )
                            if result['status'] == 'success':
                                st.success("Correction applied and added to training data!")
                                st.rerun()
                        else:
                            st.warning("Please enter a correction")


def render_performance_tab():
    """Render the Performance Metrics tab."""
    st.header("📊 Performance Metrics & Analytics")

    if not initialize_engines():
        return

    trainer = st.session_state.model_trainer
    feedback_loop = st.session_state.feedback_loop
    expert_system = st.session_state.expert_system
    neural_network = st.session_state.neural_network

    # Overall System Performance
    st.subheader("🎯 Overall System Performance")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_predictions = sum(
            s.performance_metrics.get('total_predictions', 0)
            for s in trainer.scenarios.values()
        )
        st.metric("Total Predictions", total_predictions)

    with col2:
        avg_accuracy = statistics.mean([
            s.performance_metrics.get('accuracy', 0)
            for s in trainer.scenarios.values()
            if s.performance_metrics.get('accuracy', 0) > 0
        ]) if any(s.performance_metrics.get('accuracy', 0) > 0 for s in trainer.scenarios.values()) else 0
        st.metric("Average Accuracy", f"{avg_accuracy:.2%}")

    with col3:
        total_corrections = sum(
            len(s.corrections_applied)
            for s in trainer.scenarios.values()
        )
        st.metric("Total Corrections", total_corrections)

    with col4:
        pending_reviews = len(trainer.review_queue)
        st.metric("Pending Reviews", pending_reviews)

    st.divider()

    # Engine Performance
    st.subheader("🤖 Engine Performance")

    # Get feedback loop performance
    fb_report = feedback_loop.get_performance_report()

    engine_data = []
    for engine_name, perf in fb_report['engine_performance'].items():
        engine_data.append({
            'Engine': engine_name,
            'Accuracy': f"{perf['accuracy']:.2%}",
            'Avg Confidence': f"{perf['avg_confidence']:.2%}",
            'Total Predictions': perf['total_predictions'],
            'Weight': f"{fb_report['engine_weights'].get(engine_name, 1.0):.2f}"
        })

    if engine_data:
        df = pd.DataFrame(engine_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # Expert System Rules Performance
    st.subheader("⚖️ Expert System Rules")

    es_metrics = expert_system.get_performance_metrics()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Rules", es_metrics['total_rules'])
        st.metric("Enabled Rules", es_metrics['enabled_rules'])

    with col2:
        st.metric("Total Validations", es_metrics['total_validations'])
        st.metric("Rule Categories", len(es_metrics['categories']))

    # Most triggered rules
    if es_metrics['most_triggered_rules']:
        st.write("**Most Triggered Rules:**")
        rules_df = pd.DataFrame(es_metrics['most_triggered_rules'])
        st.dataframe(rules_df, use_container_width=True, hide_index=True)

    st.divider()

    # Neural Network Performance
    st.subheader("🧠 Neural Network Metrics")

    nn_metrics = neural_network.get_performance_metrics()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Predictions", nn_metrics['total_predictions'])

    with col2:
        st.metric("Feedback Buffer Size", nn_metrics['feedback_buffer_size'])

    with col3:
        st.metric("Embeddings Cached", nn_metrics['embeddings_cached'])


# Main App
def main():
    st.title("🤖 AI Model Training & Review Dashboard")

    st.markdown("""
    Control and monitor all AI training activities, review flagged predictions,
    and track performance across all engines (Neural Network, Expert System, Bayesian, NLP, LLM).
    """)

    if TELEMETRY_HELPER:
        TELEMETRY_HELPER.render_status_panel(
            title="🛰️ Backend Telemetry Monitor",
            refresh_key="page21_backend_refresh",
        )

    # Initialize engines
    if not initialize_engines():
        st.error("Failed to initialize AI engines. Check backend setup.")
        return

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🎓 Training Scenarios",
        "🚀 Train Models",
        "🔍 Review Queue",
        "📈 Performance"
    ])

    with tab1:
        render_overview_tab()

    with tab2:
        render_scenarios_tab()

    with tab3:
        render_training_tab()

    with tab4:
        render_review_tab()

    with tab5:
        render_performance_tab()


if __name__ == "__main__":
    main()
