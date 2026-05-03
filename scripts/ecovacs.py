#!/usr/bin/env python3
"""
Ecovacs Robot Control — 通过 mcp_portal_services 与 AK 控机（不再使用 ITLogin / 账号密码）。

前置：用户在 Ecovacs 开放平台获取 AK 并配置到环境变量或本地文件（国内 https://open.ecovacs.cn/ ，国际 https://open.ecovacs.com/ ）。用户无需关心 baseurl，按所在地区进入对应开放平台即可。

Usage:
  python3 ecovacs.py set-ak <ak>
  python3 ecovacs.py devices
  python3 ecovacs.py clean <nickName> [start|pause|resume|stop]
  python3 ecovacs.py charge <nickName> [go|stop]
  python3 ecovacs.py battery <nickName>
  python3 ecovacs.py status <nickName>

环境变量：
  ECOVACS_AK          开放平台 AK（与 set-ak 二选一）
  ECOVACS_PORTAL_URL  网关根地址，默认 https://open.ecovacs.cn（国际用 https://open.ecovacs.com）

AK 保存在 ~/.ecovacs_session.json（仅 {"ak": "..."}，不含密码）。
"""
import json
import os
import sys
from urllib import parse as urlparse
from urllib import request as urlreq

SESSION_FILE = os.path.expanduser("~/.ecovacs_session.json")


def portal_base():
    # 默认走开放平台域名（按地区）；如使用自建/本地网关可用环境变量覆盖
    return os.environ.get("ECOVACS_PORTAL_URL", "https://open.ecovacs.cn").rstrip("/")


def load_ak():
    ak = os.environ.get("ECOVACS_AK", "").strip()
    if ak:
        return ak
    if os.path.exists(SESSION_FILE):
        try:
            session = json.load(open(SESSION_FILE, encoding="utf-8"))
            ak = (session.get("ak") or "").strip()
            if ak:
                return ak
        except Exception:
            pass
    raise SystemExit(
        "未配置 AK。请设置环境变量 ECOVACS_AK，或执行：python3 ecovacs.py set-ak <ak>\n"
        "AK 须在浏览器打开开放平台获取（国内 https://open.ecovacs.cn/ ，国际 https://open.ecovacs.com/ ）"
    )


def save_ak(ak):
    path = SESSION_FILE
    data = {"ak": ak.strip()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ 已保存 AK 到 {path}")


def http_get_json(url):
    req = urlreq.Request(url, headers={"Accept": "application/json"})
    with urlreq.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url, body):
    data = json.dumps(body).encode("utf-8")
    req = urlreq.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urlreq.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def skill_device_list(ak):
    q = urlparse.quote(ak, safe="")
    url = f"{portal_base()}/robot/skill/deviceList?ak={q}"
    return http_get_json(url)


def skill_ctl(ak, nick_name, ctl):
    url = f"{portal_base()}/robot/skill/ctl"
    body = {"ak": ak, "ctl": ctl}
    if nick_name:
        body["nickName"] = nick_name
    return http_post_json(url, body)


def ensure_ok(resp, what="请求"):
    if resp.get("code") != 0:
        msg = resp.get("msg", "unknown")
        raise SystemExit(f"{what}失败: {msg} | {json.dumps(resp, ensure_ascii=False)}")


def unwrap_ctl_inner_data(resp):
    """从 /robot/skill/ctl 成功响应中取出 cloudctl 内层 data（兼容多种嵌套）。"""
    ensure_ok(resp)
    root = resp.get("data")
    if not isinstance(root, dict):
        return {}
    for path in (
        lambda d: d.get("data", {}).get("ctl", {}).get("data"),
        lambda d: d.get("ctl", {}).get("data"),
        lambda d: d.get("data", {}).get("data"),
        lambda d: d.get("resp", {}).get("body", {}).get("data"),
    ):
        try:
            inner = path(root)
            if isinstance(inner, dict):
                return inner
        except Exception:
            continue
    return root if root else {}


def print_devices(resp):
    ensure_ok(resp, "设备列表")
    rows = resp.get("data")
    if not isinstance(rows, list):
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        return
    print(f"{'#':<4} {'Name':<28} {'Nick':<22} {'Status':<8}")
    print("-" * 90)
    for i, d in enumerate(rows):
        if not isinstance(d, dict):
            continue
        name = str(d.get("deviceName", "") or "")[:28]
        nick = str(d.get("nick", "") or "")[:22]
        st = d.get("status")
        st_s = "online" if st == 1 else ("offline" if st == 0 else str(st))
        print(f"{i:<4} {name:<28} {nick:<22} {st_s:<8}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd == "set-ak":
        if len(args) < 2:
            print("用法: python3 ecovacs.py set-ak <ak>")
            sys.exit(1)
        save_ak(args[1])
        sys.exit(0)

    ak = load_ak()

    if cmd == "devices":
        r = skill_device_list(ak)
        print_devices(r)
        sys.exit(0)

    if cmd == "battery":
        if len(args) < 2:
            print("用法: python3 ecovacs.py battery <nickName>")
            sys.exit(1)
        nick = args[1]
        out = skill_ctl(ak, nick, {"cmd": "GetBatteryInfo", "data": {}})
        data = unwrap_ctl_inner_data(out)
        val = data.get("value")
        if val is None and "power" in data:
            val = data.get("power")
        low = data.get("isLow")
        print(f"🔋 Battery: {val}% {'(low)' if low else ''}")
        sys.exit(0)

    if cmd == "status":
        if len(args) < 2:
            print("用法: python3 ecovacs.py status <nickName>")
            sys.exit(1)
        nick = args[1]
        out = skill_ctl(ak, nick, {"cmd": "GetWorkState", "data": {}})
        data = unwrap_ctl_inner_data(out)
        if data.get("ret") == "fail":
            print(f"❌ GetWorkState: errno={data.get('errno')} {data.get('error', '')}")
            sys.exit(1)
        rs = data.get("robotState") or {}
        ss = data.get("stationState") or {}
        if rs:
            paused = data.get("paused", 0)
            state = rs.get("state", "unknown")
            trigger = rs.get("trigger", "")
            paused_str = " [PAUSED]" if paused else ""
            print(f"🤖 robot: {state}{paused_str} | trigger: {trigger}")
            cs = rs.get("cleanState")
            if cs:
                print(f"   cleanType: {cs.get('type')} | cid: {cs.get('cid')}")
            print(f"🏠 station: {ss.get('state', 'idle')}")
        else:
            # 部分机型返回简写字段（非嵌套 robotState）
            a = data.get("cleanSt")
            b = data.get("chargeSt")
            c = data.get("stationSt")
            if a is not None or b is not None or c is not None:
                print(f"🤖 cleanSt={a} | chargeSt={b} | stationSt={c}")
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))
        sys.exit(0)

    if cmd == "clean":
        if len(args) < 2:
            print("用法: python3 ecovacs.py clean <nickName> [start|pause|resume|stop]")
            sys.exit(1)
        nick = args[1]
        act_key = args[2] if len(args) > 2 else "start"
        act_map = {"start": "s", "pause": "p", "resume": "r", "stop": "h"}
        act = act_map.get(act_key)
        if act is None:
            raise SystemExit("act 须为 start|pause|resume|stop")
        # CloudCtl Clean：按协议最小化字段
        # - act!=s 时，不携带 type/workMode/aid 等
        # - act=s 时，默认 auto + workMode
        if act != "s":
            data = {"act": act}
        else:
            data = {"act": "s", "type": "auto", "workMode": 0}
        out = skill_ctl(ak, nick, {"cmd": "Clean", "data": data})
        data = unwrap_ctl_inner_data(out)
        code = data.get("code")
        if code is None:
            code = data.get("errno")
        print(f"{'✅' if code == 0 else '❌'} Clean act={act} | code={code}")
        sys.exit(0)

    if cmd == "charge":
        if len(args) < 2:
            print("用法: python3 ecovacs.py charge <nickName> [go|stop]")
            sys.exit(1)
        nick = args[1]
        act_key = args[2] if len(args) > 2 else "go"
        act_map = {"go": "go", "stop": "stopGo"}
        act = act_map.get(act_key)
        if act is None:
            raise SystemExit("act 须为 go|stop")
        out = skill_ctl(ak, nick, {"cmd": "Charge", "data": {"act": act}})
        data = unwrap_ctl_inner_data(out)
        code = data.get("code")
        if code is None:
            code = data.get("errno")
        print(f"{'✅' if code == 0 else '❌'} Charge act={act} | code={code}")
        sys.exit(0)

    print(f"Unknown command: {cmd}")
    print(__doc__)
    sys.exit(1)
