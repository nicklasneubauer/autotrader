"""
Advanced Performance Analytics
Calculate detailed trading metrics and generate reports
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging


class PerformanceAnalyzer:
    """
    Calculate comprehensive performance metrics for trading strategies
    """

    def __init__(self, trades: List[Dict[str, Any]], equity_curve: pd.Series):
        """
        Initialize analyzer

        Args:
            trades: List of trade dictionaries
            equity_curve: Series of portfolio values over time
        """
        self.trades = pd.DataFrame(trades) if trades else pd.DataFrame()
        self.equity_curve = equity_curve
        self.logger = logging.getLogger(__name__)

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all performance metrics"""
        metrics = {}

        # Basic metrics
        metrics.update(self.calculate_returns_metrics())

        # Risk metrics
        metrics.update(self.calculate_risk_metrics())

        # Trade metrics
        metrics.update(self.calculate_trade_metrics())

        # Time-based metrics
        metrics.update(self.calculate_time_metrics())

        return metrics

    def calculate_returns_metrics(self) -> Dict[str, float]:
        """Calculate return-based metrics"""
        if self.equity_curve.empty:
            return {}

        returns = self.equity_curve.pct_change().dropna()

        initial_value = self.equity_curve.iloc[0]
        final_value = self.equity_curve.iloc[-1]
        total_return = (final_value - initial_value) / initial_value * 100

        # CAGR (Compound Annual Growth Rate)
        n_years = len(self.equity_curve) / 252  # Assuming daily data
        cagr = (pow(final_value / initial_value, 1 / n_years) - 1) * 100 if n_years > 0 else 0

        return {
            'total_return': total_return,
            'cagr': cagr,
            'avg_daily_return': returns.mean() * 100,
            'avg_monthly_return': returns.mean() * 21 * 100,  # ~21 trading days
            'avg_yearly_return': returns.mean() * 252 * 100,
            'cumulative_return': total_return
        }

    def calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate risk-based metrics"""
        if self.equity_curve.empty:
            return {}

        returns = self.equity_curve.pct_change().dropna()

        # Volatility
        daily_volatility = returns.std()
        annual_volatility = daily_volatility * np.sqrt(252) * 100

        # Sharpe Ratio
        risk_free_rate = 0.02  # 2% annual
        excess_returns = returns - (risk_free_rate / 252)
        sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / returns.std()) if returns.std() > 0 else 0

        # Sortino Ratio (penalizes downside volatility only)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        sortino_ratio = np.sqrt(252) * (returns.mean() / downside_std) if downside_std > 0 else 0

        # Calmar Ratio (return / max drawdown)
        max_drawdown = self._calculate_max_drawdown()
        calmar_ratio = (returns.mean() * 252 * 100) / abs(max_drawdown) if max_drawdown != 0 else 0

        # Value at Risk (VaR) - 95% confidence
        var_95 = np.percentile(returns, 5) * 100

        # Conditional Value at Risk (CVaR) - expected loss beyond VaR
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100

        return {
            'volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'cvar_95': cvar_95
        }

    def calculate_trade_metrics(self) -> Dict[str, Any]:
        """Calculate trade-specific metrics"""
        if self.trades.empty:
            return {}

        # Filter for completed trades (pairs of buy/sell)
        total_trades = len(self.trades)

        # Calculate P&L for each trade if not already present
        if 'pnl' not in self.trades.columns:
            return {'total_trades': total_trades}

        winning_trades = self.trades[self.trades['pnl'] > 0]
        losing_trades = self.trades[self.trades['pnl'] < 0]

        num_winning = len(winning_trades)
        num_losing = len(losing_trades)

        win_rate = (num_winning / total_trades * 100) if total_trades > 0 else 0

        avg_win = winning_trades['pnl'].mean() if num_winning > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if num_losing > 0 else 0

        # Profit factor
        total_wins = winning_trades['pnl'].sum() if num_winning > 0 else 0
        total_losses = abs(losing_trades['pnl'].sum()) if num_losing > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * abs(avg_loss))

        # Largest win/loss
        largest_win = winning_trades['pnl'].max() if num_winning > 0 else 0
        largest_loss = losing_trades['pnl'].min() if num_losing > 0 else 0

        # Win/loss streaks
        win_streak, loss_streak = self._calculate_streaks()

        return {
            'total_trades': total_trades,
            'winning_trades': num_winning,
            'losing_trades': num_losing,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'max_win_streak': win_streak,
            'max_loss_streak': loss_streak
        }

    def calculate_time_metrics(self) -> Dict[str, Any]:
        """Calculate time-based metrics"""
        if self.trades.empty or 'date' not in self.trades.columns:
            return {}

        self.trades['date'] = pd.to_datetime(self.trades['date'])

        # Trading period
        start_date = self.trades['date'].min()
        end_date = self.trades['date'].max()
        trading_days = (end_date - start_date).days

        # Trades per month
        trades_per_month = len(self.trades) / (trading_days / 30) if trading_days > 0 else 0

        # Best/worst month
        self.trades['month'] = self.trades['date'].dt.to_period('M')
        if 'pnl' in self.trades.columns:
            monthly_pnl = self.trades.groupby('month')['pnl'].sum()
            best_month = monthly_pnl.max()
            worst_month = monthly_pnl.min()
        else:
            best_month = 0
            worst_month = 0

        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'trading_days': trading_days,
            'trades_per_month': trades_per_month,
            'best_month': best_month,
            'worst_month': worst_month
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if self.equity_curve.empty:
            return 0.0

        cumulative_max = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - cumulative_max) / cumulative_max
        max_dd = drawdown.min() * 100

        return float(max_dd)

    def _calculate_streaks(self) -> tuple[int, int]:
        """Calculate maximum winning and losing streaks"""
        if self.trades.empty or 'pnl' not in self.trades.columns:
            return 0, 0

        # Create win/loss indicator
        wins = (self.trades['pnl'] > 0).astype(int)

        # Calculate streaks
        win_streak = 0
        loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0

        for is_win in wins:
            if is_win:
                current_win_streak += 1
                current_loss_streak = 0
                win_streak = max(win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                loss_streak = max(loss_streak, current_loss_streak)

        return win_streak, loss_streak

    def generate_report(self) -> str:
        """Generate text report of performance"""
        metrics = self.calculate_all_metrics()

        report = """
================================================================================
                        PERFORMANCE ANALYSIS REPORT
================================================================================

RETURNS METRICS
---------------
Total Return:           {total_return:>10.2f}%
CAGR:                   {cagr:>10.2f}%
Avg Daily Return:       {avg_daily_return:>10.2f}%
Avg Monthly Return:     {avg_monthly_return:>10.2f}%
Avg Yearly Return:      {avg_yearly_return:>10.2f}%

RISK METRICS
------------
Annual Volatility:      {volatility:>10.2f}%
Sharpe Ratio:           {sharpe_ratio:>10.2f}
Sortino Ratio:          {sortino_ratio:>10.2f}
Calmar Ratio:           {calmar_ratio:>10.2f}
Max Drawdown:           {max_drawdown:>10.2f}%
VaR (95%):              {var_95:>10.2f}%
CVaR (95%):             {cvar_95:>10.2f}%

TRADE METRICS
-------------
Total Trades:           {total_trades:>10}
Winning Trades:         {winning_trades:>10}
Losing Trades:          {losing_trades:>10}
Win Rate:               {win_rate:>10.2f}%
Profit Factor:          {profit_factor:>10.2f}
Expectancy:             {expectancy:>10.2f}
Largest Win:            {largest_win:>10.2f}
Largest Loss:           {largest_loss:>10.2f}
Max Win Streak:         {max_win_streak:>10}
Max Loss Streak:        {max_loss_streak:>10}

TIME METRICS
------------
Start Date:             {start_date}
End Date:               {end_date}
Trading Days:           {trading_days:>10}
Trades per Month:       {trades_per_month:>10.2f}
Best Month:             {best_month:>10.2f}
Worst Month:            {worst_month:>10.2f}

================================================================================
""".format(**metrics)

        return report


class MonteCarloSimulation:
    """
    Monte Carlo simulation for strategy validation
    """

    def __init__(self, returns: pd.Series, n_simulations: int = 1000):
        """
        Initialize Monte Carlo simulation

        Args:
            returns: Historical returns series
            n_simulations: Number of simulations to run
        """
        self.returns = returns.dropna()
        self.n_simulations = n_simulations
        self.logger = logging.getLogger(__name__)

    def run(self, n_periods: int = 252) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation

        Args:
            n_periods: Number of periods to simulate (default: 252 trading days)

        Returns:
            Simulation results
        """
        self.logger.info(f"Running {self.n_simulations} Monte Carlo simulations for {n_periods} periods")

        simulations = []

        for i in range(self.n_simulations):
            # Random sampling with replacement
            simulated_returns = np.random.choice(self.returns, size=n_periods, replace=True)

            # Calculate cumulative return
            cumulative_return = (1 + simulated_returns).cumprod()[-1] - 1

            simulations.append(cumulative_return)

        simulations = np.array(simulations)

        # Calculate statistics
        results = {
            'mean_return': np.mean(simulations) * 100,
            'median_return': np.median(simulations) * 100,
            'std_return': np.std(simulations) * 100,
            'min_return': np.min(simulations) * 100,
            'max_return': np.max(simulations) * 100,
            'percentile_5': np.percentile(simulations, 5) * 100,
            'percentile_25': np.percentile(simulations, 25) * 100,
            'percentile_75': np.percentile(simulations, 75) * 100,
            'percentile_95': np.percentile(simulations, 95) * 100,
            'probability_positive': np.sum(simulations > 0) / self.n_simulations * 100
        }

        self.logger.info(f"Monte Carlo complete. Mean return: {results['mean_return']:.2f}%")

        return results
