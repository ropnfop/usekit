from usekit import u, uw, ut

def save(rows):
    data = [{"name": r.name, "score": r.score} for r in rows]
    u.wjb({"generated": ut.str(), "results": data}, "score_report")
    uw.ok(f"리포트 저장: {len(data)}명")

def load():
    report = u.rjb("score_report")
    uw.info(f"생성시각: {report['generated']}")
    for item in report["results"]:
        uw.p(f"  {item['name']}: {item['score']}")
