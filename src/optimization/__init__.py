"""
Strategy Parameter Optimization
Grid search and genetic algorithms for finding optimal parameters
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from itertools import product
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from ..backtesting.backtest_engine import BacktestEngine
from ..strategies.base_strategy import BaseStrategy


class ParameterOptimizer:
    """
    Optimize strategy parameters using grid search or random search
    """

    def __init__(
        self,
        strategy_class,
        data: pd.DataFrame,
        initial_capital: float = 100000,
        metric: str = 'sharpe_ratio'
    ):
        """
        Initialize optimizer

        Args:
            strategy_class: Strategy class to optimize
            data: Historical data for backtesting
            initial_capital: Starting capital
            metric: Optimization metric (sharpe_ratio, total_return, win_rate)
        """
        self.strategy_class = strategy_class
        self.data = data
        self.initial_capital = initial_capital
        self.metric = metric
        self.logger = logging.getLogger(__name__)
        self.results = []

    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        max_workers: int = 4
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Perform grid search over parameter space

        Args:
            param_grid: Dictionary of parameter names and values to try
                       Example: {'short_window': [10, 20, 30], 'long_window': [40, 50, 60]}
            max_workers: Number of parallel workers

        Returns:
            (best_params, best_results)
        """
        self.logger.info(f"Starting grid search with {len(param_grid)} parameters")

        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        self.logger.info(f"Testing {len(combinations)} parameter combinations")

        # Test each combination
        best_score = float('-inf')
        best_params = None
        best_results = None

        self.results = []

        for i, values in enumerate(combinations):
            params = dict(zip(param_names, values))

            try:
                # Create strategy with these parameters
                strategy = self.strategy_class(**params)

                # Run backtest
                engine = BacktestEngine(initial_capital=self.initial_capital)
                results = engine.run(strategy, self.data)

                # Get score
                score = results.get(self.metric, float('-inf'))

                # Store result
                self.results.append({
                    'params': params,
                    'score': score,
                    'results': results
                })

                # Update best if better
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_results = results
                    self.logger.info(f"New best: {params} -> {self.metric}={score:.4f}")

            except Exception as e:
                self.logger.error(f"Error testing params {params}: {e}")

            # Progress
            if (i + 1) % 10 == 0:
                self.logger.info(f"Progress: {i+1}/{len(combinations)} combinations tested")

        self.logger.info(f"Grid search complete. Best {self.metric}: {best_score:.4f}")
        self.logger.info(f"Best parameters: {best_params}")

        return best_params, best_results

    def random_search(
        self,
        param_distributions: Dict[str, Tuple[Any, Any]],
        n_iter: int = 100
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Perform random search over parameter space

        Args:
            param_distributions: Dictionary of parameter names and (min, max) ranges
                                Example: {'short_window': (10, 30), 'long_window': (40, 100)}
            n_iter: Number of random samples to try

        Returns:
            (best_params, best_results)
        """
        self.logger.info(f"Starting random search with {n_iter} iterations")

        best_score = float('-inf')
        best_params = None
        best_results = None

        self.results = []

        for i in range(n_iter):
            # Sample random parameters
            params = {}
            for param_name, (min_val, max_val) in param_distributions.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param_name] = np.random.uniform(min_val, max_val)

            try:
                # Create strategy with these parameters
                strategy = self.strategy_class(**params)

                # Run backtest
                engine = BacktestEngine(initial_capital=self.initial_capital)
                results = engine.run(strategy, self.data)

                # Get score
                score = results.get(self.metric, float('-inf'))

                # Store result
                self.results.append({
                    'params': params,
                    'score': score,
                    'results': results
                })

                # Update best if better
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_results = results
                    self.logger.info(f"New best: {params} -> {self.metric}={score:.4f}")

            except Exception as e:
                self.logger.error(f"Error testing params {params}: {e}")

            # Progress
            if (i + 1) % 10 == 0:
                self.logger.info(f"Progress: {i+1}/{n_iter} iterations")

        self.logger.info(f"Random search complete. Best {self.metric}: {best_score:.4f}")
        self.logger.info(f"Best parameters: {best_params}")

        return best_params, best_results

    def walk_forward_analysis(
        self,
        best_params: Dict[str, Any],
        train_period: int = 252,  # days
        test_period: int = 63     # days
    ) -> List[Dict[str, Any]]:
        """
        Perform walk-forward analysis to test parameter stability

        Args:
            best_params: Best parameters from optimization
            train_period: Training period length (days)
            test_period: Testing period length (days)

        Returns:
            List of results for each test period
        """
        self.logger.info("Starting walk-forward analysis")

        results = []
        total_length = len(self.data)
        current_idx = train_period

        while current_idx + test_period <= total_length:
            # Split data
            train_data = self.data.iloc[current_idx - train_period:current_idx]
            test_data = self.data.iloc[current_idx:current_idx + test_period]

            # Train: optimize on training data
            optimizer = ParameterOptimizer(
                self.strategy_class,
                train_data,
                self.initial_capital,
                self.metric
            )

            # Use best_params as starting point (you could re-optimize here)
            strategy = self.strategy_class(**best_params)

            # Test: backtest on test data
            engine = BacktestEngine(initial_capital=self.initial_capital)
            test_results = engine.run(strategy, test_data)

            results.append({
                'train_start': train_data.index[0],
                'train_end': train_data.index[-1],
                'test_start': test_data.index[0],
                'test_end': test_data.index[-1],
                'params': best_params,
                'test_results': test_results
            })

            self.logger.info(f"WF: Test period {test_data.index[0]} to {test_data.index[-1]}: "
                           f"{self.metric}={test_results.get(self.metric, 0):.4f}")

            # Move to next period
            current_idx += test_period

        self.logger.info(f"Walk-forward analysis complete with {len(results)} periods")

        # Calculate aggregate statistics
        avg_score = np.mean([r['test_results'].get(self.metric, 0) for r in results])
        self.logger.info(f"Average {self.metric} across all periods: {avg_score:.4f}")

        return results

    def get_results_dataframe(self) -> pd.DataFrame:
        """Get optimization results as DataFrame"""
        if not self.results:
            return pd.DataFrame()

        # Flatten results
        rows = []
        for result in self.results:
            row = {**result['params'], 'score': result['score']}
            # Add key metrics from results
            for key in ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']:
                if key in result['results']:
                    row[key] = result['results'][key]
            rows.append(row)

        df = pd.DataFrame(rows)
        return df.sort_values('score', ascending=False)


class GeneticOptimizer:
    """
    Genetic algorithm for parameter optimization
    More efficient than grid search for large parameter spaces
    """

    def __init__(
        self,
        strategy_class,
        data: pd.DataFrame,
        param_bounds: Dict[str, Tuple[float, float]],
        initial_capital: float = 100000,
        metric: str = 'sharpe_ratio',
        population_size: int = 50,
        generations: int = 20,
        mutation_rate: float = 0.1
    ):
        """
        Initialize genetic optimizer

        Args:
            strategy_class: Strategy class to optimize
            data: Historical data
            param_bounds: Parameter bounds {name: (min, max)}
            initial_capital: Starting capital
            metric: Optimization metric
            population_size: Size of population
            generations: Number of generations
            mutation_rate: Mutation probability
        """
        self.strategy_class = strategy_class
        self.data = data
        self.param_bounds = param_bounds
        self.initial_capital = initial_capital
        self.metric = metric
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.logger = logging.getLogger(__name__)

    def optimize(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run genetic algorithm optimization

        Returns:
            (best_params, best_results)
        """
        self.logger.info(f"Starting genetic algorithm optimization")
        self.logger.info(f"Population: {self.population_size}, Generations: {self.generations}")

        # Initialize population
        population = self._initialize_population()

        best_individual = None
        best_fitness = float('-inf')
        best_results = None

        for generation in range(self.generations):
            # Evaluate fitness
            fitnesses = []
            for individual in population:
                fitness, results = self._evaluate_fitness(individual)
                fitnesses.append((fitness, results))

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_individual = individual.copy()
                    best_results = results
                    self.logger.info(f"Gen {generation}: New best {self.metric}={fitness:.4f}")

            # Selection
            selected = self._selection(population, fitnesses)

            # Crossover
            offspring = self._crossover(selected)

            # Mutation
            population = self._mutation(offspring)

            avg_fitness = np.mean([f[0] for f in fitnesses])
            self.logger.info(f"Generation {generation}: avg={avg_fitness:.4f}, best={best_fitness:.4f}")

        self.logger.info(f"Optimization complete. Best {self.metric}: {best_fitness:.4f}")
        self.logger.info(f"Best parameters: {best_individual}")

        return best_individual, best_results

    def _initialize_population(self) -> List[Dict[str, float]]:
        """Initialize random population"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param, (min_val, max_val) in self.param_bounds.items():
                individual[param] = np.random.uniform(min_val, max_val)
            population.append(individual)
        return population

    def _evaluate_fitness(self, individual: Dict[str, float]) -> Tuple[float, Dict[str, Any]]:
        """Evaluate fitness of individual"""
        try:
            # Convert to integers if needed
            params = {}
            for key, value in individual.items():
                # Check if parameter should be integer (heuristic: if bounds are integers)
                min_val, max_val = self.param_bounds[key]
                if isinstance(min_val, int) and isinstance(max_val, int):
                    params[key] = int(round(value))
                else:
                    params[key] = value

            strategy = self.strategy_class(**params)
            engine = BacktestEngine(initial_capital=self.initial_capital)
            results = engine.run(strategy, self.data)

            fitness = results.get(self.metric, float('-inf'))
            return fitness, results

        except Exception as e:
            self.logger.error(f"Error evaluating {individual}: {e}")
            return float('-inf'), {}

    def _selection(self, population: List[Dict], fitnesses: List[Tuple[float, Dict]]) -> List[Dict]:
        """Tournament selection"""
        selected = []
        for _ in range(self.population_size):
            # Tournament of size 3
            tournament = np.random.choice(len(population), size=3, replace=False)
            winner_idx = max(tournament, key=lambda i: fitnesses[i][0])
            selected.append(population[winner_idx].copy())
        return selected

    def _crossover(self, population: List[Dict]) -> List[Dict]:
        """Single-point crossover"""
        offspring = []
        for i in range(0, len(population) - 1, 2):
            parent1 = population[i]
            parent2 = population[i + 1]

            # 80% chance of crossover
            if np.random.random() < 0.8:
                child1, child2 = {}, {}
                params = list(parent1.keys())
                crossover_point = np.random.randint(1, len(params))

                for j, param in enumerate(params):
                    if j < crossover_point:
                        child1[param] = parent1[param]
                        child2[param] = parent2[param]
                    else:
                        child1[param] = parent2[param]
                        child2[param] = parent1[param]

                offspring.extend([child1, child2])
            else:
                offspring.extend([parent1, parent2])

        return offspring

    def _mutation(self, population: List[Dict]) -> List[Dict]:
        """Gaussian mutation"""
        for individual in population:
            for param, value in individual.items():
                if np.random.random() < self.mutation_rate:
                    min_val, max_val = self.param_bounds[param]
                    # Add gaussian noise
                    noise = np.random.normal(0, (max_val - min_val) * 0.1)
                    new_value = value + noise
                    # Clip to bounds
                    individual[param] = np.clip(new_value, min_val, max_val)

        return population
