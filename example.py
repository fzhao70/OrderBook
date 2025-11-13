"""
Thread-Safe Order Book Examples

This script demonstrates the thread-safe OrderBookEngine with various use cases:
1. Multi-threaded order submission
2. Synchronous and asynchronous APIs
3. Market data queries
4. Performance monitoring
5. Error handling
6. Multi-symbol trading
"""

import threading
import time
import random
from orderbook_threadsafe import (
    OrderBookEngine,
    MultiSymbolOrderBookEngine,
    OrderSide,
    OrderStatus
)


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*70}")
    print(f"{title:^70}")
    print('='*70)


def example_1_basic_sync():
    """Example 1: Basic synchronous usage"""
    print_section("Example 1: Basic Synchronous API")

    with OrderBookEngine("AAPL") as engine:
        print("\n1️⃣  Placing limit orders...")

        # Place buy orders
        buy1 = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        buy2 = engine.place_limit_order_sync(OrderSide.BUY, 200, 149.50)
        print(f"   Buy orders placed: {buy1.order_id}, {buy2.order_id}")

        # Place sell orders
        sell1 = engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)
        sell2 = engine.place_limit_order_sync(OrderSide.SELL, 150, 151.50)
        print(f"   Sell orders placed: {sell1.order_id}, {sell2.order_id}")

        print("\n2️⃣  Getting market data...")
        best_bid = engine.get_best_bid_sync()
        best_ask = engine.get_best_ask_sync()
        print(f"   Best Bid: ${best_bid}")
        print(f"   Best Ask: ${best_ask}")
        print(f"   Spread: ${best_ask - best_bid}")

        print("\n3️⃣  Placing crossing order...")
        # This will match
        buy3 = engine.place_limit_order_sync(OrderSide.BUY, 50, 151.00)
        print(f"   Order {buy3.order_id}:")
        print(f"   - Status: {buy3.status.value}")
        print(f"   - Filled: {buy3.filled_quantity}/{buy3.quantity}")

        print("\n4️⃣  Market depth...")
        bids, asks = engine.get_depth_sync(levels=5)
        print(f"   Bids: {len(bids)} levels")
        print(f"   Asks: {len(asks)} levels")

        # Engine auto-shuts down when exiting context


def example_2_async_callbacks():
    """Example 2: Asynchronous callbacks"""
    print_section("Example 2: Asynchronous Callbacks")

    engine = OrderBookEngine("GOOGL")

    print("\n1️⃣  Placing orders with callbacks...")

    results = {'placed': 0, 'filled': 0}

    def on_order_placed(order):
        """Callback for async orders"""
        results['placed'] += 1
        if order.status == OrderStatus.FILLED:
            results['filled'] += 1
        print(f"   ✓ Order {order.order_id}: {order.status.value}, "
              f"filled {order.filled_quantity}/{order.quantity}")

    # Place orders asynchronously
    for i in range(5):
        price = 140.00 + i * 0.50
        engine.place_limit_order_async(
            OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
            100,
            price,
            callback=on_order_placed
        )

    # Wait for processing
    time.sleep(0.5)

    print(f"\n2️⃣  Results: {results['placed']} placed, {results['filled']} filled")

    # Cleanup
    engine.shutdown()


def example_3_multi_threaded():
    """Example 3: Multi-threaded order submission"""
    print_section("Example 3: Multi-Threaded Trading")

    engine = OrderBookEngine("TSLA")

    print("\n1️⃣  Launching 10 trader threads...")

    def trader_thread(thread_id, num_orders):
        """Each thread places orders independently"""
        orders_placed = 0
        for i in range(num_orders):
            side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
            price = 250.00 + (thread_id * 0.10) + (i * 0.05)

            try:
                order = engine.place_limit_order_sync(side, 50, price, timeout=2.0)
                orders_placed += 1
            except Exception as e:
                print(f"   Thread {thread_id} error: {e}")

        print(f"   Thread {thread_id}: Placed {orders_placed} orders")

    # Launch threads
    start_time = time.time()
    threads = []
    for i in range(10):
        t = threading.Thread(target=trader_thread, args=(i, 100))
        t.start()
        threads.append(t)

    # Wait for completion
    for t in threads:
        t.join()

    elapsed = time.time() - start_time

    print(f"\n2️⃣  Performance metrics...")
    metrics = engine.get_metrics()
    print(f"   Commands processed: {metrics.commands_processed}")
    print(f"   Elapsed time: {elapsed:.2f}s")
    print(f"   Throughput: {metrics.throughput:.0f} orders/sec")
    print(f"   P50 latency: {metrics.latency_p50:.0f} μs")
    print(f"   P99 latency: {metrics.latency_p99:.0f} μs")
    print(f"   Max queue depth: {metrics.queue_depth_max}")

    engine.shutdown()


def example_4_market_orders():
    """Example 4: Market orders with async API"""
    print_section("Example 4: Market Orders")

    engine = OrderBookEngine("NVDA")

    print("\n1️⃣  Building order book...")

    # Place limit sells
    for i in range(5):
        price = 300.00 + i * 0.50
        engine.place_limit_order_sync(OrderSide.SELL, 100, price)

    print("   Order book built with 5 sell levels")

    print("\n2️⃣  Executing market buy order...")

    def on_market_order(order):
        print(f"   Market order executed!")
        print(f"   - Filled: {order.filled_quantity}/{order.quantity}")
        print(f"   - Status: {order.status.value}")

    engine.place_market_order_async(OrderSide.BUY, 250, callback=on_market_order)

    # Wait for processing
    time.sleep(0.2)

    print("\n3️⃣  Updated market data...")
    snapshot = engine.get_snapshot_sync()
    print(f"   Best Ask: ${snapshot['best_ask']}")
    print(f"   Total Trades: {snapshot['total_trades']}")

    engine.shutdown()


def example_5_monitoring():
    """Example 5: Performance monitoring"""
    print_section("Example 5: Performance Monitoring & Health Checks")

    engine = OrderBookEngine("AMD", max_queue_size=1000)

    print("\n1️⃣  Submitting orders and monitoring...")

    for i in range(500):
        price = 165.00 + random.uniform(-1.0, 1.0)
        side = random.choice([OrderSide.BUY, OrderSide.SELL])
        engine.place_limit_order_async(
            side, 100, price,
            callback=lambda o: None
        )

        # Monitor every 100 orders
        if i % 100 == 0:
            queue_depth = engine.get_queue_depth()
            print(f"   Submitted {i} orders, queue depth: {queue_depth}")

    # Wait for queue to drain
    print("\n2️⃣  Waiting for queue to drain...")
    while engine.get_queue_depth() > 0:
        time.sleep(0.1)

    print("\n3️⃣  Final metrics...")
    metrics = engine.get_metrics()
    print(f"   {metrics}")

    print("\n4️⃣  Health check...")
    is_healthy = engine.is_healthy(max_queue_depth=100, max_latency_p99=50000)
    print(f"   Engine healthy: {is_healthy}")

    engine.shutdown()


def example_6_multi_symbol():
    """Example 6: Multi-symbol trading"""
    print_section("Example 6: Multi-Symbol Trading")

    engine = MultiSymbolOrderBookEngine()

    print("\n1️⃣  Trading multiple symbols in parallel...")

    symbols = ["AAPL", "GOOGL", "TSLA", "NVDA", "AMD"]

    def trade_symbol(symbol):
        """Trade a specific symbol"""
        for i in range(50):
            side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
            price = 100.00 + random.uniform(0, 10)
            engine.place_limit_order_sync(symbol, side, 100, price)
        print(f"   {symbol}: Placed 50 orders")

    # Launch one thread per symbol
    threads = []
    for symbol in symbols:
        t = threading.Thread(target=trade_symbol, args=(symbol,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("\n2️⃣  Metrics by symbol...")
    all_metrics = engine.get_all_metrics()
    for symbol, metrics in all_metrics.items():
        print(f"   {symbol:6s}: {metrics.commands_processed} cmds, "
              f"{metrics.throughput:.0f}/sec")

    print("\n3️⃣  Shutting down all engines...")
    engine.shutdown_all()


def example_7_error_handling():
    """Example 7: Error handling"""
    print_section("Example 7: Error Handling")

    engine = OrderBookEngine("MSFT")

    print("\n1️⃣  Testing timeout...")
    try:
        # This will succeed (normal timeout)
        order = engine.place_limit_order_sync(
            OrderSide.BUY, 100, 380.00,
            timeout=5.0
        )
        print(f"   ✓ Order placed: {order.order_id}")
    except TimeoutError as e:
        print(f"   ✗ Timeout: {e}")

    print("\n2️⃣  Testing validation errors...")
    try:
        # Invalid quantity
        order = engine.place_limit_order_sync(
            OrderSide.BUY, -100, 380.00
        )
    except ValueError as e:
        print(f"   ✓ Caught validation error: {e}")

    try:
        # Invalid price
        order = engine.place_limit_order_sync(
            OrderSide.BUY, 100, 0.00
        )
    except ValueError as e:
        print(f"   ✓ Caught validation error: {e}")

    print("\n3️⃣  Testing callback errors...")

    def buggy_callback(order):
        raise Exception("Intentional error in callback!")

    # Error in callback should not crash the engine
    engine.place_limit_order_async(
        OrderSide.BUY, 100, 380.00,
        callback=buggy_callback
    )

    time.sleep(0.2)

    # Engine should still be healthy
    print(f"   Engine still running: {engine.running}")
    print(f"   Engine healthy: {engine.is_healthy()}")

    engine.shutdown()


def example_8_order_lifecycle():
    """Example 8: Order lifecycle management"""
    print_section("Example 8: Order Lifecycle")

    engine = OrderBookEngine("META")

    print("\n1️⃣  Placing and tracking order...")

    order = engine.place_limit_order_sync(OrderSide.BUY, 100, 450.00)
    print(f"   Order {order.order_id} placed")
    print(f"   Status: {order.status.value}")

    print("\n2️⃣  Cancelling order...")
    success = engine.cancel_order_sync(order.order_id)
    print(f"   Cancelled: {success}")
    print(f"   New status: {order.status.value}")

    print("\n3️⃣  Trying to cancel again...")
    success = engine.cancel_order_sync(order.order_id)
    print(f"   Cancelled: {success} (already cancelled)")

    print("\n4️⃣  Testing filled order cancellation...")
    # Place orders that will match
    sell = engine.place_limit_order_sync(OrderSide.SELL, 50, 450.00)
    buy = engine.place_limit_order_sync(OrderSide.BUY, 50, 450.00)

    print(f"   Buy status: {buy.status.value}")

    # Try to cancel filled order
    success = engine.cancel_order_sync(buy.order_id)
    print(f"   Can cancel filled order: {success} (should be False)")

    engine.shutdown()


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("Thread-Safe Order Book - Examples".center(70))
    print("="*70)

    examples = [
        example_1_basic_sync,
        example_2_async_callbacks,
        example_3_multi_threaded,
        example_4_market_orders,
        example_5_monitoring,
        example_6_multi_symbol,
        example_7_error_handling,
        example_8_order_lifecycle,
    ]

    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"\n❌ Error in example {i}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("All examples completed!".center(70))
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
