# Saline SDK Tests

This directory contains the tests for the Saline SDK. The tests are organized into two main categories:

## Directory Structure

```
tests/
├── unit/           # Unit tests that don't require external dependencies
└── integration/    # Integration tests that require a live Saline node
```

## Unit Tests

The `unit/` directory contains tests that can be run without any external dependencies. These tests focus on the internal logic of the SDK components and use mocks for external services like the Saline node. Unit tests should be:

- Fast and lightweight
- Independent of external services
- Run on every commit in CI
- Using pytest fixtures for setup/teardown

To run unit tests:

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=saline_sdk
```

## Integration Tests

The `integration/` directory contains tests that require a live Saline node to execute. These tests validate the SDK's functionality against an actual blockchain. Integration tests:

- Require a running Saline node
- Test the full stack from SDK to blockchain
- Might take longer to run
- Are typically run less frequently in CI (on specific branches or manually triggered)

To run integration tests:

```bash
# Run all integration tests
pytest tests/integration/

# Run against a specific node
pytest tests/integration/ --saline-url="http://your-node:26657"

# Skip integration tests
pytest tests/ --skip-integration

# For more details on running integration tests
cat tests/integration/README.md
```

## Test Markers

We use pytest markers to distinguish between test types:

- `@pytest.mark.unit`: Tests that don't require external dependencies
- `@pytest.mark.integration`: Tests that require a live Saline node

This allows for running specific types of tests:

```bash
# Run only integration tests
pytest -m integration

# Run only unit tests
pytest -m unit
```

## CI Integration

In CI, we typically:

1. Run unit tests on every commit/PR
2. Run integration tests on specific branches or manually triggered workflows

The integration tests require a running Saline node, which can be provided by:

- Spinning up an ephemeral node in a container
- Using a dedicated testnet
- Using a mock node for basic integration testing 