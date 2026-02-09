"""
ðŸ‘¨â€ðŸ« Expert Systems Builder Module
===================================
Builds all expert system types:
- Rule-based inference engines
- Forward/Backward chaining
- Fuzzy expert systems
- Case-based reasoning
- Knowledge graphs
"""

import sys
import os
import logging
from pathlib import Path
import json
import numpy as np
from datetime import datetime

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


class ExpertSystemBuilder:
    """Comprehensive expert system builder"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.data_path = Path(r"L:\antigravity_version_ai_data_final\ai_data_final")
        self.models_path = self.base_path / "trained_models" / "expert"
        self.models_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Expert Systems Builder initialized")
        logger.info(f"Systems will be saved to: {self.models_path}")

    def build_rule_engine(self):
        """Build rule-based inference engine"""
        logger.info("\nðŸ‘¨â€ðŸ« Building Rule-Based Inference Engine...")

        try:
            rules = {
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "description": "IntelliCV Candidate Assessment Rules"
                },
                "rules": [
                    {
                        "id": "R001",
                        "name": "Senior Level Assessment",
                        "condition": {
                            "AND": [
                                {"experience_years": {">=": 10}},
                                {"skills_count": {">=": 15}},
                                {"has_management": True}
                            ]
                        },
                        "action": {"seniority_level": "Senior", "confidence": 0.95}
                    },
                    {
                        "id": "R002",
                        "name": "Mid Level Assessment",
                        "condition": {
                            "AND": [
                                {"experience_years": {">=": 5, "<": 10}},
                                {"skills_count": {">=": 8}}
                            ]
                        },
                        "action": {"seniority_level": "Mid", "confidence": 0.85}
                    },
                    {
                        "id": "R003",
                        "name": "Junior Level Assessment",
                        "condition": {
                            "AND": [
                                {"experience_years": {"<": 5}},
                                {"education_count": {">=": 1}}
                            ]
                        },
                        "action": {"seniority_level": "Junior", "confidence": 0.80}
                    },
                    {
                        "id": "R004",
                        "name": "Technical Role Fit",
                        "condition": {
                            "AND": [
                                {"has_technical_skills": True},
                                {"skills_count": {">=": 10}}
                            ]
                        },
                        "action": {"role_fit": "Technical", "confidence": 0.90}
                    },
                    {
                        "id": "R005",
                        "name": "Management Role Fit",
                        "condition": {
                            "AND": [
                                {"has_management": True},
                                {"experience_years": {">=": 7}}
                            ]
                        },
                        "action": {"role_fit": "Management", "confidence": 0.88}
                    },
                    {
                        "id": "R006",
                        "name": "High Potential Candidate",
                        "condition": {
                            "OR": [
                                {
                                    "AND": [
                                        {"education_count": {">=": 2}},
                                        {"has_technical_skills": True}
                                    ]
                                },
                                {
                                    "AND": [
                                        {"experience_years": {">=": 8}},
                                        {"skills_count": {">=": 15}}
                                    ]
                                }
                            ]
                        },
                        "action": {"potential": "High", "confidence": 0.92}
                    },
                    {
                        "id": "R007",
                        "name": "Career Progression Indicator",
                        "condition": {
                            "AND": [
                                {"experience_years": {">=": 3}},
                                {"education_count": {">=": 1}},
                                {"skills_count": {">=": 5}}
                            ]
                        },
                        "action": {"career_trajectory": "Positive", "confidence": 0.85}
                    },
                    {
                        "id": "R008",
                        "name": "Specialist Profile",
                        "condition": {
                            "AND": [
                                {"has_technical_skills": True},
                                {"skills_count": {">=": 20}},
                                {"experience_years": {">=": 5}}
                            ]
                        },
                        "action": {"profile_type": "Specialist", "confidence": 0.93}
                    },
                    {
                        "id": "R009",
                        "name": "Generalist Profile",
                        "condition": {
                            "AND": [
                                {"skills_count": {">=": 10, "<": 20}},
                                {"experience_years": {">=": 3}}
                            ]
                        },
                        "action": {"profile_type": "Generalist", "confidence": 0.80}
                    },
                    {
                        "id": "R010",
                        "name": "Education Strong Indicator",
                        "condition": {
                            "AND": [
                                {"education_count": {">=": 2}},
                                {"has_degree": True}
                            ]
                        },
                        "action": {"education_strength": "Strong", "confidence": 0.87}
                    }
                ],
                "inference_strategy": {
                    "type": "forward_chaining",
                    "priority": "confidence_weighted",
                    "conflict_resolution": "highest_confidence"
                }
            }

            # Save rule engine
            with open(self.models_path / "rule_engine.json", 'w') as f:
                json.dump(rules, f, indent=2)

            logger.info(f"âœ… Rule Engine built with {len(rules['rules'])} rules")
            return {'num_rules': len(rules['rules']), 'strategy': 'forward_chaining'}

        except Exception as e:
            logger.error(f"âŒ Rule Engine build failed: {e}")
            return None

    def build_forward_chaining_engine(self):
        """Build forward chaining inference engine"""
        logger.info("\nðŸ‘¨â€ðŸ« Building Forward Chaining Engine...")

        try:
            forward_chain = {
                "metadata": {
                    "type": "forward_chaining",
                    "description": "Data-driven inference from facts to conclusions"
                },
                "working_memory": [],
                "production_rules": [
                    {
                        "rule_id": "FC001",
                        "IF": ["experience >= 10", "technical_skills = true"],
                        "THEN": ["senior_technical_expert = true"]
                    },
                    {
                        "rule_id": "FC002",
                        "IF": ["senior_technical_expert = true", "management_experience = true"],
                        "THEN": ["technical_leader = true"]
                    },
                    {
                        "rule_id": "FC003",
                        "IF": ["education_level >= bachelor", "experience >= 5"],
                        "THEN": ["mid_level_professional = true"]
                    },
                    {
                        "rule_id": "FC004",
                        "IF": ["skills_count >= 15", "certifications >= 3"],
                        "THEN": ["certified_specialist = true"]
                    },
                    {
                        "rule_id": "FC005",
                        "IF": ["technical_leader = true", "team_size >= 5"],
                        "THEN": ["technical_manager = true"]
                    }
                ],
                "inference_steps": [
                    "1. Load candidate facts into working memory",
                    "2. Match facts against rule conditions",
                    "3. Fire applicable rules",
                    "4. Add conclusions to working memory",
                    "5. Repeat until no new conclusions"
                ]
            }

            with open(self.models_path / "forward_chaining_engine.json", 'w') as f:
                json.dump(forward_chain, f, indent=2)

            logger.info("âœ… Forward Chaining Engine built")
            return {'num_rules': len(forward_chain['production_rules'])}

        except Exception as e:
            logger.error(f"âŒ Forward Chaining failed: {e}")
            return None

    def build_backward_chaining_engine(self):
        """Build backward chaining inference engine"""
        logger.info("\nðŸ‘¨â€ðŸ« Building Backward Chaining Engine...")

        try:
            backward_chain = {
                "metadata": {
                    "type": "backward_chaining",
                    "description": "Goal-driven inference from conclusions to facts"
                },
                "goals": [
                    "is_suitable_for_role",
                    "is_high_potential",
                    "is_technical_leader"
                ],
                "rules": [
                    {
                        "goal": "is_suitable_for_role",
                        "subgoals": ["has_required_skills", "has_required_experience"],
                        "rule_id": "BC001"
                    },
                    {
                        "goal": "has_required_skills",
                        "facts": ["skills_match_percentage >= 70"],
                        "rule_id": "BC002"
                    },
                    {
                        "goal": "has_required_experience",
                        "facts": ["years_of_experience >= min_required_years"],
                        "rule_id": "BC003"
                    },
                    {
                        "goal": "is_high_potential",
                        "subgoals": ["has_strong_education", "has_career_growth"],
                        "rule_id": "BC004"
                    },
                    {
                        "goal": "is_technical_leader",
                        "subgoals": ["is_technical_expert", "has_leadership_experience"],
                        "rule_id": "BC005"
                    }
                ],
                "inference_strategy": "depth_first_search"
            }

            with open(self.models_path / "backward_chaining_engine.json", 'w') as f:
                json.dump(backward_chain, f, indent=2)

            logger.info("âœ… Backward Chaining Engine built")
            return {'num_goals': len(backward_chain['goals'])}

        except Exception as e:
            logger.error(f"âŒ Backward Chaining failed: {e}")
            return None

    def build_knowledge_graph(self):
        """Build knowledge graph for domain knowledge"""
        logger.info("\nðŸ‘¨â€ðŸ« Building Knowledge Graph...")

        try:
            import networkx as nx
            import joblib

            # Create knowledge graph
            kg = nx.DiGraph()

            # Add nodes with attributes
            kg.add_node("Candidate", type="entity")
            kg.add_node("Skills", type="attribute")
            kg.add_node("Experience", type="attribute")
            kg.add_node("Education", type="attribute")
            kg.add_node("Technical_Skills", type="skill_category")
            kg.add_node("Management_Skills", type="skill_category")
            kg.add_node("Seniority_Level", type="classification")
            kg.add_node("Role_Fit", type="classification")

            # Add edges (relationships)
            kg.add_edge("Candidate", "Skills", relation="has")
            kg.add_edge("Candidate", "Experience", relation="has")
            kg.add_edge("Candidate", "Education", relation="has")
            kg.add_edge("Skills", "Technical_Skills", relation="includes")
            kg.add_edge("Skills", "Management_Skills", relation="includes")
            kg.add_edge("Experience", "Seniority_Level", relation="determines")
            kg.add_edge("Skills", "Role_Fit", relation="influences")
            kg.add_edge("Education", "Seniority_Level", relation="influences")

            # Add domain-specific knowledge
            kg.add_node("Python", type="technical_skill")
            kg.add_node("Java", type="technical_skill")
            kg.add_node("Leadership", type="soft_skill")
            kg.add_edge("Technical_Skills", "Python", relation="contains")
            kg.add_edge("Technical_Skills", "Java", relation="contains")
            kg.add_edge("Management_Skills", "Leadership", relation="contains")

            # Save knowledge graph
            joblib.dump(kg, self.models_path / "knowledge_graph.pkl")

            # Save graph structure as JSON
            graph_data = {
                "metadata": {
                    "num_nodes": kg.number_of_nodes(),
                    "num_edges": kg.number_of_edges(),
                    "graph_type": "directed"
                },
                "nodes": list(kg.nodes(data=True)),
                "edges": list(kg.edges(data=True))
            }

            with open(self.models_path / "knowledge_graph_structure.json", 'w') as f:
                json.dump(graph_data, f, indent=2, default=str)

            logger.info(f"âœ… Knowledge Graph built - {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")
            return {'num_nodes': kg.number_of_nodes(), 'num_edges': kg.number_of_edges()}

        except Exception as e:
            logger.error(f"âŒ Knowledge Graph failed: {e}")
            return None

    def build_case_base(self):
        """Build case-based reasoning system"""
        logger.info("\nðŸ‘¨â€ðŸ« Building Case Base for CBR...")

        try:
            case_base = {
                "metadata": {
                    "type": "case_based_reasoning",
                    "similarity_metric": "euclidean_distance",
                    "retrieval_k": 5
                },
                "cases": [
                    {
                        "case_id": "CASE001",
                        "features": {
                            "experience_years": 12,
                            "skills_count": 20,
                            "education_count": 2,
                            "has_management": True
                        },
                        "solution": {
                            "seniority": "Senior",
                            "role_fit": "Technical Manager",
                            "placement_success": True
                        }
                    },
                    {
                        "case_id": "CASE002",
                        "features": {
                            "experience_years": 6,
                            "skills_count": 12,
                            "education_count": 1,
                            "has_management": False
                        },
                        "solution": {
                            "seniority": "Mid",
                            "role_fit": "Technical Specialist",
                            "placement_success": True
                        }
                    },
                    {
                        "case_id": "CASE003",
                        "features": {
                            "experience_years": 2,
                            "skills_count": 5,
                            "education_count": 1,
                            "has_management": False
                        },
                        "solution": {
                            "seniority": "Junior",
                            "role_fit": "Entry Level Developer",
                            "placement_success": True
                        }
                    }
                ],
                "retrieval_algorithm": "k_nearest_neighbors",
                "adaptation_rules": [
                    "Adjust seniority based on experience delta",
                    "Modify role fit based on skill overlap",
                    "Update confidence based on case similarity"
                ]
            }

            with open(self.models_path / "case_base.json", 'w') as f:
                json.dump(case_base, f, indent=2)

            logger.info(f"âœ… Case Base built with {len(case_base['cases'])} cases")
            return {'num_cases': len(case_base['cases'])}

        except Exception as e:
            logger.error(f"âŒ Case Base failed: {e}")
            return None

    def build_all_systems(self):
        """Build all expert systems"""
        logger.info("\n" + "="*60)
        logger.info("EXPERT SYSTEMS BUILDING - ALL TYPES")
        logger.info("="*60)

        results = {}

        # Build each system type
        results['rule_engine'] = self.build_rule_engine()
        results['forward_chaining'] = self.build_forward_chaining_engine()
        results['backward_chaining'] = self.build_backward_chaining_engine()
        results['knowledge_graph'] = self.build_knowledge_graph()
        results['case_base'] = self.build_case_base()

        # Summary
        logger.info("\n" + "="*60)
        logger.info("EXPERT SYSTEMS BUILD COMPLETE")
        logger.info("="*60)
        for name, result in results.items():
            status = "âœ…" if result else "âŒ"
            logger.info(f"{status} {name.upper()}")

        return results


if __name__ == "__main__":
    builder = ExpertSystemBuilder(str(Path(__file__).parent))
    results = builder.build_all_systems()

