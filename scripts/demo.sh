#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "1) Health check"
curl -s "${BASE_URL}/health"
echo
echo

echo "2) Submit monthly declaration"
curl -s -X POST "${BASE_URL}/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "producer_id": "GREENPACK-001",
    "month": "2026-04",
    "declared_quantities_kg": {
      "rigid_plastic": 12000,
      "flexible_plastic": 8500,
      "multilayer_plastic": 3200
    }
  }'
echo
echo

echo "3) Reconciliation summary"
curl -s "${BASE_URL}/summary/GREENPACK-001/2026-04"
echo
echo

echo "4) Ask an EPR question"
curl -s -X POST "${BASE_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What should GreenPack do when a monthly category variance is greater than five percent?"}'
echo
echo

echo "5) Ask an out-of-corpus question"
curl -s -X POST "${BASE_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the corporate tax rate for GreenPack this year?"}'
echo
