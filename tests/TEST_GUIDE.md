# Unit Test Suite for iot-mcp-agent

## Overview

Comprehensive test suite for the `iot-mcp-agent` project with **6 test modules** covering:
- Configuration management
- Device simulator
- Tool implementations
- Agent logic
- LLM adapters
- Integration workflows

## Quick Start

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src/iot_mcp_agent

# Run specific test file
pytest tests/test_simulator.py -v
```

## Test Modules

### 1. **test_config.py** - Configuration Tests
Tests the `Settings` class from `config.py`

**Coverage:**
- ✅ Settings initialization with defaults
- ✅ Environment variable loading
- ✅ LLM provider configuration (Anthropic, OpenAI, Gemini)
- ✅ Cumulocity authentication settings
- ✅ Log level validation
- ✅ Custom model overrides

**Example:**
```python
def test_settings_c8y_configuration(self, monkeypatch):
    monkeypatch.setenv("C8Y_BASE_URL", "https://test.cumulocity.com")
    settings = Settings()
    assert settings.c8y_base_url == "https://test.cumulocity.com"
```

### 2. **test_simulator.py** - Device Simulator Tests
Tests the `DeviceSimulator` class from `utils/simulator.py`

**Coverage:**
- ✅ Device listing with various filters (status, type, limit)
- ✅ Single device retrieval
- ✅ Time-series measurement retrieval
- ✅ Measurement type filtering
- ✅ Alarm management (get, create)
- ✅ Device configuration updates
- ✅ Group health summaries

**Tests:** 12 async tests
```python
@pytest.mark.asyncio
async def test_list_devices_with_status_filter(self, simulator):
    result = await simulator.list_devices(status="AVAILABLE")
    for device in result["devices"]:
        assert device["status"] == "AVAILABLE"
```

### 3. **test_tools.py** - Tools Integration Tests
Tests the tool implementations from `tools/` directory

**Coverage:**
- **DeviceTools:**
  - ✅ List devices with filters
  - ✅ Get individual device details
  - ✅ Retrieve measurements
  - ✅ Get device group summaries

- **AlarmTools:**
  - ✅ Get alarms (all, by device, by severity)
  - ✅ Create alarms with severity levels
  - ✅ Alarm filtering

- **ActionTools:**
  - ✅ Update device configuration
  - ✅ Send notifications (email, Slack, SMS)
  - ✅ Notification with priority levels

**Tests:** 18 async tests
```python
@pytest.mark.asyncio
async def test_create_alarm(self, mock_adapter):
    mock_adapter.create_alarm.return_value = {...}
    tools = AlarmTools(mock_adapter)
    result = await tools.create_alarm(...)
    assert result["severity"] == "CRITICAL"
```

### 4. **test_agents.py** - Agent Logic Tests
Tests the `BaseAgent` class and agentic loop

**Coverage:**
- ✅ Agent initialization with different platforms
- ✅ Custom iteration limits
- ✅ Basic goal execution
- ✅ Iteration limit enforcement
- ✅ Tool execution flow
- ✅ Multi-provider agent creation (Anthropic, OpenAI, Gemini)

**Tests:** 10 tests (mix of sync and async)
```python
@pytest.mark.asyncio
async def test_agent_run_basic_goal(self, mock_env_vars):
    agent = BaseAgent(platform="simulate", max_iterations=1)
    run = await agent.run_once("List all devices")
    assert "devices" in run.final_summary.lower()
```

### 5. **test_llm.py** - LLM Adapter Tests
Tests the LLM adapter factory and provider implementations

**Coverage:**
- ✅ Anthropic adapter creation and initialization
- ✅ OpenAI adapter creation and initialization
- ✅ Gemini adapter creation and initialization
- ✅ Invalid provider error handling
- ✅ Factory pattern from environment settings

**Tests:** 8 tests
```python
def test_create_anthropic_adapter(self, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    adapter = create_llm_adapter(provider="anthropic")
    assert hasattr(adapter, "chat")
```

### 6. **test_integration.py** - Integration Tests
Tests components working together in realistic workflows

**Coverage:**
- ✅ Complete device monitoring lifecycle
- ✅ Multi-tool workflows
- ✅ Anomaly detection workflow
- ✅ Device status filtering
- ✅ Alarm severity filtering
- ✅ Configuration file loading
- ✅ Error handling for invalid inputs

**Tests:** 12 async tests
```python
@pytest.mark.asyncio
async def test_anomaly_detection_workflow(self, simulator):
    # Detect high temperatures across devices
    # Create alarms for anomalies
    # Simulate realistic agent workflow
```

## Test Statistics

| Module | Tests | Type | Status |
|--------|-------|------|--------|
| test_config.py | 8 | Unit | ✅ |
| test_simulator.py | 12 | Unit | ✅ |
| test_tools.py | 18 | Unit | ✅ |
| test_agents.py | 10 | Unit | ✅ |
| test_llm.py | 8 | Unit | ✅ |
| test_integration.py | 12 | Integration | ✅ |
| **TOTAL** | **68** | Mixed | **✅** |

## Fixtures (conftest.py)

Reusable fixtures for all tests:

```python
@pytest.fixture
def mock_env_vars(monkeypatch)
    # Sets: LLM_PROVIDER=anthropic, PLATFORM=simulate, etc.

@pytest.fixture
def mock_llm_response()
    # Mocks LLM response with stop_reason="end_turn"

@pytest.fixture
def mock_tool_call()
    # Mocks a tool call with name="list_devices"

@pytest.fixture
async def simulator()
    # Creates initialized DeviceSimulator
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Coverage Report
```bash
pytest --cov=src/iot_mcp_agent --cov-report=html
```
Coverage report generated in `htmlcov/index.html`

### Run Specific Test Module
```bash
pytest tests/test_simulator.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_simulator.py::TestDeviceSimulator -v
```

### Run Specific Test
```bash
pytest tests/test_simulator.py::TestDeviceSimulator::test_list_devices_basic -v
```

### Run with Markers
```bash
pytest -m asyncio              # Only async tests
pytest -m "not integration"    # Skip integration tests
```

### Run in Watch Mode
```bash
pytest-watch                   # Requires: pip install pytest-watch
```

## CI/CD Integration

GitHub Actions workflow provided in `.github/workflows/tests.yml`

**Features:**
- ✅ Tests on push to main/develop
- ✅ Tests on pull requests
- ✅ Python 3.11 and 3.12 matrix
- ✅ Linting with ruff
- ✅ Type checking with mypy
- ✅ Coverage report upload to Codecov

**Workflow Status:** Active on GitHub Actions

## Code Coverage Goals

| Component | Target Coverage | Current |
|-----------|-----------------|---------|
| config.py | 95% | ✅ |
| simulator.py | 90% | ✅ |
| tools/ | 85% | ✅ |
| agents/ | 80% | ✅ |
| llm/ | 80% | ✅ |
| **Overall** | **85%** | ✅ |

## Mocking Strategy

All tests use `unittest.mock` for external dependencies:

**Adapters:** Mocked with `AsyncMock` to simulate real behavior
```python
mock_adapter = AsyncMock()
mock_adapter.list_devices.return_value = {"devices": [...]}
```

**LLM Responses:** Mocked to avoid API calls
```python
mock_llm.chat = AsyncMock(return_value=MagicMock(...))
```

**Environment:** Mocked with `monkeypatch`
```python
monkeypatch.setenv("LLM_PROVIDER", "openai")
```

## Best Practices Implemented

✅ **Clear Naming:** Descriptive test names (test_list_devices_with_status_filter)
✅ **Single Responsibility:** One assertion focus per test
✅ **DRY Principle:** Shared fixtures for common setup
✅ **Async Support:** @pytest.mark.asyncio for all async tests
✅ **Error Cases:** Tests for both success and failure paths
✅ **Documentation:** Docstrings for complex tests
✅ **Isolation:** Tests don't depend on each other
✅ **Parametrization:** Reusable test templates

## Troubleshooting

### Tests Timeout
Increase timeout in pytest.ini or mark specific tests:
```python
@pytest.mark.timeout(30)
```

### Import Errors
Ensure `src/` is in Python path:
```bash
export PYTHONPATH=/workspace/src:$PYTHONPATH
```

### Mock Not Working
Use correct mock type:
```python
# For async functions:
from unittest.mock import AsyncMock
# For sync functions:
from unittest.mock import MagicMock
```

### Environment Variables Not Set
Use monkeypatch fixture:
```python
def test_something(monkeypatch):
    monkeypatch.setenv("VAR", "value")
```

## Contributing Tests

When adding new features:

1. **Write tests first** (TDD approach)
2. **Use existing fixtures** when possible
3. **Follow naming conventions** (test_module_function_scenario)
4. **Add docstrings** to complex tests
5. **Ensure tests pass** before submitting PR
6. **Check coverage** doesn't decrease:
   ```bash
   pytest --cov=src/iot_mcp_agent --cov-report=term-missing
   ```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/how-to-use-fixtures.html)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Async Testing with Pytest](https://docs.pytest.org/en/stable/how-to-use-fixtures.html#using-fixtures-with-asyncio)

## License

All tests are MIT licensed, matching the project license.
