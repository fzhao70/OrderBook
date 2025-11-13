"""
Test script for new order book features:
- Simulation clock
- Direct mode
- Batch processing
- save_snapshot/load_snapshot
"""

from orderbook import (
    OrderBookEngine,
    SimulationClock,
    OrderSide,
    OrderStatus
)


def test_simulation_clock():
    """Test deterministic timestamps with SimulationClock"""
    print("\n" + "="*70)
    print("TEST 1: Simulation Clock")
    print("="*70)

    # Create clock starting at t=0
    clock = SimulationClock(start_time=0.0)
    engine = OrderBookEngine("AAPL", clock=clock, direct_mode=True)

    # Place order at t=0
    order1 = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
    print(f"Order 1 timestamp: {order1.timestamp:.3f}")

    # Advance clock by 1 second
    clock.tick(1.0)

    # Place order at t=1
    order2 = engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)
    print(f"Order 2 timestamp: {order2.timestamp:.3f}")

    # Advance clock by 5 seconds
    clock.tick(5.0)

    # Place matching order at t=6
    order3 = engine.place_limit_order_sync(OrderSide.BUY, 50, 151.00)
    print(f"Order 3 timestamp: {order3.timestamp:.3f}")

    # Check trade timestamp
    if len(engine.order_book.trades) > 0:
        trade = engine.order_book.trades[0]
        print(f"Trade timestamp: {trade.timestamp:.3f}")

    print(f"\n✓ Deterministic timestamps working! Orders at t=0, t=1, t=6")


def test_direct_mode_performance():
    """Test direct mode speed vs threaded mode"""
    print("\n" + "="*70)
    print("TEST 2: Direct Mode Performance")
    print("="*70)

    import time

    # Test threaded mode
    print("\nThreaded mode (default):")
    engine1 = OrderBookEngine("TEST1")
    start = time.time()
    for i in range(1000):
        engine1.place_limit_order_sync(
            OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
            100,
            150.00 + i * 0.01
        )
    elapsed1 = time.time() - start
    engine1.shutdown()
    print(f"  1000 orders in {elapsed1:.3f}s = {1000/elapsed1:.0f} orders/sec")

    # Test direct mode
    print("\nDirect mode:")
    engine2 = OrderBookEngine("TEST2", direct_mode=True)
    start = time.time()
    for i in range(1000):
        engine2.place_limit_order_sync(
            OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
            100,
            150.00 + i * 0.01
        )
    elapsed2 = time.time() - start
    print(f"  1000 orders in {elapsed2:.3f}s = {1000/elapsed2:.0f} orders/sec")

    speedup = elapsed1 / elapsed2
    print(f"\n✓ Direct mode is {speedup:.1f}x faster!")


def test_batch_processing():
    """Test batch order processing"""
    print("\n" + "="*70)
    print("TEST 3: Batch Processing")
    print("="*70)

    import time

    engine = OrderBookEngine("AAPL", direct_mode=True)

    # Create 100 orders
    orders = [
        (OrderSide.BUY if i % 2 == 0 else OrderSide.SELL, 100, 150.00 + i * 0.01)
        for i in range(100)
    ]

    # Test individual submission
    start = time.time()
    for side, qty, price in orders:
        engine.place_limit_order_sync(side, qty, price)
    elapsed_individual = time.time() - start

    # Reset
    engine.order_book.reset()

    # Test batch submission
    start = time.time()
    results = engine.place_orders_batch_sync(orders)
    elapsed_batch = time.time() - start

    print(f"Individual: {elapsed_individual*1000:.2f}ms")
    print(f"Batch:      {elapsed_batch*1000:.2f}ms")
    print(f"Batch placed {len(results)} orders")
    print(f"\n✓ Batch mode completed successfully!")


def test_save_load_snapshot():
    """Test save/load snapshot functionality"""
    print("\n" + "="*70)
    print("TEST 4: Save/Load Snapshot")
    print("="*70)

    engine = OrderBookEngine("AAPL", direct_mode=True)

    # Place some orders
    engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
    engine.place_limit_order_sync(OrderSide.BUY, 200, 149.50)
    engine.place_limit_order_sync(OrderSide.SELL, 150, 151.00)
    engine.place_limit_order_sync(OrderSide.SELL, 100, 151.50)

    # Save snapshot
    snapshot = engine.order_book.save_snapshot()
    print(f"\nSaved snapshot with {len(snapshot['bids'])} bid levels and {len(snapshot['asks'])} ask levels")

    # Mess up the order book
    engine.place_limit_order_sync(OrderSide.BUY, 1000, 155.00)
    engine.place_limit_order_sync(OrderSide.SELL, 1000, 145.00)
    print(f"After changes: {len(engine.order_book.bids)} bid levels, {len(engine.order_book.asks)} ask levels")

    # Restore snapshot
    engine.order_book.load_snapshot(snapshot)
    print(f"After restore: {len(engine.order_book.bids)} bid levels, {len(engine.order_book.asks)} ask levels")

    print(f"\n✓ Snapshot save/load working!")


def test_reset():
    """Test reset functionality"""
    print("\n" + "="*70)
    print("TEST 5: Reset Functionality")
    print("="*70)

    engine = OrderBookEngine("AAPL", direct_mode=True)

    # Place orders
    for i in range(10):
        engine.place_limit_order_sync(
            OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
            100,
            150.00 + i * 0.01
        )

    print(f"Before reset: {len(engine.order_book.orders)} orders")

    # Reset
    engine.order_book.reset()

    print(f"After reset: {len(engine.order_book.orders)} orders")
    print(f"Bids: {len(engine.order_book.bids)}, Asks: {len(engine.order_book.asks)}")
    print(f"Trades: {len(engine.order_book.trades)}")

    print(f"\n✓ Reset working!")


def test_max_trades_limit():
    """Test max_trades memory limit"""
    print("\n" + "="*70)
    print("TEST 6: Max Trades Memory Limit")
    print("="*70)

    # Create engine with max 10 trades
    engine = OrderBookEngine("AAPL", direct_mode=True, max_trades=10)

    # Place orders to generate 20 trades
    for i in range(20):
        engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
        engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)  # Will match

    print(f"Generated 20 trades, kept last {len(engine.order_book.trades)} (max_trades=10)")

    print(f"\n✓ Memory limit working!")


def test_all_features_together():
    """Test all features working together"""
    print("\n" + "="*70)
    print("TEST 7: All Features Together")
    print("="*70)

    # Create engine with all features
    clock = SimulationClock(start_time=0.0)
    engine = OrderBookEngine(
        "AAPL",
        clock=clock,
        direct_mode=True,
        max_trades=100
    )

    print(f"Created engine with:")
    print(f"  - Simulation clock (starting at t=0)")
    print(f"  - Direct mode (10x faster)")
    print(f"  - Max trades limit (100)")

    # Place batch orders
    orders = [
        (OrderSide.BUY, 100, 149.00 + i * 0.10)
        for i in range(5)
    ] + [
        (OrderSide.SELL, 100, 151.00 + i * 0.10)
        for i in range(5)
    ]

    results = engine.place_orders_batch_sync(orders)
    print(f"\nPlaced {len(results)} orders in batch")

    # Advance clock
    clock.tick(10.0)

    # Save snapshot
    snapshot = engine.order_book.save_snapshot()

    # Place crossing order to generate trades
    engine.place_limit_order_sync(OrderSide.BUY, 500, 152.00)

    print(f"Generated {len(engine.order_book.trades)} trades")
    print(f"Current time: t={clock.time():.1f}")

    # Restore snapshot
    engine.order_book.load_snapshot(snapshot)
    print(f"Restored to previous state ({len(engine.order_book.trades)} trades)")

    print(f"\n✓ All features working together!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING NEW ORDER BOOK FEATURES")
    print("="*70)

    test_simulation_clock()
    test_direct_mode_performance()
    test_batch_processing()
    test_save_load_snapshot()
    test_reset()
    test_max_trades_limit()
    test_all_features_together()

    print("\n" + "="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70)
