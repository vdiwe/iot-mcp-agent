# Unit Tests for IoT MCP Agent

Comprehensive test suite for the `iot-mcp-agent` project covering all major components.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_config.py           # Configuration (Settings) tests
├── test_simulator.py        # Device simulator tests
├── test_tools.py            # Tools (device, alarm, action) tests
├── test_agents.py           # Agent and agentic loop tests
├── test_llm.py             # LLM adapter factory tests
└── __init__.py
```

## Running Tests

### Install Test Dependencies

```bash
pip install -e ".[test]"
# or for full dev environment:
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_simulator.py
```

### Run Specific Test Class

```bash
pytest tests/test_simulator.py::TestDeviceSimulator
```

### Run Specific Test

```bash
pytest tests/test_simulator.py::TestDeviceSimulator::test_list_devices_basic
```

### Run with Coverage Report

```bash
pytest --cov=src/iot_mcp_agent --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run Only Unit Tests (Exclude Integration Tests)

```bash
pytest -m "not integration"
```

### Run Only Async Tests

```bash
pytest -m asyncio
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Print Statements

```bash
pytest -s
```

## Test Coverage

Current test coverage includes:

- **Configuration Tests** (`test_config.py`)
  - Settings initialization
  - Environment variable loading
  - LLM provider configuration (Anthropic, OpenAI, Gemini)
  - Cumulocity credentials

- **Device Simulator Tests** (`test_simulator.py`)
  - Device listing with filters
  - Device retrieval
  - Measurement collection
  - Alarm management
  - Device configuration updates
  - Group summaries

- **Tools Tests** (`test_tools.py`)
  - Device tools (list, get, measurements)
  - Alarm tools (get, create)
  - Action tools (config update, notifications)
  - Tool integration with adapters

- **Agent Tests** (`test_agents.py`)
  - Agent initialization
  - Goal execution
  - Iteration limits
  - Tool call recording
  - Action tracking

- **LLM Tests** (`test_llm.py`)
  - Adapter factory creation
  - Provider selection (Anthropic, OpenAI, Gemini)
  - API method validation

## Test Fixtures (conftest.py)

### Available Fixtures

- `mock_env_vars`: Sets up standard environment variables
- `mock_llm_response`: Mocks an LLM API response
- `mock_tool_call`: Mocks a tool call
- `mock_async_context`: Mocks an async context manager

Usage:
```python
@pytest.mark.asyncio
async def test_something(mock_env_vars):
    # Test code here
    pass
```

## Writing New Tests

### Template for Async Test

```python
@pytest.mark.asyncio
async def test_async_operation(mock_env_vars):
    """Test description."""
    # Arrange
    adapter = AsyncMock()
    adapter.list_devices.return_value = {"total": 1, "devices": [...]}
    
    # Act
    tools = DeviceTools(adapter)
    result = await tools.list_devices()
    
    # Assert
    assert result["total"] == 1
```

### Template for Tool Mock

```python
def test_with_mocked_tool(mock_adapter):
    """Test with mocked adapter."""
    # Mock adapter behavior
    mock_adapter.get_device.return_value = {
        "id": "device-001",
        "name": "Sensor A"
    }
    
    # Use adapter
    tools = DeviceTools(mock_adapter)
    # ... test code
```

## Common Issues

### AsyncIO Test Timeout
If tests timeout, increase the timeout in `pytest.ini` or mark specific tests:
```python
@pytest.mark.asyncio
@pytest.mark.timeout(10)  # 10 second timeout
async def test_something():
    pass
```

### Mock Issues
Ensure you're using `AsyncMock` for async functions:
```python
from unittest.mock import AsyncMock

mock_adapter = AsyncMock()
mock_adapter.list_devices = AsyncMock(return_value={...})
```

### Environment Variable Not Set
Use the `mock_env_vars` fixture or monkeypatch manually:
```python
def test_with_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    # test code
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest --cov
```

## Best Practices

1. **Use fixtures** for common setup (mock_adapter, mock_env_vars)
2. **Mock external dependencies** (LLM APIs, device adapters)
3. **Test async code** with `@pytest.mark.asyncio`
4. **Organize tests** by component (TestDeviceTools, TestAlarmTools, etc.)
5. **Use descriptive names** (test_list_devices_with_filters)
6. **Test both success and error cases**
7. **Keep tests focused** (one assertion per test when possible)

## Contributing Tests

When adding new features, please:
1. Write tests first (TDD approach recommended)
2. Ensure tests pass locally
3. Check coverage doesn't decrease
4. Update this README if adding new test categories
