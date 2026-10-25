"""Central settings. Credentials come from the environment (.env), never from code."""

import os

from dotenv import load_dotenv

load_dotenv()

# Agent model: runs the borrower conversation and calls tools.
AGENT_MODEL = os.getenv("AGENT_MODEL", "claude-opus-5-5")

# Simulator and judge models used by the eval suite.
SIMULATOR_MODEL = os.getenv("SIMULATOR_MODEL", "claude-opus-5-5")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "claude-opus-5-5")

# "medium" balances tone and rule-following against latency for chat turns.
AGENT_EFFORT = os.getenv("AGENT_EFFORT", "medium")

# Contact window (borrower's local time), per RBI recovery-agent directions.
CONTACT_HOURS_START = 8   # 8 AM
CONTACT_HOURS_END = 19    # 7 PM

# Escalate after this many failed identity checks.
MAX_VERIFICATION_ATTEMPTS = 2
