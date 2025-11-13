"""
Test direct mode functionality
- Performance comparison
- Correctness in direct mode
- Direct mode vs thread-safe mode equivalence
"""

import unittest
import time
from orderbook import (
    OrderBookEngine,
    OrderSide,
    OrderStatus
)


class TestDirectMode(unittest.TestCase):
    """Test direct mode features"""

    def test_direct_mode_basic_operation(self):
        """Test basic operations work in direct mode"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Place orders
        buy = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        sell = engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)

        # Should match correctly
        self.assertEqual(buy.status, OrderStatus.FILLED)
        self.assertEqual(sell.status, OrderStatus.FILLED)
        self.assertEqual(len(engine.order_book.trades), 1)

    def test_direct_mode_faster_than_threaded(self):
        """Test that direct mode is significantly faster"""
        n_orders = 1000

        # Test threaded mode
        engine_threaded = OrderBookEngine("TEST1")
        start = time.time()
        for i in range(n_orders):
            engine_threaded.place_limit_order_sync(
                OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                100,
                150.00 + i * 0.01
            )
        threaded_time = time.time() - start
        engine_threaded.shutdown()

        # Test direct mode
        engine_direct = OrderBookEngine("TEST2", direct_mode=True)
        start = time.time()
        for i in range(n_orders):
            engine_direct.place_limit_order_sync(
                OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                100,
                150.00 + i * 0.01
            )
        direct_time = time.time() - start

        # Direct mode should be at least 5x faster
        speedup = threaded_time / direct_time
        self.assertGreater(speedup, 5.0,
                          f"Direct mode only {speedup:.1f}x faster, expected >5x")

    def test_direct_mode_same_results_as_threaded(self):
        """Test direct mode produces same results as threaded mode"""
        # Run in threaded mode
        engine1 = OrderBookEngine("TEST1")
        for i in range(100):
            engine1.place_limit_order_sync(
                OrderSide.BUY if i % 3 == 0 else OrderSide.SELL,
                100,
                150.00 + (i % 10) * 0.1
            )
        engine1.shutdown()

        # Run in direct mode
        engine2 = OrderBookEngine("TEST2", direct_mode=True)
        for i in range(100):
            engine2.place_limit_order_sync(
                OrderSide.BUY if i % 3 == 0 else OrderSide.SELL,
                100,
                150.00 + (i % 10) * 0.1
            )

        # Should have same number of trades
        self.assertEqual(
            len(engine1.order_book.trades),
            len(engine2.order_book.trades)
        )

        # Should have same best bid/ask
        self.assertEqual(
            engine1.order_book.get_best_bid(),
            engine2.order_book.get_best_bid()
        )
        self.assertEqual(
            engine1.order_book.get_best_ask(),
            engine2.order_book.get_best_ask()
        )

    def test_direct_mode_no_queue(self):
        """Test direct mode has no queue overhead"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Queue depth should always be 0
        self.assertEqual(engine.get_queue_depth(), 0)

        # Place orders
        for i in range(10):
            engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00 + i)

        # Still 0
        self.assertEqual(engine.get_queue_depth(), 0)

    def test_direct_mode_is_healthy(self):
        """Test health check works in direct mode"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Should be healthy
        self.assertTrue(engine.is_healthy())

        # Shutdown
        engine.shutdown()

        # Should not be healthy after shutdown
        self.assertFalse(engine.is_healthy())

    def test_direct_mode_with_batch(self):
        """Test batch processing works in direct mode"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        orders = [
            (OrderSide.BUY, 100, 150.00 + i * 0.1)
            for i in range(100)
        ]

        # Process batch
        start = time.time()
        results = engine.place_orders_batch_sync(orders)
        elapsed = time.time() - start

        # All orders should be processed
        self.assertEqual(len(results), 100)

        # Should be very fast in direct mode
        self.assertLess(elapsed, 0.1, f"Batch took {elapsed:.3f}s, expected <0.1s")

    def test_direct_mode_shutdown_immediate(self):
        """Test shutdown is immediate in direct mode"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        start = time.time()
        engine.shutdown()
        elapsed = time.time() - start

        # Should be nearly instant (no thread to wait for)
        self.assertLess(elapsed, 0.01)


if __name__ == '__main__':
    unittest.main()
