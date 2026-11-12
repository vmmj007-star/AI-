"""PyOS 셸: 스케줄러·메모리·파일시스템을 묶는 커널 인터페이스."""
import shlex
from .filesystem import FileSystem, FSError
from . import memory, scheduler

HELP = """명령어:
 [파일시스템] ls [경로] | cd <경로> | pwd | mkdir <경로> | cat <파일> | tree | rm [-r] <경로>
              echo <텍스트> > <파일> (또는 >> 로 추가)
 [프로세스]   spawn <이름> <실행시간> [우선순위]   프로세스 생성(현재 시각에 도착)
              ps                                   프로세스 목록
              sched <fcfs|sjf|priority|rr> [quantum]  스케줄링 시뮬레이션
              tick [n]                             시각을 n만큼 진행
 [메모리]     vmem <fifo|lru|opt> <프레임수> <페이지 참조열...>   예: vmem lru 3 7 0 1 2 0 3
 help | exit"""


class Shell:
    def __init__(self):
        self.fs = FileSystem()
        self.procs, self.next_pid, self.clock = [], 1, 0

    def run(self, line):
        """한 줄을 실행하고 출력 문자열 반환. 종료 시 None."""
        line = line.strip()
        if not line:
            return ""
        if ">" in line and line.startswith("echo"):
            return self._echo(line)
        try:
            args = shlex.split(line)
        except ValueError as e:
            return f"파싱 오류: {e}"
        cmd, a = args[0], args[1:]
        try:
            return self._dispatch(cmd, a)
        except FSError as e:
            return f"오류: {e}"
        except (ValueError, IndexError):
            return "사용법이 올바르지 않습니다. help 를 참고하세요."

    def _echo(self, line):
        append = ">>" in line
        text, _, path = line[4:].partition(">>" if append else ">")
        self.fs.write(path.strip(), text.strip().strip("\"'") + "\n", append)
        return ""

    def _dispatch(self, cmd, a):
        fs = self.fs
        if cmd in ("exit", "quit"):
            return None
        if cmd == "help":
            return HELP
        if cmd == "pwd":
            return fs.pwd()
        if cmd == "ls":
            return "  ".join(fs.ls(a[0] if a else "."))
        if cmd == "cd":
            fs.cd(a[0] if a else "/")
            return ""
        if cmd == "mkdir":
            fs.mkdir(a[0])
            return ""
        if cmd == "cat":
            return fs.read(a[0]).rstrip("\n")
        if cmd == "tree":
            return "\n".join(["."] + fs.tree())
        if cmd == "rm":
            rec = a[0] == "-r"
            fs.rm(a[1] if rec else a[0], rec)
            return ""
        if cmd == "spawn":
            p = scheduler.Process(self.next_pid, a[0], self.clock, int(a[1]), int(a[2]) if len(a) > 2 else 0)
            self.procs.append(p)
            self.next_pid += 1
            return f"프로세스 생성: pid={p.pid} name={p.name} burst={p.burst}"
        if cmd == "ps":
            if not self.procs:
                return "(프로세스 없음)"
            rows = [f"{'PID':<4}{'이름':<8}{'도착':>4}{'실행':>4}{'우선':>4}"]
            rows += [f"{p.pid:<4}{p.name:<8}{p.arrival:>4}{p.burst:>4}{p.priority:>4}" for p in self.procs]
            return "\n".join(rows)
        if cmd == "tick":
            self.clock += int(a[0]) if a else 1
            return f"현재 시각: {self.clock}"
        if cmd == "sched":
            if not self.procs:
                return "먼저 spawn 으로 프로세스를 만드세요."
            gantt, res = scheduler.schedule(self.procs, a[0], int(a[1]) if len(a) > 1 else 2)
            return scheduler.render(gantt, res)
        if cmd == "vmem":
            return memory.render([int(x) for x in a[2:]], int(a[1]), a[0])
        return f"{cmd}: 명령을 찾을 수 없습니다 (help)"


def main():
    sh = Shell()
    print("PyOS 학습용 OS 시뮬레이터 — help 로 명령어 확인, exit 로 종료")
    while True:
        try:
            out = sh.run(input(f"pyos:{sh.fs.pwd()}$ "))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if out is None:
            break
        if out:
            print(out)
