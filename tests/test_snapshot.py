"""
Test snapshot and reset functionality
- save_snapshot
- load_snapshot
- reset
"""

import unittest
from orderbook import (
    OrderBookEngine,
    OrderSide,
    OrderStatus
)


class TestSnapshot(unittest.TestCase):
    """Test snapshot/restore/reset features"""

    def test_save_snapshot_basic(self):
        """Test basic snapshot save"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Place some orders
        engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)

        # Save snapshot
        snapshot = engine.order_book.save_snapshot()

        # Should contain all data
        self.assertEqual(snapshot['symbol'], 'TEST')
        self.assertIn(150.00, snapshot['bids'])
        self.assertIn(151.00, snapshot['asks'])

    def test_load_snapshot_restores_state(self):
        """Test loading snapshot restores exact state"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Create initial state
        buy1 = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        buy2 = engine.place_limit_order_sync(OrderSide.BUY, 200, 149.00)
        sell1 = engine.place_limit_order_sync(OrderSide.SELL, 150, 151.00)

        # Save snapshot
        snapshot = engine.order_book.save_snapshot()

        # Modify state
        engine.place_limit_order_sync(OrderSide.BUY, 1000, 155.00)
        engine.place_limit_order_sync(OrderSide.SELL, 1000, 145.00)

        # State should be different (sell at 145 matches all bids except partial at 149)
        self.assertEqual(len(engine.order_book.bids), 1)
        self.assertEqual(len(engine.order_book.asks), 0)

        # Restore snapshot
        engine.order_book.load_snapshot(snapshot)

        # State should be restored
        self.assertEqual(len(engine.order_book.bids), 2)
        self.assertEqual(len(engine.order_book.asks), 1)
        self.assertEqual(engine.order_book.get_best_bid(), 150.00)
        self.assertEqual(engine.order_book.get_best_ask(), 151.00)

    def test_snapshot_preserves_order_details(self):
        """Test snapshot preserves all order details"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Place order
        original = engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        original_id = original.order_id

        # Save and restore
        snapshot = engine.order_book.save_snapshot()
        engine.order_book.load_snapshot(snapshot)

        # Check order is preserved
        self.assertIn(original_id, engine.order_book.orders)
        restored = engine.order_book.orders[original_id]

        self.assertEqual(restored.order_id, original.order_id)
        self.assertEqual(restored.quantity, original.quantity)
        self.assertEqual(restored.price, original.price)
        self.assertEqual(restored.side, original.side)
        self.assertEqual(restored.status, original.status)

    def test_snapshot_after_partial_fill(self):
        """Test snapshot with partially filled orders"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Create partially filled order
        buy = engine.place_limit_order_sync(OrderSide.BUY, 200, 150.00)
        engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)

        # Buy should be partially filled
        self.assertEqual(buy.status, OrderStatus.PARTIAL)
        self.assertEqual(buy.filled_quantity, 100)

        # Save snapshot
        snapshot = engine.order_book.save_snapshot()

        # Reset and restore
        engine.order_book.reset()
        engine.order_book.load_snapshot(snapshot)

        # Partial fill should be preserved
        restored_buy = engine.order_book.orders[buy.order_id]
        self.assertEqual(restored_buy.status, OrderStatus.PARTIAL)
        self.assertEqual(restored_buy.filled_quantity, 100)

    def test_reset_clears_everything(self):
        """Test reset clears all state"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Create complex state
        for i in range(10):
            engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00 + i)
            engine.place_limit_order_sync(OrderSide.SELL, 100, 160.00 + i)

        # Generate some trades
        engine.place_limit_order_sync(OrderSide.BUY, 100, 161.00)

        # Should have orders and trades
        self.assertGreater(len(engine.order_book.orders), 0)
        self.assertGreater(len(engine.order_book.trades), 0)
        self.assertGreater(len(engine.order_book.bids), 0)
        self.assertGreater(len(engine.order_book.asks), 0)

        # Reset
        engine.order_book.reset()

        # Everything should be cleared
        self.assertEqual(len(engine.order_book.orders), 0)
        self.assertEqual(len(engine.order_book.trades), 0)
        self.assertEqual(len(engine.order_book.bids), 0)
        self.assertEqual(len(engine.order_book.asks), 0)
        self.assertIsNone(engine.order_book.get_best_bid())
        self.assertIsNone(engine.order_book.get_best_ask())

    def test_multiple_snapshots(self):
        """Test multiple snapshots and restores"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # State 1
        engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        snapshot1 = engine.order_book.save_snapshot()

        # State 2
        engine.place_limit_order_sync(OrderSide.BUY, 200, 149.00)
        snapshot2 = engine.order_book.save_snapshot()

        # State 3
        engine.place_limit_order_sync(OrderSide.BUY, 300, 148.00)

        # Should have 3 bid levels
        self.assertEqual(len(engine.order_book.bids), 3)

        # Restore to state 2
        engine.order_book.load_snapshot(snapshot2)
        self.assertEqual(len(engine.order_book.bids), 2)

        # Restore to state 1
        engine.order_book.load_snapshot(snapshot1)
        self.assertEqual(len(engine.order_book.bids), 1)

    def test_snapshot_with_no_orders(self):
        """Test snapshot of empty order book"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Save empty state
        snapshot = engine.order_book.save_snapshot()

        # Add orders
        engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

        # Restore empty state
        engine.order_book.load_snapshot(snapshot)

        # Should be empty again
        self.assertEqual(len(engine.order_book.bids), 0)
        self.assertEqual(len(engine.order_book.asks), 0)

    def test_reset_between_simulations(self):
        """Test reset for running multiple simulations"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Simulation 1
        for i in range(100):
            engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00 + i * 0.01)
        sim1_orders = len(engine.order_book.orders)

        # Reset
        engine.order_book.reset()

        # Simulation 2
        for i in range(50):
            engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00 + i * 0.01)
        sim2_orders = len(engine.order_book.orders)

        # Should be different
        self.assertEqual(sim1_orders, 100)
        self.assertEqual(sim2_orders, 50)

    def test_snapshot_preserves_best_prices(self):
        """Test snapshot preserves cached best prices"""
        engine = OrderBookEngine("TEST", direct_mode=True)

        # Create market
        engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        engine.place_limit_order_sync(OrderSide.BUY, 100, 149.00)
        engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)

        # Save snapshot
        snapshot = engine.order_book.save_snapshot()

        # Verify cached prices in snapshot
        self.assertEqual(snapshot['best_bid'], 150.00)
        self.assertEqual(snapshot['best_ask'], 151.00)

        # Reset and restore
        engine.order_book.reset()
        engine.order_book.load_snapshot(snapshot)

        # Cached prices should work immediately (O(1))
        self.assertEqual(engine.order_book.get_best_bid(), 150.00)
        self.assertEqual(engine.order_book.get_best_ask(), 151.00)


if __name__ == '__main__':
    unittest.main()
