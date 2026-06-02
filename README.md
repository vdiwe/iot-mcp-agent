# 🤖 IoT-MCP-Agent

**Agentic AI for Industrial IoT using the Model Context Protocol (MCP)**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg)](https://modelcontextprotocol.io)
[![Cumulocity](https://img.shields.io/badge/IoT-Cumulocity-orange.svg)](https://cumulocity.com)

> Autonomous AI agents that monitor, diagnose, and act on industrial IoT device data — powered by the Model Context Protocol (MCP) and Large Language Models.

---

## 🌟 What Is This?

`iot-mcp-agent` is an open-source framework that connects **AI reasoning** to **industrial IoT platforms** through the **Model Context Protocol**.

**Currently supported platforms:**
- ✅ **Cumulocity IoT** (production-ready REST API adapter)
- ✅ **Built-in simulator** (for demo and testing)

**Planned platforms (roadmap):**
- 🔜 AWS IoT Core
- 🔜 Azure IoT Hub

Instead of writing brittle if-else rules for device monitoring, you define **goals** and let the agent reason about what actions to take — pulling telemetry, diagnosing anomalies, triggering alerts, and updating device configurations autonomously.

```
Device Telemetry ──► MCP Server ──► AI Agent ──► Decision ──► Action
   (Cumulocity)        (Tools)      (Claude/GPT)   (Reason)   (Alert/Fix/Log)
```

---

## 🎯 Use Cases

| Scenario | What the Agent Does |
|---|---|
| 🌡️ Temperature spike on factory floor | Detects anomaly → checks device history → cross-references nearby sensors → raises priority alert |
| 🔋 Battery drain on field devices | Identifies affected device group → adjusts reporting interval → notifies field team |
| ⚙️ Predictive maintenance | Monitors vibration patterns → compares to baseline → schedules maintenance ticket before failure |
| 🔌 Device goes offline | Checks network topology → attempts remote restart → escalates if unresolved |
| 📊 Daily fleet health summary | Scans all devices → generates natural language report → posts to Slack |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    IoT-MCP-Agent                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │  MCP Server  │    │  AI Agent    │    │  Action  │  │
│  │              │    │              │    │  Engine  │  │
│  │ • list_devices│◄─►│ • Reasoning  │───►│          │  │
│  │ • get_device  │   │ • Planning   │    │• Alerts  │  │
│  │ • get_measurements   │ • Tool Use   │    │• Configs │  │
│  │ • update_device_config   │ • Memory     │    │• Tickets │  │
│  │ • send_notification      │              │    │• Reports │  │
│  └──────────────┘    └──────────────┘    └──────────┘  │
│          │                                              │
│  ┌───────▼──────────────────────────────────────┐      │
│  │            IoT Platform Adapters             │      │
│  │  Cumulocity IoT │ AWS IoT Core │ Azure IoT   │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Cumulocity IoT tenant (or use the built-in simulator)
- Anthropic API key (or OpenAI)

### Install

```bash
git clone https://github.com/YOUR_USERNAME/iot-mcp-agent.git
cd iot-mcp-agent
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your credentials
```

### Run the Demo (Simulated Devices)

```bash
  # The agent spawns its own MCP server subprocess — just run it directly
  python -m iot_mcp_agent --platform simulate --goal "Monitor all devices and alert on any anomalies"
  ```

  **Note:** You don't need to start the MCP server separately. `BaseAgent` and `MonitorAgent` spawn the server internally via stdio.

  ### Run Against Real Cumulocity

```

### Run Against Real Cumulocity
### Run the Demo (Simulated Devices)

```bash
# The agent spawns its own MCP server subprocess — just run it directly
python -m iot_mcp_agent --platform simulate --goal "Monitor all devices and alert on any anomalies"
```

**Note:** You don't need to start the MCP server separately. `BaseAgent` and `MonitorAgent` spawn the server internally via stdio.

### Run Against Real Cumulocity

```bash
# Set credentials in .env
C8Y_BASE_URL=https://your-tenant.cumulocity.com
C8Y_USERNAME=your@email.com
C8Y_PASSWORD=yourpassword
ANTHROPIC_API_KEY=sk-ant-...

python -m iot_mcp_agent \
  --platform cumulocity \
  --goal "Generate a health report for all devices in the 'Factory Floor' group"
```

---

## 📁 Project Structure

```
iot-mcp-agent/
├── src/
│   └── iot_mcp_agent/
│       ├── __init__.py
│       ├── __main__.py        # CLI entry point
│       ├── config.py          # Environment-driven settings
│       ├── py.typed
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base_agent.py
│       │   └── monitor_agent.py
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── server.py
│       ├── platforms/
│       │   ├── __init__.py
│       │   └── cumulocity.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── action_tools.py
│       │   ├── alarm_tools.py
│       │   └── device_tools.py
│       └── utils/
│           ├── __init__.py
│           └── simulator.py
├── examples/
│   ├── temperature_monitor.py
│   └── fleet_health_report.py
├── pyproject.toml
└── .env.example
```

---

## 🔧 Configuration

`.env.example`:
```env
# IoT Platform
PLATFORM=simulate                # Currently supported: simulate | cumulocity
C8Y_BASE_URL=https://tenant.cumulocity.com
C8Y_USERNAME=user@example.com
C8Y_PASSWORD=

# LLM Provider
LLM_PROVIDER=anthropic           # anthropic | openai
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LLM_MODEL=claude-sonnet-4-5

# Agent Settings
AGENT_MAX_ITERATIONS=20
AGENT_CHECK_INTERVAL_SECONDS=60
LOG_LEVEL=INFO
```

---

## 📖 Examples

### Temperature Anomaly Monitor

```python
from iot_mcp_agent import MonitorAgent
    Monitor all temperature sensors on the factory floor.
    If any sensor reads above 85°C:
    1. Check if neighbouring sensors also show elevation
    2. Look at the last 24h trend for that device  
    3. If confirmed anomaly, create a CRITICAL alarm
    4. Suggest whether this needs immediate shutdown or just monitoring
    """,
    check_interval_seconds=30
)

await agent.run()
```

### Predictive Maintenance *(To be implemented)*

```python
# Coming soon: DiagnosticAgent specialized for predictive maintenance
# For now, use BaseAgent with this goal:

from iot_mcp_agent.agents import BaseAgent

agent = BaseAgent(
  python -m iot_mcp_agent --platform simulate --goal "Monitor all devices and alert on any anomalies"
  ```
    
  **Note:** You don't need to start the MCP server separately. `BaseAgent` and `MonitorAgent` spawn the server internally via stdio.
    
  ### Run Against Real Cumulocity
    Analyse vibration data for all motors in the 'Pump Station' device group.
    Compare current readings to the 30-day baseline.
    Flag any motors showing >20% deviation and estimate time-to-failure
    based on degradation trend. Output a maintenance schedule.
    """,
)

report = await agent.run_once()
print(report)
```

**Note:** `DiagnosticAgent` is planned but not yet implemented. Currently available: `BaseAgent`, `MonitorAgent`.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

**Good first issues:**
- Add Azure IoT Hub adapter
- Add Slack/Teams notification action
- Add MQTT device simulator
- Improve anomaly detection heuristics

---

[LinkedIn](https://linkedin.com/in/vachaspati-diwevedi) · [Email](mailto:vachhy@gmail.com)
