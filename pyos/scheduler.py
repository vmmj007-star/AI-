"""프로세스 & CPU 스케줄러 (FCFS, SJF, Priority, Round Robin)."""
from dataclasses import dataclass, field


@dataclass
class Process:
    pid: int
    name: str
    arrival: int
    burst: int
    priority: int = 0
    remaining: int = field(init=False)
    start: int | None = None
    finish: int | None = None

    def __post_init__(self):
        self.remaining = self.burst

    @property
    def turnaround(self):
        return self.finish - self.arrival

    @property
    def waiting(self):
        return self.turnaround - self.burst


def schedule(procs, algo="rr", quantum=2):
    """시뮬레이션 실행. (간트차트 리스트, 프로세스 리스트) 반환.
    간트차트: [(시작, 끝, 이름)]  idle 구간은 이름 'idle'."""
    procs = [Process(p.pid, p.name, p.arrival, p.burst, p.priority) for p in procs]
    t, gantt, done = 0, [], 0
    ready, pending = [], sorted(procs, key=lambda p: (p.arrival, p.pid))

    def admit():
        while pending and pending[0].arrival <= t:
            ready.append(pending.pop(0))

    def pick():
        if algo == "fcfs":
            return ready[0]
        if algo == "sjf":
            return min(ready, key=lambda p: (p.burst, p.arrival))
        if algo == "priority":  # 숫자가 작을수록 우선
            return min(ready, key=lambda p: (p.priority, p.arrival))
        return ready[0]  # rr

    def record(s, e, name):
        if gantt and gantt[-1][2] == name and gantt[-1][1] == s:
            gantt[-1] = (gantt[-1][0], e, name)
        else:
            gantt.append((s, e, name))

    while done < len(procs):
        admit()
        if not ready:
            nxt = pending[0].arrival
            record(t, nxt, "idle")
            t = nxt
            continue
        p = pick()
        ready.remove(p)
        if p.start is None:
            p.start = t
        run = min(quantum, p.remaining) if algo == "rr" else p.remaining
        record(t, t + run, p.name)
        t += run
        p.remaining -= run
        admit()  # 실행 중 도착한 프로세스를 먼저 큐에 넣고
        if p.remaining:
            ready.append(p)  # 그 뒤에 선점당한 프로세스를 넣는다
        else:
            p.finish = t
            done += 1
    return gantt, procs


def render(gantt, procs):
    bar = "".join(f"|{n:^{max(3, (e - s) * 2)}}" for s, e, n in gantt) + "|"
    times = "".join(f"{s:<{max(4, (e - s) * 2 + 1)}}" for s, e, _ in gantt) + str(gantt[-1][1])
    lines = [bar, times, "", f"{'PID':<4}{'이름':<8}{'도착':>4}{'실행':>4}{'종료':>4}{'반환':>5}{'대기':>5}"]
    for p in sorted(procs, key=lambda p: p.pid):
        lines.append(f"{p.pid:<4}{p.name:<8}{p.arrival:>4}{p.burst:>4}{p.finish:>4}{p.turnaround:>5}{p.waiting:>5}")
    n = len(procs)
    lines.append(f"평균 대기시간: {sum(p.waiting for p in procs) / n:.2f}  평균 반환시간: {sum(p.turnaround for p in procs) / n:.2f}")
    return "\n".join(lines)
