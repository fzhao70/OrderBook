"""
Test SimulationClock functionality
- Deterministic timestamps
- Clock advancement
- Order and trade timestamps
"""

import unittest
import time
from orderbook import (
    OrderBookEngine,
    SimulationClock,
    OrderSide
)


class TestSimulationClock(unittest.TestCase):
    """Test simulation clock features"""

    def test_clock_initialization(self):
        """Test clock starts at specified time"""
        clock = SimulationClock(start_time=100.0)
        self.assertEqual(clock.time(), 100.0)

    def test_clock_tick(self):
        """Test clock advancement"""
        clock = SimulationClock(start_time=0.0)

        # Advance by 1 second
        new_time = clock.tick(1.0)
        self.assertEqual(new_time, 1.0)
        self.assertEqual(clock.time(), 1.0)

        # Advance by 0.5 seconds
        clock.tick(0.5)
        self.assertEqual(clock.time(), 1.5)

    def test_clock_set_time(self):
        """Test setting clock to specific time"""
        clock = SimulationClock()
        clock.set_time(42.0)
        self.assertEqual(clock.time(), 42.0)

    def test_deterministic_order_timestamps(self):
        """Test orders get deterministic timestamps from clock"""
        clock = SimulationClock(start_time=0.0)
        engine = OrderBookEngine("TEST", clock=clock, direct_mode=True)

        # Place order at t=0
        order1 = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        self.assertEqual(order1.timestamp, 0.0)

        # Advance clock
        clock.tick(5.0)

        # Place order at t=5
        order2 = engine.place_limit_order_sync(OrderSide.BUY, 100, 149.00)
        self.assertEqual(order2.timestamp, 5.0)

        # Verify timestamps are different
        self.assertNotEqual(order1.timestamp, order2.timestamp)

    def test_deterministic_trade_timestamps(self):
        """Test trades get deterministic timestamps from clock"""
        clock = SimulationClock(start_time=0.0)
        engine = OrderBookEngine("TEST", clock=clock, direct_mode=True)

        # Place buy order at t=0
        engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

        # Advance clock
        clock.tick(10.0)

        # Place matching sell order at t=10
        engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)

        # Trade should have timestamp of t=10 (when matching occurred)
        trade = engine.order_book.trades[0]
        self.assertEqual(trade.timestamp, 10.0)

    def test_without_clock_uses_system_time(self):
        """Test that without clock, system time is used"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        before = time.time()
        order = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        after = time.time()

        # Timestamp should be between before and after
        self.assertGreaterEqual(order.timestamp, before)
        self.assertLessEqual(order.timestamp, after)

    def test_clock_reproducibility(self):
        """Test that simulations with same clock are reproducible"""
        # Simulation 1
        clock1 = SimulationClock(start_time=0.0)
        engine1 = OrderBookEngine("TEST", clock=clock1, direct_mode=True)

        for i in range(10):
            clock1.tick(0.1)
            engine1.place_limit_order_sync(OrderSide.BUY, 100, 150.00 + i)

        timestamps1 = [order.timestamp for order in engine1.order_book.orders.values()]

        # Simulation 2 (exact same operations)
        clock2 = SimulationClock(start_time=0.0)
        engine2 = OrderBookEngine("TEST", clock=clock2, direct_mode=True)

        for i in range(10):
            clock2.tick(0.1)
            engine2.place_limit_order_sync(OrderSide.BUY, 100, 150.00 + i)

        timestamps2 = [order.timestamp for order in engine2.order_book.orders.values()]

        # Timestamps should be identical
        self.assertEqual(timestamps1, timestamps2)

    def test_clock_with_batch_orders(self):
        """Test clock works with batch order processing"""
        clock = SimulationClock(start_time=0.0)
        engine = OrderBookEngine("TEST", clock=clock, direct_mode=True)

        # Place batch at t=0
        orders = [
            (OrderSide.BUY, 100, 150.00 + i * 0.1)
            for i in range(5)
        ]
        results = engine.place_orders_batch_sync(orders)

        # All should have same timestamp (t=0)
        for order in results:
            self.assertEqual(order.timestamp, 0.0)

        # Advance clock
        clock.tick(1.0)

        # Place another batch at t=1
        orders2 = [
            (OrderSide.SELL, 100, 151.00 + i * 0.1)
            for i in range(5)
        ]
        results2 = engine.place_orders_batch_sync(orders2)

        # All should have timestamp t=1
        for order in results2:
            self.assertEqual(order.timestamp, 1.0)


if __name__ == '__main__':
    unittest.main()
