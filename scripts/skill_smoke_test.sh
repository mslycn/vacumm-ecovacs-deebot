#!/usr/bin/env bash
# 技能冒烟：验证 mcp_portal_services 网关与 ecovacs.py 行为。
# 用法：
#   export ECOVACS_AK='你的AK'
#   export ECOVACS_PORTAL_URL='http://127.0.0.1:3000'   # 可选
#   export ECOVACS_TEST_NICK='小蓝'                     # 可选，用于 ctl 匹配
#   bash scripts/skill_smoke_test.sh
#
# 仅做只读类请求（设备列表、电量、工作状态）；不自动下发清扫/回充。

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="${ECOVACS_PORTAL_URL:-http://127.0.0.1:3000}"
BASE="${BASE%/}"
PY="${PYTHON:-python3}"

echo "== BASE_URL=$BASE"

echo "== 1) GET /robot/skill/deviceList（无 ak 应失败）"
code=$(curl -sS -o /tmp/_dl.json -w "%{http_code}" "${BASE}/robot/skill/deviceList?ak=" || true)
echo "HTTP $code body: $(head -c 200 /tmp/_dl.json || true)"
echo ""

if [[ -z "${ECOVACS_AK:-}" ]]; then
  echo "未设置 ECOVACS_AK，跳过真实联调。请 export ECOVACS_AK 后重跑本脚本。"
  echo "== $PY scripts/ecovacs.py（无 AK 应报错）"
  _err="$($PY "$ROOT/scripts/ecovacs.py" devices 2>&1 || true)"
  if [[ "$_err" != *ECOVACS_AK* ]]; then
    echo "FAIL: 预期未配置 AK 时的提示"
    exit 1
  fi
  echo "OK（无 AK 提示符合预期）"
  exit 0
fi

AK="$ECOVACS_AK"
NICK="${ECOVACS_TEST_NICK:-小蓝}"

echo "== 2) GET /robot/skill/deviceList?ak=***"
curl -sS "${BASE}/robot/skill/deviceList?ak=${AK}" | $PY -m json.tool | head -60

echo ""
echo "== 3) POST /robot/skill/ctl — GetBatteryInfo（只读）"
curl -sS -X POST "${BASE}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetBatteryInfo\",\"data\":{}}}" | $PY -m json.tool | head -40

echo ""
echo "== 4) POST /robot/skill/ctl — GetWorkState（与脚本 status 一致，只读）"
curl -sS -X POST "${BASE}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetWorkState\",\"data\":{}}}" | $PY -m json.tool | head -40

echo ""
echo "== 5) ecovacs.py devices / battery / status"
export ECOVACS_PORTAL_URL="$BASE"
export ECOVACS_AK="$AK"
$PY "$ROOT/scripts/ecovacs.py" devices | head -40
$PY "$ROOT/scripts/ecovacs.py" battery "$NICK" || true
$PY "$ROOT/scripts/ecovacs.py" status "$NICK" || true

echo ""
echo "OK 冒烟完成（未执行清扫/回充）。"
