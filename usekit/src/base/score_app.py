from usekit import use, uw

def main():
    use.imp.pyp.sub("score_parts.db : reset, insert, fetch_all")
    use.imp.pyp.sub("score_parts.report : save, load")

    reset()
    for name, score in [("Alice", 95), ("Bob", 72), ("Charlie", 88)]:
        insert(name, score)

    rows = fetch_all()
    uw.info("점수 순위")
    for r in rows:
        uw.p(f"  {r.name}: {r.score}")

    save(rows)
    uw.info("저장된 리포트")
    load()

if __name__ == "__main__":
    main()
