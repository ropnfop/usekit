from usekit import u, uw, ut


PLAN = {
    "title": "Python & USEKIT 학습 계획",
    "duration_weeks": 6,
    "goal": "Python 기초부터 USEKIT 실전 활용까지 마스터",
    "weeks": [
        {
            "week": 1,
            "theme": "Python 기초",
            "topics": ["변수와 자료형", "조건문/반복문", "함수 정의", "리스트/딕셔너리"],
            "daily_hours": 1.5,
            "status": "pending",
        },
        {
            "week": 2,
            "theme": "Python 중급",
            "topics": ["클래스와 객체", "파일 입출력", "예외 처리", "모듈 활용"],
            "daily_hours": 1.5,
            "status": "pending",
        },
        {
            "week": 3,
            "theme": "USEKIT 입문",
            "topics": ["USEKIT 설치 및 구조 이해", "u.rjb/wjb 기초", "3-letter 라우팅 익히기", "uw/ut 유틸리티"],
            "daily_hours": 2.0,
            "status": "pending",
        },
        {
            "week": 4,
            "theme": "USEKIT 데이터 조작",
            "topics": ["JSON append 패턴", "keydata 중첩 접근", "SQL DDL/DML 실습", "CSV/TXT/MD 파일 다루기"],
            "daily_hours": 2.0,
            "status": "pending",
        },
        {
            "week": 5,
            "theme": "USEKIT 실행 레이어",
            "topics": ["u.xpb 함수 실행", "u.ipb 모듈 임포트", "base/sub 분리 구조", "동적 경로 g/s 패턴"],
            "daily_hours": 2.0,
            "status": "pending",
        },
        {
            "week": 6,
            "theme": "실전 프로젝트",
            "topics": ["미니 앱 설계", "USEKIT 전체 API 통합", "코드 리뷰 및 리팩토링", "결과 발표 준비"],
            "daily_hours": 2.5,
            "status": "pending",
        },
    ],
}


def build():
    plan = dict(PLAN, created=ut.str())
    u.wjb(plan, "learning_plan")
    uw.ok("학습 계획 JSON 저장 완료 → data/json/base/learning_plan.json")

    total_hours = sum(w["daily_hours"] * 7 for w in plan["weeks"])

    lines = [
        f"# {plan['title']}",
        "",
        f"> 생성일: {plan['created']}  ",
        f"> 총 기간: {plan['duration_weeks']}주  ",
        f"> 목표: {plan['goal']}  ",
        f"> 예상 총 학습시간: {total_hours:.0f}시간",
        "",
        "---",
        "",
    ]

    for w in plan["weeks"]:
        lines += [
            f"## Week {w['week']} — {w['theme']}",
            "",
            "| 항목 | 내용 |",
            "|------|------|",
            f"| 주제 | {', '.join(w['topics'])} |",
            f"| 일일 학습시간 | {w['daily_hours']}시간 |",
            f"| 주간 합계 | {w['daily_hours'] * 7:.1f}시간 |",
            f"| 상태 | {w['status']} |",
            "",
        ]

    lines += [
        "---",
        "",
        "## 전체 요약",
        "",
        "| 주차 | 테마 | 주간 시간 |",
        "|------|------|----------|",
    ]
    for w in plan["weeks"]:
        lines.append(f"| {w['week']}주차 | {w['theme']} | {w['daily_hours'] * 7:.1f}h |")

    lines += ["", f"**총 학습시간: {total_hours:.0f}시간**", ""]

    u.wmb("\n".join(lines), "learning_plan")
    uw.ok("마크다운 리포트 저장 완료 → docs/base/learning_plan.md")

    return plan


if __name__ == "__main__":
    build()
