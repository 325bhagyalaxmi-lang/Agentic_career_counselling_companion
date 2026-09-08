#!/usr/bin/env bash
# =============================================================================
# import-all.sh — Import all tools, flows, and agents for the
# Agentic Career Counselling Companion into watsonx Orchestrate.
#
# Usage:
#   chmod +x career_counsellor/import-all.sh
#   ./career_counsellor/import-all.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo ""
echo "============================================================"
echo " Agentic Career Counselling Companion — Import Script"
echo "============================================================"
echo ""

# -----------------------------------------------------------------------------
# 1. Import Python Tools
# -----------------------------------------------------------------------------
echo "[1/3] Importing Python tools..."

for tool_file in \
  granite_llm_tool.py \
  student_profile_tool.py \
  market_trends_tool.py \
  career_pathway_tool.py \
  skill_gap_tool.py; do

  echo "  → Importing tool: ${tool_file}"
  orchestrate tools import -k python -f "${SCRIPT_DIR}/tools/${tool_file}"
done

echo "[✓] Python tools imported successfully."
echo ""

# -----------------------------------------------------------------------------
# 2. Import Flow Tools
# -----------------------------------------------------------------------------
echo "[2/3] Importing flow tools..."

for flow_file in \
  career_assessment_flow.py \
  skill_gap_coaching_flow.py; do

  echo "  → Importing flow: ${flow_file}"
  orchestrate tools import -k flow -f "${SCRIPT_DIR}/tools/${flow_file}"
done

echo "[✓] Flow tools imported successfully."
echo ""

# -----------------------------------------------------------------------------
# 3. Import Agents (sub-agents first, then main orchestrator)
# -----------------------------------------------------------------------------
echo "[3/3] Importing agents..."

for agent_file in \
  career_profile_agent.yaml \
  career_pathway_agent.yaml \
  skill_gap_agent.yaml \
  career_counsellor_agent.yaml; do

  echo "  → Importing agent: ${agent_file}"
  orchestrate agents import -f "${SCRIPT_DIR}/agents/${agent_file}"
done

echo "[✓] Agents imported successfully."
echo ""

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo "============================================================"
echo " All components imported successfully!"
echo ""
echo " To start chatting:"
echo "   orchestrate chat start"
echo ""
echo " Then select: career_counsellor_agent"
echo "============================================================"
echo ""
