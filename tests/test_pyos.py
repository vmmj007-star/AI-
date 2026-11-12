from pyos import memory, scheduler
from pyos.filesystem import FileSystem, FSError
from pyos.shell import Shell
import pytest


def P(pid, name, arr, burst, pri=0):
    return scheduler.Process(pid, name, arr, burst, pri)


def test_fcfs():
    _, r = scheduler.schedule([P(1, "A", 0, 5), P(2, "B", 1, 3), P(3, "C", 2, 1)], "fcfs")
    assert [p.finish for p in r] == [5, 8, 9]


def test_sjf():
    _, r = scheduler.schedule([P(1, "A", 0, 5), P(2, "B", 1, 3), P(3, "C", 2, 1)], "sjf")
    assert [p.finish for p in r] == [5, 9, 6]


def test_rr_classic():
    # 교과서 예제: quantum=4, burst 24/3/3 -> 평균 대기 5.67
    _, r = scheduler.schedule([P(1, "P1", 0, 24), P(2, "P2", 0, 3), P(3, "P3", 0, 3)], "rr", 4)
    assert sum(p.waiting for p in r) / 3 == pytest.approx(17 / 3)


def test_idle_gap():
    g, _ = scheduler.schedule([P(1, "A", 3, 2)], "fcfs")
    assert g[0] == (0, 3, "idle")


def test_page_faults_classic():
    refs = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    assert memory.simulate(refs, 3, "fifo")[0] == 15
    assert memory.simulate(refs, 3, "lru")[0] == 12
    assert memory.simulate(refs, 3, "opt")[0] == 9


def test_fs():
    fs = FileSystem()
    fs.mkdir("/a")
    fs.cd("/a")
    fs.write("f.txt", "hi")
    assert fs.read("/a/f.txt") == "hi" and fs.pwd() == "/a"
    with pytest.raises(FSError):
        fs.rm("/a")
    with pytest.raises(FSError):
        fs.cd("/nope")


def test_shell():
    sh = Shell()
    sh.run("mkdir docs")
    sh.run("echo hello > docs/a.txt")
    assert sh.run("cat docs/a.txt") == "hello"
    sh.run("spawn A 5")
    assert "평균 대기시간" in sh.run("sched fcfs")
    assert "폴트" in sh.run("vmem lru 3 1 2 3 4")
    assert sh.run("exit") is None


from pyos import sync


def run_preset(name):
    return sync.run_semaphores(*sync.parse_script(sync.PRESETS[name]))


def test_semaphore_deadlock_and_fix():
    assert run_preset("deadlock")[1:] == ("deadlock", ["P1", "P2"])
    assert run_preset("ordered")[1] == "done"
    trace, res, _ = run_preset("mutex")
    assert res == "done" and all(t["sems"]["m"] in (0, 1) for t in trace)


def test_banker_textbook():
    av = [3, 3, 2]
    mx = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
    al = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
    assert sync.safe_sequence(av, mx, al) == [1, 3, 4, 0, 2]
    ok, _, av, al = sync.request_resources(1, [1, 0, 2], av, mx, al)
    assert ok and av == [2, 3, 0]
    assert not sync.request_resources(4, [3, 3, 0], av, mx, al)[0]      # 가용 부족
    assert "불안전" in sync.request_resources(0, [0, 2, 0], av, mx, al)[1]


def test_detect_deadlock():
    # P0,P1이 서로 상대의 자원을 기다림, P2는 정상
    assert sync.detect_deadlock([0], [[1], [1], [0]], [[1], [1], [0]]) == [0, 1]
    assert sync.detect_deadlock([1], [[1], [1]], [[1], [0]]) == []


def test_shell_sync():
    sh = Shell()
    assert "데드락 발생" in sh.run("sem deadlock")
    assert "P1 → P3" in sh.run("banker")
    assert "승인" in sh.run("banker req 1 1 0 2")
    assert "불안전" in sh.run("banker req 0 0 2 0")
