"""
Performance Analysis and Benchmarking for Order Book
"""

import time
import numpy as np
from orderbook import OrderBookManager, OrderSide


def benchmark_order_placement(num_orders=10000):
    """Benchmark order placement speed"""
    print(f"\n{'='*60}")
    print(f"Benchmark 1: Placing {num_orders:,} Orders")
    print('='*60)

    manager = OrderBookManager()
    manager.create_order_book("PERF")

    start = time.time()

    # Place alternating buy/sell orders
    for i in range(num_orders):
        if i % 2 == 0:
            manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00 - i * 0.01)
        else:
            manager.place_limit_order("PERF", OrderSide.SELL, 100, 110.00 + i * 0.01)

    elapsed = time.time() - start

    print(f"Time: {elapsed:.3f}s")
    print(f"Orders/sec: {num_orders/elapsed:,.0f}")
    print(f"Avg time per order: {elapsed/num_orders*1000:.3f}ms")

    return elapsed


def benchmark_matching(num_matches=1000):
    """Benchmark order matching speed"""
    print(f"\n{'='*60}")
    print(f"Benchmark 2: Matching {num_matches:,} Orders")
    print('='*60)

    manager = OrderBookManager()
    manager.create_order_book("PERF")

    # Build one side of the book
    for i in range(num_matches):
        manager.place_limit_order("PERF", OrderSide.SELL, 100, 100.00 + i * 0.01)

    start = time.time()

    # Match with buy orders
    for i in range(num_matches):
        manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00 + i * 0.01)

    elapsed = time.time() - start

    trades = manager.get_all_trades("PERF")

    print(f"Time: {elapsed:.3f}s")
    print(f"Matches/sec: {num_matches/elapsed:,.0f}")
    print(f"Avg time per match: {elapsed/num_matches*1000:.3f}ms")
    print(f"Trades executed: {len(trades):,}")

    return elapsed


def benchmark_deep_book_matching():
    """Benchmark matching against deep order book"""
    print(f"\n{'='*60}")
    print(f"Benchmark 3: Matching Against Deep Book")
    print('='*60)

    manager = OrderBookManager()
    manager.create_order_book("PERF")

    # Build deep book with many price levels
    print("Building book with 1000 price levels...")
    for i in range(1000):
        manager.place_limit_order("PERF", OrderSide.SELL, 100, 100.00 + i * 0.01)

    # Place market order that sweeps through many levels
    print("Executing large market order...")
    start = time.time()
    market_order = manager.place_market_order("PERF", OrderSide.BUY, 50000)
    elapsed = time.time() - start

    print(f"Time: {elapsed:.3f}s")
    print(f"Quantity filled: {market_order.filled_quantity:,}")
    print(f"Price levels crossed: {len(manager.get_all_trades('PERF'))}")

    return elapsed


def benchmark_depth_calculation():
    """Benchmark market depth calculation"""
    print(f"\n{'='*60}")
    print(f"Benchmark 4: Market Depth Calculation")
    print('='*60)

    manager = OrderBookManager()
    manager.create_order_book("PERF")

    # Build book
    for i in range(1000):
        manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00 - i * 0.01)
        manager.place_limit_order("PERF", OrderSide.SELL, 100, 101.00 + i * 0.01)

    book = manager.get_order_book("PERF")

    # Benchmark depth calculation
    iterations = 1000
    start = time.time()
    for _ in range(iterations):
        bids, asks = book.get_depth(levels=10)
    elapsed = time.time() - start

    print(f"Time for {iterations} depth calls: {elapsed:.3f}s")
    print(f"Depth calls/sec: {iterations/elapsed:,.0f}")
    print(f"Avg time per call: {elapsed/iterations*1000:.3f}ms")

    return elapsed


def benchmark_cancellation():
    """Benchmark order cancellation"""
    print(f"\n{'='*60}")
    print(f"Benchmark 5: Order Cancellation")
    print('='*60)

    manager = OrderBookManager()
    manager.create_order_book("PERF")

    # Place orders and store IDs
    num_orders = 10000
    order_ids = []

    print(f"Placing {num_orders:,} orders...")
    for i in range(num_orders):
        order = manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00 - i * 0.01)
        order_ids.append(order.order_id)

    # Cancel all orders
    print(f"Cancelling {num_orders:,} orders...")
    start = time.time()
    for order_id in order_ids:
        manager.cancel_order(order_id)
    elapsed = time.time() - start

    print(f"Time: {elapsed:.3f}s")
    print(f"Cancellations/sec: {num_orders/elapsed:,.0f}")
    print(f"Avg time per cancel: {elapsed/num_orders*1000:.3f}ms")

    return elapsed


def analyze_complexity():
    """Analyze time complexity with different book sizes"""
    print(f"\n{'='*60}")
    print(f"Benchmark 6: Complexity Analysis")
    print('='*60)

    sizes = [100, 500, 1000, 5000, 10000]

    print("\nOrder Placement Scaling:")
    print(f"{'Size':>10} {'Time (s)':>12} {'Orders/sec':>15}")
    print('-'*40)

    for size in sizes:
        manager = OrderBookManager()
        manager.create_order_book("PERF")

        start = time.time()
        for i in range(size):
            manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00 - i * 0.01)
        elapsed = time.time() - start

        print(f"{size:>10,} {elapsed:>12.4f} {size/elapsed:>15,.0f}")


def profile_memory_usage():
    """Profile memory characteristics"""
    print(f"\n{'='*60}")
    print(f"Benchmark 7: Memory Analysis")
    print('='*60)

    import sys

    manager = OrderBookManager()
    manager.create_order_book("PERF")

    # Measure order object size
    order = manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00)
    order_size = sys.getsizeof(order)

    print(f"Order object size: {order_size} bytes")

    # Estimate memory for 10k orders
    num_orders = 10000
    for i in range(num_orders - 1):
        manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00 - i * 0.01)

    book = manager.get_order_book("PERF")
    estimated = order_size * num_orders

    print(f"Estimated memory for {num_orders:,} orders: {estimated/1024/1024:.2f} MB")
    print(f"Price levels in book: {len(book.bids)}")


def test_numpy_efficiency():
    """Test if NumPy is being used efficiently"""
    print(f"\n{'='*60}")
    print(f"Benchmark 8: NumPy Usage Analysis")
    print('='*60)

    manager = OrderBookManager()
    manager.create_order_book("PERF")

    # Build book
    for i in range(100):
        manager.place_limit_order("PERF", OrderSide.BUY, 100, 100.00 - i * 0.01)

    book = manager.get_order_book("PERF")

    # Test current implementation
    iterations = 10000
    start = time.time()
    for _ in range(iterations):
        # This is what happens in _match_buy_order line 205
        ask_prices = np.array(sorted(book.bids.keys()))
    elapsed_numpy = time.time() - start

    # Test without NumPy
    start = time.time()
    for _ in range(iterations):
        ask_prices = sorted(book.bids.keys())
    elapsed_plain = time.time() - start

    print(f"With np.array(): {elapsed_numpy:.4f}s")
    print(f"Without np.array(): {elapsed_plain:.4f}s")
    print(f"Overhead: {(elapsed_numpy/elapsed_plain - 1)*100:.1f}%")
    print(f"\n⚠️  NumPy array creation is {elapsed_numpy/elapsed_plain:.1f}x SLOWER")
    print("   Recommendation: Remove np.array() wrapper in matching loop")


def run_all_benchmarks():
    """Run all performance benchmarks"""
    print("\n" + "="*60)
    print("Order Book Performance Analysis".center(60))
    print("="*60)

    benchmark_order_placement(10000)
    benchmark_matching(1000)
    benchmark_deep_book_matching()
    benchmark_depth_calculation()
    benchmark_cancellation()
    analyze_complexity()
    profile_memory_usage()
    test_numpy_efficiency()

    print("\n" + "="*60)
    print("Performance Analysis Complete".center(60))
    print("="*60)


if __name__ == "__main__":
    run_all_benchmarks()
