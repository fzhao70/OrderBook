# Simple Order Book for Trading

A simple, efficient, and easy-to-use order book implementation for trading multiple stocks and derivatives using Python and NumPy.

## Features

- **Multiple Instruments**: Trade stocks, options, futures, and other derivatives
- **Order Types**: Support for limit and market orders
- **Price-Time Priority**: Standard FIFO matching at each price level
- **Efficient Data Structures**: Uses NumPy for fast market depth calculations
- **Real-time Matching**: Automatic order matching and trade execution
- **Event Callbacks**: Real-time notifications for trades and order updates
- **Market Data**: Best bid/ask, spread, market depth, and trade history
- **Order Management**: Place, cancel, and track orders across multiple instruments

## Installation

### Requirements

- Python 3.7+
- NumPy

```bash
pip install numpy
```

## Quick Start

```python
from orderbook import OrderBookManager, OrderSide

# Create the manager
manager = OrderBookManager()

# Create order book for a symbol
manager.create_order_book("AAPL")

# Place limit orders
buy_order = manager.place_limit_order("AAPL", OrderSide.BUY, 100, 150.00)
sell_order = manager.place_limit_order("AAPL", OrderSide.SELL, 100, 151.00)

# Place market order
market_order = manager.place_market_order("AAPL", OrderSide.BUY, 50)

# Check order status
print(f"Order status: {buy_order.status.value}")
print(f"Filled quantity: {buy_order.filled_quantity}")

# Get market data
aapl_book = manager.get_order_book("AAPL")
print(f"Best bid: ${aapl_book.get_best_bid()}")
print(f"Best ask: ${aapl_book.get_best_ask()}")
print(f"Spread: ${aapl_book.get_spread()}")

# View trades
trades = manager.get_all_trades("AAPL")
for trade in trades:
    print(trade)
```

## Usage Examples

### Example 1: Basic Limit Orders

```python
from orderbook import OrderBookManager, OrderSide

manager = OrderBookManager()
manager.create_order_book("AAPL")

# Place buy orders
manager.place_limit_order("AAPL", OrderSide.BUY, 100, 150.00)
manager.place_limit_order("AAPL", OrderSide.BUY, 200, 149.50)

# Place sell orders
manager.place_limit_order("AAPL", OrderSide.SELL, 100, 151.00)
manager.place_limit_order("AAPL", OrderSide.SELL, 150, 151.50)

# View order book depth
aapl_book = manager.get_order_book("AAPL")
bids, asks = aapl_book.get_depth(levels=5)
print("Bids:", bids)  # NumPy array of [price, quantity]
print("Asks:", asks)  # NumPy array of [price, quantity]
```

### Example 2: Market Orders

```python
from orderbook import OrderBookManager, OrderSide

manager = OrderBookManager()
manager.create_order_book("TSLA")

# Build order book
manager.place_limit_order("TSLA", OrderSide.SELL, 50, 250.00)
manager.place_limit_order("TSLA", OrderSide.SELL, 100, 251.00)

# Execute market buy (fills against best asks)
market_order = manager.place_market_order("TSLA", OrderSide.BUY, 120)

# Check execution
print(f"Status: {market_order.status.value}")
print(f"Filled: {market_order.filled_quantity}/{market_order.quantity}")

# View executed trades
trades = manager.get_all_trades("TSLA")
for trade in trades:
    print(f"{trade.quantity} shares @ ${trade.price}")
```

### Example 3: Multiple Instruments (Stocks & Derivatives)

```python
from orderbook import OrderBookManager, OrderSide

manager = OrderBookManager()

# Create order books for different instruments
instruments = ["AAPL", "GOOGL", "SPY_CALL_450", "QQQ_PUT_380"]
for symbol in instruments:
    manager.create_order_book(symbol)

# Place orders across instruments
manager.place_limit_order("AAPL", OrderSide.BUY, 100, 150.00)
manager.place_limit_order("SPY_CALL_450", OrderSide.BUY, 10, 5.50)
manager.place_limit_order("QQQ_PUT_380", OrderSide.SELL, 20, 3.40)

# Get market summary
summary = manager.get_market_summary()
for symbol, data in summary.items():
    print(f"{symbol}: Bid=${data['best_bid']}, Ask=${data['best_ask']}")

# Portfolio statistics
stats = manager.get_portfolio_stats()
print(f"Total instruments: {stats['total_instruments']}")
print(f"Total orders: {stats['total_orders']}")
print(f"Total trades: {stats['total_trades']}")
```

### Example 4: Order Cancellation

```python
from orderbook import OrderBookManager, OrderSide

manager = OrderBookManager()
manager.create_order_book("MSFT")

# Place order
order = manager.place_limit_order("MSFT", OrderSide.BUY, 100, 380.00)
print(f"Order ID: {order.order_id}")

# Cancel order
success = manager.cancel_order(order.order_id)
print(f"Cancelled: {success}")
print(f"Status: {order.status.value}")
```

### Example 5: Market Depth Analysis with NumPy

```python
import numpy as np
from orderbook import OrderBookManager, OrderSide

manager = OrderBookManager()
manager.create_order_book("NVDA")

# Build order book
prices = np.array([300.0, 300.5, 301.0, 301.5, 302.0])
quantities = np.array([100, 150, 200, 120, 180])

for price, qty in zip(prices, quantities):
    manager.place_limit_order("NVDA", OrderSide.SELL, float(qty), float(price))

# Analyze depth
nvda_book = manager.get_order_book("NVDA")
bids, asks = nvda_book.get_depth(levels=10)

# Calculate statistics with NumPy
total_volume = np.sum(asks[:5, 1])
avg_price = np.mean(asks[:5, 0])
vwap = np.sum(asks[:, 0] * asks[:, 1]) / np.sum(asks[:, 1])

print(f"Total volume: {total_volume}")
print(f"Average price: ${avg_price:.2f}")
print(f"VWAP: ${vwap:.2f}")
```

### Example 6: Real-time Callbacks

```python
from orderbook import OrderBookManager, OrderSide, Trade, Order

# Define callbacks
def on_trade(trade: Trade):
    print(f"Trade executed: {trade.symbol} - {trade.quantity} @ ${trade.price}")

def on_order_update(order: Order):
    print(f"Order {order.order_id} updated: {order.status.value}")

# Set up manager with callbacks
manager = OrderBookManager()
manager.on_trade_callback = on_trade
manager.on_order_update_callback = on_order_update

# Create order book and trade
manager.create_order_book("AMD")
manager.place_limit_order("AMD", OrderSide.BUY, 100, 165.00)
manager.place_limit_order("AMD", OrderSide.SELL, 50, 165.00)  # Triggers callbacks
```

## API Reference

### OrderBookManager

Main interface for managing multiple order books.

#### Methods

- `create_order_book(symbol: str) -> OrderBook`: Create order book for a symbol
- `get_order_book(symbol: str) -> Optional[OrderBook]`: Get order book for a symbol
- `place_order(symbol, side, quantity, order_type, price) -> Order`: Place an order
- `place_limit_order(symbol, side, quantity, price) -> Order`: Place limit order
- `place_market_order(symbol, side, quantity) -> Order`: Place market order
- `cancel_order(order_id: str) -> bool`: Cancel an order
- `get_order(order_id: str) -> Optional[Order]`: Get order by ID
- `get_all_trades(symbol: Optional[str]) -> List[Trade]`: Get trades
- `get_market_summary() -> dict`: Get summary of all order books
- `get_portfolio_stats() -> dict`: Get overall statistics

### OrderBook

Represents an order book for a single instrument.

#### Methods

- `add_order(order: Order) -> List[Trade]`: Add order and match
- `cancel_order(order_id: str) -> bool`: Cancel an order
- `get_best_bid() -> Optional[float]`: Get highest bid price
- `get_best_ask() -> Optional[float]`: Get lowest ask price
- `get_spread() -> Optional[float]`: Get bid-ask spread
- `get_depth(levels: int) -> Tuple[np.ndarray, np.ndarray]`: Get market depth
- `get_order_book_snapshot() -> dict`: Get complete snapshot

### Order

Represents a trading order.

#### Attributes

- `order_id: str`: Unique identifier
- `symbol: str`: Trading symbol
- `side: OrderSide`: BUY or SELL
- `order_type: OrderType`: LIMIT or MARKET
- `quantity: float`: Order quantity
- `price: Optional[float]`: Limit price
- `status: OrderStatus`: Order status
- `filled_quantity: float`: Amount filled

### Trade

Represents an executed trade.

#### Attributes

- `trade_id: str`: Unique identifier
- `symbol: str`: Trading symbol
- `buy_order_id: str`: Buy order ID
- `sell_order_id: str`: Sell order ID
- `price: float`: Execution price
- `quantity: float`: Executed quantity
- `timestamp: float`: Execution time

## Architecture

### Order Matching

The order book uses **price-time priority** matching:

1. **Price Priority**: Orders at better prices match first
   - For buy orders: higher prices match first
   - For sell orders: lower prices match first

2. **Time Priority**: At the same price level, orders match in FIFO order

### Data Structures

- **Price Levels**: Dictionary mapping prices to deques of orders
- **Order Lookup**: Dictionary for O(1) order retrieval
- **NumPy Arrays**: Used for efficient market depth calculations and analysis

### Matching Algorithm

1. Incoming order is checked against opposite side of the book
2. Orders are matched at each price level until:
   - Incoming order is completely filled, or
   - No more matching orders exist
3. Unfilled limit orders are added to the book
4. Market orders are only matched (never added to book)

## Running Examples

Run the comprehensive example script:

```bash
python example.py
```

This will demonstrate:
- Basic limit order matching
- Market order execution
- Multiple instruments (stocks and derivatives)
- Order cancellation
- Market depth analysis with NumPy
- Real-time callbacks

## Performance Considerations

- **NumPy Arrays**: Used for efficient vectorized operations on market depth
- **Deques**: O(1) append/pop for FIFO order queues
- **Dictionaries**: O(1) average case for order and price level lookup
- **Efficient Matching**: Only iterates through necessary price levels

## Use Cases

- **Algorithmic Trading**: Build and test trading strategies
- **Market Simulation**: Simulate order flow and market dynamics
- **Educational**: Learn how order books work
- **Backtesting**: Test trading algorithms with historical data
- **Derivatives Trading**: Support for options, futures, and other instruments

## Limitations

This is a simplified order book implementation. For production use, consider:

- **Persistence**: Orders are stored in memory only
- **Concurrency**: Not thread-safe (use locks for multi-threaded environments)
- **Order Types**: Only limit and market orders (no stop, IOC, FOK, etc.)
- **Validation**: Limited order validation and risk checks
- **Performance**: For ultra-high-frequency trading, consider more optimized data structures

## Contributing

Feel free to extend this implementation with:
- Additional order types (stop-loss, trailing stop, etc.)
- Order validation and risk management
- Persistence layer (database integration)
- WebSocket API for real-time updates
- Performance optimizations
- Advanced analytics and visualizations

## License

This is a simple educational implementation. Use at your own risk for any production purposes.

## Contact

For questions or improvements, please open an issue or submit a pull request.
