# Deebot Control User Guide

This document is for **end users** and explains how to control an Ecovacs robot vacuum (Deebot) through a gateway. It does not provide “arbitrary cmd passthrough”; it only documents a fixed set of capability commands and how to use them.

---

## What you need to prepare

- **AK (Access Key)**: Get it from “Service Overview” on the Ecovacs Open Platform and provide it yourself (**Mainland China**: `https://open.ecovacs.cn/`, **International**: `https://open.ecovacs.com/`). Users do not need to care about baseurl—just use the platform for their region.
- **Gateway base URL**: By default it is the Open Platform domain (**CN**: `https://open.ecovacs.cn`, **Intl**: `https://open.ecovacs.com`), referenced as `BASE_URL` below. If you use a self-hosted/local gateway, override it yourself.
- **Device nickname fragment**: A string to match the device (from `nick` / `name` in the device list).

Optional environment variables:

```bash
export ECOVACS_AK="your_ak"
# If using a self-hosted/local gateway, override:
# export ECOVACS_PORTAL_URL="http://127.0.0.1:3000"
```

---

## Entry 1: Use the script (recommended)

Script path: `scripts/ecovacs.py`

### Devices & queries

- **Device list**:

```bash
python3 scripts/ecovacs.py devices
```

- **Battery (GetBatteryInfo)**:

```bash
python3 scripts/ecovacs.py battery "<nick_fragment>"
```

- **Work state (GetWorkState)**:

```bash
python3 scripts/ecovacs.py status "<nick_fragment>"
```

### Cleaning (Clean)

- **Start full-house auto cleaning**:

```bash
python3 scripts/ecovacs.py clean "<nick_fragment>" start
```

- **Pause / resume / stop**:

```bash
python3 scripts/ecovacs.py clean "<nick_fragment>" pause
python3 scripts/ecovacs.py clean "<nick_fragment>" resume
python3 scripts/ecovacs.py clean "<nick_fragment>" stop
```

### Charging (Charge)

```bash
python3 scripts/ecovacs.py charge "<nick_fragment>" go
python3 scripts/ecovacs.py charge "<nick_fragment>" stop   # actually sends act=stopGo
```

---

## Entry 2: Call the gateway via HTTP (without Python)

Convention:

```bash
export BASE_URL="https://open.ecovacs.cn"   # CN example; use https://open.ecovacs.com for Intl
export AK="your_ak"
export NICK="nick_fragment"
```

### Devices

- **Device list (redacted)**:

```bash
curl -sS "${BASE_URL}/robot/skill/deviceList?ak=${AK}"
```

### Queries (read-only)

- **Battery (GetBatteryInfo)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetBatteryInfo\",\"data\":{}}}"
```

- **Work state (GetWorkState)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetWorkState\",\"data\":{}}}"
```

- **Water level query (GetWaterInfo)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetWaterInfo\",\"data\":{}}}"
```

- **Suction query (GetSpeed)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetSpeed\",\"data\":{}}}"
```

- **Current-clean stats (GetStats)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetStats\",\"data\":{}}}"
```

### Cleaning (Clean)

- **Start full-house auto cleaning**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"Clean\",\"data\":{\"act\":\"s\",\"type\":\"auto\",\"workMode\":0}}}"
```

- **Pause / resume / stop** (minimal fields per ROP protocol):

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"Clean\",\"data\":{\"act\":\"p\"}}}"

curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"Clean\",\"data\":{\"act\":\"r\"}}}"

curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"Clean\",\"data\":{\"act\":\"h\"}}}"
```

- **Area cleaning (GetAreaList + Clean spotarea)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"GetAreaList\",\"data\":{}}}"

curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"Clean\",\"data\":{\"act\":\"s\",\"type\":\"spotarea\",\"workMode\":0,\"aid\":[\"<mssid1>\",\"<mssid2>\"]}}}"
```

### Charging (Charge)

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"Charge\",\"data\":{\"act\":\"go\"}}}"

curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"Charge\",\"data\":{\"act\":\"stopGo\"}}}"
```

### Settings (common)

- **Set suction (SetSpeed)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"SetSpeed\",\"data\":{\"speed\":\"standard\"}}}"
```

- **Set water level (SetWaterInfo)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"SetWaterInfo\",\"data\":{\"gear\":\"medium\"}}}"
```

Constraint: **vacuum-only mode usually does not allow setting water level**. If `SetWaterInfo` returns `ret=fail`, switch to a mopping-capable work mode and try again.

- **Set volume (SetVolume)** (if supported by your model):

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"SetVolume\",\"data\":{\"volume\":2}}}"
```

### Station capabilities (if supported)

- **Auto-empty (StationEmpty)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"StationEmpty\",\"data\":{\"act\":\"start\"}}}"
```

- **Drying (StationDry)**:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"${NICK}\",\"ctl\":{\"cmd\":\"StationDry\",\"data\":{\"act\":\"start\"}}}"
```

---

## Responses & troubleshooting (generic)

Gateway responses are typically two-layered:

- **Outer layer**: `code` / `msg`
- **Inner layer** (CloudCtl): `ret` (`ok/fail`) + `errno` + optional `error`

Common meanings:

- `errno=5009`: model does not support the command/params (or wrong name/casing)
- `errno=4000`: request body/field error
- `errno=10004`: device offline/timeout
- `errno=10006`: internal fault / capability unavailable
