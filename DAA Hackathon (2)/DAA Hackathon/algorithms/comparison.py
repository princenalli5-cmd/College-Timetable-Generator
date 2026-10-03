"""
DAA Algorithm Comparative Evaluation Engine
Executes Backtracking, Greedy, Graph Coloring, and Hybrid algorithms
under identical problem instances and constraints.
"""

from algorithms.backtracking import BacktrackingScheduler
from algorithms.greedy import GreedyScheduler
from algorithms.graph_coloring import GraphColoringScheduler
from algorithms.hybrid import HybridScheduler

class AlgorithmComparator:
    def __init__(self, problem_data):
        self.problem_data = problem_data

    def run_all(self):
        # 1. Backtracking
        bt = BacktrackingScheduler(self.problem_data)
        bt_res = bt.solve()

        # 2. Greedy
        gr = GreedyScheduler(self.problem_data)
        gr_res = gr.solve()

        # 3. Graph Coloring
        gc = GraphColoringScheduler(self.problem_data)
        gc_res = gc.solve()

        # 4. Hybrid
        hb = HybridScheduler(self.problem_data)
        hb_res = hb.solve()

        # Rank algorithms based on a composite score:
        # Score = (scheduled / total) * 100 - conflicts * 50 - (time_ms / 100)
        def score(res):
            total = res["total_classes"] or 1
            ratio = (res["scheduled_classes"] / total) * 100
            conf = res["conflicts_count"] * 50
            penalty = res["execution_time_ms"] / 100.0
            return ratio - conf - penalty

        ranking = sorted(
            [
                ("Backtracking", bt_res),
                ("Greedy", gr_res),
                ("Graph Coloring", gc_res),
                ("Hybrid (Greedy + BT)", hb_res)
            ],
            key=lambda item: score(item[1]),
            reverse=True
        )

        return {
            "backtracking": bt_res,
            "greedy": gr_res,
            "graph_coloring": gc_res,
            "hybrid": hb_res,
            "ranking": [name for name, _ in ranking]
        }
