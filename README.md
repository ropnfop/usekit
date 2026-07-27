# EMO RAG — backfill limit fix (260609)

## 이번 패치
`ua.emo.backfill(limit=N)` 버그 수정.

기존: limit이 SQL에서 "id 순 앞 N개"만 가져옴 -> 앞부분이 이미 코딩됐으면
전부 skip되고 뒤쪽 미처리분은 영영 안 잡힘("다 스킵" 증상).
수정: limit은 이제 "이번 실행에서 **새로 처리할** 행 수"를 뜻한다.
전체를 fetch한 뒤 skip을 거르고, 새로 처리한 게 limit에 도달하면 멈춘다.

- `usekit/llm/handler/ua_emo.py`만 변경. 덮어쓰고 서버 재시작:
    pkill -f open_editor   # 후 재시작

## 사용 (RUN 패널 15초 제한 회피)
    ua.conn("groq_api")
    ua.emo.backfill(limit=8)   # 안 된 것 중 8개만 처리 -> 15초 안에 끝
이 한 세트를 반복하면 매번 안 된 것 8개씩 채워진다. skipped만 남고
stored=0 / total 다 참이면 완료.

전체를 한 번에(타임아웃 걱정 없을 때):
    ua.emo.backfill()

## 검증
    ua.emo.recall("요즘 너무 지친다")
