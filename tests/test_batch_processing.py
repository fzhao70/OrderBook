"""
Test batch order processing
- Batch submission
- Performance comparison
- Correctness
"""

import unittest
import time
from orderbook import (
    OrderBookEngine,
    OrderSide,
    OrderStatus
)


class TestBatchProcessing(unittest.TestCase):
    """Test batch order processing"""

    def test_batch_orders_basic(self):
        """Test basic batch order submission"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        orders = [
            (OrderSide.BUY, 100, 150.00),
            (OrderSide.BUY, 200, 149.00),
            (OrderSide.SELL, 150, 151.00),
        ]

        results = engine.place_orders_batch_sync(orders)

        # Should return all orders
        self.assertEqual(len(results), 3)

        # Check orders were created correctly
        self.assertEqual(results[0].side, OrderSide.BUY)
        self.assertEqual(results[0].quantity, 100)
        self.assertEqual(results[0].price, 150.00)

    def test_batch_orders_all_processed(self):
        """Test all batch orders are processed"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        orders = [
            (OrderSide.BUY, 100, 150.00 + i * 0.01)
            for i in range(100)
        ]

        results = engine.place_orders_batch_sync(orders)

        # All orders should be in order book
        self.assertEqual(len(results), 100)
        self.assertEqual(len(engine.order_book.bids), 100)

    def test_batch_matching(self):
        """Test orders within batch can match"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Place batch with matching orders
        orders = [
            (OrderSide.BUY, 100, 150.00),
            (OrderSide.SELL, 100, 150.00),  # Should match with first
        ]

        results = engine.place_orders_batch_sync(orders)

        # First order should be filled by second
        buy_order = results[0]
        sell_order = results[1]

        self.assertEqual(buy_order.status, OrderStatus.FILLED)
        self.assertEqual(sell_order.status, OrderStatus.FILLED)

        # Should have generated trade
        self.assertEqual(len(engine.order_book.trades), 1)

    def test_batch_vs_individual_same_result(self):
        """Test batch produces same result as individual orders"""
        # Individual orders
        engine1 = OrderBookEngine("TEST1", direct_mode=True)
        orders = [
            (OrderSide.BUY, 100, 150.00 + i * 0.1)
            for i in range(50)
        ]
        for side, qty, price in orders:
            engine1.place_limit_order_sync(side, qty, price)

        # Batch orders
        engine2 = OrderBookEngine("TEST2", direct_mode=True)
        results = engine2.place_orders_batch_sync(orders)

        # Should have same number of orders
        self.assertEqual(
            len(engine1.order_book.bids),
            len(engine2.order_book.bids)
        )

        # Should have same best bid
        self.assertEqual(
            engine1.order_book.get_best_bid(),
            engine2.order_book.get_best_bid()
        )

    def test_batch_empty_list(self):
        """Test batch with empty list"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        results = engine.place_orders_batch_sync([])

        self.assertEqual(len(results), 0)

    def test_batch_large_size(self):
        """Test batch with large number of orders"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # 10,000 orders
        orders = [
            (OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
             100,
             150.00 + (i % 100) * 0.01)
            for i in range(10000)
        ]

        start = time.time()
        results = engine.place_orders_batch_sync(orders)
        elapsed = time.time() - start

        # All orders processed
        self.assertEqual(len(results), 10000)

        # Should be fast (under 1 second)
        self.assertLess(elapsed, 1.0,
                       f"10k orders took {elapsed:.3f}s, expected <1s")

    def test_batch_in_threaded_mode(self):
        """Test batch works in threaded mode too"""
        engine = OrderBookEngine("TEST", direct_mode=False)

        orders = [
            (OrderSide.BUY, 100, 150.00 + i * 0.1)
            for i in range(100)
        ]

        results = engine.place_orders_batch_sync(orders)

        # All orders should be processed
        self.assertEqual(len(results), 100)

        engine.shutdown()

    def test_batch_preserves_order_ids(self):
        """Test batch orders get sequential IDs"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        orders = [
            (OrderSide.BUY, 100, 150.00 + i)
            for i in range(5)
        ]

        results = engine.place_orders_batch_sync(orders)

        # Order IDs should be sequential
        ids = [order.order_id for order in results]
        self.assertEqual(ids, ["ORD000001", "ORD000002", "ORD000003", "ORD000004", "ORD000005"])


if __name__ == '__main__':
    unittest.main()
