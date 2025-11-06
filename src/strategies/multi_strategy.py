"""
Multi-Strategy Portfolio Manager
Combine multiple strategies for better risk-adjusted returns

This approach is used by:
- Renaissance Technologies (combines 100+ strategies)
- Bridgewater Associates
- AQR Capital Management

Benefits:
- Diversification reduces strategy-specific risk
- Smoother equity curve
- Better Sharpe ratio
- More consistent returns
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base_strategy import BaseStrategy
import logging


class MultiStrategyPortfolio(BaseStrategy):
    """
    Multi-Strategy Portfolio Manager

    Combines multiple strategies with configurable weights.
    Generates signals based on weighted voting or consensus.

    Parameters:
        strategies: List of (strategy, weight) tuples
        voting_method: 'weighted' or 'majority' or 'unanimous'
        rebalance_frequency: Days between rebalancing (default: 1)
    """

    def __init__(
        self,
        strategies: List[tuple[BaseStrategy, float]],
        voting_method: str = 'weighted',
        rebalance_frequency: int = 1
    ):
        """
        Initialize multi-strategy portfolio

        Args:
            strategies: List of (strategy_instance, weight) tuples
                       Weights should sum to 1.0
            voting_method: How to combine signals
                          'weighted': Weighted average of signals
                          'majority': Majority vote wins
                          'unanimous': All must agree
            rebalance_frequency: How often to rebalance
        """
        # Validate weights
        total_weight = sum(weight for _, weight in strategies)
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        strategy_names = [s.name for s, _ in strategies]
        parameters = {
            'strategies': strategy_names,
            'weights': [w for _, w in strategies],
            'voting_method': voting_method,
            'rebalance_frequency': rebalance_frequency
        }

        super().__init__('MultiStrategy', parameters)

        self.strategies = strategies
        self.voting_method = voting_method
        self.rebalance_frequency = rebalance_frequency
        self.logger = logging.getLogger(__name__)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate combined signals from all strategies

        Returns:
            Combined signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if data.empty:
            self.logger.warning("No data provided")
            return pd.Series(dtype=int)

        # Collect signals from all strategies
        all_signals = []
        weights = []

        for strategy, weight in self.strategies:
            try:
                signals = strategy.generate_signals(data)
                if not signals.empty:
                    all_signals.append(signals)
                    weights.append(weight)
                    self.logger.debug(f"{strategy.name}: {signals.sum()} total signals")
            except Exception as e:
                self.logger.error(f"Error in {strategy.name}: {e}")
                continue

        if not all_signals:
            self.logger.warning("No valid signals from any strategy")
            return pd.Series(0, index=data.index)

        # Combine signals based on voting method
        combined = pd.Series(0, index=data.index)

        if self.voting_method == 'weighted':
            # Weighted average of signals
            for signals, weight in zip(all_signals, weights):
                combined += signals * weight

            # Round to discrete signals
            combined = combined.apply(lambda x: 1 if x > 0.5 else (-1 if x < -0.5 else 0))

        elif self.voting_method == 'majority':
            # Count votes for each signal
            signal_counts = pd.DataFrame(all_signals).T

            def majority_vote(row):
                if row.sum() > 0:  # More buys than sells
                    return 1
                elif row.sum() < 0:  # More sells than buys
                    return -1
                else:
                    return 0

            combined = signal_counts.apply(majority_vote, axis=1)

        elif self.voting_method == 'unanimous':
            # All strategies must agree
            signal_counts = pd.DataFrame(all_signals).T

            def unanimous_vote(row):
                if all(row == 1):  # All buy
                    return 1
                elif all(row == -1):  # All sell
                    return -1
                else:
                    return 0

            combined = signal_counts.apply(unanimous_vote, axis=1)

        else:
            raise ValueError(f"Unknown voting method: {self.voting_method}")

        self.logger.info(f"Combined signals: {(combined == 1).sum()} buys, {(combined == -1).sum()} sells")

        return combined

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze all strategies and combine results"""

        if data.empty:
            return {'strategy': self.name, 'error': 'No data provided'}

        # Analyze each strategy
        strategy_analyses = []

        for strategy, weight in self.strategies:
            try:
                analysis = strategy.analyze(data)
                analysis['weight'] = weight
                strategy_analyses.append(analysis)
            except Exception as e:
                self.logger.error(f"Error analyzing {strategy.name}: {e}")

        # Count signals
        buy_votes = sum(1 for a in strategy_analyses if a.get('signal') == 'BUY')
        sell_votes = sum(1 for a in strategy_analyses if a.get('signal') == 'SELL')
        hold_votes = sum(1 for a in strategy_analyses if a.get('signal') == 'HOLD')

        # Calculate weighted signal
        weighted_signal = sum(
            (1 if a.get('signal') == 'BUY' else (-1 if a.get('signal') == 'SELL' else 0)) * a.get('weight', 0)
            for a in strategy_analyses
        )

        # Determine combined signal
        if self.voting_method == 'weighted':
            if weighted_signal > 0.5:
                combined_signal = 'BUY'
            elif weighted_signal < -0.5:
                combined_signal = 'SELL'
            else:
                combined_signal = 'HOLD'
        elif self.voting_method == 'majority':
            if buy_votes > sell_votes:
                combined_signal = 'BUY'
            elif sell_votes > buy_votes:
                combined_signal = 'SELL'
            else:
                combined_signal = 'HOLD'
        elif self.voting_method == 'unanimous':
            if buy_votes == len(self.strategies):
                combined_signal = 'BUY'
            elif sell_votes == len(self.strategies):
                combined_signal = 'SELL'
            else:
                combined_signal = 'HOLD'
        else:
            combined_signal = 'HOLD'

        return {
            'strategy': self.name,
            'signal': combined_signal,
            'voting_method': self.voting_method,
            'buy_votes': buy_votes,
            'sell_votes': sell_votes,
            'hold_votes': hold_votes,
            'weighted_signal_score': float(weighted_signal),
            'individual_strategies': strategy_analyses,
            'timestamp': data.index[-1] if not data.empty else None
        }

    def get_strategy_performance(self, data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Analyze individual strategy performance

        Useful for rebalancing weights
        """
        from ..backtesting.backtest_engine import BacktestEngine

        performance = {}

        for strategy, weight in self.strategies:
            try:
                engine = BacktestEngine(initial_capital=100000)
                results = engine.run(strategy, data)

                performance[strategy.name] = {
                    'total_return': results['total_return'],
                    'sharpe_ratio': results['sharpe_ratio'],
                    'max_drawdown': results['max_drawdown'],
                    'win_rate': results['win_rate'],
                    'current_weight': weight
                }
            except Exception as e:
                self.logger.error(f"Error backtesting {strategy.name}: {e}")

        return performance

    def optimize_weights(
        self,
        data: pd.DataFrame,
        method: str = 'sharpe'
    ) -> List[tuple[BaseStrategy, float]]:
        """
        Optimize strategy weights based on historical performance

        Args:
            data: Historical data for optimization
            method: 'sharpe' (Sharpe ratio), 'returns' (total return), or 'equal' (equal weight)

        Returns:
            New list of (strategy, weight) tuples
        """
        if method == 'equal':
            # Equal weight
            n = len(self.strategies)
            return [(s, 1.0/n) for s, _ in self.strategies]

        # Get performance metrics
        performance = self.get_strategy_performance(data)

        if not performance:
            self.logger.warning("No performance data, using equal weights")
            return self.optimize_weights(data, method='equal')

        # Extract scores
        if method == 'sharpe':
            scores = {name: perf['sharpe_ratio'] for name, perf in performance.items()}
        elif method == 'returns':
            scores = {name: perf['total_return'] for name, perf in performance.items()}
        else:
            raise ValueError(f"Unknown method: {method}")

        # Normalize to positive values (shift if negative)
        min_score = min(scores.values())
        if min_score < 0:
            scores = {k: v - min_score + 0.1 for k, v in scores.items()}

        # Calculate weights proportional to scores
        total_score = sum(scores.values())
        if total_score == 0:
            return self.optimize_weights(data, method='equal')

        new_weights = []
        for strategy, _ in self.strategies:
            weight = scores[strategy.name] / total_score
            new_weights.append((strategy, weight))

        self.logger.info(f"Optimized weights using {method}: {[(s.name, w) for s, w in new_weights]}")

        return new_weights
