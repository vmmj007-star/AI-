"""페이징 메모리 관리: 페이지 교체 알고리즘 (FIFO, LRU, OPT)."""
from collections import OrderedDict, deque


def simulate(refs, frames, algo="lru"):
    """참조열에 대해 페이지 폴트 시뮬레이션. (폴트 수, 단계별 로그) 반환."""
    mem, log, faults = [], [], 0
    fifo, lru = deque(), OrderedDict()
    for i, page in enumerate(refs):
        fault = page not in mem
        victim = None
        if fault:
            faults += 1
            if len(mem) >= frames:
                if algo == "fifo":
                    victim = fifo.popleft()
                elif algo == "lru":
                    victim = next(iter(lru))
                elif algo == "opt":
                    future = refs[i + 1:]
                    victim = max(mem, key=lambda m: future.index(m) if m in future else len(future) + 1)
                else:
                    raise ValueError(f"알 수 없는 알고리즘: {algo}")
                mem.remove(victim)
                lru.pop(victim, None)
            mem.append(page)
            fifo.append(page)
        if page in lru:
            lru.move_to_end(page)
        else:
            lru[page] = True
        log.append((page, list(mem), fault, victim))
    return faults, log


def render(refs, frames, algo):
    faults, log = simulate(refs, frames, algo)
    out = [f"[{algo.upper()}] 프레임={frames}"]
    for page, mem, fault, victim in log:
        note = f" 폴트(교체: {victim})" if fault and victim is not None else (" 폴트" if fault else " 히트")
        out.append(f"  참조 {page:>2} -> {str(mem):<20}{note}")
    out.append(f"  페이지 폴트: {faults}/{len(refs)}  (폴트율 {faults / len(refs):.0%})")
    return "\n".join(out)
