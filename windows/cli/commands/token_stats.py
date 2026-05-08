"""AI 夏娃 — Token 用量统计"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

TOKEN_LOG_PATH = Path.home() / ".ai-eve" / "data" / "logs" / "token_usage.jsonl"


def _load_records():
    """读取所有 token 日志记录"""
    records = []
    if not TOKEN_LOG_PATH.exists():
        return records
    with open(TOKEN_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def _filter_by_time(records, since: datetime):
    """只保留 since 之后的记录"""
    return [r for r in records if datetime.fromisoformat(r["timestamp"]) >= since]


def _summarize(records, label: str) -> dict:
    """生成一段时间的汇总"""
    if not records:
        return {"label": label, "calls": 0, "prompt": 0, "completion": 0, "total": 0}
    return {
        "label": label,
        "calls": len(records),
        "prompt": sum(r["prompt_tokens"] for r in records),
        "completion": sum(r["completion_tokens"] for r in records),
        "total": sum(r["total_tokens"] for r in records),
    }


def _get_periods(now, records):
    """生成各时间段汇总"""
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    periods = [
        ("本月", now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)),
        ("昨天", yesterday_start),
        ("今天", today_start),
        ("12小时内", now - timedelta(hours=12)),
        ("8小时内", now - timedelta(hours=8)),
        ("4小时内", now - timedelta(hours=4)),
        ("2小时内", now - timedelta(hours=2)),
        ("1小时内", now - timedelta(hours=1)),
        ("30分钟内", now - timedelta(minutes=30)),
        ("15分钟内", now - timedelta(minutes=15)),
    ]

    results = []
    for label, since in periods:
        filtered = _filter_by_time(records, since)
        results.append(_summarize(filtered, label))

    return results


def show_token_stats():
    """显示 token 用量统计"""
    now = datetime.now(timezone.utc)
    records = _load_records()

    if not records:
        print("  暂无 token 消耗记录")
        print("  （调用 AI 模型后会自动记录）")
        return

    periods = _get_periods(now, records)

    # 总览
    total_prompt = sum(r["prompt"] for r in records)
    total_completion = sum(r["completion"] for r in records)
    total_all = sum(r["total"] for r in records)
    total_calls = len(records)

    print(f"\n  📊 Token 消耗统计")
    print(f"  {'='*50}")
    print(f"  累计调用次数: {total_calls}")
    print(f"  累计 Prompt tokens: {total_prompt:,}")
    print(f"  累计 Completion tokens: {total_completion:,}")
    print(f"  累计总消耗:     {total_all:,}")
    print()

    # 时间段明细表
    header = f"  {'时间段':<12} {'调用次数':>8} {'Prompt':>10} {'Completion':>12} {'总计':>10}"
    sep = f"  {'-'*12} {'-'*8} {'-'*10} {'-'*12} {'-'*10}"
    print(header)
    print(sep)

    for p in periods:
        if p["calls"] == 0:
            print(f"  {p['label']:<12} {'0':>8} {'-':>10} {'-':>12} {'-':>10}")
        else:
            prompt_fmt = f"{p['prompt']:,}"
            comp_fmt = f"{p['completion']:,}"
            total_fmt = f"{p['total']:,}"
            print(f"  {p['label']:<12} {p['calls']:>8} {prompt_fmt:>10} {comp_fmt:>12} {total_fmt:>10}")

    print()
