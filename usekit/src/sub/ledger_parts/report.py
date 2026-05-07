from usekit import u, uw, ut

def save_md(rows, summary, income, expense, net):
    lines = ["# 가계부 리포트", f"\n생성: {ut.str()}\n"]

    lines.append("## 수입/지출 내역\n")
    lines.append("| 날짜 | 구분 | 카테고리 | 금액 | 메모 |")
    lines.append("|------|------|----------|-----:|------|")
    for r in rows:
        lines.append(f"| {r.date} | {r.type} | {r.category} | {r.amount:,} | {r.memo} |")

    lines.append("\n## 카테고리별 합계\n")
    lines.append("| 구분 | 카테고리 | 합계 |")
    lines.append("|------|----------|-----:|")
    for r in summary:
        lines.append(f"| {r.type} | {r.category} | {r.total:,} |")

    lines.append(f"\n## 요약\n")
    lines.append(f"- 총 수입: **{income:,}원**")
    lines.append(f"- 총 지출: **{expense:,}원**")
    lines.append(f"- 잔액:   **{net:,}원**")

    u.wmb("\n".join(lines), "ledger_report")
    uw.ok("리포트 저장 → docs/base/ledger_report.md")

def save_json(rows):
    data = [{"date": r.date, "type": r.type, "category": r.category,
             "amount": r.amount, "memo": r.memo} for r in rows]
    u.wjb({"generated": ut.str(), "records": data}, "ledger_data")
    uw.ok("데이터 저장 → data/json/base/ledger_data.json")
