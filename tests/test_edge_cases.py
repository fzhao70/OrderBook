"""
Test edge cases and error handling
- Invalid inputs
- Empty order books
- Extreme values
"""

import unittest
from orderbook import (
    OrderBookEngine,
    OrderSide,
    OrderType,
    OrderStatus,
    Order
)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = OrderBookEngine("TEST", direct_mode=True)

    def test_empty_order_book(self):
        """Test operations on empty order book"""
        # Empty book
        self.assertIsNone(self.engine.order_book.get_best_bid())
        self.assertIsNone(self.engine.order_book.get_best_ask())
        self.assertIsNone(self.engine.order_book.get_spread())

        # Depth should be empty
        bids, asks = self.engine.order_book.get_depth()
        self.assertEqual(len(bids), 0)
        self.assertEqual(len(asks), 0)

    def test_market_order_no_liquidity(self):
        """Test market order with no liquidity"""
        # Place market order on empty book
        order = self.engine.place_market_order_sync(OrderSide.BUY, 100)

        # Should remain unfilled
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.filled_quantity, 0)

    def test_cancel_nonexistent_order(self):
        """Test cancelling non-existent order"""
        result = self.engine.order_book.cancel_order("NONEXISTENT")
        self.assertFalse(result)

    def test_very_large_quantity(self):
        """Test very large order quantities"""
        order = self.engine.place_limit_order_sync(OrderSide.BUY, 1_000_000_000, 150.00)

        self.assertEqual(order.quantity, 1_000_000_000)
        self.assertEqual(order.status, OrderStatus.PENDING)

    def test_very_small_price(self):
        """Test very small prices"""
        order = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 0.0001)

        self.assertEqual(order.price, 0.0001)

    def test_very_large_price(self):
        """Test very large prices"""
        order = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 1_000_000.00)

        self.assertEqual(order.price, 1_000_000.00)

    def test_fractional_quantities(self):
        """Test fractional order quantities"""
        order = self.engine.place_limit_order_sync(OrderSide.BUY, 0.5, 150.00)

        self.assertEqual(order.quantity, 0.5)

        # Should match with fractional quantity
        sell = self.engine.place_limit_order_sync(OrderSide.SELL, 0.5, 150.00)

        self.assertEqual(order.status, OrderStatus.FILLED)
        self.assertEqual(sell.status, OrderStatus.FILLED)

    def test_many_orders_same_price(self):
        """Test many orders at same price level"""
        # Place 1000 orders at same price
        orders = []
        for i in range(1000):
            order = self.engine.place_limit_order_sync(OrderSide.BUY, 1, 150.00)
            orders.append(order)

        # All should be at same price
        self.assertEqual(len(self.engine.order_book.bids[150.00]), 1000)

        # Match one by one
        for i in range(1000):
            self.engine.place_limit_order_sync(OrderSide.SELL, 1, 150.00)

        # All should be filled
        for order in orders:
            self.assertEqual(order.status, OrderStatus.FILLED)

    def test_alternating_sides(self):
        """Test rapidly alternating buy/sell orders"""
        for i in range(100):
            if i % 2 == 0:
                self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
            else:
                self.engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)

        # Should have many trades
        self.assertGreater(len(self.engine.order_book.trades), 40)

    def test_crossing_spread(self):
        """Test orders that cross the spread"""
        # Create spread
        self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)

        # Buy order above best ask (crosses spread)
        buy = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 152.00)

        # Should match immediately
        self.assertEqual(buy.status, OrderStatus.FILLED)

    def test_partial_fill_sequence(self):
        """Test sequence of partial fills"""
        # Large buy order
        buy = self.engine.place_limit_order_sync(OrderSide.BUY, 1000, 150.00)

        # Partial fills
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)
        self.assertEqual(buy.status, OrderStatus.PARTIAL)
        self.assertEqual(buy.filled_quantity, 100)

        self.engine.place_limit_order_sync(OrderSide.SELL, 200, 150.00)
        self.assertEqual(buy.status, OrderStatus.PARTIAL)
        self.assertEqual(buy.filled_quantity, 300)

        self.engine.place_limit_order_sync(OrderSide.SELL, 700, 150.00)
        self.assertEqual(buy.status, OrderStatus.FILLED)
        self.assertEqual(buy.filled_quantity, 1000)

    def test_multiple_symbols_isolation(self):
        """Test multiple engines don't interfere"""
        engine1 = OrderBookEngine("AAPL", direct_mode=True)
        engine2 = OrderBookEngine("GOOGL", direct_mode=True)

        # Place orders on different engines
        order1 = engine1.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        order2 = engine2.place_limit_order_sync(OrderSide.BUY, 100, 2800.00)

        # Should be isolated
        self.assertEqual(len(engine1.order_book.orders), 1)
        self.assertEqual(len(engine2.order_book.orders), 1)

        self.assertEqual(order1.symbol, "AAPL")
        self.assertEqual(order2.symbol, "GOOGL")

    def test_best_price_update_after_cancel(self):
        """Test best prices update correctly after cancellation"""
        # Place multiple orders
        order1 = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        order2 = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 149.00)

        self.assertEqual(self.engine.order_book.get_best_bid(), 150.00)

        # Cancel best bid
        self.engine.order_book.cancel_order(order1.order_id)

        # Best bid should update
        self.assertEqual(self.engine.order_book.get_best_bid(), 149.00)

    def test_best_price_update_after_fill(self):
        """Test best prices update correctly after fills"""
        # Place orders
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 152.00)

        self.assertEqual(self.engine.order_book.get_best_ask(), 151.00)

        # Fill best ask
        self.engine.place_limit_order_sync(OrderSide.BUY, 100, 151.00)

        # Best ask should update
        self.assertEqual(self.engine.order_book.get_best_ask(), 152.00)

    def test_empty_batch(self):
        """Test empty batch submission"""
        results = self.engine.place_orders_batch_sync([])
        self.assertEqual(len(results), 0)

    def test_single_order_batch(self):
        """Test batch with single order"""
        results = self.engine.place_orders_batch_sync([
            (OrderSide.BUY, 100, 150.00)
        ])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].quantity, 100)


if __name__ == '__main__':
    unittest.main()
