"""
Test basic order book functionality
- Order matching
- Order cancellation
- Market data queries
- Price-time priority
"""

import unittest
from orderbook import (
    OrderBookEngine,
    OrderBook,
    OrderSide,
    OrderType,
    OrderStatus,
    Order
)


class TestBasicFunctionality(unittest.TestCase):
    """Test core order book functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = OrderBookEngine("TEST", direct_mode=True)

    def test_simple_limit_order(self):
        """Test placing a simple limit order"""
        order = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

        self.assertEqual(order.symbol, "TEST")
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.quantity, 100)
        self.assertEqual(order.price, 150.00)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.filled_quantity, 0)

    def test_matching_orders(self):
        """Test orders matching"""
        # Place buy order
        buy = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        self.assertEqual(buy.status, OrderStatus.PENDING)

        # Place matching sell order
        sell = self.engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)
        self.assertEqual(sell.status, OrderStatus.FILLED)

        # Buy order should now be filled
        self.assertEqual(buy.status, OrderStatus.FILLED)
        self.assertEqual(buy.filled_quantity, 100)

        # Should have generated 1 trade
        self.assertEqual(len(self.engine.order_book.trades), 1)
        trade = self.engine.order_book.trades[0]
        self.assertEqual(trade.quantity, 100)
        self.assertEqual(trade.price, 150.00)

    def test_partial_fill(self):
        """Test partial order fills"""
        # Place large buy order
        buy = self.engine.place_limit_order_sync(OrderSide.BUY, 200, 150.00)

        # Match with smaller sell order
        sell = self.engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)

        self.assertEqual(sell.status, OrderStatus.FILLED)
        self.assertEqual(buy.status, OrderStatus.PARTIAL)
        self.assertEqual(buy.filled_quantity, 100)
        self.assertEqual(buy.remaining_quantity(), 100)

    def test_market_order(self):
        """Test market orders"""
        # Place limit order to provide liquidity
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)

        # Place market buy order
        market_order = self.engine.place_market_order_sync(OrderSide.BUY, 100)

        self.assertEqual(market_order.status, OrderStatus.FILLED)
        self.assertEqual(market_order.order_type, OrderType.MARKET)
        self.assertEqual(market_order.price, None)

    def test_order_cancellation(self):
        """Test order cancellation"""
        order = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

        # Cancel the order
        result = self.engine.order_book.cancel_order(order.order_id)

        self.assertTrue(result)
        self.assertEqual(order.status, OrderStatus.CANCELLED)

        # Cannot cancel again
        result2 = self.engine.order_book.cancel_order(order.order_id)
        self.assertFalse(result2)

    def test_cannot_cancel_filled_order(self):
        """Test that filled orders cannot be cancelled"""
        buy = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        sell = self.engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)

        # Buy is now filled
        self.assertEqual(buy.status, OrderStatus.FILLED)

        # Cannot cancel filled order
        result = self.engine.order_book.cancel_order(buy.order_id)
        self.assertFalse(result)

    def test_best_bid_ask(self):
        """Test best bid/ask calculations"""
        # Initially empty
        self.assertIsNone(self.engine.order_book.get_best_bid())
        self.assertIsNone(self.engine.order_book.get_best_ask())

        # Place orders
        self.engine.place_limit_order_sync(OrderSide.BUY, 100, 149.00)
        self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 151.00)
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 152.00)

        # Check best prices
        self.assertEqual(self.engine.order_book.get_best_bid(), 150.00)
        self.assertEqual(self.engine.order_book.get_best_ask(), 151.00)
        self.assertEqual(self.engine.order_book.get_spread(), 1.00)

    def test_market_depth(self):
        """Test market depth calculation"""
        # Place multiple orders
        self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        self.engine.place_limit_order_sync(OrderSide.BUY, 200, 149.00)
        self.engine.place_limit_order_sync(OrderSide.SELL, 150, 151.00)
        self.engine.place_limit_order_sync(OrderSide.SELL, 100, 152.00)

        bids, asks = self.engine.order_book.get_depth(levels=5)

        # Check bid depth (descending price)
        self.assertEqual(len(bids), 2)
        self.assertEqual(bids[0][0], 150.00)  # Best bid
        self.assertEqual(bids[0][1], 100)     # Quantity
        self.assertEqual(bids[1][0], 149.00)
        self.assertEqual(bids[1][1], 200)

        # Check ask depth (ascending price)
        self.assertEqual(len(asks), 2)
        self.assertEqual(asks[0][0], 151.00)  # Best ask
        self.assertEqual(asks[0][1], 150)
        self.assertEqual(asks[1][0], 152.00)
        self.assertEqual(asks[1][1], 100)

    def test_price_time_priority(self):
        """Test price-time priority matching"""
        # Place two orders at same price
        order1 = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)
        order2 = self.engine.place_limit_order_sync(OrderSide.BUY, 100, 150.00)

        # Place sell order - should match with order1 first (time priority)
        sell = self.engine.place_limit_order_sync(OrderSide.SELL, 100, 150.00)

        self.assertEqual(order1.status, OrderStatus.FILLED)
        self.assertEqual(order2.status, OrderStatus.PENDING)

        # Trade should be with order1
        trade = self.engine.order_book.trades[0]
        self.assertEqual(trade.buy_order_id, order1.order_id)

    def test_validation_errors(self):
        """Test input validation"""
        # Zero quantity should raise error
        with self.assertRaises(ValueError):
            order = Order(
                order_id="TEST",
                symbol="TEST",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0,
                price=150.00
            )
            self.engine.order_book.add_order(order)

        # Negative price should raise error
        with self.assertRaises(ValueError):
            order = Order(
                order_id="TEST",
                symbol="TEST",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100,
                price=-150.00
            )
            self.engine.order_book.add_order(order)


if __name__ == '__main__':
    unittest.main()
