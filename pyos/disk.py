"""디스크 스케줄링: FCFS, SSTF, SCAN, C-SCAN, LOOK.

하드디스크는 LP판처럼 생겼고, 읽기/쓰기 '헤드'가 안쪽↔바깥쪽(실린더 번호 0~max)으로
움직여 데이터를 찾는다. 헤드 이동(탐색 시간, seek time)이 디스크에서 가장 느린 동작이라,
여러 요청을 '어떤 순서로' 처리할지에 따라 총 이동 거리가 크게 달라진다.
"""

INTRO = """[디스크 스케줄링이란?]
하드디스크는 LP판처럼 원판 위를 '헤드'가 안쪽↔바깥쪽(실린더 번호 0~max)으로 오가며 데이터를 읽어요.
헤드를 움직이는 건 느린 작업이라, 여러 요청이 밀려 있을 때 '어떤 순서로 처리할지'에 따라
총 이동 거리가 크게 달라집니다. 이 순서를 정하는 것이 디스크 스케줄링이에요.
목표: 헤드 총 이동 거리를 줄이기 (이동이 적을수록 빠름)"""

EXPLAIN = {
    "fcfs": ("FCFS (선착순)", "먼저 도착한 요청부터 처리해요. 줄 서는 순서 그대로라 공평하고 단순하지만, 요청이 멀리 흩어져 있으면 헤드가 이리저리 왔다갔다 해서 이동이 많아요."),
    "sstf": ("SSTF (최단 탐색 우선)", "지금 헤드에서 '가장 가까운' 요청부터 처리해요. 택시가 가까운 손님부터 태우는 것과 같아요. 이동은 적지만, 멀리 있는 요청이 계속 뒤로 밀리는 '기아(starvation)' 문제가 생길 수 있어요."),
    "scan": ("SCAN (엘리베이터)", "엘리베이터처럼 한 방향으로 끝까지 가면서 지나는 길의 요청을 처리하고, 끝에 닿으면 방향을 바꿔 되돌아오며 처리해요. 요청이 없어도 끝까지 가는 게 특징이에요."),
    "cscan": ("C-SCAN (순환 스캔)", "SCAN과 비슷하지만 '한 방향으로만' 처리해요. 끝에 닿으면 반대편 처음으로 한 번에 돌아가고(돌아오는 길엔 처리 안 함), 다시 같은 방향으로 처리해요. 어느 위치든 기다리는 시간이 고르게 돼요."),
    "look": ("LOOK", "SCAN의 똑똑한 버전이에요. 끝까지 가지 않고 '마지막 요청'까지만 갔다가 방향을 바꿔요. 쓸데없는 이동이 줄어요."),
}
ALGOS = list(EXPLAIN)


def _up_points(reqs, head, algo, mx):
    """위쪽(번호가 커지는 방향) 먼저 가는 경우의 방문 지점 [(위치, 종류)]. 종류: req/edge/jump."""
    if algo == "fcfs":
        return [(r, "req") for r in reqs]
    if algo == "sstf":
        left, cur, pts = list(reqs), head, []
        while left:
            r = min(left, key=lambda x: abs(x - cur))
            left.remove(r)
            pts.append((r, "req"))
            cur = r
        return pts
    right = sorted(r for r in reqs if r >= head)
    low = sorted(r for r in reqs if r < head)
    pts = [(r, "req") for r in right]
    if algo == "look":
        return pts + [(r, "req") for r in reversed(low)]
    if not pts or pts[-1][0] != mx:
        pts.append((mx, "edge"))
    if algo == "scan":
        return pts + [(r, "req") for r in reversed(low)]
    if algo == "cscan":
        if low:
            pts.append((0, "jump"))
            pts += [(r, "req") for r in low]
        return pts
    raise ValueError(f"알 수 없는 알고리즘: {algo}")


def simulate(requests, head, algo, max_cyl=199, direction="up"):
    """(단계 리스트, 총 이동거리) 반환. 단계: {to, dist, kind, note}.
    C-SCAN의 '점프'(끝→처음)도 헤드가 실제로 움직이므로 이동거리에 포함한다."""
    if not 0 <= head <= max_cyl or any(not 0 <= r <= max_cyl for r in requests):
        raise ValueError(f"실린더 번호는 0~{max_cyl} 범위여야 합니다")
    if direction == "down":  # 좌우 반전해서 계산한 뒤 되돌린다
        pts = [(max_cyl - p, k) for p, k in _up_points([max_cyl - r for r in requests], max_cyl - head, algo, max_cyl)]
    else:
        pts = _up_points(list(requests), head, algo, max_cyl)
    notes = {"req": "요청 처리", "edge": "끝까지 이동 (요청은 없지만 SCAN 계열은 끝까지 가요)",
             "jump": "반대편 처음으로 점프 (돌아오는 길엔 처리 안 함)"}
    steps, cur = [], head
    for pos, kind in pts:
        steps.append({"to": pos, "dist": abs(pos - cur), "kind": kind, "note": notes[kind]})
        cur = pos
    return steps, sum(s["dist"] for s in steps)


def render(requests, head, algo, max_cyl=199, direction="up"):
    steps, total = simulate(requests, head, algo, max_cyl, direction)
    title, desc = EXPLAIN[algo]
    out = [f"■ {title}", f"  {desc}", "", f"  시작 위치: {head}   요청 큐: {list(requests)}   범위: 0~{max_cyl}"]
    cur = head
    for i, s in enumerate(steps, 1):
        out.append(f"  {i:>2}) {cur:>3} → {s['to']:>3}  ({s['dist']:>3}칸)  {s['note']}")
        cur = s["to"]
    calc = " + ".join(str(s["dist"]) for s in steps)
    out.append(f"  총 이동 거리 = {calc} = {total}")
    return "\n".join(out)


def compare(requests, head, max_cyl=199, direction="up"):
    rows = [(a, simulate(requests, head, a, max_cyl, direction)[1]) for a in ALGOS]
    best = min(t for _, t in rows)
    out = ["[알고리즘 비교] 총 이동 거리가 작을수록 디스크가 빨리 일해요"]
    for a, t in rows:
        out.append(f"  {EXPLAIN[a][0]:<22}{t:>5}  {'█' * (t * 30 // max(x for _, x in rows))}{'  ← 최소' if t == best else ''}")
    out.append("  ※ 숫자만 보면 SSTF/LOOK이 좋아 보여도, SSTF는 멀리 있는 요청이 굶을 수 있고,")
    out.append("    SCAN/C-SCAN은 이동이 조금 더 많아도 모든 요청이 반드시 처리되는 공평함이 장점이에요.")
    return "\n".join(out)
