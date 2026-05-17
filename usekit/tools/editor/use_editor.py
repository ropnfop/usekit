"""
USEKIT Editor launcher.

Signatures:
    u.editor()                              # default
    u.editor("test01")                      # fpb resolve → 없으면 신규+바인딩
    u.editor(data, "test03")                # 내용 + 파일명
    u.editor(data, "test03", "/storage/..") # 내용 + 파일명 + 디렉토리
"""
from __future__ import annotations

from typing import Optional, Any


def run(data: Optional[str] = None,
        name: Optional[str] = None,
        dir_path: Optional[str] = None,
        file: Optional[str] = None,   # 하위호환
        path: Optional[str] = None,   # 하위호환
        **kwargs: Any):
    """
    data:     초기 내용 or 단순이름(fpb resolve 시도)
    name:     파일명 e.g. "test03" or "test03.py"
    dir_path: 저장 디렉토리 e.g. "/storage/.../src/base/"
    """
    from usekit.tools.editor.open_editor import main

    # 하위호환: file=/path= 단독 사용
    if data is None and name is None and dir_path is None:
        return main(file=file or path, **kwargs)

    return main(data=data, name=name, dir_path=dir_path, **kwargs)
