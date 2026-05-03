---
name: ecovacs-robot-control-en
description: Control Ecovacs Deebot robot vacuums via the Ecovacs Open Platform AK and a gateway (/robot/skill/*). Use when the user asks to control a Deebot, check battery/status, start/pause/resume/stop cleaning, or send Charge/Clean CloudCtl commands. Requires the user-provided Access Key (AK); does not log in with username/password.
---

# Ecovacs Robot Vacuum Control (Ecovacs)

## What you need to prepare

| You provide | Notes |
|------------|------|
| **AK (Access Key)** | Open the Ecovacs Open Platform in a browser and get the AK from “Service Overview” (**Mainland China**: `https://open.ecovacs.cn/`, **International**: `https://open.ecovacs.com/`). Create/view it on the page and **copy it yourself** to the integrator (env var, config file, or chat). Users do not need to care about baseurl—just use the platform for their region. **Do not** hand over account/password for “login on your behalf”; this skill does **not** obtain tokens for the user. |
| **Gateway base URL** (optional) | Defaults to the Open Platform domain for your region (**CN**: `https://open.ecovacs.cn`, **Intl**: `https://open.ecovacs.com`). If you use a self-hosted/local gateway, set `ECOVACS_PORTAL_URL` to override. |
| **Device nickname fragment** | Used to match a specific robot. Take a substring from `nick` or `name` in “Device List” below (supports fuzzy match). |

If AK is invalid/expired (e.g. errno **3000**): go back to the Open Platform and **check/rotate the AK**, then retry. Do not attempt to “log in for the user” via any open API.

---

## Three-step flow

1. **Configure AK** → 2. **List devices** → 3. **Send commands**

### 1) Configure AK (choose one)

```bash
export ECOVACS_AK="your_ak"
# Or: python3 scripts/ecovacs.py set-ak <ak>
# It writes ~/.ecovacs_session.json (stores only ak; no password)
```

### 2) Device list

```bash
python3 scripts/ecovacs.py devices
```

Note the **nick / name** fragment of the device you want. Use it as `<nick_fragment>` in later commands.

### 3) Common operations (script)

Assume `SCRIPT=scripts/ecovacs.py`.

#### Queries

- Battery: `python3 "$SCRIPT" battery <nick_fragment>`
- Work state (cleaning/charging/station): `python3 "$SCRIPT" status <nick_fragment>`

#### Cleaning

- Start full-house auto clean: `python3 "$SCRIPT" clean <nick_fragment> start`
- Pause / resume / stop: `python3 "$SCRIPT" clean <nick_fragment> pause` or `resume` / `stop`

#### Charging

- Go charge / stop charging: `python3 "$SCRIPT" charge <nick_fragment> go` or `stop`

---

## Call the gateway via HTTP (without Python)

`BASE_URL` follows `ECOVACS_PORTAL_URL` (if unset, defaults to the Open Platform domain for your region).

**Device list**

```bash
curl -sS "${BASE_URL}/robot/skill/deviceList?ak=YOUR_AK"
```

**Control**: `POST /robot/skill/ctl`, JSON includes `ak`, optional `nickName` (fuzzy matches nick/name from the list), and `ctl.cmd` / `ctl.data`.

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"nickname_fragment\",\"ctl\":{\"cmd\":\"Charge\",\"data\":{\"act\":\"go\"}}}"
```

(CloudCtl requires `cmd` to be official fixed case like **`Charge`** / **`Clean`** etc. Do not use `charge`.)

For JSON examples like area cleaning, see [references/api.md](references/api.md).

---

## Errors & enums (for troubleshooting)

Gateway responses are usually two-layered: the **outer layer** has `msg`/`code`; the **inner layer** is CloudCtl nested in `data` as **`ctl.data`**, including **`ret`** (`ok`/`fail`), **`errno`**, and optional **`error`** text.

| Scenario | Meaning / what to do |
|------|----------------|
| Appendix F **5009** | The model **does not support the command or parameter combination** (e.g. wrong cmd casing, protocol/firmware mismatch). Verify model, use names like `GetWorkState`/`GetBatteryInfo`, and check parameters. |
| Appendix F **10004** | Device offline / timeout / powered off / re-paired |
| Appendix F **10000** | Low battery; cannot execute |
| Appendix F **10005** | Robot fault (cliff detected, dustbin missing, etc.) |
| Clean **10006** / Charge **10006** | Internal robot fault (Appendix C/D) |
| Appendix F **4000** | Invalid request body; verify JSON and required fields |
| Appendix F **4504** | Token validation failed; check AK / Open Platform |
| `ret=fail` | Interpret with `errno` and `error` text |

**Water setting constraint**: In **vacuum-only mode** (no mopping / tank not enabled), the robot may **reject water-level settings**. In this case `SetWaterInfo` often fails (`ret=fail`). Switch to a mopping-capable work mode before setting water.

**Common Clean enums**: `act` = `s`/`p`/`r`/`h`; `workMode` 0–3; area cleaning uses **`type=spotarea`** + **`aid`** (from **GetAreaList** `mssid`). **Charge**: `go` / `stopGo`.

For the complete error code table and atype/subType/ftype mappings, see the end of [references/api.md](references/api.md) (“CloudCtl error codes and command enums”).

---

## How to read the docs

| File | Audience | What it contains |
|------|--------|------|
| **This SKILL.md** | Entry point | Required inputs, three steps, common commands, gateway usage |
| [references/api.md](references/api.md) | When you need fields/enums | Gateway routes, request bodies, `cmd`/`data`, common errors/enums, curl examples |
| [references/agent-internal.md](references/agent-internal.md) | Internal implementation reference | Smart cleaning, room/capability probing, subsets parsing, polling & notification templates, `GetWorkState` interpretation, quick error lookup |

**Convention**: For external guidance, prefer “What you need to prepare” and “Common operations” on this page. More complete implementation strategy and state interpretation live in `references/agent-internal.md` and are not expanded by default unless deeper troubleshooting is explicitly requested.
