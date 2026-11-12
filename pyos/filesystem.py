"""인메모리 계층형 파일시스템."""


class FSError(Exception):
    pass


class Node:
    def __init__(self, name, is_dir, parent=None):
        self.name, self.is_dir, self.parent = name, is_dir, parent
        self.children = {} if is_dir else None
        self.data = "" if not is_dir else None


class FileSystem:
    def __init__(self):
        self.root = Node("", True)
        self.cwd = self.root

    def _resolve(self, path, start=None):
        node = self.root if path.startswith("/") else (start or self.cwd)
        for part in [p for p in path.split("/") if p]:
            if part == ".":
                continue
            if part == "..":
                node = node.parent or node
                continue
            if not node.is_dir or part not in node.children:
                raise FSError(f"{path}: 그런 파일이나 디렉터리가 없습니다")
            node = node.children[part]
        return node

    def _split(self, path):
        parent_path, _, name = path.rstrip("/").rpartition("/")
        if not name:
            raise FSError("잘못된 경로")
        parent = self._resolve(parent_path or ("/" if path.startswith("/") else "."))
        if not parent.is_dir:
            raise FSError(f"{parent_path}: 디렉터리가 아닙니다")
        return parent, name

    def pwd(self):
        parts, n = [], self.cwd
        while n.parent:
            parts.append(n.name)
            n = n.parent
        return "/" + "/".join(reversed(parts))

    def mkdir(self, path):
        parent, name = self._split(path)
        if name in parent.children:
            raise FSError(f"{path}: 이미 존재합니다")
        parent.children[name] = Node(name, True, parent)

    def cd(self, path):
        node = self._resolve(path)
        if not node.is_dir:
            raise FSError(f"{path}: 디렉터리가 아닙니다")
        self.cwd = node

    def ls(self, path="."):
        node = self._resolve(path)
        if not node.is_dir:
            return [node.name]
        return [n + "/" if c.is_dir else n for n, c in sorted(node.children.items())]

    def write(self, path, data, append=False):
        parent, name = self._split(path)
        node = parent.children.get(name)
        if node is None:
            node = parent.children[name] = Node(name, False, parent)
        elif node.is_dir:
            raise FSError(f"{path}: 디렉터리입니다")
        node.data = (node.data + data) if append else data

    def read(self, path):
        node = self._resolve(path)
        if node.is_dir:
            raise FSError(f"{path}: 디렉터리입니다")
        return node.data

    def rm(self, path, recursive=False):
        node = self._resolve(path)
        if node is self.root:
            raise FSError("루트는 삭제할 수 없습니다")
        if node.is_dir and node.children and not recursive:
            raise FSError(f"{path}: 비어있지 않습니다 (rm -r 사용)")
        if node is self.cwd or self._is_ancestor(node, self.cwd):
            raise FSError("현재 위치를 포함한 디렉터리는 삭제할 수 없습니다")
        del node.parent.children[node.name]

    @staticmethod
    def _is_ancestor(a, b):
        while b:
            if b is a:
                return True
            b = b.parent
        return False

    def tree(self, node=None, prefix=""):
        node = node or self.cwd
        lines = []
        items = sorted(node.children.items())
        for i, (name, child) in enumerate(items):
            last = i == len(items) - 1
            lines.append(f"{prefix}{'└── ' if last else '├── '}{name}{'/' if child.is_dir else ''}")
            if child.is_dir:
                lines += self.tree(child, prefix + ("    " if last else "│   "))
        return lines
