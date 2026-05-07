from usekit import use, uw, ut

def main():
    use.imp.pyp.sub("ledger_parts.db : reset, insert, fetch_all, fetch_summary, balance")
    use.imp.pyp.sub("ledger_parts.report : save_md, save_json")

    reset()

    # 샘플 데이터
    records = [
        ("2026-05-01", "수입", "월급",    3000000, "5월 급여"),
        ("2026-05-02", "지출", "식비",      45000, "마트"),
        ("2026-05-03", "지출", "교통",      12000, "버스/지하철"),
        ("2026-05-04", "지출", "식비",      32000, "외식"),
        ("2026-05-05", "수입", "부수입",   200000, "프리랜서"),
        ("2026-05-06", "지출", "통신비",    55000, "핸드폰"),
        ("2026-05-07", "지출", "식비",      28000, "편의점"),
        ("2026-05-07", "지출", "여가",      80000, "영화/카페"),
    ]
    for r in records:
        insert(*r)

    # 조회
    rows = fetch_all()
    uw.info(f"총 {len(rows)}건")
    for r in rows:
        sign = "+" if r.type == "수입" else "-"
        uw.p(f"  {r.date} [{r.type}] {r.category:8s} {sign}{r.amount:>10,}원  {r.memo}")

    # 요약
    income, expense, net = balance()
    uw.p("")
    uw.ok(f"수입 {income:,}원 / 지출 {expense:,}원 / 잔액 {net:,}원")

    # 저장
    save_json(rows)
    save_md(rows, fetch_summary(), income, expense, net)

if __name__ == "__main__":
    main()
