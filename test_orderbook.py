"""
Test suite to verify order book correctness
"""

from orderbook import OrderBookManager, OrderSide, OrderType, OrderStatus


def test_basic_matching():
    """Test basic order matching"""
    print("Test 1: Basic Matching")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Place orders
    buy = manager.place_limit_order("TEST", OrderSide.BUY, 100, 150.00)
    sell = manager.place_limit_order("TEST", OrderSide.SELL, 100, 150.00)

    # Verify both filled
    assert buy.status == OrderStatus.FILLED, f"Buy status: {buy.status}"
    assert sell.status == OrderStatus.FILLED, f"Sell status: {sell.status}"
    assert buy.filled_quantity == 100, f"Buy filled: {buy.filled_quantity}"
    assert sell.filled_quantity == 100, f"Sell filled: {sell.filled_quantity}"

    # Verify trade
    trades = manager.get_all_trades("TEST")
    assert len(trades) == 1, f"Trades: {len(trades)}"
    assert trades[0].price == 150.00, f"Trade price: {trades[0].price}"
    assert trades[0].quantity == 100, f"Trade qty: {trades[0].quantity}"

    print("✓ Basic matching works correctly")


def test_partial_fill():
    """Test partial order fills"""
    print("\nTest 2: Partial Fills")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Sell 100
    sell = manager.place_limit_order("TEST", OrderSide.SELL, 100, 150.00)

    # Buy only 60
    buy = manager.place_limit_order("TEST", OrderSide.BUY, 60, 150.00)

    # Verify
    assert buy.status == OrderStatus.FILLED, f"Buy status: {buy.status}"
    assert sell.status == OrderStatus.PARTIAL, f"Sell status: {sell.status}"
    assert sell.filled_quantity == 60, f"Sell filled: {sell.filled_quantity}"
    assert sell.remaining_quantity() == 40, f"Sell remaining: {sell.remaining_quantity()}"

    print("✓ Partial fills work correctly")


def test_price_priority():
    """Test price-time priority"""
    print("\nTest 3: Price Priority")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Place multiple sell orders at different prices
    sell1 = manager.place_limit_order("TEST", OrderSide.SELL, 100, 152.00)
    sell2 = manager.place_limit_order("TEST", OrderSide.SELL, 100, 150.00)
    sell3 = manager.place_limit_order("TEST", OrderSide.SELL, 100, 151.00)

    # Place buy that matches best price
    buy = manager.place_limit_order("TEST", OrderSide.BUY, 100, 152.00)

    # Should match with sell2 (best ask at 150)
    assert buy.filled_quantity == 100
    assert sell2.status == OrderStatus.FILLED, "Should match best price first"
    assert sell1.status == OrderStatus.PENDING
    assert sell3.status == OrderStatus.PENDING

    trades = manager.get_all_trades("TEST")
    assert trades[0].price == 150.00, f"Trade price: {trades[0].price}"

    print("✓ Price priority works correctly")


def test_time_priority():
    """Test time priority (FIFO)"""
    print("\nTest 4: Time Priority (FIFO)")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Place multiple orders at same price
    sell1 = manager.place_limit_order("TEST", OrderSide.SELL, 50, 150.00)
    sell2 = manager.place_limit_order("TEST", OrderSide.SELL, 50, 150.00)

    # Buy should match first order first
    buy = manager.place_limit_order("TEST", OrderSide.BUY, 75, 150.00)

    # Verify FIFO
    assert sell1.status == OrderStatus.FILLED, "First order should fill first"
    assert sell2.status == OrderStatus.PARTIAL, "Second order partial"
    assert sell2.filled_quantity == 25, f"Sell2 filled: {sell2.filled_quantity}"

    print("✓ Time priority (FIFO) works correctly")


def test_market_order():
    """Test market order execution"""
    print("\nTest 5: Market Orders")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Build book
    manager.place_limit_order("TEST", OrderSide.SELL, 50, 150.00)
    manager.place_limit_order("TEST", OrderSide.SELL, 50, 151.00)

    # Market buy
    market_buy = manager.place_market_order("TEST", OrderSide.BUY, 75)

    # Verify execution at multiple prices
    assert market_buy.status == OrderStatus.FILLED
    assert market_buy.filled_quantity == 75

    trades = manager.get_all_trades("TEST")
    assert len(trades) == 2
    assert trades[0].price == 150.00  # First match at best price
    assert trades[0].quantity == 50
    assert trades[1].price == 151.00  # Second match at next price
    assert trades[1].quantity == 25

    print("✓ Market orders work correctly")


def test_unfilled_market_order():
    """Test market order with insufficient liquidity"""
    print("\nTest 6: Market Order - Insufficient Liquidity")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Only 50 available
    manager.place_limit_order("TEST", OrderSide.SELL, 50, 150.00)

    # Try to buy 100
    market_buy = manager.place_market_order("TEST", OrderSide.BUY, 100)

    # Should only fill 50
    assert market_buy.filled_quantity == 50, f"Filled: {market_buy.filled_quantity}"
    assert market_buy.status == OrderStatus.PARTIAL, f"Status: {market_buy.status}"

    print("✓ Unfilled market orders handled correctly")


def test_cancel_pending_order():
    """Test cancelling a pending order"""
    print("\nTest 7: Cancel Pending Order")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    order = manager.place_limit_order("TEST", OrderSide.BUY, 100, 150.00)

    # Cancel it
    success = manager.cancel_order(order.order_id)

    assert success, "Cancel should succeed"
    assert order.status == OrderStatus.CANCELLED, f"Status: {order.status}"

    # Verify removed from book
    book = manager.get_order_book("TEST")
    assert book.get_best_bid() is None, "Order should be removed from book"

    print("✓ Cancelling pending orders works correctly")


def test_cancel_filled_order_bug():
    """Test cancelling an already filled order (potential bug)"""
    print("\nTest 8: Cancel Filled Order (Bug Check)")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Place and fill orders
    buy = manager.place_limit_order("TEST", OrderSide.BUY, 100, 150.00)
    sell = manager.place_limit_order("TEST", OrderSide.SELL, 100, 150.00)

    # Both should be filled
    assert buy.status == OrderStatus.FILLED, f"Buy status: {buy.status}"

    # Try to cancel filled order
    success = manager.cancel_order(buy.order_id)

    print(f"  Cancel filled order returned: {success}")
    print(f"  Order status after cancel: {buy.status}")

    # BUG: Status changes from FILLED to CANCELLED
    if buy.status == OrderStatus.CANCELLED:
        print("  ⚠️  BUG FOUND: Filled order status changed to CANCELLED")
        print("  ⚠️  Expected: Should remain FILLED or cancel should fail")
    else:
        print("  ✓ Correctly handled")


def test_negative_quantity():
    """Test negative quantity (no validation)"""
    print("\nTest 9: Negative Quantity (Validation Check)")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    try:
        # This should ideally fail, but no validation exists
        order = manager.place_limit_order("TEST", OrderSide.BUY, -100, 150.00)
        print(f"  ⚠️  WARNING: Negative quantity accepted: {order.quantity}")
        print("  ⚠️  Recommendation: Add input validation")
    except Exception as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_zero_quantity():
    """Test zero quantity"""
    print("\nTest 10: Zero Quantity (Validation Check)")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    try:
        order = manager.place_limit_order("TEST", OrderSide.BUY, 0, 150.00)
        print(f"  ⚠️  WARNING: Zero quantity accepted")
        print("  ⚠️  Recommendation: Add input validation")
    except Exception as e:
        print(f"  ✓ Correctly rejected: {e}")


def test_market_depth():
    """Test market depth calculation"""
    print("\nTest 11: Market Depth")
    manager = OrderBookManager()
    manager.create_order_book("TEST")

    # Build book
    manager.place_limit_order("TEST", OrderSide.BUY, 100, 150.00)
    manager.place_limit_order("TEST", OrderSide.BUY, 200, 149.00)
    manager.place_limit_order("TEST", OrderSide.SELL, 150, 151.00)
    manager.place_limit_order("TEST", OrderSide.SELL, 250, 152.00)

    book = manager.get_order_book("TEST")
    bids, asks = book.get_depth(levels=5)

    # Verify structure
    assert bids.shape[1] == 2, "Bids should have [price, qty]"
    assert asks.shape[1] == 2, "Asks should have [price, qty]"

    # Verify values
    assert bids[0][0] == 150.00, f"Best bid: {bids[0][0]}"
    assert bids[0][1] == 100, f"Best bid qty: {bids[0][1]}"
    assert asks[0][0] == 151.00, f"Best ask: {asks[0][0]}"
    assert asks[0][1] == 150, f"Best ask qty: {asks[0][1]}"

    print("✓ Market depth calculation works correctly")


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Order Book Correctness Tests")
    print("="*60)

    tests = [
        test_basic_matching,
        test_partial_fill,
        test_price_priority,
        test_time_priority,
        test_market_order,
        test_unfilled_market_order,
        test_cancel_pending_order,
        test_cancel_filled_order_bug,
        test_negative_quantity,
        test_zero_quantity,
        test_market_depth,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
