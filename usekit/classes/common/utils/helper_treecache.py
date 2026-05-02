# Path: usekit/classes/common/utils/helper_treecache.py
# -----------------------------------------------------------------------------------------------
#  A creation by: The Little Prince × ROP × FOP
#  TreeCache + PathResolver
#  - nested(dict/list) → flat index 캐싱
#  - leaf 인덱스/키 기반 접근
#  - 상대 경로("/info/age") + 상위 트리(include_parent) 지원
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from usekit.classes.common.utils.helper_keypath import resolve_key_path


class TreeCache:
    """
    TreeCache with:
      - flat index (전역 leaf 인덱스)
      - leaf key 인덱스 (name[0], age[1] 등)
      - 상대 경로("/info/age") 기반 PathResolver
      - 인덱스 범위 + 상위 트리 포함(range + include_parent)
    """

    def __init__(self, root: Any):
        """
        Args:
            root: dict / list 기반의 중첩 트리 구조
        """
        self.root: Any = root

        # flat: full_path → value
        self.tree: Dict[str, Any] = {}

        # leaf 인덱스 구조
        self._flat_index: List[str] = []           # 순서대로 정렬된 모든 leaf path
        self._key_index: Dict[str, List[str]] = {} # leaf 이름 → full paths
        self._leaf_positions: Dict[str, List[int]] = {}  # leaf 이름 → flat index 목록

        self._build_flat()
        self._build_indices()

    # -------------------------------------------------------------------------
    # 내부: 플랫 딕셔너리 생성 (nested → flat)
    # -------------------------------------------------------------------------
    def _build_flat(self) -> None:
        def _walk(node: Any, path: str) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    new_path = f"{path}.{k}" if path else k
                    _walk(v, new_path)
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    seg = f"{path}[{i}]" if path else f"[{i}]"
                    _walk(v, seg)
            else:
                # leaf
                if path:  # 빈 path는 무시 (루트가 바로 스칼라인 경우)
                    self.tree[path] = node

        _walk(self.root, "")

    def _build_indices(self) -> None:
        for full_key in sorted(self.tree.keys()):
            leaf = full_key.split(".")[-1].split("[")[0]  # 마지막 세그먼트의 베이스 이름
            self._key_index.setdefault(leaf, []).append(full_key)

            idx = len(self._flat_index)
            self._flat_index.append(full_key)
            self._leaf_positions.setdefault(leaf, []).append(idx)

    # -------------------------------------------------------------------------
    # 기본 접근 API
    # -------------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._flat_index)

    def __getitem__(self, index: int) -> Tuple[str, Any]:
        """cache[0] → ('users[0].name', 'Alice')"""
        full_key = self._flat_index[index]
        return full_key, self.tree[full_key]

    def __repr__(self) -> str:
        return f"TreeCache(keys={len(self.tree)}, flat={len(self._flat_index)})"

    # -------------------------------------------------------------------------
    # leaf key 기반 접근: name[0], age[1], name_first, name_last, ...
    # -------------------------------------------------------------------------
    def get_leaf_at(self, leaf_key: str, index: int) -> Any:
        if leaf_key not in self._leaf_positions:
            raise KeyError(f"No keys ending with '{leaf_key}' found")

        positions = self._leaf_positions[leaf_key]
        if index >= len(positions):
            raise IndexError(
                f"Index {index} out of range for '{leaf_key}' "
                f"(max: {len(positions) - 1})"
            )
        flat_idx = positions[index]
        full_key = self._flat_index[flat_idx]
        return self.tree[full_key]

    def get(self, key_pattern: str, index: Optional[int] = None) -> Any:
        """
        Smart key access:

        - 'name[0]', 'age[1]'       → leaf 인덱스 기반
        - 'name_first', 'name_last' → 첫/마지막 leaf
        - 'name_idx' + index        → n번째 leaf
        - 직접 full key             → self.tree.get(key_pattern)
        """
        # 배열 스타일: 'name[0]'
        if "[" in key_pattern and key_pattern.endswith("]"):
            leaf, idx_str = key_pattern[:-1].split("[", 1)
            idx = int(idx_str)
            return self.get_leaf_at(leaf, idx)

        # 패턴 스타일: 'leaf_first', 'leaf_last', 'leaf_idx'
        if "_" in key_pattern:
            leaf_key, accessor = key_pattern.split("_", 1)
            if leaf_key not in self._key_index:
                raise KeyError(f"No keys ending with '{leaf_key}' found")

            paths = self._key_index[leaf_key]
            if accessor == "first":
                return self.tree[paths[0]]
            if accessor == "last":
                return self.tree[paths[-1]]
            if accessor == "idx":
                if index is None:
                    raise ValueError("Index required for 'idx' accessor")
                return self.tree[paths[index]]

            raise KeyError(f"Unknown accessor: {accessor}")

        # full key 직접 접근
        return self.tree.get(key_pattern)

    # -------------------------------------------------------------------------
    # 상대 경로 기반 PathResolver
    #   - "/info/age" → 트리 전체에서 suffix가 info/age 인 leaf 검색
    #   - include_parent=True 이면 상위 트리(subtree) 반환
    # -------------------------------------------------------------------------
    def resolve(
        self,
        rel_path: str,
        *,
        include_parent: bool = False,
        as_path: bool = False,
    ) -> List[Any]:
        """
        상대 경로로 leaf 탐색.

        Args:
            rel_path: "/info/age" 또는 "info/age" 형태
            include_parent:
                False → leaf 값만 반환
                True  → leaf가 포함된 상위 트리(subtree) 반환 (예: users[0] 전체)
            as_path:
                True  → 값 대신 full path 문자열 반환

        Returns:
            List[값] 또는 List[경로] 또는 List[subtree]
        """
        target = rel_path.lstrip("/")
        if not target:
            # "/" 만 주면 root 반환
            return [self.root] if not as_path else [""]

        rel_segs = target.split("/")
        rel_bases = [seg.split("[")[0] for seg in rel_segs]

        matched_paths: List[str] = []

        # suffix 매칭
        for full in self._flat_index:
            segs = full.split(".")
            bases = [s.split("[")[0] for s in segs]
            if len(bases) < len(rel_bases):
                continue
            if bases[-len(rel_bases) :] == rel_bases:
                matched_paths.append(full)

        if as_path:
            return matched_paths

        results: List[Any] = []

        # 상위 트리 포함 모드
        if include_parent:
            # 같은 상위(root segment)를 중복 없이 모은다.
            seen_roots: List[str] = []
            for full in matched_paths:
                root_seg = full.split(".")[0]  # 예: "users[0]"
                if root_seg in seen_roots:
                    continue
                seen_roots.append(root_seg)
                keydata = root_seg.replace(".", "/")  # helper_keypath는 "/" 사용
                subtree = resolve_key_path(self.root, keydata)
                results.append(subtree)
            return results

        # leaf 값만 추출
        for full in matched_paths:
            keydata = full.replace(".", "/")
            val = resolve_key_path(self.root, keydata)
            results.append(val)

        return results

    # -------------------------------------------------------------------------
    # flat index 범위 접근 + 상위 트리 포함
    # -------------------------------------------------------------------------
    def range(
        self,
        start: int,
        end: Optional[int] = None,
        *,
        include_parent: bool = False,
        as_path: bool = False,
    ) -> List[Any]:
        """
        flat index 범위를 이용해 부분 트리를 조회.

        Args:
            start: 시작 인덱스 (0 기반)
            end: 끝 인덱스(포함 X). None 이면 start+1
            include_parent:
                False → leaf 값만
                True  → 각 leaf의 최상위 세그먼트(subtree) 반환
            as_path:
                True  → 값 대신 full path 문자열 반환

        Returns:
            List[값] 또는 List[경로] 또는 List[subtree]
        """
        if end is None:
            end = start + 1

        start = max(0, start)
        end = min(end, len(self._flat_index))
        if start >= end:
            return []

        paths = self._flat_index[start:end]

        if as_path:
            return list(paths)

        if include_parent:
            # 해당 범위 안에 등장하는 상위 트리들을 반환
            seen_roots: List[str] = []
            results: List[Any] = []
            for full in paths:
                root_seg = full.split(".")[0]
                if root_seg in seen_roots:
                    continue
                seen_roots.append(root_seg)
                keydata = root_seg.replace(".", "/")
                subtree = resolve_key_path(self.root, keydata)
                results.append(subtree)
            return results

        # leaf 값만 반환
        results: List[Any] = []
        for full in paths:
            keydata = full.replace(".", "/")
            val = resolve_key_path(self.root, keydata)
            results.append(val)
        return results

    # -------------------------------------------------------------------------
    # 헬퍼: flat dict / 트리 그대로 가져오기
    # -------------------------------------------------------------------------
    def to_flat(self) -> Dict[str, Any]:
        """flat dict (full_path → value) 그대로 반환"""
        return dict(self.tree)

    def to_root(self) -> Any:
        """원래 root 트리 반환"""
        return self.root