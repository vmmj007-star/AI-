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
