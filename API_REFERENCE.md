# 📖 Order Book API Reference

Complete API reference for the thread-safe order book system.

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![NumPy](https://img.shields.io/badge/numpy-required-orange.svg)](https://numpy.org/)
[![Thread-Safe](https://img.shields.io/badge/thread--safe-yes-green.svg)](API_REFERENCE.md)

**📚 Other Documentation:**
- [← Back to README](README.md)
- [Usage Guide](THREAD_SAFE_USAGE.md)
- [Examples](example.py)

---

## Table of Contents

### Core Classes
1. [OrderBookEngine](#orderbookengine) - Single-symbol thread-safe order book
   - [Constructor](#constructor)
   - [Synchronous API](#synchronous-api-blocking)
   - [Asynchronous API](#asynchronous-api-non-blocking)
   - [Monitoring & Utility](#monitoring--utility-methods)
2. [MultiSymbolOrderBookEngine](#multisymbolorderbookengine) - Multi-symbol trading

### Data Types
3. [Data Classes](#data-classes) - Order, Trade, Metrics
4. [Enums](#enums) - OrderSide, OrderType, OrderStatus, CommandType

### Reference
5. [Quick Reference](#quick-reference) - Common operations
6. [Error Handling](#error-handling) - Exceptions and examples
7. [Performance](#performance-characteristics) - Time complexity and latency

---

## OrderBookEngine

Thread-safe order book for a single symbol using lock-free queue architecture.

### Method Summary

| Category | Method | Description |
|----------|--------|-------------|
| **Sync API** | `place_limit_order_sync()` | Place limit order (blocking) |
| | `place_market_order_sync()` | Place market order (blocking) |
| | `cancel_order_sync()` | Cancel order (blocking) |
| | `get_best_bid_sync()` | Get best bid price (blocking) |
| | `get_best_ask_sync()` | Get best ask price (blocking) |
| | `get_depth_sync()` | Get market depth (blocking) |
| | `get_snapshot_sync()` | Get order book snapshot (blocking) |
| **Async API** | `place_limit_order_async()` | Place limit order (non-blocking) |
| | `place_market_order_async()` | Place market order (non-blocking) |
| | `cancel_order_async()` | Cancel order (non-blocking) |
| | `get_depth_async()` | Get market depth (non-blocking) |
| **Monitoring** | `get_metrics()` | Get performance metrics |
| | `get_queue_depth()` | Get current queue depth |
| | `is_healthy()` | Check engine health |
| **Lifecycle** | `shutdown()` | Gracefully shutdown engine |

[Jump to detailed documentation ↓](#constructor)

---

### Constructor

```python
OrderBookEngine(symbol: str, max_queue_size: int = 10000)
```

**Parameters:**
- `symbol` (str): Trading symbol (e.g., 'AAPL', 'GOOGL')
- `max_queue_size` (int): Maximum queue size (0 = unlimited, default = 10000)

**Example:**
```python
engine = OrderBookEngine("AAPL")
engine = OrderBookEngine("TSLA", max_queue_size=5000)
```

---

### Synchronous API (Blocking)

Methods that block until the command completes and return the result.

#### place_limit_order_sync()

```python
place_limit_order_sync(
    side: OrderSide,
    quantity: float,
    price: float,
    timeout: float = 5.0
) -> Order
```

Place a limit order (blocks until executed).

**Parameters:**
- `side` (OrderSide): BUY or SELL
- `quantity` (float): Order quantity (must be > 0)
- `price` (float): Limit price (must be > 0)
- `timeout` (float): Maximum wait time in seconds (default = 5.0)

**Returns:**
- `Order`: The created order with status and fill information

**Raises:**
- `TimeoutError`: If command doesn't complete within timeout
- `ValueError`: If validation fails (negative/zero quantity or price)

**Example:**
```python
order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
print(f"Order {order.order_id}: {order.status.value}")
```

---

#### place_market_order_sync()

```python
place_market_order_sync(
    side: OrderSide,
    quantity: float,
    timeout: float = 5.0
) -> Order
```

Place a market order (blocks until executed).

**Parameters:**
- `side` (OrderSide): BUY or SELL
- `quantity` (float): Order quantity (must be > 0)
- `timeout` (float): Maximum wait time in seconds (default = 5.0)

**Returns:**
- `Order`: The created order with status and fill information

**Raises:**
- `TimeoutError`: If command doesn't complete within timeout
- `ValueError`: If validation fails (negative/zero quantity)

**Example:**
```python
order = engine.place_market_order_sync(OrderSide.BUY, 100)
print(f"Filled: {order.filled_quantity}/{order.quantity}")
```

---

#### cancel_order_sync()

```python
cancel_order_sync(
    order_id: str,
    timeout: float = 5.0
) -> bool
```

Cancel an order (blocks until executed).

**Parameters:**
- `order_id` (str): ID of order to cancel
- `timeout` (float): Maximum wait time in seconds (default = 5.0)

**Returns:**
- `bool`: True if cancelled, False if not found or already filled/cancelled

**Raises:**
- `TimeoutError`: If command doesn't complete within timeout

**Example:**
```python
success = engine.cancel_order_sync("ORD000001")
print(f"Cancelled: {success}")
```

---

#### get_best_bid_sync()

```python
get_best_bid_sync(timeout: float = 5.0) -> Optional[float]
```

Get the highest bid price (blocks until retrieved).

**Parameters:**
- `timeout` (float): Maximum wait time in seconds (default = 5.0)

**Returns:**
- `Optional[float]`: Best bid price, or None if no bids

**Example:**
```python
best_bid = engine.get_best_bid_sync()
print(f"Best bid: ${best_bid}")
```

---

#### get_best_ask_sync()

```python
get_best_ask_sync(timeout: float = 5.0) -> Optional[float]
```

Get the lowest ask price (blocks until retrieved).

**Parameters:**
- `timeout` (float): Maximum wait time in seconds (default = 5.0)

**Returns:**
- `Optional[float]`: Best ask price, or None if no asks

**Example:**
```python
best_ask = engine.get_best_ask_sync()
print(f"Best ask: ${best_ask}")
```

---

#### get_depth_sync()

```python
get_depth_sync(
    levels: int = 5,
    timeout: float = 5.0
) -> Tuple[np.ndarray, np.ndarray]
```

Get market depth (blocks until retrieved).

**Parameters:**
- `levels` (int): Number of price levels to return (default = 5)
- `timeout` (float): Maximum wait time in seconds (default = 5.0)

**Returns:**
- `Tuple[np.ndarray, np.ndarray]`: (bids, asks) as NumPy arrays with shape (levels, 2)
  - Each row is [price, total_quantity]

**Example:**
```python
bids, asks = engine.get_depth_sync(levels=10)
print(f"Top bid: ${bids[0][0]} x {bids[0][1]}")
```

---

#### get_snapshot_sync()

```python
get_snapshot_sync(timeout: float = 5.0) -> dict
```

Get complete order book snapshot (blocks until retrieved).

**Parameters:**
- `timeout` (float): Maximum wait time in seconds (default = 5.0)

**Returns:**
- `dict`: Snapshot with keys:
  - `symbol` (str): Trading symbol
  - `best_bid` (Optional[float]): Best bid price
  - `best_ask` (Optional[float]): Best ask price
  - `spread` (Optional[float]): Bid-ask spread
  - `bids` (np.ndarray): Bid depth
  - `asks` (np.ndarray): Ask depth
  - `total_trades` (int): Total trades executed

**Example:**
```python
snapshot = engine.get_snapshot_sync()
print(f"Symbol: {snapshot['symbol']}")
print(f"Spread: ${snapshot['spread']}")
```

---

### Asynchronous API (Non-Blocking)

Methods that return immediately and invoke a callback when the command completes.

#### place_limit_order_async()

```python
place_limit_order_async(
    side: OrderSide,
    quantity: float,
    price: float,
    callback: Callable[[Order], None]
)
```

Place a limit order (returns immediately).

**Parameters:**
- `side` (OrderSide): BUY or SELL
- `quantity` (float): Order quantity (must be > 0)
- `price` (float): Limit price (must be > 0)
- `callback` (Callable): Function to call with result (receives Order object)

**Returns:**
- None (result provided via callback)

**Example:**
```python
def on_order(order):
    print(f"Order placed: {order.order_id}, status: {order.status.value}")

engine.place_limit_order_async(OrderSide.BUY, 100, 150.00, callback=on_order)
```

---

#### place_market_order_async()

```python
place_market_order_async(
    side: OrderSide,
    quantity: float,
    callback: Callable[[Order], None]
)
```

Place a market order (returns immediately).

**Parameters:**
- `side` (OrderSide): BUY or SELL
- `quantity` (float): Order quantity (must be > 0)
- `callback` (Callable): Function to call with result (receives Order object)

**Returns:**
- None (result provided via callback)

**Example:**
```python
engine.place_market_order_async(
    OrderSide.BUY, 100,
    callback=lambda o: print(f"Filled: {o.filled_quantity}")
)
```

---

#### cancel_order_async()

```python
cancel_order_async(
    order_id: str,
    callback: Callable[[bool], None]
)
```

Cancel an order (returns immediately).

**Parameters:**
- `order_id` (str): ID of order to cancel
- `callback` (Callable): Function to call with result (receives bool)

**Returns:**
- None (result provided via callback)

**Example:**
```python
engine.cancel_order_async(
    "ORD000001",
    callback=lambda success: print(f"Cancelled: {success}")
)
```

---

#### get_depth_async()

```python
get_depth_async(
    levels: int,
    callback: Callable[[Tuple[np.ndarray, np.ndarray]], None]
)
```

Get market depth (returns immediately).

**Parameters:**
- `levels` (int): Number of price levels to return
- `callback` (Callable): Function to call with result (receives (bids, asks))

**Returns:**
- None (result provided via callback)

**Example:**
```python
def on_depth(result):
    bids, asks = result
    print(f"Top bid: ${bids[0][0]}")

engine.get_depth_async(10, callback=on_depth)
```

---

### Monitoring & Utility Methods

#### get_metrics()

```python
get_metrics() -> Metrics
```

Get current performance metrics.

**Returns:**
- `Metrics`: Object with attributes:
  - `commands_processed` (int): Total commands processed
  - `trades_executed` (int): Total trades executed
  - `queue_depth_current` (int): Current queue depth
  - `queue_depth_max` (int): Maximum queue depth observed
  - `latency_p50` (float): 50th percentile latency (μs)
  - `latency_p99` (float): 99th percentile latency (μs)
  - `latency_max` (float): Maximum latency (μs)
  - `throughput` (float): Commands per second

**Example:**
```python
metrics = engine.get_metrics()
print(f"Throughput: {metrics.throughput:.0f} orders/sec")
print(f"P99 latency: {metrics.latency_p99:.0f} μs")
```

---

#### get_queue_depth()

```python
get_queue_depth() -> int
```

Get current queue depth.

**Returns:**
- `int`: Number of commands currently in queue

**Example:**
```python
depth = engine.get_queue_depth()
if depth > 1000:
    print("⚠️ High queue depth!")
```

---

#### is_healthy()

```python
is_healthy(
    max_queue_depth: int = 1000,
    max_latency_p99: float = 100000
) -> bool
```

Check if the engine is healthy.

**Parameters:**
- `max_queue_depth` (int): Maximum acceptable queue depth (default = 1000)
- `max_latency_p99` (float): Maximum acceptable P99 latency in μs (default = 100000)

**Returns:**
- `bool`: True if healthy, False otherwise

**Example:**
```python
if engine.is_healthy():
    print("✓ Engine healthy")
else:
    print("✗ Engine unhealthy")
```

---

#### shutdown()

```python
shutdown(timeout: float = 10.0)
```

Gracefully shutdown the engine.

**Parameters:**
- `timeout` (float): Maximum time to wait for shutdown in seconds (default = 10.0)

**Returns:**
- None

**Example:**
```python
engine.shutdown()
```

---

### Context Manager Support

```python
with OrderBookEngine("AAPL") as engine:
    # Use engine
    order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
# Automatically shuts down
```

---

### Properties

#### symbol

```python
engine.symbol  # str
```

Trading symbol for this engine.

#### running

```python
engine.running  # bool
```

Whether the worker thread is running.

---

## MultiSymbolOrderBookEngine

Manages multiple order books (one per symbol) with parallel processing.

### Constructor

```python
MultiSymbolOrderBookEngine()
```

**Example:**
```python
engine = MultiSymbolOrderBookEngine()
```

---

### Methods

#### get_or_create_engine()

```python
get_or_create_engine(symbol: str) -> OrderBookEngine
```

Get or create an engine for a symbol (thread-safe).

**Parameters:**
- `symbol` (str): Trading symbol

**Returns:**
- `OrderBookEngine`: Engine for the symbol

**Example:**
```python
aapl_engine = engine.get_or_create_engine("AAPL")
```

---

#### place_limit_order_sync()

```python
place_limit_order_sync(
    symbol: str,
    side: OrderSide,
    quantity: float,
    price: float
) -> Order
```

Place limit order on specific symbol.

**Parameters:**
- `symbol` (str): Trading symbol
- `side` (OrderSide): BUY or SELL
- `quantity` (float): Order quantity
- `price` (float): Limit price

**Returns:**
- `Order`: The created order

**Example:**
```python
aapl = engine.place_limit_order_sync("AAPL", OrderSide.BUY, 100, 150.00)
googl = engine.place_limit_order_sync("GOOGL", OrderSide.BUY, 50, 140.00)
```

---

#### place_market_order_sync()

```python
place_market_order_sync(
    symbol: str,
    side: OrderSide,
    quantity: float
) -> Order
```

Place market order on specific symbol.

**Parameters:**
- `symbol` (str): Trading symbol
- `side` (OrderSide): BUY or SELL
- `quantity` (float): Order quantity

**Returns:**
- `Order`: The created order

**Example:**
```python
order = engine.place_market_order_sync("TSLA", OrderSide.SELL, 75)
```

---

#### get_all_metrics()

```python
get_all_metrics() -> Dict[str, Metrics]
```

Get metrics for all symbols.

**Returns:**
- `Dict[str, Metrics]`: Dictionary mapping symbol to Metrics object

**Example:**
```python
for symbol, metrics in engine.get_all_metrics().items():
    print(f"{symbol}: {metrics.throughput:.0f} orders/sec")
```

---

#### shutdown_all()

```python
shutdown_all()
```

Shutdown all engines.

**Returns:**
- None

**Example:**
```python
engine.shutdown_all()
```

---

## Data Classes

### Order

Represents a trading order.

```python
@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
```

**Attributes:**
- `order_id` (str): Unique identifier (auto-generated)
- `symbol` (str): Trading symbol
- `side` (OrderSide): BUY or SELL
- `order_type` (OrderType): LIMIT or MARKET
- `quantity` (float): Order quantity
- `price` (Optional[float]): Limit price (None for market orders)
- `timestamp` (float): Order creation time (Unix timestamp)
- `status` (OrderStatus): Current order status
- `filled_quantity` (float): Amount filled so far

**Methods:**

```python
order.remaining_quantity() -> float
```
Get the remaining unfilled quantity.

```python
order.is_complete() -> bool
```
Check if order is completely filled.

**Example:**
```python
order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
print(f"Order ID: {order.order_id}")
print(f"Status: {order.status.value}")
print(f"Filled: {order.filled_quantity}/{order.quantity}")
print(f"Remaining: {order.remaining_quantity()}")
```

---

### Trade

Represents an executed trade.

```python
@dataclass
class Trade:
    trade_id: str
    symbol: str
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)
```

**Attributes:**
- `trade_id` (str): Unique trade identifier (auto-generated)
- `symbol` (str): Trading symbol
- `buy_order_id` (str): ID of the buy order
- `sell_order_id` (str): ID of the sell order
- `price` (float): Execution price
- `quantity` (float): Executed quantity
- `timestamp` (float): Execution time (Unix timestamp)

**Example:**
```python
# Trades are created automatically during order matching
# Access via order book's trades list
trades = engine.order_book.trades
for trade in trades:
    print(f"{trade.symbol}: {trade.quantity} @ ${trade.price}")
```

---

### Metrics

Performance metrics for the order book engine.

```python
@dataclass
class Metrics:
    commands_processed: int = 0
    trades_executed: int = 0
    queue_depth_current: int = 0
    queue_depth_max: int = 0
    latency_p50: float = 0.0
    latency_p99: float = 0.0
    latency_max: float = 0.0
    throughput: float = 0.0
```

**Attributes:**
- `commands_processed` (int): Total number of commands processed
- `trades_executed` (int): Total number of trades executed
- `queue_depth_current` (int): Current number of commands in queue
- `queue_depth_max` (int): Maximum queue depth observed
- `latency_p50` (float): 50th percentile latency (microseconds)
- `latency_p99` (float): 99th percentile latency (microseconds)
- `latency_max` (float): Maximum latency observed (microseconds)
- `throughput` (float): Commands per second

**Example:**
```python
metrics = engine.get_metrics()
print(f"Processed: {metrics.commands_processed} commands")
print(f"P99 latency: {metrics.latency_p99:.0f} μs")
print(f"Throughput: {metrics.throughput:.0f}/sec")
```

---

## Enums

### OrderSide

```python
class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"
```

**Usage:**
```python
from orderbook import OrderSide

order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
```

---

### OrderType

```python
class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
```

**Note:** This enum is used internally. Use `place_limit_order_*` or `place_market_order_*` methods instead.

---

### OrderStatus

```python
class OrderStatus(Enum):
    PENDING = "PENDING"    # Order placed, not filled
    PARTIAL = "PARTIAL"    # Order partially filled
    FILLED = "FILLED"      # Order completely filled
    CANCELLED = "CANCELLED" # Order cancelled
```

**Usage:**
```python
order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

if order.status == OrderStatus.FILLED:
    print("Order filled!")
elif order.status == OrderStatus.PARTIAL:
    print(f"Partially filled: {order.filled_quantity}/{order.quantity}")
```

---

### CommandType

```python
class CommandType(Enum):
    PLACE_LIMIT_ORDER = "PLACE_LIMIT_ORDER"
    PLACE_MARKET_ORDER = "PLACE_MARKET_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    GET_BEST_BID = "GET_BEST_BID"
    GET_BEST_ASK = "GET_BEST_ASK"
    GET_SPREAD = "GET_SPREAD"
    GET_DEPTH = "GET_DEPTH"
    GET_SNAPSHOT = "GET_SNAPSHOT"
    SHUTDOWN = "SHUTDOWN"
```

**Note:** This enum is used internally by the command pattern. Users don't need to use it directly.

---

## Quick Reference

### Common Operations

```python
# Import
from orderbook import OrderBookEngine, OrderSide

# Create engine
engine = OrderBookEngine("AAPL")

# Place orders (sync)
buy = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
sell = engine.place_market_order_sync(OrderSide.SELL, 50)

# Place orders (async)
engine.place_limit_order_async(
    OrderSide.BUY, 100, 150.00,
    callback=lambda o: print(o.order_id)
)

# Cancel order
engine.cancel_order_sync(buy.order_id)

# Get market data
best_bid = engine.get_best_bid_sync()
best_ask = engine.get_best_ask_sync()
bids, asks = engine.get_depth_sync(levels=5)

# Monitor performance
metrics = engine.get_metrics()
is_healthy = engine.is_healthy()

# Shutdown
engine.shutdown()
```

---

## Error Handling

### Exceptions

- `ValueError`: Raised for validation errors (negative/zero quantity/price, missing price for limit orders)
- `TimeoutError`: Raised when sync operations exceed timeout

### Example

```python
try:
    order = engine.place_limit_order_sync(
        OrderSide.BUY, -100, 150.00  # Invalid quantity
    )
except ValueError as e:
    print(f"Validation error: {e}")

try:
    order = engine.place_limit_order_sync(
        OrderSide.BUY, 100, 150.00,
        timeout=0.001  # Very short timeout
    )
except TimeoutError as e:
    print(f"Timeout: {e}")
```

---

## Performance Characteristics

| Operation | Time Complexity | Typical Latency |
|-----------|----------------|-----------------|
| place_*_sync() | O(1) enqueue + O(k) matching | 300-800 μs |
| place_*_async() | O(1) enqueue | <10 μs |
| cancel_order_sync() | O(1) enqueue + O(n) search | 50-100 μs |
| get_best_bid/ask_sync() | O(1) enqueue + O(1) lookup | 30-50 μs |
| get_depth_sync() | O(1) enqueue + O(n log k) | 50-100 μs |

Where:
- k = number of price levels crossed during matching
- n = number of orders at a price level

---

## See Also

- **THREAD_SAFE_USAGE.md**: Comprehensive usage guide with examples
- **README.md**: Project overview and quick start
- **example.py**: Working examples demonstrating all features
