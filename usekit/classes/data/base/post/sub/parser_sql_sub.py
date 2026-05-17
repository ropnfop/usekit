# Path: usekit.classes.data.base.post.sub.parser_sql_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for SQL parser - variable binding and multi-dialect support
# Features:
#   - SQL style detection: USEKIT($), SQLite(?), Oracle(:), MSSQL(@), psycopg(%)
#   - Variable parsing: declarative string format ("$name: John | $age: 20")
#   - Type inference: auto-detect int/float/bool/None/str
#   - Dialect conversion: bidirectional conversion between SQL dialects
#   - Variable replacement: safe SQL injection prevention
#   - Context-aware scanner: code/string/comment 구간 분리로 placeholder 오치환 방지
# -----------------------------------------------------------------------------------------------

import re
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union


# ===============================================================================
# Constants
# ===============================================================================

SQL_STYLES = {
    "usekit": "$",      # $variable_name
    "sqlite": "?",      # positional ?
    "oracle": ":",      # :variable_name
    "mssql": "@",       # @variable_name
    "psycopg": "%",     # %(variable_name)s or %s
}

# Regex patterns for variable detection
PATTERN_USEKIT = re.compile(r'\$(\w+)')           # $name
PATTERN_ORACLE = re.compile(r'(?<!:):(\w+)')      # :name  (:: 이중콜론 제외)
PATTERN_MSSQL = re.compile(r'@(\w+)')             # @name
PATTERN_PSYCOPG_NAMED = re.compile(r'%\((\w+)\)s')  # %(name)s
PATTERN_SQLITE = re.compile(r'\?')                # ?


# ===============================================================================
# SQL Segment Scanner (context-aware)
# ===============================================================================

def _iter_sql_segments(sql: str) -> Iterator[Tuple[str, str]]:
    """
    SQL을 순회하며 (kind, text) 튜플을 yield.

    kind ∈ {'code', 'sq', 'dq', 'line_comment', 'block_comment'}
    - code          : 일반 SQL 코드 (placeholder 치환 대상)
    - sq            : 'single quoted string' (내용 보존)
    - dq            : "double quoted identifier" (내용 보존)
    - line_comment  : -- comment (내용 보존, 개행 제외)
    - block_comment : /* comment */ (내용 보존, 비중첩)

    규칙 (표준 SQL):
    - 문자열 이스케이프는 '' 연속 두 개만 허용 ("" 도 동일)
    - 블록 주석 중첩 없음
    - 모든 구간을 이어붙이면 원본과 동일 (round-trip safe)

    Args:
        sql: SQL string to scan

    Yields:
        (kind, text) tuples
    """
    i = 0
    n = len(sql)
    buf: List[str] = []

    def flush_code() -> Optional[Tuple[str, str]]:
        if buf:
            v = ('code', ''.join(buf))
            buf.clear()
            return v
        return None

    while i < n:
        ch = sql[i]
        ch2 = sql[i:i+2]

        # line comment: -- ... (개행 전까지)
        if ch2 == '--':
            c = flush_code()
            if c: yield c
            j = sql.find('\n', i)
            if j == -1:
                yield ('line_comment', sql[i:])
                i = n
            else:
                yield ('line_comment', sql[i:j])  # \n은 다음 code로 넘김
                i = j
            continue

        # block comment: /* ... */ (비중첩)
        if ch2 == '/*':
            c = flush_code()
            if c: yield c
            j = sql.find('*/', i + 2)
            if j == -1:
                # 미종결: 나머지 전체를 주석으로 간주
                yield ('block_comment', sql[i:])
                i = n
            else:
                yield ('block_comment', sql[i:j+2])
                i = j + 2
            continue

        # single-quoted string: '...' ('' 이스케이프)
        if ch == "'":
            c = flush_code()
            if c: yield c
            j = i + 1
            while j < n:
                if sql[j] == "'":
                    if j + 1 < n and sql[j+1] == "'":
                        j += 2  # '' 이스케이프
                        continue
                    j += 1
                    break
                j += 1
            yield ('sq', sql[i:j])
            i = j
            continue

        # double-quoted identifier: "..." ("" 이스케이프)
        if ch == '"':
            c = flush_code()
            if c: yield c
            j = i + 1
            while j < n:
                if sql[j] == '"':
                    if j + 1 < n and sql[j+1] == '"':
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            yield ('dq', sql[i:j])
            i = j
            continue

        # 일반 코드 문자
        buf.append(ch)
        i += 1

    # 남은 code flush
    c = flush_code()
    if c: yield c


def _transform_code_only(sql: str, transform) -> str:
    """
    _iter_sql_segments로 구간 분리 후 code 구간에만 transform(text) 적용.
    문자열/주석/식별자 구간은 원본 그대로 보존.

    Args:
        sql: Original SQL string
        transform: code text → transformed text 함수

    Returns:
        Transformed SQL
    """
    out: List[str] = []
    for kind, text in _iter_sql_segments(sql):
        if kind == 'code':
            out.append(transform(text))
        else:
            out.append(text)
    return ''.join(out)


# ===============================================================================
# SQL Style Detection
# ===============================================================================

def _detect_sql_style(sql: str) -> str:
    """
    Auto-detect SQL variable placeholder style.

    Priority order (first match wins):
    1. psycopg: %(name)s
    2. usekit: $variable
    3. oracle: :variable  (:: cast 제외)
    4. mssql: @variable   (이메일 제외)
    5. sqlite: ?
    6. default: usekit

    문맥 인지: 문자열/주석 구간은 판단에서 제외.

    Args:
        sql: SQL string to analyze

    Returns:
        Style name ('usekit', 'sqlite', 'oracle', 'mssql', 'psycopg')
    """

    # code 구간만 추출해서 감지 (문자열/주석 제거)
    code_only = ''.join(
        text for kind, text in _iter_sql_segments(sql) if kind == 'code'
    )

    # 1. psycopg named (가장 특이) — %(name)s
    if PATTERN_PSYCOPG_NAMED.search(code_only):
        return 'psycopg'

    # 2. USEKIT — $variable
    if PATTERN_USEKIT.search(code_only):
        return 'usekit'

    # 3. Oracle — :variable (:: 제외)
    if PATTERN_ORACLE.search(code_only):
        return 'oracle'

    # 4. MSSQL — @variable
    # (이메일은 sq 문자열 안일 가능성이 높은데 이미 제거됨)
    if PATTERN_MSSQL.search(code_only):
        return 'mssql'

    # 5. SQLite — ?
    if '?' in code_only:
        return 'sqlite'

    # Default
    return 'usekit'


def _remove_sql_noise(sql: str) -> str:
    """
    Remove SQL comments and string literals for cleaner detection.

    (Legacy helper — 유지하되 내부에서 _iter_sql_segments로 구현)

    Args:
        sql: Original SQL string

    Returns:
        SQL with strings/comments replaced by empty equivalents
    """
    out: List[str] = []
    for kind, text in _iter_sql_segments(sql):
        if kind == 'code':
            out.append(text)
        elif kind == 'sq':
            out.append("''")
        elif kind == 'dq':
            out.append('""')
        # comments: drop
    return ''.join(out)


# ===============================================================================
# Parameter String Parsing
# ===============================================================================

def _parse_param_string(param_str: str) -> Dict[str, Any]:
    """
    Parse declarative parameter string to dict.

    Supports formats:
    - Pipe-separated: "$name: John | $age: 20 | $active: True"
    - Multi-line:
        '''
        $name: John
        $age: 20
        $active: True
        '''

    Args:
        param_str: Parameter string

    Returns:
        Dict of variable_name -> value
    """

    if not param_str or not isinstance(param_str, str):
        return {}

    result = {}

    # Detect format: pipe-separated vs multi-line
    if '|' in param_str:
        items = param_str.split('|')
    else:
        items = param_str.strip().split('\n')

    for item in items:
        item = item.strip()
        if not item or ':' not in item:
            continue

        parts = item.split(':', 1)
        if len(parts) != 2:
            continue

        key, value = parts
        key = key.strip().lstrip('$')
        value = value.strip()

        if not key:
            continue

        result[key] = _infer_type(value)

    return result


def _infer_type(value: str) -> Any:
    """
    Auto-detect and convert value type.

    Conversion priority:
    1. None/NULL
    2. Boolean (True/False)
    3. Integer
    4. Float
    5. String (with quote removal)
    """

    value = value.strip()

    if value.lower() in ('none', 'null'):
        return None

    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'

    if value.lstrip('-').isdigit():
        return int(value)

    try:
        if '.' in value:
            return float(value)
    except ValueError:
        pass

    if len(value) >= 2:
        if (value[0] == value[-1]) and value[0] in ('"', "'"):
            return value[1:-1]

    return value


# ===============================================================================
# Dialect Conversion (context-aware: code 구간에서만 치환)
# ===============================================================================

def _convert_to_usekit(sql: str, style: str) -> str:
    """
    Convert various SQL dialects to USEKIT format ($variable).

    문자열/주석 안의 placeholder는 보호됨.

    Args:
        sql: Original SQL string
        style: Source style ('sqlite', 'oracle', 'mssql', 'psycopg', 'usekit')

    Returns:
        SQL in USEKIT format
    """

    if style == 'usekit':
        return sql

    if style == 'sqlite':
        # ? → $1, $2, $3 (전역 카운터, code 구간에서만)
        counter = [1]

        def transform(text: str) -> str:
            result = []
            for ch in text:
                if ch == '?':
                    result.append(f'${counter[0]}')
                    counter[0] += 1
                else:
                    result.append(ch)
            return ''.join(result)

        return _transform_code_only(sql, transform)

    if style == 'oracle':
        # :variable → $variable  (:: cast는 제외)
        def transform(text: str) -> str:
            return PATTERN_ORACLE.sub(r'$\1', text)

        return _transform_code_only(sql, transform)

    if style == 'mssql':
        # @variable → $variable
        def transform(text: str) -> str:
            return PATTERN_MSSQL.sub(r'$\1', text)

        return _transform_code_only(sql, transform)

    if style == 'psycopg':
        # %(variable)s → $variable
        def transform(text: str) -> str:
            return PATTERN_PSYCOPG_NAMED.sub(r'$\1', text)

        return _transform_code_only(sql, transform)

    return sql


def _convert_from_usekit(
    sql: str,
    param_dict: Dict[str, Any],
    target_style: str = 'sqlite'
) -> Tuple[str, Union[tuple, dict]]:
    """
    Convert USEKIT format to target SQL dialect.

    문자열/주석 안의 $variable은 보호됨.
    SQLite 타겟은 (sql_with_?, tuple_of_values) 반환.
    그 외는 (converted_sql, param_dict) 반환.

    Args:
        sql: SQL in USEKIT format ($variable)
        param_dict: Variable values
        target_style: Target dialect ('sqlite', 'oracle', 'mssql', 'psycopg', 'usekit')

    Returns:
        (converted_sql, params_in_target_format)
    """

    if target_style == 'usekit':
        return sql, param_dict

    ordered_vars: List[str] = []

    if target_style == 'sqlite':
        def transform(text: str) -> str:
            def repl(m):
                ordered_vars.append(m.group(1))
                return '?'
            return PATTERN_USEKIT.sub(repl, text)

        result_sql = _transform_code_only(sql, transform)
        param_tuple = tuple(param_dict.get(v) for v in ordered_vars)
        return result_sql, param_tuple

    if target_style == 'oracle':
        def transform(text: str) -> str:
            def repl(m):
                ordered_vars.append(m.group(1))
                return f':{m.group(1)}'
            return PATTERN_USEKIT.sub(repl, text)

        result_sql = _transform_code_only(sql, transform)
        return result_sql, param_dict

    if target_style == 'mssql':
        def transform(text: str) -> str:
            def repl(m):
                ordered_vars.append(m.group(1))
                return f'@{m.group(1)}'
            return PATTERN_USEKIT.sub(repl, text)

        result_sql = _transform_code_only(sql, transform)
        return result_sql, param_dict

    if target_style == 'psycopg':
        def transform(text: str) -> str:
            def repl(m):
                ordered_vars.append(m.group(1))
                return f'%({m.group(1)})s'
            return PATTERN_USEKIT.sub(repl, text)

        result_sql = _transform_code_only(sql, transform)
        return result_sql, param_dict

    return sql, param_dict


# ===============================================================================
# Bind Variable Extraction & Validation
# ===============================================================================

def _extract_bind_variables(sql: str, style: str = 'auto') -> List[str]:
    """
    SQL에서 bind variable 이름을 순서대로 추출 (중복 포함).

    문자열/주석 안의 변수는 제외.

    Args:
        sql: SQL string
        style: Source style ('auto', 'usekit', 'oracle', 'mssql', 'psycopg', 'sqlite')
               'auto'면 _detect_sql_style 사용.
               'sqlite'는 positional ?라 이름 없음 → 빈 리스트.

    Returns:
        List of variable names in appearance order (중복 포함)
    """
    if style == 'auto':
        style = _detect_sql_style(sql)

    if style == 'sqlite':
        return []

    # usekit으로 정규화 후 $var 추출
    if style != 'usekit':
        sql = _convert_to_usekit(sql, style)

    vars_found: List[str] = []
    for kind, text in _iter_sql_segments(sql):
        if kind == 'code':
            for m in PATTERN_USEKIT.finditer(text):
                vars_found.append(m.group(1))
    return vars_found


def _validate_bind_params(
    sql: str,
    param_dict: Dict[str, Any],
    style: str = 'auto'
) -> None:
    """
    실행 전 bind variable 누락 검증.

    Args:
        sql: SQL string
        param_dict: Provided parameters
        style: Source style (passed to _extract_bind_variables)

    Raises:
        ValueError: 누락된 변수가 있을 때
    """
    required = _extract_bind_variables(sql, style)
    if not required:
        return

    # 중복 제거, 순서 유지
    seen = set()
    unique_required = []
    for v in required:
        if v not in seen:
            seen.add(v)
            unique_required.append(v)

    missing = [v for v in unique_required if v not in param_dict]
    if missing:
        raise ValueError(
            f"Missing bind variables: {', '.join(missing)} "
            f"(required: {', '.join(unique_required)})"
        )


# ===============================================================================
# Variable Replacement (Direct substitution - use with caution)
# ===============================================================================

def _replace_variables(
    sql: str,
    param_dict: Dict[str, Any],
    quote_strings: bool = True
) -> str:
    """
    Replace $variables with actual values in SQL string.

    WARNING: SQL injection risk. 신뢰 가능한 입력/표시용으로만 사용.
    실행용은 _convert_from_usekit 파라미터 바인딩 사용 권장.

    문자열/주석 안의 $variable은 보호됨.

    Args:
        sql: SQL with $variables
        param_dict: Variable values
        quote_strings: Auto-quote string values

    Returns:
        SQL with values substituted
    """

    def replace_match(match):
        var_name = match.group(1)
        if var_name not in param_dict:
            return match.group(0)
        value = param_dict[var_name]
        return _to_sql_literal(value, quote_strings)

    def transform(text: str) -> str:
        return PATTERN_USEKIT.sub(replace_match, text)

    return _transform_code_only(sql, transform)


def _to_sql_literal(value: Any, quote_strings: bool = True) -> str:
    """
    Convert Python value to SQL literal string.
    """

    if value is None:
        return 'NULL'

    if isinstance(value, bool):
        return '1' if value else '0'

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        if quote_strings:
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        return value

    return str(value)


# ===============================================================================
# Parameter Merging
# ===============================================================================

def _merge_params(*args, **kwargs) -> Dict[str, Any]:
    """
    Merge positional and keyword parameters into unified dict.

    Handles:
    - Positional param strings: "$name: John | $age: 20"
    - Keyword arguments: name="John", age=20
    - Dict unpacking: **{"name": "John", "age": 20}

    Priority: kwargs > positional param strings > earlier args
    """

    result = {}

    for arg in args:
        if isinstance(arg, str):
            parsed = _parse_param_string(arg)
            if parsed:
                result.update(parsed)
        elif isinstance(arg, dict):
            result.update(arg)

    result.update(kwargs)

    return result


# ===============================================================================
# Quote Handling
# ===============================================================================

def _handle_quoted_variables(sql: str) -> str:
    """
    Convert '$variable' (with quotes) to $variable (without quotes).

    This allows users to write:
        WHERE name = '$name'
    Instead of:
        WHERE name = $name

    주의: 이 함수는 문자열 안의 $variable 인용을 의도적으로 벗겨내므로
    _iter_sql_segments 기반 치환과는 별개로 동작. (입력 전처리 용도)

    Args:
        sql: SQL string

    Returns:
        SQL with quoted USEKIT variables unquoted
    """
    sql = re.sub(r"'(\$\w+)'", r'\1', sql)
    sql = re.sub(r'"(\$\w+)"', r'\1', sql)
    return sql


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "SQL_STYLES",
    "_iter_sql_segments",
    "_transform_code_only",
    "_detect_sql_style",
    "_remove_sql_noise",
    "_parse_param_string",
    "_infer_type",
    "_convert_to_usekit",
    "_convert_from_usekit",
    "_extract_bind_variables",
    "_validate_bind_params",
    "_replace_variables",
    "_to_sql_literal",
    "_merge_params",
    "_handle_quoted_variables",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
