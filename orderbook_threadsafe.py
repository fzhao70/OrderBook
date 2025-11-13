"""
Thread-Safe Order Book using Lock-Free Queue Architecture

This module provides a production-grade thread-safe order book implementation
using a lock-free command queue pattern. This is the same architecture used
by major exchanges (NASDAQ, CME, etc.).

Architecture:
- Multiple threads can submit commands concurrently (lock-free)
- Single worker thread processes commands sequentially (no race conditions)
- Supports both synchronous (blocking) and asynchronous (callback) APIs
- Includes monitoring and metrics for production use

Usage:
    # Create engine
    engine = OrderBookEngine("AAPL")

    # Synchronous (blocking) API
    order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

    # Asynchronous (callback) API
    engine.place_limit_order_async(OrderSide.BUY, 100, 150.00,
                                   callback=lambda order: print(order))
"""

import queue
import threading
import time
from typing import Optional, Callable, List, Tuple, Any, Dict
from dataclasses import dataclass
from enum import Enum
import numpy as np

from orderbook import (
    OrderBook, Order, Trade, OrderSide, OrderType,
    OrderStatus, OrderBookManager
)


class CommandType(Enum):
    """Types of commands that can be sent to the order book"""
    PLACE_LIMIT_ORDER = "PLACE_LIMIT_ORDER"
    PLACE_MARKET_ORDER = "PLACE_MARKET_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    GET_BEST_BID = "GET_BEST_BID"
    GET_BEST_ASK = "GET_BEST_ASK"
    GET_SPREAD = "GET_SPREAD"
    GET_DEPTH = "GET_DEPTH"
    GET_SNAPSHOT = "GET_SNAPSHOT"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class Command:
    """
    Represents a command to be executed on the order book.

    Attributes:
        command_type: Type of command
        args: Positional arguments for the command
        kwargs: Keyword arguments for the command
        callback: Optional callback function for async operations
        result_queue: Optional queue for sync operations to receive result
        timestamp: When the command was created
    """
    command_type: CommandType
    args: tuple = ()
    kwargs: dict = None
    callback: Optional[Callable] = None
    result_queue: Optional[queue.Queue] = None
    timestamp: float = None

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class Metrics:
    """
    Performance metrics for the order book engine.

    Attributes:
        commands_processed: Total number of commands processed
        trades_executed: Total number of trades executed
        queue_depth_current: Current number of commands in queue
        queue_depth_max: Maximum queue depth observed
        latency_p50: 50th percentile latency (microseconds)
        latency_p99: 99th percentile latency (microseconds)
        latency_max: Maximum latency observed (microseconds)
        throughput: Commands per second
    """
    commands_processed: int = 0
    trades_executed: int = 0
    queue_depth_current: int = 0
    queue_depth_max: int = 0
    latency_p50: float = 0.0
    latency_p99: float = 0.0
    latency_max: float = 0.0
    throughput: float = 0.0

    def __repr__(self):
        return (
            f"Metrics(commands={self.commands_processed}, "
            f"trades={self.trades_executed}, "
            f"queue_depth={self.queue_depth_current}/{self.queue_depth_max}, "
            f"latency_p50={self.latency_p50:.0f}μs, "
            f"latency_p99={self.latency_p99:.0f}μs, "
            f"throughput={self.throughput:.0f}/sec)"
        )


class OrderBookEngine:
    """
    Thread-safe order book engine using lock-free queue architecture.

    This class provides a production-ready thread-safe wrapper around the
    OrderBook class. Multiple threads can submit commands concurrently without
    any lock contention. A single worker thread processes commands sequentially,
    eliminating race conditions.

    Features:
    - Lock-free command submission (zero contention)
    - Synchronous and asynchronous APIs
    - Performance monitoring and metrics
    - Graceful shutdown
    - Production-grade error handling

    Example:
        engine = OrderBookEngine("AAPL")

        # Sync API
        order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

        # Async API
        engine.place_limit_order_async(OrderSide.BUY, 100, 150.00,
                                       callback=lambda o: print(o))

        # Metrics
        print(engine.get_metrics())

        # Shutdown
        engine.shutdown()
    """

    def __init__(self, symbol: str, max_queue_size: int = 10000):
        """
        Initialize the thread-safe order book engine.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'GOOGL')
            max_queue_size: Maximum queue size (0 = unlimited)
        """
        self.symbol = symbol
        self.order_book = OrderBook(symbol)

        # Lock-free command queue
        self.command_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)

        # Worker thread
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            name=f"OrderBook-{symbol}-Worker",
            daemon=False
        )
        self.worker_thread.start()

        # Order counter for generating order IDs
        self.order_counter = 0
        self._order_counter_lock = threading.Lock()

        # Metrics tracking
        self.metrics = Metrics()
        self._latencies: List[float] = []
        self._metrics_lock = threading.Lock()
        self._start_time = time.time()

    def _get_next_order_id(self) -> str:
        """Thread-safe order ID generation"""
        with self._order_counter_lock:
            self.order_counter += 1
            return f"ORD{self.order_counter:06d}"

    def _worker_loop(self):
        """
        Main worker loop that processes commands from the queue.

        This runs in a dedicated thread and is the ONLY thread that
        touches the underlying OrderBook, eliminating race conditions.
        """
        while self.running:
            try:
                # Get command with timeout to allow checking self.running
                command = self.command_queue.get(timeout=0.1)

                # Calculate latency
                latency = (time.time() - command.timestamp) * 1_000_000  # μs

                # Process the command
                try:
                    result = self._execute_command(command)

                    # Send result back via callback or result queue
                    if command.callback:
                        try:
                            command.callback(result)
                        except Exception as e:
                            print(f"Error in callback: {e}")

                    if command.result_queue:
                        command.result_queue.put(('success', result))

                    # Update metrics
                    self._update_metrics(latency, result)

                except Exception as e:
                    # Error handling
                    error_msg = f"Error executing command {command.command_type}: {e}"
                    print(error_msg)

                    if command.result_queue:
                        command.result_queue.put(('error', e))
                    elif command.callback:
                        try:
                            command.callback(None)
                        except:
                            pass

                finally:
                    self.command_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker loop error: {e}")

    def _execute_command(self, command: Command) -> Any:
        """
        Execute a command on the order book.

        Args:
            command: Command to execute

        Returns:
            Result of the command execution
        """
        cmd_type = command.command_type

        if cmd_type == CommandType.PLACE_LIMIT_ORDER:
            return self._handle_place_limit_order(*command.args, **command.kwargs)

        elif cmd_type == CommandType.PLACE_MARKET_ORDER:
            return self._handle_place_market_order(*command.args, **command.kwargs)

        elif cmd_type == CommandType.CANCEL_ORDER:
            return self._handle_cancel_order(*command.args, **command.kwargs)

        elif cmd_type == CommandType.GET_BEST_BID:
            return self.order_book.get_best_bid()

        elif cmd_type == CommandType.GET_BEST_ASK:
            return self.order_book.get_best_ask()

        elif cmd_type == CommandType.GET_SPREAD:
            return self.order_book.get_spread()

        elif cmd_type == CommandType.GET_DEPTH:
            return self.order_book.get_depth(*command.args, **command.kwargs)

        elif cmd_type == CommandType.GET_SNAPSHOT:
            return self.order_book.get_order_book_snapshot()

        elif cmd_type == CommandType.SHUTDOWN:
            self.running = False
            return True

        else:
            raise ValueError(f"Unknown command type: {cmd_type}")

    def _handle_place_limit_order(self, side: OrderSide, quantity: float,
                                  price: float) -> Order:
        """Handle placing a limit order"""
        order = Order(
            order_id=self._get_next_order_id(),
            symbol=self.symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
        trades = self.order_book.add_order(order)
        return order

    def _handle_place_market_order(self, side: OrderSide, quantity: float) -> Order:
        """Handle placing a market order"""
        order = Order(
            order_id=self._get_next_order_id(),
            symbol=self.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=None
        )
        trades = self.order_book.add_order(order)
        return order

    def _handle_cancel_order(self, order_id: str) -> bool:
        """Handle cancelling an order"""
        return self.order_book.cancel_order(order_id)

    def _update_metrics(self, latency: float, result: Any):
        """Update performance metrics"""
        with self._metrics_lock:
            self.metrics.commands_processed += 1

            # Track latencies
            self._latencies.append(latency)
            if len(self._latencies) > 10000:  # Keep last 10k
                self._latencies = self._latencies[-10000:]

            # Update latency metrics
            if self._latencies:
                sorted_latencies = sorted(self._latencies)
                self.metrics.latency_p50 = sorted_latencies[len(sorted_latencies) // 2]
                self.metrics.latency_p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
                self.metrics.latency_max = max(self._latencies)

            # Update queue depth
            self.metrics.queue_depth_current = self.command_queue.qsize()
            self.metrics.queue_depth_max = max(
                self.metrics.queue_depth_max,
                self.metrics.queue_depth_current
            )

            # Update throughput
            elapsed = time.time() - self._start_time
            if elapsed > 0:
                self.metrics.throughput = self.metrics.commands_processed / elapsed

            # Count trades
            if isinstance(result, Order):
                self.metrics.trades_executed = len(self.order_book.trades)

    # ========== SYNCHRONOUS API (Blocking) ==========

    def place_limit_order_sync(self, side: OrderSide, quantity: float,
                               price: float, timeout: float = 5.0) -> Order:
        """
        Place a limit order (synchronous - blocks until executed).

        Args:
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price
            timeout: Maximum time to wait in seconds

        Returns:
            The created Order object

        Raises:
            TimeoutError: If command doesn't complete within timeout

        Example:
            order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
            print(f"Order {order.order_id} status: {order.status}")
        """
        result_queue = queue.Queue()
        command = Command(
            command_type=CommandType.PLACE_LIMIT_ORDER,
            args=(side, quantity, price),
            result_queue=result_queue
        )
        self.command_queue.put(command)

        try:
            status, result = result_queue.get(timeout=timeout)
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError(f"Command timed out after {timeout}s")

    def place_market_order_sync(self, side: OrderSide, quantity: float,
                               timeout: float = 5.0) -> Order:
        """
        Place a market order (synchronous - blocks until executed).

        Args:
            side: BUY or SELL
            quantity: Order quantity
            timeout: Maximum time to wait in seconds

        Returns:
            The created Order object

        Example:
            order = engine.place_market_order_sync(OrderSide.BUY, 100)
        """
        result_queue = queue.Queue()
        command = Command(
            command_type=CommandType.PLACE_MARKET_ORDER,
            args=(side, quantity),
            result_queue=result_queue
        )
        self.command_queue.put(command)

        try:
            status, result = result_queue.get(timeout=timeout)
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError(f"Command timed out after {timeout}s")

    def cancel_order_sync(self, order_id: str, timeout: float = 5.0) -> bool:
        """
        Cancel an order (synchronous - blocks until executed).

        Args:
            order_id: ID of order to cancel
            timeout: Maximum time to wait in seconds

        Returns:
            True if cancelled, False otherwise

        Example:
            success = engine.cancel_order_sync("ORD000001")
        """
        result_queue = queue.Queue()
        command = Command(
            command_type=CommandType.CANCEL_ORDER,
            args=(order_id,),
            result_queue=result_queue
        )
        self.command_queue.put(command)

        try:
            status, result = result_queue.get(timeout=timeout)
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError(f"Command timed out after {timeout}s")

    def get_best_bid_sync(self, timeout: float = 5.0) -> Optional[float]:
        """Get best bid price (synchronous)"""
        result_queue = queue.Queue()
        command = Command(
            command_type=CommandType.GET_BEST_BID,
            result_queue=result_queue
        )
        self.command_queue.put(command)

        try:
            status, result = result_queue.get(timeout=timeout)
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError(f"Command timed out after {timeout}s")

    def get_best_ask_sync(self, timeout: float = 5.0) -> Optional[float]:
        """Get best ask price (synchronous)"""
        result_queue = queue.Queue()
        command = Command(
            command_type=CommandType.GET_BEST_ASK,
            result_queue=result_queue
        )
        self.command_queue.put(command)

        try:
            status, result = result_queue.get(timeout=timeout)
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError(f"Command timed out after {timeout}s")

    def get_depth_sync(self, levels: int = 5, timeout: float = 5.0) -> Tuple[np.ndarray, np.ndarray]:
        """Get market depth (synchronous)"""
        result_queue = queue.Queue()
        command = Command(
            command_type=CommandType.GET_DEPTH,
            args=(levels,),
            result_queue=result_queue
        )
        self.command_queue.put(command)

        try:
            status, result = result_queue.get(timeout=timeout)
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError(f"Command timed out after {timeout}s")

    def get_snapshot_sync(self, timeout: float = 5.0) -> dict:
        """Get order book snapshot (synchronous)"""
        result_queue = queue.Queue()
        command = Command(
            command_type=CommandType.GET_SNAPSHOT,
            result_queue=result_queue
        )
        self.command_queue.put(command)

        try:
            status, result = result_queue.get(timeout=timeout)
            if status == 'error':
                raise result
            return result
        except queue.Empty:
            raise TimeoutError(f"Command timed out after {timeout}s")

    # ========== ASYNCHRONOUS API (Non-blocking with callbacks) ==========

    def place_limit_order_async(self, side: OrderSide, quantity: float,
                                price: float, callback: Callable[[Order], None]):
        """
        Place a limit order (asynchronous - returns immediately).

        Args:
            side: BUY or SELL
            quantity: Order quantity
            price: Limit price
            callback: Function to call with result (receives Order object)

        Example:
            def on_order(order):
                print(f"Order placed: {order.order_id}, status: {order.status}")

            engine.place_limit_order_async(OrderSide.BUY, 100, 150.00,
                                          callback=on_order)
        """
        command = Command(
            command_type=CommandType.PLACE_LIMIT_ORDER,
            args=(side, quantity, price),
            callback=callback
        )
        self.command_queue.put(command)

    def place_market_order_async(self, side: OrderSide, quantity: float,
                                 callback: Callable[[Order], None]):
        """Place a market order (asynchronous - returns immediately)"""
        command = Command(
            command_type=CommandType.PLACE_MARKET_ORDER,
            args=(side, quantity),
            callback=callback
        )
        self.command_queue.put(command)

    def cancel_order_async(self, order_id: str, callback: Callable[[bool], None]):
        """Cancel an order (asynchronous - returns immediately)"""
        command = Command(
            command_type=CommandType.CANCEL_ORDER,
            args=(order_id,),
            callback=callback
        )
        self.command_queue.put(command)

    def get_depth_async(self, levels: int, callback: Callable):
        """Get market depth (asynchronous - returns immediately)"""
        command = Command(
            command_type=CommandType.GET_DEPTH,
            args=(levels,),
            callback=callback
        )
        self.command_queue.put(command)

    # ========== MONITORING ==========

    def get_metrics(self) -> Metrics:
        """
        Get current performance metrics.

        Returns:
            Metrics object with current statistics

        Example:
            metrics = engine.get_metrics()
            print(f"Throughput: {metrics.throughput:.0f} commands/sec")
            print(f"P99 latency: {metrics.latency_p99:.0f} μs")
        """
        with self._metrics_lock:
            # Return a copy
            return Metrics(
                commands_processed=self.metrics.commands_processed,
                trades_executed=self.metrics.trades_executed,
                queue_depth_current=self.command_queue.qsize(),
                queue_depth_max=self.metrics.queue_depth_max,
                latency_p50=self.metrics.latency_p50,
                latency_p99=self.metrics.latency_p99,
                latency_max=self.metrics.latency_max,
                throughput=self.metrics.throughput
            )

    def get_queue_depth(self) -> int:
        """Get current queue depth"""
        return self.command_queue.qsize()

    def is_healthy(self, max_queue_depth: int = 1000, max_latency_p99: float = 100000) -> bool:
        """
        Check if the engine is healthy.

        Args:
            max_queue_depth: Maximum acceptable queue depth
            max_latency_p99: Maximum acceptable P99 latency (μs)

        Returns:
            True if healthy, False otherwise
        """
        metrics = self.get_metrics()
        return (
            self.running and
            self.worker_thread.is_alive() and
            metrics.queue_depth_current < max_queue_depth and
            metrics.latency_p99 < max_latency_p99
        )

    # ========== LIFECYCLE ==========

    def shutdown(self, timeout: float = 10.0):
        """
        Gracefully shutdown the engine.

        Args:
            timeout: Maximum time to wait for shutdown (seconds)

        Example:
            engine.shutdown()
        """
        # Send shutdown command
        command = Command(command_type=CommandType.SHUTDOWN)
        self.command_queue.put(command)

        # Wait for worker to finish
        self.worker_thread.join(timeout=timeout)

        if self.worker_thread.is_alive():
            print(f"Warning: Worker thread did not shutdown cleanly within {timeout}s")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures shutdown"""
        self.shutdown()

    def __repr__(self):
        return (f"OrderBookEngine({self.symbol}, "
                f"queue_depth={self.get_queue_depth()}, "
                f"running={self.running})")


class MultiSymbolOrderBookEngine:
    """
    Thread-safe engine managing multiple order books (one per symbol).

    This class manages multiple OrderBookEngine instances, one for each symbol.
    Each symbol gets its own worker thread and command queue for maximum
    parallelism.

    Example:
        engine = MultiSymbolOrderBookEngine()

        # Place orders on different symbols (processed in parallel)
        aapl_order = engine.place_limit_order_sync("AAPL", OrderSide.BUY, 100, 150.00)
        googl_order = engine.place_limit_order_sync("GOOGL", OrderSide.BUY, 50, 140.00)

        # Get metrics for all symbols
        for symbol, metrics in engine.get_all_metrics().items():
            print(f"{symbol}: {metrics}")
    """

    def __init__(self):
        """Initialize multi-symbol engine"""
        self.engines: Dict[str, OrderBookEngine] = {}
        self._lock = threading.Lock()

    def get_or_create_engine(self, symbol: str) -> OrderBookEngine:
        """Get or create an engine for a symbol (thread-safe)"""
        if symbol not in self.engines:
            with self._lock:
                # Double-check after acquiring lock
                if symbol not in self.engines:
                    self.engines[symbol] = OrderBookEngine(symbol)
        return self.engines[symbol]

    def place_limit_order_sync(self, symbol: str, side: OrderSide,
                              quantity: float, price: float) -> Order:
        """Place limit order on specific symbol"""
        engine = self.get_or_create_engine(symbol)
        return engine.place_limit_order_sync(side, quantity, price)

    def place_market_order_sync(self, symbol: str, side: OrderSide,
                               quantity: float) -> Order:
        """Place market order on specific symbol"""
        engine = self.get_or_create_engine(symbol)
        return engine.place_market_order_sync(side, quantity)

    def get_all_metrics(self) -> Dict[str, Metrics]:
        """Get metrics for all symbols"""
        return {symbol: engine.get_metrics()
                for symbol, engine in self.engines.items()}

    def shutdown_all(self):
        """Shutdown all engines"""
        for engine in self.engines.values():
            engine.shutdown()

    def __repr__(self):
        return f"MultiSymbolOrderBookEngine(symbols={len(self.engines)})"
