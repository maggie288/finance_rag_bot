from __future__ import annotations
import numpy as np
from numpy.linalg import matrix_power


class MarkovPredictor:
    """Markov chain stock price prediction engine."""

    def __init__(self, n_states: int = 5):
        self.n_states = n_states
        self.state_labels = ["大幅下跌", "小幅下跌", "横盘", "小幅上涨", "大幅上涨"]

    def predict(self, prices: list[float], horizon: str) -> dict:
        """
        Run Markov chain prediction.

        Args:
            prices: Historical closing prices (at least 30 data points)
            horizon: '3day' | '1week' | '1month'

        Returns:
            Complete prediction result with computation log
        """
        prices_arr = np.array(prices, dtype=float)
        computation_steps = []

        # Step 1: Calculate daily returns
        returns = np.diff(prices_arr) / prices_arr[:-1]
        computation_steps.append({
            "step": 1,
            "title": "计算日收益率",
            "description": f"基于 {len(prices)} 个历史价格数据，计算得到 {len(returns)} 个日收益率。"
                          f"收益率范围: [{returns.min():.4f}, {returns.max():.4f}]，"
                          f"平均收益率: {returns.mean():.4f}",
            "data": {
                "count": len(returns),
                "min": float(returns.min()),
                "max": float(returns.max()),
                "mean": float(returns.mean()),
                "std": float(returns.std()),
            },
        })

        # Step 2: Discretize returns into states using quantiles
        bin_edges = np.quantile(returns, np.linspace(0, 1, self.n_states + 1))
        # Ensure unique bin edges
        bin_edges = np.unique(bin_edges)
        if len(bin_edges) < self.n_states + 1:
            bin_edges = np.linspace(returns.min() - 0.001, returns.max() + 0.001, self.n_states + 1)

        states = np.digitize(returns, bin_edges[1:-1])  # 0 to n_states-1

        state_ranges = []
        for i in range(len(bin_edges) - 1):
            state_ranges.append({
                "state": self.state_labels[i] if i < len(self.state_labels) else f"State {i}",
                "range": f"[{bin_edges[i]:.4f}, {bin_edges[i+1]:.4f}]",
                "count": int(np.sum(states == i)),
            })

        computation_steps.append({
            "step": 2,
            "title": "离散化收益率为状态",
            "description": f"将收益率按分位数划分为 {self.n_states} 个状态，"
                          f"使用等频分箱确保每个状态有足够的样本。",
            "data": {"state_ranges": state_ranges},
        })

        # Step 3: Build transition frequency matrix
        n = min(self.n_states, len(bin_edges) - 1)
        freq_matrix = np.zeros((n, n))
        for i in range(len(states) - 1):
            s_from = min(states[i], n - 1)
            s_to = min(states[i + 1], n - 1)
            freq_matrix[s_from][s_to] += 1

        computation_steps.append({
            "step": 3,
            "title": "构建状态转移频率矩阵",
            "description": "统计相邻交易日之间的状态转移次数，"
                          "构建转移频率矩阵。",
            "data": {"frequency_matrix": freq_matrix.tolist()},
        })

        # Step 4: Normalize to get transition probability matrix
        row_sums = freq_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # avoid division by zero
        transition_matrix = freq_matrix / row_sums

        computation_steps.append({
            "step": 4,
            "title": "归一化为转移概率矩阵",
            "description": "将频率矩阵每行归一化，使每行概率之和为1，"
                          "得到马尔可夫转移概率矩阵 P(i→j)。",
            "data": {"transition_matrix": transition_matrix.tolist()},
        })

        # Step 5: Determine forecast horizon steps
        steps_map = {"3day": 3, "1week": 5, "1month": 22}
        forecast_steps = steps_map.get(horizon, 5)

        # Step 6: Current state detection
        current_return = returns[-1]
        current_state = min(int(np.digitize(current_return, bin_edges[1:-1])), n - 1)

        computation_steps.append({
            "step": 5,
            "title": "确定当前状态和预测步数",
            "description": f"最近一日收益率为 {current_return:.4f}，"
                          f"对应状态: {self.state_labels[current_state]}。"
                          f"预测时间窗口: {horizon} ({forecast_steps}个交易日)。",
            "data": {
                "current_return": float(current_return),
                "current_state": self.state_labels[current_state],
                "forecast_steps": forecast_steps,
            },
        })

        # Step 7: Matrix exponentiation for n-step prediction
        n_step_matrix = matrix_power(transition_matrix, forecast_steps)
        predicted_probs = n_step_matrix[current_state]

        computation_steps.append({
            "step": 6,
            "title": "矩阵幂运算预测",
            "description": f"对转移概率矩阵进行 {forecast_steps} 次幂运算，"
                          f"P^{forecast_steps}，得到 {forecast_steps} 步后的状态概率分布。",
            "data": {
                "n_step_matrix": n_step_matrix.tolist(),
                "predicted_probs": {
                    self.state_labels[i]: float(predicted_probs[i])
                    for i in range(n)
                },
            },
        })

        # Step 8: Map to price predictions
        state_means = []
        for s in range(n):
            mask = states == s
            if mask.any():
                state_means.append(float(np.mean(returns[:-1][mask[:-1]] if len(mask) > len(returns[:-1]) else returns[mask[:len(returns)]])))
            else:
                state_means.append(0.0)

        # Use properly computed state means
        for s in range(n):
            mask = (states == s)
            indices = np.where(mask)[0]
            if len(indices) > 0:
                state_means[s] = float(np.mean(returns[indices]))

        expected_return = np.dot(predicted_probs[:len(state_means)], state_means)
        current_price = float(prices_arr[-1])

        # Compound return over forecast period
        predicted_mid = current_price * (1 + expected_return) ** forecast_steps
        predicted_low = current_price * (1 + min(state_means)) ** forecast_steps
        predicted_high = current_price * (1 + max(state_means)) ** forecast_steps

        # Confidence based on entropy of prediction distribution
        entropy = -np.sum(predicted_probs * np.log2(predicted_probs + 1e-10))
        max_entropy = np.log2(n)
        confidence = float(1 - entropy / max_entropy) if max_entropy > 0 else 0.0

        computation_steps.append({
            "step": 7,
            "title": "价格预测结果",
            "description": f"基于状态概率加权平均计算期望收益率: {expected_return:.4f}。"
                          f"当前价格: {current_price:.2f}，"
                          f"预测价格区间: [{predicted_low:.2f}, {predicted_mid:.2f}, {predicted_high:.2f}]。"
                          f"预测置信度: {confidence:.2%}",
            "data": {
                "expected_return": float(expected_return),
                "state_means": state_means,
                "predicted_low": float(predicted_low),
                "predicted_mid": float(predicted_mid),
                "predicted_high": float(predicted_high),
                "confidence": confidence,
            },
        })

        return {
            "current_price": current_price,
            "current_state": self.state_labels[current_state],
            "state_labels": self.state_labels[:n],
            "transition_matrix": transition_matrix.tolist(),
            "predicted_state_probs": {
                self.state_labels[i]: float(predicted_probs[i])
                for i in range(n)
            },
            "predicted_range": {
                "low": float(predicted_low),
                "mid": float(predicted_mid),
                "high": float(predicted_high),
            },
            "confidence": confidence,
            "computation_steps": computation_steps,
        }


# Singleton
markov_predictor = MarkovPredictor()
