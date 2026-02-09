"""
Statistical Analysis Engine
===========================
Provides robust statistical methods for the IntelliCV Platform.
Designed to run in both heavy (Pandas) and light (Pure Python) environments.

Capabilities (Top 15 Techniques):
1. Descriptive Statistics
2. Regression Analysis
3. Hypothesis Testing (T-test, ANOVA)
4. Correlation Analysis
5. Chi-Square Test
6. Time Series Analysis
7. Principal Component Analysis (Simulated)
8. Cluster Analysis (K-Means)
9. Factor Analysis (Simulated)
10. Bayesian Analysis (Naive)
11. Monte Carlo Simulation
12. Non-Parametric Tests (Mann-Whitney U)
13. Survival Analysis (Kaplan-Meier Logic)
14. Visuals (Data for Plots)
15. Boids/Flocking Optimizer (Starling Murmuration)
"""

import math
import statistics
import random
from typing import List, Dict, Any, Union, Tuple
from collections import Counter

class StatisticalAnalysisEngine:
    
    def __init__(self):
        pass

    # 1. Descriptive Statistics
    def descriptive_stats(self, data: List[float]) -> Dict[str, float]:
        if not data: return {}
        return {
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "mode": statistics.mode(data) if len(data) > 0 else 0,
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
            "count": len(data)
        }

    # 2. Regression Analysis (Simple Linear)
    def linear_regression(self, x: List[float], y: List[float]) -> Dict[str, float]:
        """Returns slope, intercept, r_value for y = mx + c"""
        if len(x) != len(y) or len(x) < 2: return {}
        
        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = sum((xi - mean_x) ** 2 for xi in x)
        
        if denominator == 0: return {"slope": 0, "intercept": mean_y, "r_squared": 0}
        
        slope = numerator / denominator
        intercept = mean_y - slope * mean_x
        
        # R-squared
        y_pred = [slope * xi + intercept for xi in x]
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        ss_res = sum((yi - y_p) ** 2 for yi, y_p in zip(y, y_pred))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {"slope": slope, "intercept": intercept, "r_squared": r_squared}

    # 3. Hypothesis Testing (Independent T-test)
    def t_test_ind(self, group1: List[float], group2: List[float]) -> Dict[str, float]:
        """Returns t-statistic and degrees of freedom"""
        if len(group1) < 2 or len(group2) < 2: return {}
        
        mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
        var1, var2 = statistics.variance(group1), statistics.variance(group2)
        n1, n2 = len(group1), len(group2)
        
        numerator = mean1 - mean2
        denominator = math.sqrt((var1/n1) + (var2/n2))
        
        if denominator == 0: return {"t_stat": 0, "dof": 0}
        
        t_stat = numerator / denominator
        # Welch-Satterthwaite equation for degrees of freedom
        dof = ((var1/n1 + var2/n2)**2) / ((var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1))
        
        return {"t_stat": t_stat, "dof": dof, "significant": abs(t_stat) > 1.96} # Approx for p<0.05

    # 4. Correlation Analysis (Pearson)
    def correlation(self, x: List[float], y: List[float]) -> float:
        if len(x) != len(y) or len(x) < 2: return 0.0
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den_x = sum((xi - mean_x) ** 2 for xi in x)
        den_y = sum((yi - mean_y) ** 2 for yi in y)
        
        if den_x == 0 or den_y == 0: return 0.0
        
        return numerator / math.sqrt(den_x * den_y)

    # 5. Chi-Square Test (Independence)
    def chi_square(self, observed: List[List[int]]) -> Dict[str, float]:
        """Calculates Chi-Square for a contingency table"""
        total = sum(sum(row) for row in observed)
        row_totals = [sum(row) for row in observed]
        col_totals = [sum(row[i] for row in observed) for i in range(len(observed[0]))]
        
        chi2 = 0.0
        for i, row in enumerate(observed):
            for j, val in enumerate(row):
                expected = (row_totals[i] * col_totals[j]) / total
                if expected > 0:
                    chi2 += ((val - expected) ** 2) / expected
                    
        return {"chi_square": chi2}

    # 6. Time Series (Simple Moving Average)
    def moving_average(self, data: List[float], window: int = 3) -> List[float]:
        if len(data) < window: return data
        return [statistics.mean(data[i:i+window]) for i in range(len(data) - window + 1)]

    # 7. PCA (Simulated/Simplified)
    def pca_simulated(self, features: List[List[float]]) -> Dict[str, Any]:
        """
        Pure python PCA is complex. Returning a simulation mapping high-dim
        features to a 2D projection for visualization.
        """
        # Simply projecting first two dims or random projection for structure
        if not features: return {}
        projected = [{"x": f[0] if len(f)>0 else 0, "y": f[1] if len(f)>1 else 0} for f in features]
        return {"variance_ratio": [0.8, 0.2], "projection": projected}

    # 8. Clustering (K-Means Simplified)
    def k_means(self, data: List[List[float]], k: int = 3, iterations: int = 10) -> Dict[str, Any]:
        """Simple K-Means implementation"""
        if not data: return {}
        dims = len(data[0])
        # Initialize centroids randomly
        centroids = random.sample(data, min(k, len(data)))
        
        labels = []
        for _ in range(iterations):
            # Assign clusters
            labels = []
            for point in data:
                distances = [math.sqrt(sum((a-b)**2 for a,b in zip(point, c))) for c in centroids]
                labels.append(distances.index(min(distances)))
            
            # Update centroids
            new_centroids = []
            for i in range(k):
                cluster_points = [data[j] for j, l in enumerate(labels) if l == i]
                if cluster_points:
                    mean_point = [statistics.mean(p[d] for p in cluster_points) for d in range(dims)]
                    new_centroids.append(mean_point)
                else:
                    new_centroids.append(centroids[i]) # Keep old if empty
            
            if new_centroids == centroids: break
            centroids = new_centroids
            
        return {"centroids": centroids, "labels": labels}

    # 9. Factor Analysis (Stub)
    def factor_analysis(self, correlation_matrix: List[List[float]]) -> Dict[str, Any]:
        # Returns simulated factors
        return {"factors": ["Skill_Group_A", "Skill_Group_B"], "loadings": [[0.8, 0.1], [0.2, 0.9]]}

    # 10. Bayesian Analysis (Naive likelihood)
    def bayesian_probability(self, prior: float, likelihood: float, evidence: float) -> float:
        """P(H|E) = (P(E|H) * P(H)) / P(E)"""
        if evidence == 0: return 0.0
        return (likelihood * prior) / evidence

    # 11. Monte Carlo Simulation
    def monte_carlo_salary(self, base: float, volatility: float, runs: int = 1000) -> List[float]:
        """Simulates salary range outcomes"""
        results = []
        for _ in range(runs):
            shock = random.gauss(0, volatility)
            results.append(base * (1 + shock))
        return sorted(results)

    # 12. Non-Parametric (Mann-Whitney U Simplified)
    def mann_whitney_u_sim(self, x: List[float], y: List[float]) -> Dict[str, float]:
        """Simulated U statistic logic"""
        combined = sorted([(v, 'x') for v in x] + [(v, 'y') for v in y], key=lambda i: i[0])
        rank_sum_x = sum(i + 1 for i, v in enumerate(combined) if v[1] == 'x')
        n1, n2 = len(x), len(y)
        u1 = rank_sum_x - (n1 * (n1 + 1)) / 2
        return {"u_stat": u1}

    # 13. Survival Analysis (Kaplan-Meier Logic Simplified)
    def kaplan_meier_logic(self, durations: List[int], events: List[int]) -> List[Dict[str, float]]:
        """Calculates survival probability at each time step"""
        # Pack and sort
        data = sorted(zip(durations, events))
        survival = 1.0
        at_risk = len(data)
        curve = []
        
        for t, e in data:
            if at_risk > 0:
                survival *= (1 - e/at_risk)
                at_risk -= 1
                curve.append({"time": t, "prob": survival})
        return curve

    # 14. Visuals (Histogram Data)
    def histogram_data(self, data: List[float], bins: int = 10) -> Dict[str, List]:
        if not data: return {}
        mn, mx = min(data), max(data)
        width = (mx - mn) / bins if mx > mn else 1
        
        bin_counts = [0] * bins
        bin_edges = [mn + i*width for i in range(bins+1)]
        
        for v in data:
            idx = int((v - mn) / width)
            if idx >= bins: idx = bins - 1
            bin_counts[idx] += 1
            
        return {"counts": bin_counts, "edges": bin_edges}

    # 15. Boids / Flocking Optimizer (Starling Murmuration)
    def starling_murmuration_optimizer(self, agents: List[Dict], target: Dict) -> List[Dict]:
        """
        Simulates Boids behavior for agents moving towards a target (optimal fit).
        Rules: Separation, Alignment, Cohesion.
        """
        config = {"cohesion": 0.01, "alignment": 0.1, "separation": 1.5, "target_attraction": 0.05}
        
        new_agents = []
        for agent in agents:
            pos = agent["pos"] # [x, y]
            vel = agent["vel"] # [vx, vy]
            
            # Center of mass (Cohesion)
            center = [statistics.mean([a["pos"][0] for a in agents]), statistics.mean([a["pos"][1] for a in agents])]
            cohesion = [(center[0] - pos[0]) * config["cohesion"], (center[1] - pos[1]) * config["cohesion"]]
            
            # Align velocity (Alignment)
            avg_vel = [statistics.mean([a["vel"][0] for a in agents]), statistics.mean([a["vel"][1] for a in agents])]
            alignment = [(avg_vel[0] - vel[0]) * config["alignment"], (avg_vel[1] - vel[1]) * config["alignment"]]
            
            # Separation
            separation = [0.0, 0.0]
            for other in agents:
                if other != agent:
                    dist = math.sqrt((pos[0]-other["pos"][0])**2 + (pos[1]-other["pos"][1])**2)
                    if dist < 5: # crowded
                        separation[0] -= (other["pos"][0] - pos[0])
                        separation[1] -= (other["pos"][1] - pos[1])
            separation = [s * config["separation"] for s in separation]
            
            # Target Attraction
            attract = [(target["pos"][0] - pos[0]) * config["target_attraction"], (target["pos"][1] - pos[1]) * config["target_attraction"]]
            
            # Update Velocity
            new_vel = [vel[0] + cohesion[0] + alignment[0] + separation[0] + attract[0],
                       vel[1] + cohesion[1] + alignment[1] + separation[1] + attract[1]]
            
            # Update Position
            new_pos = [pos[0] + new_vel[0], pos[1] + new_vel[1]]
            
            new_agents.append({"id": agent["id"], "pos": new_pos, "vel": new_vel})
            
        return new_agents

if __name__ == "__main__":
    # Smoke Test
    engine = StatisticalAnalysisEngine()
    print("Descriptive:", engine.descriptive_stats([1, 2, 3, 4, 10]))
    print("Regression:", engine.linear_regression([1, 2, 3], [2, 4, 6]))
