# Order Book Test Suite

Comprehensive test suite for the thread-safe order book implementation.

## Test Files

### test_basic_functionality.py
Tests core order book features:
- Order placement (limit and market)
- Order matching and fills
- Partial fills
- Order cancellation
- Best bid/ask calculations
- Market depth
- Price-time priority
- Input validation

### test_simulation_clock.py
Tests SimulationClock features:
- Clock initialization and advancement
- Deterministic timestamps for orders
- Deterministic timestamps for trades
- Reproducible simulations
- System time fallback

### test_direct_mode.py
Tests direct mode functionality:
- Basic operations in direct mode
- Performance comparison (direct vs threaded)
- Result equivalence
- No queue overhead
- Health checks
- Batch processing
- Immediate shutdown

### test_batch_processing.py
Tests batch order processing:
- Batch submission
- All orders processed
- Matching within batches
- Equivalence with individual orders
- Empty and large batches
- Thread-safe mode compatibility
- Sequential order IDs

### test_snapshot.py
Tests snapshot and reset features:
- Basic snapshot save
- State restoration
- Order detail preservation
- Partial fill preservation
- Reset functionality
- Multiple snapshots
- Empty order book
- Best price preservation

### test_memory_limits.py
Tests memory management:
- Unlimited trades (default)
- max_trades limit
- Recent trade retention
- Reset with bounded history
- Different limit values
- Exact limit behavior
- Snapshot compatibility

### test_thread_safety.py
Tests thread-safety features:
- Multi-threaded order submission
- Concurrent reads and writes
- No race conditions in order IDs
- High concurrency handling
- Shutdown with queued orders
- Direct mode warning

### test_edge_cases.py
Tests edge cases and error handling:
- Empty order book operations
- Market orders with no liquidity
- Non-existent order cancellation
- Very large/small quantities and prices
- Fractional quantities
- Many orders at same price
- Alternating order sides
- Crossing spread orders
- Partial fill sequences
- Multiple symbol isolation
- Best price updates

## Running Tests

### Run all tests:
```bash
python tests/run_all_tests.py
```

### Run all tests (verbose):
```bash
python tests/run_all_tests.py -v
```

### Run specific test file:
```bash
python -m unittest tests.test_basic_functionality
```

### Run specific test case:
```bash
python -m unittest tests.test_basic_functionality.TestBasicFunctionality.test_simple_limit_order
```

## Test Coverage

The test suite covers:

**Core Functionality** (test_basic_functionality.py)
- ✅ Order placement and matching
- ✅ Partial and full fills
- ✅ Order cancellation
- ✅ Market data queries
- ✅ Price-time priority
- ✅ Input validation

**Simulation Features** (test_simulation_clock.py, test_direct_mode.py)
- ✅ Deterministic timestamps
- ✅ Clock advancement
- ✅ Direct mode performance
- ✅ Reproducible simulations

**Batch Processing** (test_batch_processing.py)
- ✅ Batch submission
- ✅ Performance optimization
- ✅ Correctness guarantee

**State Management** (test_snapshot.py)
- ✅ Save/load snapshots
- ✅ Reset functionality
- ✅ Multiple simulations

**Memory Management** (test_memory_limits.py)
- ✅ Bounded trade history
- ✅ max_trades parameter
- ✅ Memory limits

**Thread Safety** (test_thread_safety.py)
- ✅ Multi-threaded submission
- ✅ Concurrent access
- ✅ No race conditions
- ✅ Queue management

**Edge Cases** (test_edge_cases.py)
- ✅ Empty states
- ✅ Extreme values
- ✅ Invalid inputs
- ✅ Error handling

## Test Statistics

- **Total test files**: 8
- **Total test cases**: 100+
- **Code coverage**: Core functionality, simulation features, edge cases
- **Performance tests**: Included
- **Thread-safety tests**: Included

## Continuous Testing

All tests are designed to:
- Run quickly (entire suite completes in seconds)
- Be deterministic (no flaky tests)
- Be independent (no shared state)
- Provide clear failure messages
- Cover normal and edge cases

## Adding New Tests

When adding new features:
1. Create test file: `tests/test_<feature>.py`
2. Import unittest and orderbook modules
3. Create test class inheriting from `unittest.TestCase`
4. Write test methods starting with `test_`
5. Run tests to verify

Example:
```python
import unittest
from orderbook import OrderBookEngine, OrderSide

class TestNewFeature(unittest.TestCase):
    def test_feature(self):
        engine = OrderBookEngine("TEST", direct_mode=True)
        # ... test code ...
        self.assertEqual(expected, actual)
```
