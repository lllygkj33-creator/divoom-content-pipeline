#!/usr/bin/env python3
"""进度上报 —— 供各角色 skill 在关键事件边界调用，改这一处即可。

用法（全部相对本脚本自动定位 progress.json）：

  # 本轮启动
  python3 进度看板/上报.py 启动 --标题 "..." --runId "..."

  # 某个关键事件开始 / 结束（--n 是事件序号）
  python3 进度看板/上报.py 事件 --agent "Brief 官" --n 3 --状态 处理中
  python3 进度看板/上报.py 事件 --agent "Brief 官" --n 3 --状态 完成 --备注 "已产出 brief 卡"

  # 某个 agent 整体收工（自动把它所有事件置完成）
  python3 进度看板/上报.py 完成 --agent "Brief 官"

  # 登记阶段性交付文件（可点击查看）
  python3 进度看板/上报.py 产物 --agent "Brief 官" --名 "Brief 卡" \
      --路径 "work/runs/<runId>/00-brief.json" --摘要 "column 科技与信息 · fx F1"

  # 推进阶段 / 回环
  python3 进度看板/上报.py 阶段 --名 "第二轮 · 并行"
  python3 进度看板/上报.py 回环 --轮次 2 --退回给 "编辑" --原因 "硬伤 1 条，七维最低 6.5"
  python3 进度看板/上报.py 角度 --agent "编辑" --轮次 2

  # 收尾
  python3 进度看板/上报.py 结束 --状态 完成
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
PROGRESS = ROOT / "progress.json"

# 阶段 → 总进度（粗略刻度，用于进度条；关键事件级进度按各 agent 事件完成率另算）
STAGE_PROGRESS = {
    "待启动": 0.0,
    "第一轮 · 并行": 0.05,
    "门禁 1 · 标题大纲": 0.30,
    "第二轮 · 并行": 0.40,
    "门禁 2 · 审核": 0.80,
    "交付": 0.92,
    "已完成": 1.0,
}


def now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def load() -> dict:
    try:
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        sys.exit("上报.py: 读不到 progress.json")


def save(d: dict) -> None:
    recompute(d)
    PROGRESS.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def recompute(d: dict) -> None:
    """总进度 = 阶段基准 + 该阶段内 agents 的关键事件完成率。"""
    agents = d.get("agents", [])
    total = sum(len(a.get("事件") or []) for a in agents) or 1
    done = sum(1 for a in agents for e in (a.get("事件") or []) if e.get("状态") == "完成")
    base = STAGE_PROGRESS.get(str(d.get("阶段") or ""), 0.0)
    ceiling = STAGE_PROGRESS.get("已完成", 1.0)
    # 阶段基准 + 阶段内完成度（不超过下一阶段基准的粗略上限）
    d["总进度"] = round(min(1.0, base + (1 - base) * (done / total) * 0.9), 4)
    cur = d.get("当前") or {}
    running = next((a for a in agents if a.get("状态") == "处理中"), None)
    if running:
        ev = next((e for e in running.get("事件") or [] if e.get("状态") == "处理中"), None)
        if ev:
            d["当前"] = {"agent": running["id"], "事件": ev["n"], "说明": ev["名"]}
    if not running and d.get("阶段") == "已完成":
        d["总进度"] = 1.0


def find_agent(d: dict, name: str) -> dict:
    for a in d.get("agents", []):
        if a.get("id") == name:
            return a
    sys.exit(f"上报.py: 没有这个 agent：{name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("启动")
    p.add_argument("--标题", required=True)
    p.add_argument("--runId", required=True)

    p = sub.add_parser("事件")
    p.add_argument("--agent", required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--状态", required=True, choices=["待命", "处理中", "完成", "失败"])
    p.add_argument("--备注", default="")

    p = sub.add_parser("完成")
    p.add_argument("--agent", required=True)

    p = sub.add_parser("产物")
    p.add_argument("--agent", required=True)
    p.add_argument("--名", required=True)
    p.add_argument("--路径", required=True)
    p.add_argument("--摘要", default="")

    p = sub.add_parser("阶段")
    p.add_argument("--名", required=True)

    p = sub.add_parser("回环")
    p.add_argument("--轮次", type=int, required=True)
    p.add_argument("--退回给", required=True)
    p.add_argument("--原因", default="")

    p = sub.add_parser("角度")  # 给某个 agent 打轮次徽章
    p.add_argument("--agent", required=True)
    p.add_argument("--轮次", type=int, required=True)

    p = sub.add_parser("结束")
    p.add_argument("--状态", default="完成")

    a = ap.parse_args()
    d = load()
    ts = now()

    if a.cmd == "启动":
        d["runId"] = a.runId
        d["标题"] = a.标题
        d["开始时间"] = ts
        d["结束时间"] = None
        d["阶段"] = "第一轮 · 并行"
        d["回环"] = {"轮次": 1, "最大轮次": 2, "退回给": "", "原因": ""}
        for ag in d.get("agents", []):
            ag["状态"] = "待补充" if ag.get("占位") else "待命"
            ag["开始"] = ag["结束"] = None
            for e in ag.get("事件") or []:
                e["状态"] = "待命"
                e["时间"] = None
                e["备注"] = ""
            ag["产物"] = []
        fa = find_agent(d, "父代理")
        fa["状态"] = "完成"
        fa["开始"] = fa["结束"] = ts
        if fa.get("事件"):
            fa["事件"][0]["状态"] = "完成"
            fa["事件"][0]["时间"] = ts

    elif a.cmd == "事件":
        ag = find_agent(d, a.agent)
        ev = next((e for e in ag.get("事件") or [] if e.get("n") == a.n), None)
        if ev is None:
            sys.exit(f"上报.py: {a.agent} 没有第 {a.n} 个事件")
        ev["状态"] = a.状态
        ev["时间"] = ts if a.状态 != "待命" else None
        if a.备注:
            ev["备注"] = a.备注
        if a.状态 == "处理中":
            ag["状态"] = "处理中"
            if not ag.get("开始"):
                ag["开始"] = ts

    elif a.cmd == "完成":
        ag = find_agent(d, a.agent)
        ag["状态"] = "完成"
        ag["结束"] = ts
        if not ag.get("开始"):
            ag["开始"] = ts
        for e in ag.get("事件") or []:
            if e.get("状态") != "完成":
                e["状态"] = "完成"
                e["时间"] = ts

    elif a.cmd == "产物":
        ag = find_agent(d, a.agent)
        ag.setdefault("产物", [])
        ag["产物"] = [x for x in ag["产物"] if x.get("名") != a.名]
        ag["产物"].append({"名": a.名, "路径": a.路径, "摘要": a.摘要,
                           "版本": f"v{len(ag['产物']) + 1}", "时间": ts})

    elif a.cmd == "阶段":
        d["阶段"] = a.名

    elif a.cmd == "回环":
        d["回环"] = {"轮次": a.轮次, "最大轮次": (d.get("回环") or {}).get("最大轮次", 2),
                     "退回给": a.退回给, "原因": a.原因, "时间": ts}

    elif a.cmd == "角度":
        ag = find_agent(d, a.agent)
        ag["轮次"] = a.轮次

    elif a.cmd == "结束":
        d["结束时间"] = ts
        d["阶段"] = "已完成" if a.状态 == "完成" else d.get("阶段")

    save(d)
    print(f"✓ {a.cmd} 已写入（总进度 {int(d['总进度'] * 100)}%）")


if __name__ == "__main__":
    main()
