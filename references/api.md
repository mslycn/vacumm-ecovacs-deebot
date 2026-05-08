# Ecovacs Robot Control API Reference

**Entry point**: For quick start, see [SKILL.md](../SKILL.md) in the parent directory. This document is for looking up gateway request bodies, fields, and enums. For more complete implementation strategy and state interpretation logic, see [agent-internal.md](agent-internal.md) (internal reference).

## Step 1.Authentication (AK)

**The Access Key (AK) must be created/viewed by the user on the Ecovacs Open Platform “Service Overview” page, and provided by the user to the integrator (CN `https://open.ecovacs.cn/`, Intl `https://open.ecovacs.com/`). Users do not need to care about baseurl—just use the platform for their region.**

This skill package no longer uses username/password or client-side login (e.g. ITLogin) to obtain tokens. The AK is parsed by a gateway (e.g. `mcp_portal_services`), and the server handles cloud authentication and forwarding. External docs do **not** include vendor-internal domains or login payloads.

---

## Step 2.Gateway integration (recommended)

Let `BASE_URL` be the gateway deployment root. 

- By default it matches the Open Platform domain (CN `https://open.ecovacs.cn`, Intl `https://open.ecovacs.com`). 

- If you use a self-hosted/local gateway, override with the `ECOVACS_PORTAL_URL` environment variable.

### Step 2.1 Device list (GET, redacted externally)

Recommended **GET**:

```bash
curl -sS "${BASE_URL}/robot/skill/deviceList?ak=YOUR_AK"
```

Example response:

```json
{
  "msg": "OK",
  "code": 0,
  "data": [
    { "nick": "T90pro201", "name": "..." }
  ]
}
```

Each entry in `data` does **not** include `did`, `class`, or `resource` (the gateway fills these for control requests based on `nickName`).

You can also `POST ${BASE_URL}/robot/skill/deviceList` with `Content-Type: application/json` and body `{"ak":"<AK>"}`. Semantics are the same as GET.

### Step 2.2  Control (CloudCtl)

- `POST ${BASE_URL}/robot/skill/ctl`
- `Content-Type: application/json`

```json
{
  "ak": "<AK>",
  "nickName": "<string used to fuzzy match nick or name>",
  "ctl": {
    "cmd": "<capability command name>",
    "data": { }
  }
}
```

If `nickName` is provided, the server matches a device and fills the cloud-control parameters before sending. In the “Protocol quick reference” below, `cmdName` / `body.data` correspond to `ctl.cmd` / `ctl.data`.

#### Send examples (curl)

```bash
export BASE_URL="https://open.ecovacs.cn"   # CN example; use https://open.ecovacs.com for Intl
export AK="YOUR_AK"
```

Area cleaning (`Clean` + `type=spotarea`; `nickName` is a nickname or name fragment):

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"device nick or name fragment\",\"ctl\":{\"cmd\":\"Clean\",\"data\":{\"act\":\"s\",\"type\":\"spotarea\",\"workMode\":0,\"aid\":[\"<mssid1>\",\"<mssid2>\"]}}}"
```

Go charge:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"Deebot\",\"ctl\":{\"cmd\":\"Charge\",\"data\":{\"act\":\"go\"}}}"
```

Stop charging:

```bash
curl -sS -X POST "${BASE_URL}/robot/skill/ctl" -H 'Content-Type: application/json' \
  -d "{\"ak\":\"${AK}\",\"nickName\":\"Deebot\",\"ctl\":{\"cmd\":\"Charge\",\"data\":{\"act\":\"stopGo\"}}}"
```

---

## External API boundaries (no cloud URL / login payload)

Device discovery and control must go through the **gateway** endpoints above (`/robot/skill/deviceList`, `/robot/skill/ctl`). Vendor-internal hostnames and app-layer login / direct-to-device APIs are **not** expanded in external docs. The local script `scripts/ecovacs.py` only calls the gateway and does not build internal addresses on the client.

### Device list (external request/response semantics)

| Item | Notes |
|------|------|
| Request | `GET ${BASE_URL}/robot/skill/deviceList?ak=<AK>`; or `POST` same path with `Content-Type: application/json`, body `{"ak":"<AK>"}` |
| Success `data[]` | Each entry is a redacted device object; common fields include `nick`, `name`, `deviceName`, `status` (meaning aligns with the cloud list; e.g. `1`≈online, `0`≈offline, depending on gateway implementation) |
| Not included | `did`, `class`, `resource`, etc. (filled by the gateway on control requests using `ak` + `nickName`) |

### Control (external request/response semantics)

| Item | Notes |
|------|------|
| Request | `POST ${BASE_URL}/robot/skill/ctl` with body `ak`, optional `nickName`, and `ctl` (`cmd` + `data`), see JSON/curl above |
| Success response | Outer `msg` / `code`; business result uses the same **`data` shape** as in the “Protocol quick reference” below (field names and enum values follow the same protocol) |

---

## Core protocol reference (by capability)

**The gateway `/robot/skill/ctl` uses CloudCtl** (with `cmd` / `data` inside `data.ctl`). For cleaning/charging you must use **`Clean`** and **`Charge`** (fixed casing), **not** lowercase `charge`.

Put the following **`ctl.cmd` / `ctl.data`** into **`POST /robot/skill/ctl`** (add `nickName` when needed). On success, the inner result shape matches CloudCtl responses (e.g. `ret` / `errno`).

### CloudCtl: `Clean`

| `data.act` | Meaning |
|------------|---------|
| `s` | start cleaning (combine with `type`, `workMode`, etc.; see vendor Appendix C) |
| `p` | pause |
| `r` | resume |
| `h` | stop (after stop you cannot resume; see vendor docs) |

Area cleaning: set `act=s` and **`type=spotarea`**, and provide `aid` as an array of area IDs. Area IDs come from **`GetAreaList`** `list[].mssid` (see vendor Appendix E). Vendor doc type name is **`spotarea`** (lowercase). If your model returns `unknown type`, try the variant that matches your firmware’s expectations.

### CloudCtl: `Charge`

| `data.act` | Meaning |
|------------|---------|
| `go` | start charging |
| `stopGo` | stop charging |

```json
{ "cmd": "Charge", "data": { "act": "go" } }
```

---

### GetBatteryInfo

| cmd | body.data |
|-----|-----------|
| `GetBatteryInfo` | `{}` |
| `onBattery` (report) | `{ value: 0-100, isLow: 0/1 }` |

On success, the inner `ctl.data` can be `{ ret, value, isLow }`. Some models return **`{ ret, power }`** where `power` is the battery percentage.

---

### Clean state — `GetWorkState` (replaces deprecated `getCleanInfo_V2`)

When calling through the gateway/CloudCtl, use **`GetWorkState`** (PascalCase). Lowercase `getWorkState` returns `errno=5009` on some models.

(For work state queries, prefer the script `status` command, or call the fixed capability command via `POST /robot/skill/ctl` as above.)

Response `data`:

```json
{
  "paused": 0,
  "robotState": {
    "state": "idle | mapping | cleaning | moving | video",
    "trigger": "app | voice | button | kick | schedule | batteryLow | alert | workComplete | breakPoint",
    "cleanState": {
      "cid": 123456,
      "type": "auto | freeClean | qcClean | entrust | spotClean | comeClean | smartClean | sprayClean | mapping",
      "entrust": 0
    }
  },
  "stationState": {
    "state": "idle | goCharging | emptying | goEmptying | washing | goWashing | spinDrying | drying | goDrying | selfCleaning | goSelfCleaning | dewatering",
    "trigger": "app | voice | button | breakPoint"
  }
}
```

**robotState.state meanings**

- `idle` → idle
- `cleaning` → cleaning task exists (check `paused` for paused vs running)
- `mapping` → mapping
- `moving` → remote control
- `video` → video task

⚠️ `cleaning` + `paused=1` means paused, not completed.

**Triggers (useful for completion interpretation)**

| trigger | Meaning | Conclusion |
|---------|---------|------------|
| `workComplete` | task completed normally | ✅ completed |
| `breakPoint` | breakpoint resume | ⏳ continuing |
| `batteryLow` | low-battery return | ⚠️ interrupted |
| `alert` | stopped due to alert | ❌ error |
| `app` | triggered/stopped by app | depends on state |
| `button` | physical button | depends on state |
| `kick` | collision trigger | depends on state |
| `voice` | voice trigger | depends on state |
| `schedule` | schedule trigger | depends on state |

**stationState.state meanings**

`emptying`=emptying dust, `goEmptying`=going to empty, `washing`=mop washing, `goWashing`=going to wash, `drying`=drying, `goDrying`=going to dry, `selfCleaning`=self cleaning, `goCharging`=charging, `dewatering`=dewatering

---

### Stats (`GetStats` / `onStats`)

Response `data`:

```json
{ "cid": "...", "area": 10, "time": 600, "type": "auto", "avoidCount": 3, "aiopen": 1 }
```

- `area`: square meters
- `time`: seconds

---

### Speed (suction)

```json
// get: {}
// set: { "speed": 0 }
```

Values: `1000`=mute, `0`=standard, `1`=strong, `2`=super-strong

---

### WaterInfo (water level)

```json
// get: {}
// set: { "amount": 2 }
```

Values: `1`=low, `2`=medium, `3`=high, `4`=max
`enable`: 1=mop mode, 0=vacuum-only

Constraint: vacuum-only mode usually rejects water settings. Per ROP protocol, `SetWaterInfo` uses `gear` (`low|medium|large|superLarge`) rather than numeric `amount`.

---

### WorkMode (vacuum/mop mode)

```json
// get: {}
// set: { "mode": 0 }
```

Values: `0`=vacuum+mop, `1`=vacuum-only, `2`=mop-only, `3`=vacuum then mop

Per ROP protocol:

- `GetWorkMode`: `{"cmd":"GetWorkMode","data":{"noVoiceResp":1}}`
- `SetWorkMode`: `{"cmd":"SetWorkMode","data":{"noVoiceResp":1,"mode":0}}`

---

### LifeSpan (consumables)

```json
// get (ROP): { "type": ["brush","sideBrush","heap","filter"], "noVoiceResp": 1 }
```

Returns array: `[ { "type": "brush", "left": 80, "total": 100 } ]`

Types: `brush` main brush, `sideBrush` side brush, `heap` dust filter, `filter` air filter, `roundMop` mop, `wbHeap` water tank filter

---

### AutoEmpty (3D dust collection)

```json
// get: {}
// start: { "act": "start" }
// set auto: { "enable": 1, "frequency": "auto|standard|smart|10|15|25" }
```

Status: `0`=off, `1`=emptying, `2`=done, `3`=lid open, `4`=bag not installed, `5`=bag full

---

### CachedMapInfo (map list)

```json
// get: {}
```

Returns: `[ { "mid": "...", "index": 0, "name": "...", "status": 0, "using": 1 } ]`

---

### MapSet / MapSet_V2 (area info)

```json
// get: { "mid": "<map_id>", "type": "ar" }
```

Returns subsets (rooms): `[ { "mssid": "...", "name": "Living room", "subtype": 1 } ]`

subtype: `0` unspecified, `1` living room, `2` dining room, `3` bedroom, `4` study, `5` kitchen, `6` bathroom

---

### Sched_V2 (schedule)

```json
// get: { "type": 1 }
// add:
{
  "act": "add", "enable": 1,
  "sid": "1", "repeat": "0000000",
  "hour": 8, "minute": 0,
  "mid": "<map_id>",
  "content": {
    "name": "clean",
    "jsonStr": "{\"router\":\"plan\",\"content\":{\"type\":\"auto\",\"value\":\"\"}}"
  }
}
// delete: { "act": "del", "sid": "1", "mid": "<map_id>" }
```

`repeat`: 7 chars (Sun→Sat), `1`=scheduled, `0000000`=one-time

---

### Error codes (`onError`)

Common: `0`=completed, `102`=stuck, `103`=cliff, `104`=low battery, `110`=dustbin missing

---

### Event codes (`onEvt`)

Common: `1`=start, `2`=pause, `3`=stop, `1025`=low-battery charging, `1099`=emptying complete

---

## CloudCtl error codes and command enums (protocol excerpt)

Used for interpreting gateway/cloud responses. Outer layer is usually gateway `code`/`msg`. Business result is in **`data` → … → `ctl.data`**, containing **`ret`** (`ok`/`fail`), **`errno`**, and optional **`error`** text. The following aligns with vendor Appendices C/D/E/F.

### Common cloud error codes (Appendix F)

| Code | Meaning |
|--------|------|
| 4000 | invalid request body |
| 4500 | internal server error |
| 4501 | invalid appid |
| 4504 | token validation failed |
| 4508 | request `ts` differs from server time by ~2 minutes, or invalid `sig` |
| 4509 | appid deleted |
| 4511 | appid not configured for this model |
| 4512 | appid not configured for this model’s command |
| 5009 | **server does not support this model’s command** (wrong cmd casing/protocol mismatch/unsupported capability) |
| 10000 | low battery; cannot execute |
| 10004 | device offline/timeout/powered off/re-paired |
| 10005 | device fault (cliff, dustbin missing, etc.) |

### Clean errno in responses (Appendix C)

May appear on failures (can coexist with Appendix F codes; interpret based on actual response):

| errno | Meaning |
|--------|------------------|
| 10000 | low battery |
| 10005 | device fault (breakdown) |
| 10006 | internal device fault |

### Charge errno in responses (Appendix D)

| errno | Meaning |
|--------|------|
| 10006 | internal device fault |

### Clean: common fields & enums (Appendix C)

| Field | Meaning |
|------|------|
| `act` | `s` start · `p` pause · `r` resume · `h` stop (after stop you **cannot** resume) |
| `workMode` | `0` vacuum+mop · `1` vacuum-only · `2` mop-only · `3` vacuum then mop |
| `type` (common when `act=s`) | `auto` full-house · **`spotarea`** area · `spot` near-robot spot · `combination` combo · `border` edge · `voiceBorder` voice edge, etc. |
| `aid` | array of area IDs; required for `type=spotarea`; IDs come from **`GetAreaList`** `list[].mssid` |
| `atype` | used for `type=combination`; room type enum see “room atype” below |
| `tri` | trigger source such as `btn`, `val`, `app` (doc examples `btn\|val\|app`) |

**Room atype (Appendix C; similar category to GetAreaList `subType`)**: `1` living room · `2` dining room · `3` bedroom · `4` study · `5` kitchen · `6` bathroom · `7` laundry · `8` living room (rest) · `9` storage · `10` kids room · `11` sunroom · `12` corridor · `13` balcony · `14` gym · `15` cloakroom · `16` my place · `17` in place

**Furniture ftype (Appendix C; for combination)**: `2000` sofa · `2001` dining table · `2002` coffee table · `2003` TV stand · `2004` bed · `2005` trash bin · `2006` carpet · `2007` sideboard · `2008` cabinet · `2009` shoe cabinet · `2010` nightstand · `2011` fridge · `2012` pet house · `2013` washing machine · `2014` plant · `2015` bookshelf · `2021` area cleaning

### Charge: `data.act` (Appendix D)

| `act` | Meaning |
|--------|------|
| `go` | start charging |
| `stopGo` | stop charging |

### GetAreaList: response `list[]` (Appendix E)

| Field | Meaning |
|------|------|
| `mssid` | unique area ID used for Clean `spotarea` `aid` |
| `name` | area name (may be empty) |
| `subType` | area type: `0` unspecified · `1`–`6` living room→bathroom · `7`–`14` laundry→gym, etc. (aligns with Appendix E table) |

### Inner result `ret` (Appendix C/D/E)

| `ret` | Meaning |
|--------|------|
| `ok` | command succeeded |
| `fail` | failed; interpret with `errno` / `error` |
