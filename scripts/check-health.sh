#!/usr/bin/env bash
set -euo pipefail

curl -s http://localhost:8000/health
echo
curl -s http://localhost:8001/health
echo
curl -s http://localhost:8002/health
echo