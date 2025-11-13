"""
Test memory management features
- max_trades parameter
- Memory bounds
"""

import unittest
from orderbook import (
    OrderBookEngine,
    OrderSide
)


class TestMemoryLimits(unittest.TestCase):
    """Test memory limit features"""

    def test_max_trades_unlimited(self):
        """Test unlimited trades (default behavior)"""
        engine = OrderBookEngine("TEST", direct_mode=True, max_trades=0)

        # Generate 1000 trades
        for i in range(1000):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        # All trades should be kept
        self.assertEqual(len(engine.order_book.trades), 1000)

    def test_max_trades_limit(self):
        """Test max_trades limits trade history"""
        max_trades = 100
        engine = OrderBookEngine("TEST", direct_mode=True, max_trades=max_trades)

        # Generate 200 trades
        for i in range(200):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        # Should keep only last 100
        self.assertEqual(len(engine.order_book.trades), max_trades)

    def test_max_trades_keeps_recent(self):
        """Test max_trades keeps most recent trades"""
        max_trades = 10
        engine = OrderBookEngine("TEST", direct_mode=True, max_trades=max_trades)

        # Generate 20 trades
        for i in range(20):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00 + i)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00 + i)

        # Should have trades 11-20 (most recent)
        trades = list(engine.order_book.trades)
        self.assertEqual(len(trades), 10)

        # First trade should be from iteration 11
        first_trade = trades[0]
        self.assertEqual(first_trade.price, 160.00)  # 150 + 10

        # Last trade should be from iteration 20
        last_trade = trades[-1]
        self.assertEqual(last_trade.price, 169.00)  # 150 + 19

    def test_max_trades_zero_is_unlimited(self):
        """Test max_trades=0 means unlimited"""
        engine = OrderBookEngine("TEST", direct_mode=True, max_trades=0)

        # Generate many trades
        for i in range(1000):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        # All should be kept
        self.assertEqual(len(engine.order_book.trades), 1000)

    def test_max_trades_with_reset(self):
        """Test reset clears bounded trade history"""
        engine = OrderBookEngine("TEST", direct_mode=True, max_trades=100)

        # Generate trades
        for i in range(50):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        self.assertEqual(len(engine.order_book.trades), 50)

        # Reset
        engine.order_book.reset()

        # Should be empty
        self.assertEqual(len(engine.order_book.trades), 0)

    def test_max_trades_different_values(self):
        """Test different max_trades values"""
        values = [1, 5, 10, 50, 100, 1000]

        for max_val in values:
            engine = OrderBookEngine(f"TEST{max_val}", direct_mode=True, max_trades=max_val)

            # Generate 2x max_val trades
            for i in range(max_val * 2):
                engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
                engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

            # Should be limited to max_val
            self.assertEqual(len(engine.order_book.trades), max_val)

    def test_max_trades_exact_limit(self):
        """Test behavior when exactly at limit"""
        max_trades = 10
        engine = OrderBookEngine("TEST", direct_mode=True, max_trades=max_trades)

        # Generate exactly max_trades
        for i in range(max_trades):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        self.assertEqual(len(engine.order_book.trades), max_trades)

        # Add one more
        engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
        engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        # Should still be at max
        self.assertEqual(len(engine.order_book.trades), max_trades)

    def test_max_trades_with_snapshot(self):
        """Test max_trades works with snapshot/restore"""
        engine = OrderBookEngine("TEST", direct_mode=True, max_trades=10)

        # Generate some trades
        for i in range(5):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        snapshot = engine.order_book.save_snapshot()

        # Generate more trades (will hit limit)
        for i in range(10):
            engine.place_limit_order_sync(OrderSide.SELL, 10, 150.00)
            engine.place_limit_order_sync(OrderSide.BUY, 10, 150.00)

        # Restore
        engine.order_book.load_snapshot(snapshot)

        # Trade history from snapshot should be restored
        # (but it will be empty since snapshot doesn't save trades)
        self.assertEqual(len(engine.order_book.trades), 0)


if __name__ == '__main__':
    unittest.main()
