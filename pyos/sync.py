"""동기화 시뮬레이션: 세마포어 실행 추적 + 교착상태(데드락) 탐지 + 은행원 알고리즘."""

PRESETS = {
    "deadlock": "sem a=1 b=1\nP1: P a; P b; work; V b; V a\nP2: P b; P a; work; V a; V b",
    "ordered": "sem a=1 b=1\nP1: P a; P b; work; V b; V a\nP2: P a; P b; work; V b; V a",
    "mutex": "sem m=1\nP1: P m; work; work; V m\nP2: P m; work; V m\nP3: P m; work; V m",
}


def parse_script(text):
    """'sem a=1 b=1' 와 'P1: P a; work; V a' 형식의 스크립트를 파싱."""
    sems, procs = {}, {}
    for line in filter(None, (l.strip() for l in text.splitlines())):
        if line.startswith("sem "):
            for tok in line[4:].split():
                k, _, v = tok.partition("=")
                sems[k] = int(v or 1)
        else:
            name, _, body = line.partition(":")
            procs[name.strip()] = [o.strip() for o in body.split(";") if o.strip()]
    for ops in procs.values():
        for op in ops:
            kind, _, arg = op.partition(" ")
            if kind not in ("P", "V", "work") or (kind != "work" and arg not in sems):
                raise ValueError(f"잘못된 연산: {op!r}")
    return sems, procs


def run_semaphores(sems, procs, max_steps=500):
    """프로세스를 라운드로빈으로 한 연산씩 실행. (trace, 결과, 막힌 프로세스) 반환.
    결과: 'done' | 'deadlock'."""
    sems, pc = dict(sems), {p: 0 for p in procs}
    waiters, blocked, trace = {s: [] for s in sems}, {}, []
    order, i = list(procs), 0
    for step in range(1, max_steps + 1):
        runnable = [p for p in order if pc[p] < len(procs[p]) and p not in blocked]
        if not runnable:
            stuck = [p for p in order if p in blocked]
            return trace, ("deadlock" if stuck else "done"), stuck
        p = next(order[(i + k) % len(order)] for k in range(len(order)) if order[(i + k) % len(order)] in runnable)
        i = (order.index(p) + 1) % len(order)
        op = procs[p][pc[p]]
        kind, _, s = op.partition(" ")
        note = "작업 수행"
        if kind == "P":
            if sems[s] > 0:
                sems[s] -= 1
                pc[p] += 1
                note = f"{s} 획득"
            else:
                waiters[s].append(p)
                blocked[p] = s
                note = f"{s} 대기 → 블록"
        elif kind == "V":
            pc[p] += 1
            if waiters[s]:
                w = waiters[s].pop(0)
                del blocked[w]
                pc[w] += 1
                note = f"{s} 반납 → {w} 깨움(획득)"
            else:
                sems[s] += 1
                note = f"{s} 반납"
        else:
            pc[p] += 1
        trace.append({"step": step, "proc": p, "op": op, "note": note, "sems": dict(sems), "blocked": dict(blocked)})
    return trace, "timeout", []


def _reduce(work, alloc, need):
    """종료 가능한 프로세스를 반복 제거. (종료 순서, 남은 프로세스 인덱스)."""
    work, left, seq = list(work), list(range(len(alloc))), []
    progress = True
    while progress:
        progress = False
        for i in list(left):
            if all(n <= w for n, w in zip(need[i], work)):
                work = [w + a for w, a in zip(work, alloc[i])]
                left.remove(i)
                seq.append(i)
                progress = True
    return seq, left


def safe_sequence(available, maximum, allocation):
    """은행원 알고리즘 안전성 검사. 안전하면 종료 순서(인덱스), 아니면 None."""
    need = [[m - a for m, a in zip(mx, al)] for mx, al in zip(maximum, allocation)]
    seq, left = _reduce(available, allocation, need)
    return None if left else seq


def request_resources(pid, req, available, maximum, allocation):
    """자원 요청 처리. (승인 여부, 사유, 새 available, 새 allocation) 반환."""
    need = [m - a for m, a in zip(maximum[pid], allocation[pid])]
    if any(r > n for r, n in zip(req, need)):
        return False, "최대 선언량 초과", available, allocation
    if any(r > a for r, a in zip(req, available)):
        return False, "가용 자원 부족 (대기)", available, allocation
    new_av = [a - r for a, r in zip(available, req)]
    new_al = [row[:] for row in allocation]
    new_al[pid] = [a + r for a, r in zip(new_al[pid], req)]
    if safe_sequence(new_av, maximum, new_al) is None:
        return False, "승인 시 불안전 상태 → 거부", available, allocation
    return True, "안전 상태 유지 → 승인", new_av, new_al


def detect_deadlock(available, allocation, request):
    """현재 요청(request) 기준 데드락 프로세스 인덱스 목록 (없으면 빈 리스트)."""
    return _reduce(available, allocation, request)[1]
