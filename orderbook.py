"""
Simple Order Book for Multiple Stocks and Derivative Trading
Uses Python and NumPy for efficient order management and matching.
"""

import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable
import time


class OrderSide(Enum):
    """Order side: BUY or SELL"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type: LIMIT or MARKET"""
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    """
    Represents a trading order.

    Attributes:
        order_id: Unique identifier for the order
        symbol: Trading symbol (e.g., 'AAPL', 'TSLA', 'SPY_CALL_450')
        side: BUY or SELL
        order_type: LIMIT or MARKET
        quantity: Number of shares/contracts
        price: Limit price (None for market orders)
        timestamp: Order creation time
        status: Current order status
        filled_quantity: Amount filled so far
    """
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0

    def remaining_quantity(self) -> float:
        """Get the remaining unfilled quantity"""
        return self.quantity - self.filled_quantity

    def is_complete(self) -> bool:
        """Check if order is completely filled"""
        return self.filled_quantity >= self.quantity

    def __repr__(self):
        return (f"Order({self.order_id}, {self.symbol}, {self.side.value}, "
                f"{self.order_type.value}, qty={self.quantity}, "
                f"price={self.price}, filled={self.filled_quantity})")


@dataclass
class Trade:
    """
    Represents an executed trade.

    Attributes:
        trade_id: Unique trade identifier
        symbol: Trading symbol
        buy_order_id: ID of the buy order
        sell_order_id: ID of the sell order
        price: Execution price
        quantity: Executed quantity
        timestamp: Execution time
    """
    trade_id: str
    symbol: str
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return (f"Trade({self.trade_id}, {self.symbol}, "
                f"price={self.price}, qty={self.quantity})")


class OrderBook:
    """
    Order book for a single instrument using NumPy for efficient operations.

    Features:
    - Price-time priority matching
    - Efficient price level management with NumPy
    - Support for limit and market orders
    - Real-time trade execution
    """

    def __init__(self, symbol: str):
        """
        Initialize an order book for a specific symbol.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'GOOGL')
        """
        self.symbol = symbol
        # Price levels: {price: deque of orders}
        self.bids: Dict[float, deque] = defaultdict(deque)  # Buy orders
        self.asks: Dict[float, deque] = defaultdict(deque)  # Sell orders
        # Order lookup
        self.orders: Dict[str, Order] = {}
        # Trade history
        self.trades: List[Trade] = []
        self.trade_counter = 0

        # Callbacks for events
        self.on_trade_callback: Optional[Callable] = None
        self.on_order_update_callback: Optional[Callable] = None

    def add_order(self, order: Order) -> List[Trade]:
        """
        Add an order to the book and attempt to match it.

        Args:
            order: Order to add

        Returns:
            List of trades executed
        """
        if order.symbol != self.symbol:
            raise ValueError(f"Order symbol {order.symbol} doesn't match book symbol {self.symbol}")

        # Store order
        self.orders[order.order_id] = order

        # Try to match the order
        trades = self._match_order(order)

        # If order is not completely filled, add to book
        if not order.is_complete() and order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                self.bids[order.price].append(order)
            else:
                self.asks[order.price].append(order)

            if order.filled_quantity > 0:
                order.status = OrderStatus.PARTIAL

        # Trigger callbacks
        if trades and self.on_trade_callback:
            for trade in trades:
                self.on_trade_callback(trade)

        if self.on_order_update_callback:
            self.on_order_update_callback(order)

        return trades

    def _match_order(self, order: Order) -> List[Trade]:
        """
        Match an incoming order against the book.

        Args:
            order: Order to match

        Returns:
            List of executed trades
        """
        trades = []

        if order.side == OrderSide.BUY:
            # Match against asks (sell orders)
            trades = self._match_buy_order(order)
        else:
            # Match against bids (buy orders)
            trades = self._match_sell_order(order)

        # Update order status
        if order.is_complete():
            order.status = OrderStatus.FILLED

        return trades

    def _match_buy_order(self, buy_order: Order) -> List[Trade]:
        """Match a buy order against sell orders"""
        trades = []

        # Get sorted ask prices (ascending)
        if not self.asks:
            return trades

        ask_prices = np.array(sorted(self.asks.keys()))

        for ask_price in ask_prices:
            # Check if we can match at this price
            if buy_order.order_type == OrderType.LIMIT and buy_order.price < ask_price:
                break

            # Match orders at this price level
            while self.asks[ask_price] and not buy_order.is_complete():
                sell_order = self.asks[ask_price][0]

                # Calculate trade quantity
                trade_qty = min(buy_order.remaining_quantity(),
                               sell_order.remaining_quantity())

                # Execute trade
                trade = self._execute_trade(buy_order, sell_order, ask_price, trade_qty)
                trades.append(trade)

                # Update order filled quantities
                buy_order.filled_quantity += trade_qty
                sell_order.filled_quantity += trade_qty

                # Remove filled sell order
                if sell_order.is_complete():
                    self.asks[ask_price].popleft()
                    sell_order.status = OrderStatus.FILLED
                    if self.on_order_update_callback:
                        self.on_order_update_callback(sell_order)

            # Clean up empty price level
            if not self.asks[ask_price]:
                del self.asks[ask_price]

            if buy_order.is_complete():
                break

        return trades

    def _match_sell_order(self, sell_order: Order) -> List[Trade]:
        """Match a sell order against buy orders"""
        trades = []

        # Get sorted bid prices (descending)
        if not self.bids:
            return trades

        bid_prices = np.array(sorted(self.bids.keys(), reverse=True))

        for bid_price in bid_prices:
            # Check if we can match at this price
            if sell_order.order_type == OrderType.LIMIT and sell_order.price > bid_price:
                break

            # Match orders at this price level
            while self.bids[bid_price] and not sell_order.is_complete():
                buy_order = self.bids[bid_price][0]

                # Calculate trade quantity
                trade_qty = min(sell_order.remaining_quantity(),
                               buy_order.remaining_quantity())

                # Execute trade
                trade = self._execute_trade(buy_order, sell_order, bid_price, trade_qty)
                trades.append(trade)

                # Update order filled quantities
                sell_order.filled_quantity += trade_qty
                buy_order.filled_quantity += trade_qty

                # Remove filled buy order
                if buy_order.is_complete():
                    self.bids[bid_price].popleft()
                    buy_order.status = OrderStatus.FILLED
                    if self.on_order_update_callback:
                        self.on_order_update_callback(buy_order)

            # Clean up empty price level
            if not self.bids[bid_price]:
                del self.bids[bid_price]

            if sell_order.is_complete():
                break

        return trades

    def _execute_trade(self, buy_order: Order, sell_order: Order,
                       price: float, quantity: float) -> Trade:
        """Create a trade record"""
        self.trade_counter += 1
        trade = Trade(
            trade_id=f"{self.symbol}_T{self.trade_counter}",
            symbol=self.symbol,
            buy_order_id=buy_order.order_id,
            sell_order_id=sell_order.order_id,
            price=price,
            quantity=quantity
        )
        self.trades.append(trade)
        return trade

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if cancelled, False if not found
        """
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]

        # Remove from book
        if order.side == OrderSide.BUY and order.price in self.bids:
            try:
                self.bids[order.price].remove(order)
                if not self.bids[order.price]:
                    del self.bids[order.price]
            except ValueError:
                pass
        elif order.side == OrderSide.SELL and order.price in self.asks:
            try:
                self.asks[order.price].remove(order)
                if not self.asks[order.price]:
                    del self.asks[order.price]
            except ValueError:
                pass

        order.status = OrderStatus.CANCELLED

        if self.on_order_update_callback:
            self.on_order_update_callback(order)

        return True

    def get_best_bid(self) -> Optional[float]:
        """Get the highest bid price"""
        if not self.bids:
            return None
        return max(self.bids.keys())

    def get_best_ask(self) -> Optional[float]:
        """Get the lowest ask price"""
        if not self.asks:
            return None
        return min(self.asks.keys())

    def get_spread(self) -> Optional[float]:
        """Get the bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid is None or best_ask is None:
            return None
        return best_ask - best_bid

    def get_depth(self, levels: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get market depth (top N price levels).

        Args:
            levels: Number of price levels to return

        Returns:
            Tuple of (bids, asks) as NumPy arrays with shape (levels, 2)
            Each row is [price, total_quantity]
        """
        # Get bids (descending order)
        bid_data = []
        if self.bids:
            sorted_bids = sorted(self.bids.keys(), reverse=True)[:levels]
            for price in sorted_bids:
                total_qty = sum(o.remaining_quantity() for o in self.bids[price])
                bid_data.append([price, total_qty])

        # Get asks (ascending order)
        ask_data = []
        if self.asks:
            sorted_asks = sorted(self.asks.keys())[:levels]
            for price in sorted_asks:
                total_qty = sum(o.remaining_quantity() for o in self.asks[price])
                ask_data.append([price, total_qty])

        # Convert to NumPy arrays
        bids_array = np.array(bid_data) if bid_data else np.zeros((0, 2))
        asks_array = np.array(ask_data) if ask_data else np.zeros((0, 2))

        return bids_array, asks_array

    def get_order_book_snapshot(self) -> dict:
        """Get a complete snapshot of the order book"""
        bids, asks = self.get_depth(levels=10)
        return {
            'symbol': self.symbol,
            'best_bid': self.get_best_bid(),
            'best_ask': self.get_best_ask(),
            'spread': self.get_spread(),
            'bids': bids,
            'asks': asks,
            'total_trades': len(self.trades)
        }

    def __repr__(self):
        return (f"OrderBook({self.symbol}, "
                f"best_bid={self.get_best_bid()}, "
                f"best_ask={self.get_best_ask()}, "
                f"spread={self.get_spread()})")


class OrderBookManager:
    """
    Manages multiple order books for different instruments.

    Provides a unified interface for trading multiple stocks and derivatives.
    """

    def __init__(self):
        """Initialize the order book manager"""
        self.order_books: Dict[str, OrderBook] = {}
        self.order_counter = 0
        self.all_orders: Dict[str, Order] = {}

        # Global callbacks
        self.on_trade_callback: Optional[Callable] = None
        self.on_order_update_callback: Optional[Callable] = None

    def create_order_book(self, symbol: str) -> OrderBook:
        """
        Create an order book for a new symbol.

        Args:
            symbol: Trading symbol

        Returns:
            The created order book
        """
        if symbol in self.order_books:
            return self.order_books[symbol]

        order_book = OrderBook(symbol)

        # Set up callbacks
        if self.on_trade_callback:
            order_book.on_trade_callback = self.on_trade_callback
        if self.on_order_update_callback:
            order_book.on_order_update_callback = self.on_order_update_callback

        self.order_books[symbol] = order_book
        return order_book

    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for a symbol"""
        return self.order_books.get(symbol)

    def place_order(self, symbol: str, side: OrderSide, quantity: float,
                   order_type: OrderType = OrderType.LIMIT,
                   price: Optional[float] = None) -> Order:
        """
        Place an order (simplified interface).

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            order_type: LIMIT or MARKET
            price: Limit price (required for limit orders)

        Returns:
            The created order
        """
        # Create order book if it doesn't exist
        if symbol not in self.order_books:
            self.create_order_book(symbol)

        # Generate order ID
        self.order_counter += 1
        order_id = f"ORD{self.order_counter:06d}"

        # Validate price for limit orders
        if order_type == OrderType.LIMIT and price is None:
            raise ValueError("Limit orders require a price")

        # Create order
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )

        # Store order
        self.all_orders[order_id] = order

        # Submit to order book
        self.order_books[symbol].add_order(order)

        return order

    def place_limit_order(self, symbol: str, side: OrderSide,
                         quantity: float, price: float) -> Order:
        """Convenience method to place a limit order"""
        return self.place_order(symbol, side, quantity, OrderType.LIMIT, price)

    def place_market_order(self, symbol: str, side: OrderSide,
                          quantity: float) -> Order:
        """Convenience method to place a market order"""
        return self.place_order(symbol, side, quantity, OrderType.MARKET)

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if cancelled, False if not found
        """
        if order_id not in self.all_orders:
            return False

        order = self.all_orders[order_id]
        symbol = order.symbol

        if symbol in self.order_books:
            return self.order_books[symbol].cancel_order(order_id)

        return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        return self.all_orders.get(order_id)

    def get_all_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """
        Get all trades, optionally filtered by symbol.

        Args:
            symbol: Optional symbol filter

        Returns:
            List of trades
        """
        if symbol:
            if symbol in self.order_books:
                return self.order_books[symbol].trades
            return []

        # Get all trades from all order books
        all_trades = []
        for order_book in self.order_books.values():
            all_trades.extend(order_book.trades)

        # Sort by timestamp
        all_trades.sort(key=lambda t: t.timestamp)
        return all_trades

    def get_market_summary(self) -> dict:
        """Get summary of all order books"""
        summary = {}
        for symbol, order_book in self.order_books.items():
            summary[symbol] = order_book.get_order_book_snapshot()
        return summary

    def get_portfolio_stats(self) -> dict:
        """Get overall statistics"""
        total_orders = len(self.all_orders)
        total_trades = sum(len(ob.trades) for ob in self.order_books.values())

        orders_by_status = defaultdict(int)
        for order in self.all_orders.values():
            orders_by_status[order.status.value] += 1

        return {
            'total_instruments': len(self.order_books),
            'total_orders': total_orders,
            'total_trades': total_trades,
            'orders_by_status': dict(orders_by_status)
        }

    def __repr__(self):
        return f"OrderBookManager(instruments={len(self.order_books)}, orders={len(self.all_orders)})"
