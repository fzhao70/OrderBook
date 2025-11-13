"""
Example usage of the Simple Order Book system.

This script demonstrates:
1. Creating order books for multiple instruments
2. Placing limit and market orders
3. Order matching and trade execution
4. Market data queries
5. Order cancellation
"""

import numpy as np
from orderbook import (
    OrderBookManager, OrderSide, OrderType,
    Order, Trade
)


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print('='*60)


def print_order_book(order_book):
    """Pretty print an order book"""
    print(f"\n📊 Order Book: {order_book.symbol}")
    print("-" * 60)

    bids, asks = order_book.get_depth(levels=5)

    # Print asks (sell orders) in reverse order
    if len(asks) > 0:
        print("\n  ASKS (Sell Orders)")
        print("  " + "-" * 30)
        for price, qty in reversed(asks):
            print(f"  {qty:8.2f} @ ${price:8.2f}")

    # Print spread
    spread = order_book.get_spread()
    if spread is not None:
        print(f"\n  {'SPREAD':^30}")
        print(f"  {f'${spread:.2f}':^30}")

    # Print bids (buy orders)
    if len(bids) > 0:
        print("\n  BIDS (Buy Orders)")
        print("  " + "-" * 30)
        for price, qty in bids:
            print(f"  {qty:8.2f} @ ${price:8.2f}")

    print()


def example_1_basic_limit_orders():
    """Example 1: Basic limit order matching"""
    print_section("Example 1: Basic Limit Order Matching")

    manager = OrderBookManager()

    # Create order book for AAPL
    print("\n1️⃣  Creating order book for AAPL...")
    manager.create_order_book("AAPL")

    # Place some buy orders
    print("\n2️⃣  Placing buy orders...")
    order1 = manager.place_limit_order("AAPL", OrderSide.BUY, 100, 150.00)
    order2 = manager.place_limit_order("AAPL", OrderSide.BUY, 200, 149.50)
    order3 = manager.place_limit_order("AAPL", OrderSide.BUY, 150, 149.00)
    print(f"   - Buy 100 @ $150.00 - Order ID: {order1.order_id}")
    print(f"   - Buy 200 @ $149.50 - Order ID: {order2.order_id}")
    print(f"   - Buy 150 @ $149.00 - Order ID: {order3.order_id}")

    # Place some sell orders
    print("\n3️⃣  Placing sell orders...")
    order4 = manager.place_limit_order("AAPL", OrderSide.SELL, 100, 151.00)
    order5 = manager.place_limit_order("AAPL", OrderSide.SELL, 150, 151.50)
    order6 = manager.place_limit_order("AAPL", OrderSide.SELL, 200, 152.00)
    print(f"   - Sell 100 @ $151.00 - Order ID: {order4.order_id}")
    print(f"   - Sell 150 @ $151.50 - Order ID: {order5.order_id}")
    print(f"   - Sell 200 @ $152.00 - Order ID: {order6.order_id}")

    # Display order book
    aapl_book = manager.get_order_book("AAPL")
    print_order_book(aapl_book)

    # Place a sell order that crosses the spread
    print("\n4️⃣  Placing aggressive sell order that matches...")
    order7 = manager.place_limit_order("AAPL", OrderSide.SELL, 150, 150.00)
    print(f"   - Sell 150 @ $150.00 - Order ID: {order7.order_id}")
    print(f"   - Order Status: {order7.status.value}")
    print(f"   - Filled Quantity: {order7.filled_quantity}")

    # Show trades
    trades = manager.get_all_trades("AAPL")
    print(f"\n5️⃣  Trades Executed: {len(trades)}")
    for trade in trades:
        print(f"   - {trade}")

    # Display updated order book
    print_order_book(aapl_book)


def example_2_market_orders():
    """Example 2: Market order execution"""
    print_section("Example 2: Market Order Execution")

    manager = OrderBookManager()
    manager.create_order_book("TSLA")

    # Build the order book
    print("\n1️⃣  Building order book for TSLA...")

    # Add sell orders
    manager.place_limit_order("TSLA", OrderSide.SELL, 50, 250.00)
    manager.place_limit_order("TSLA", OrderSide.SELL, 100, 251.00)
    manager.place_limit_order("TSLA", OrderSide.SELL, 75, 252.00)

    # Add buy orders
    manager.place_limit_order("TSLA", OrderSide.BUY, 60, 248.00)
    manager.place_limit_order("TSLA", OrderSide.BUY, 100, 247.00)

    tsla_book = manager.get_order_book("TSLA")
    print_order_book(tsla_book)

    # Execute market buy order
    print("\n2️⃣  Executing market buy order for 120 shares...")
    market_order = manager.place_market_order("TSLA", OrderSide.BUY, 120)
    print(f"   - Order ID: {market_order.order_id}")
    print(f"   - Status: {market_order.status.value}")
    print(f"   - Filled: {market_order.filled_quantity}/{market_order.quantity}")

    # Show executed trades
    trades = manager.get_all_trades("TSLA")
    print(f"\n3️⃣  Trades Executed:")
    for trade in trades:
        print(f"   - {trade.quantity} shares @ ${trade.price}")

    # Display updated order book
    print_order_book(tsla_book)


def example_3_multiple_instruments():
    """Example 3: Trading multiple instruments"""
    print_section("Example 3: Multiple Instruments (Stocks & Derivatives)")

    manager = OrderBookManager()

    # Create order books for different instruments
    instruments = ["AAPL", "GOOGL", "SPY_CALL_450", "QQQ_PUT_380"]

    print("\n1️⃣  Creating order books for multiple instruments...")
    for symbol in instruments:
        manager.create_order_book(symbol)
        print(f"   - Created order book for {symbol}")

    # Place orders across different instruments
    print("\n2️⃣  Placing orders across instruments...")

    # AAPL
    manager.place_limit_order("AAPL", OrderSide.BUY, 100, 150.00)
    manager.place_limit_order("AAPL", OrderSide.SELL, 100, 151.00)

    # GOOGL
    manager.place_limit_order("GOOGL", OrderSide.BUY, 50, 140.00)
    manager.place_limit_order("GOOGL", OrderSide.SELL, 50, 142.00)

    # SPY CALL option
    manager.place_limit_order("SPY_CALL_450", OrderSide.BUY, 10, 5.50)
    manager.place_limit_order("SPY_CALL_450", OrderSide.SELL, 10, 5.75)

    # QQQ PUT option
    manager.place_limit_order("QQQ_PUT_380", OrderSide.BUY, 20, 3.20)
    manager.place_limit_order("QQQ_PUT_380", OrderSide.SELL, 20, 3.40)

    # Execute some crossing orders
    print("\n3️⃣  Executing crossing orders...")
    manager.place_limit_order("AAPL", OrderSide.BUY, 50, 151.00)
    manager.place_limit_order("SPY_CALL_450", OrderSide.SELL, 5, 5.50)

    # Get market summary
    print("\n4️⃣  Market Summary:")
    summary = manager.get_market_summary()
    for symbol, data in summary.items():
        print(f"\n   {symbol}:")
        print(f"   - Best Bid: ${data['best_bid']}")
        print(f"   - Best Ask: ${data['best_ask']}")
        print(f"   - Spread: ${data['spread']}")
        print(f"   - Total Trades: {data['total_trades']}")

    # Portfolio statistics
    print("\n5️⃣  Portfolio Statistics:")
    stats = manager.get_portfolio_stats()
    print(f"   - Total Instruments: {stats['total_instruments']}")
    print(f"   - Total Orders: {stats['total_orders']}")
    print(f"   - Total Trades: {stats['total_trades']}")
    print(f"   - Orders by Status: {stats['orders_by_status']}")


def example_4_order_cancellation():
    """Example 4: Order cancellation"""
    print_section("Example 4: Order Cancellation")

    manager = OrderBookManager()
    manager.create_order_book("MSFT")

    print("\n1️⃣  Placing orders...")
    order1 = manager.place_limit_order("MSFT", OrderSide.BUY, 100, 380.00)
    order2 = manager.place_limit_order("MSFT", OrderSide.BUY, 200, 379.50)
    order3 = manager.place_limit_order("MSFT", OrderSide.SELL, 150, 381.00)

    print(f"   - Order 1: {order1.order_id} - Buy 100 @ $380.00")
    print(f"   - Order 2: {order2.order_id} - Buy 200 @ $379.50")
    print(f"   - Order 3: {order3.order_id} - Sell 150 @ $381.00")

    msft_book = manager.get_order_book("MSFT")
    print_order_book(msft_book)

    print(f"\n2️⃣  Cancelling order {order2.order_id}...")
    success = manager.cancel_order(order2.order_id)
    print(f"   - Cancellation {'successful' if success else 'failed'}")
    print(f"   - Order Status: {order2.status.value}")

    print_order_book(msft_book)


def example_5_depth_analysis():
    """Example 5: Market depth analysis with NumPy"""
    print_section("Example 5: Market Depth Analysis")

    manager = OrderBookManager()
    manager.create_order_book("NVDA")

    # Build a deeper order book
    print("\n1️⃣  Building order book with multiple price levels...")

    # Sell orders
    prices_asks = np.array([300.0, 300.5, 301.0, 301.5, 302.0, 302.5, 303.0])
    quantities_asks = np.array([100, 150, 200, 120, 180, 90, 150])

    for price, qty in zip(prices_asks, quantities_asks):
        manager.place_limit_order("NVDA", OrderSide.SELL, float(qty), float(price))

    # Buy orders
    prices_bids = np.array([299.0, 298.5, 298.0, 297.5, 297.0, 296.5, 296.0])
    quantities_bids = np.array([120, 100, 180, 150, 200, 110, 160])

    for price, qty in zip(prices_bids, quantities_bids):
        manager.place_limit_order("NVDA", OrderSide.BUY, float(qty), float(price))

    nvda_book = manager.get_order_book("NVDA")
    print_order_book(nvda_book)

    # Analyze depth
    print("\n2️⃣  Depth Analysis:")
    bids, asks = nvda_book.get_depth(levels=10)

    print(f"\n   Total Bid Volume (top 5): {np.sum(bids[:5, 1]):.2f}")
    print(f"   Total Ask Volume (top 5): {np.sum(asks[:5, 1]):.2f}")
    print(f"   Average Bid Price (top 5): ${np.mean(bids[:5, 0]):.2f}")
    print(f"   Average Ask Price (top 5): ${np.mean(asks[:5, 0]):.2f}")

    # Calculate VWAP (Volume Weighted Average Price)
    if len(bids) > 0:
        bid_vwap = np.sum(bids[:, 0] * bids[:, 1]) / np.sum(bids[:, 1])
        print(f"   Bid VWAP: ${bid_vwap:.2f}")

    if len(asks) > 0:
        ask_vwap = np.sum(asks[:, 0] * asks[:, 1]) / np.sum(asks[:, 1])
        print(f"   Ask VWAP: ${ask_vwap:.2f}")


def example_6_callbacks():
    """Example 6: Using callbacks for real-time updates"""
    print_section("Example 6: Real-time Callbacks")

    # Define callback functions
    def on_trade(trade: Trade):
        print(f"   🔔 TRADE: {trade.symbol} - {trade.quantity} @ ${trade.price}")

    def on_order_update(order: Order):
        if order.status == order.status.FILLED:
            print(f"   ✅ ORDER FILLED: {order.order_id} - {order.symbol}")
        elif order.status == order.status.CANCELLED:
            print(f"   ❌ ORDER CANCELLED: {order.order_id} - {order.symbol}")

    manager = OrderBookManager()
    manager.on_trade_callback = on_trade
    manager.on_order_update_callback = on_order_update

    manager.create_order_book("AMD")

    print("\n1️⃣  Placing orders with real-time callbacks...")

    # Place limit orders
    manager.place_limit_order("AMD", OrderSide.BUY, 100, 165.00)
    manager.place_limit_order("AMD", OrderSide.SELL, 50, 166.00)

    # Execute crossing order (will trigger callbacks)
    print("\n2️⃣  Executing crossing order...")
    manager.place_limit_order("AMD", OrderSide.BUY, 75, 166.00)


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Simple Order Book - Examples".center(60))
    print("="*60)

    examples = [
        example_1_basic_limit_orders,
        example_2_market_orders,
        example_3_multiple_instruments,
        example_4_order_cancellation,
        example_5_depth_analysis,
        example_6_callbacks,
    ]

    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"\n❌ Error in example {i}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("All examples completed!".center(60))
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
