# Internal Implementation Reference (do not expand externally by default)

For automation/script integration: smart cleaning, room/area cleaning, async polling, notifications, and status parsing. Users only need AK, gateway, and nickname; this document is **implementation detail**.

When controlling via the gateway, prefer CloudCtl **`Clean` / `Charge`** (`act` is `s`/`p`/`r`/`h`; area cleaning uses `type=spotarea` + `aid`; “stop charging” uses `stopGo`). See [api.md](api.md) “CloudCtl: `Clean` / `Charge`”.

---

## Execution strategy overview

```
Environment sensing: use smart-clean logic to infer environment params, set work parameters
Room/area: get area mssid via GetAreaList, then send Clean(type=spotarea, aid=[...])
Notifications: after cleaning completes, notify the user via scheduled task (e.g. Feishu)
Capability cache: cache successfully resolved clean types to did; reuse on subsequent runs
```

---

## Area cleaning (GetAreaList + Clean)

Goal: implement “clean by area/room” using only commands covered by `product_design_rop`.

```bash
# 1) Get area list (returns list[].mssid)
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"device nick or name fragment\",\"ctl\":{\"cmd\":\"GetAreaList\",\"data\":{}}}"

# 2) Area cleaning: Clean(type=spotarea) + aid=[mssid...]
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"device nick or name fragment\",\"ctl\":{\"cmd\":\"Clean\",\"data\":{\"act\":\"s\",\"type\":\"spotarea\",\"workMode\":0,\"aid\":[\"<mssid1>\",\"<mssid2>\"]}}}"
```
Samples

```
AK="FOcadaKSxfWGsZ65bsDeGl"
NAME="DEEBOTX5PRO"

curl -sS -X POST "https://open.ecovacs.cn/robot/skill/ctl" \
  -H "Content-Type: application/json" \
  -d "{\"ak\":\"$AK\",\"nickName\":\"$NAME\",\"ctl\":{\"cmd\":\"GetAreaList\",\"data\":{}}}" \
  | python -m json.tool
```

---

## Protocol quick reference (ctl.cmd / ctl.data)

| Goal | cmd | data notes |
|------|-----|-----------|
| Full-house auto (CloudCtl, recommended) | `Clean` | `act:"s"` + `type:"auto"` + `workMode` etc. (see api.md) |
| Area/room cleaning (CloudCtl, recommended) | `Clean` | `act:"s"` + `type:"spotarea"` + `aid` (from GetAreaList `mssid`) |
| Pause/resume/stop (CloudCtl) | `Clean` | `act:"p"` / `"r"` / `"h"` |
| Charge / stop charging (CloudCtl) | `Charge` | `act:"go"` / `"stopGo"` |
| Battery | `GetBatteryInfo` | `{}` |
| Work state | `GetWorkState` | `{}` (**do not use deprecated `getCleanInfo_V2`**; do not use lowercase `getWorkState`—some models return 5009) |
| Current-clean stats | `GetStats` | `{}` |
| Suction | `GetSpeed` / `SetSpeed` | `SetSpeed`: `{speed:"mute|standard|strong|superStrong"}` (per protocol) |
| Water level | `GetWaterInfo` / `SetWaterInfo` | `SetWaterInfo`: `{gear:"low|medium|large|superLarge"}`; vacuum-only mode usually rejects water settings |
| Vacuum/mop mode | `GetWorkMode` / `SetWorkMode` | `GetWorkMode`: `{noVoiceResp:1}`; `SetWorkMode`: `{noVoiceResp:1,mode:0}` (0 = vacuum+mop, etc.) |
| Consumables | `getLifeSpan` | `{type:"brush,sideBrush,heap,filter"}` |
| Consumables | `GetLifeSpan` | `{type:["brush","sideBrush","heap","filter"],noVoiceResp:1}` (omit `type` to get all) |
| Manual emptying | `StationEmpty` | `{act:"start"}` |

For full fields and enums, see [api.md](api.md).

---

## `GetWorkState` state machine

(For state queries, reuse the script `status`, or call `GetWorkState` via `POST /robot/skill/ctl`.)

Response structure is documented in [api.md](api.md) “Clean state — GetWorkState”. Some models return nested `robotState`; others return abbreviated fields like `cleanSt` / `chargeSt`.

**robotState.state**

- `idle` → idle
- `cleaning` → cleaning task exists (including paused; check `paused`)
- `mapping` → mapping
- `moving` → remote control
- `video` → video task

⚠️ `cleaning` + `paused=1` means paused, **not completed**.

**trigger (completion interpretation)**

| trigger | Meaning | Conclusion |
|---------|------|------|
| `workComplete` | completed normally | ✅ completed |
| `breakPoint` | breakpoint resume | ⏳ continuing |
| `batteryLow` | low-battery return | ⚠️ interrupted |
| `alert` | stopped due to alert | ❌ error |
| `app` / `button` etc. | interpret with state | follow your product logic |

**stationState**: `emptying` emptying dust, `washing` mop washing, `drying` drying, `goCharging` charging, etc.

---

## Smart cleaning (weather + time window example: Suzhou)

**Humidity → water gear (SetWaterInfo.gear)**

- ≥75%: `gear:"low"`
- 45–74%: `gear:"medium"`
- <45%: `gear:"large"`

**Time window → suction (example rule)**

- Quiet hours (e.g. 12:30–14:00, 22:00–08:00): `speed:1000` or `0`
- Daytime: `speed:1` or `2`

Order: first ensure the robot is in a mopping-capable mode (not vacuum-only), then `SetWaterInfo(gear=...)`, then `SetSpeed`, then `Clean act=s` (e.g. `type=auto`). Default behavior can follow smart-clean rules.

---

## Charging state (`GetChargeState`)

- `isCharging`: 1=on dock
- `mode`: e.g. `autoEmpty`=emptying, etc.
- `chargeRate` is **power**, not battery percentage; battery must be queried via `GetBatteryInfo`

During charging/emptying, you can still send cleaning commands (if `code=0`, the robot executes when ready).

---

## Async polling & completion notifications (e.g. Feishu)

**When to start**: after a cleaning command (e.g. `Clean act=s`) returns success, **immediately** create a polling job (independent of the robot’s instantaneous state).

### Polling decision (priority)

1. Call `GetWorkState` and read `data.robotState.state` / `trigger` / `data.paused` (if no nesting, read `cleanSt`/`chargeSt`/`stationSt`).
2. `cleaning` and `paused==0` → cleaning; silent.
3. `cleaning` and `paused==1` → paused; silent.
4. `mapping` → mapping; silent.
5. `idle` and `stationState.state != idle` → station task in progress; silent.
6. `idle` and `trigger == workComplete` → ✅ completed; send summary.
7. `idle` and `trigger` is `batteryLow` / `alert` → ⚠️ abnormal end; notify with reason.
8. `idle` and `trigger` is `app` / `button` → can treat as normal end and notify (if consistent with product expectations).
9. `idle` with other triggers (incl. `none`) → not started/initial; silent.

### Completion summary

- `GetStats` → `area` (㎡), `time` (seconds → minutes)
- `battery` (script) / `GetBatteryInfo`
- Send a conversational summary via Feishu etc.; **delete the scheduled job after sending**
- **Anti-stuck**: after ~60 polls (~2 hours) without completion → alert and delete job

Rule: only “completed/abnormal end” branches send messages and delete the job; all other branches remain silent.

---

## Error handling (gateway/business)

### Gateway / ngiot (historical table)

| code | Meaning | Action |
|------|------|------|
| 0 | success | — |
| 3000 | token expired | ask the user to update AK on the Open Platform |
| 3003 | permission denied | check device `class` and `toType` |
| 30000 | device timeout | device offline |
| 20011 + format | invalid value format | adjust `value` per protocol |

### CloudCtl inner layer (official cleaning/charging codes, excerpt)

Parse **`errno`** / **`error`** inside **`ctl.data`** (aligns with Appendices F/C/D; **full table is in [api.md](api.md) “CloudCtl error codes and command enums”**):

| errno | Common meaning |
|--------|----------|
| 4000 | invalid request body |
| 4504 | token validation failed |
| 5009 | **model does not support the command/params** (e.g. lowercase `getWorkState`, wrong cmd name) |
| 10000 | low battery; cannot execute |
| 10004 | offline/timeout/powered off/re-paired |
| 10005 | device fault (dustbin/cliff/etc.) |
| 10006 | internal device fault (Clean/Charge responses) |

**`ret`**: `ok` success, `fail` failure (interpret with `errno`).

---

## Communication boundaries with users

- Do **not** paste the polling pseudocode or full protocol tables in default responses.
- If the user asks “how to control” → point them to SKILL sections “What you need to prepare” and the script commands.
- If the user asks “why it failed” → explain based on the error table and AK/Open Platform guidance.
