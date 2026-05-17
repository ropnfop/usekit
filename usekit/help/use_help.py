# Path: usekit.help.use_help.py
# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Memory-Oriented Software Architecture Documentation
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from typing import Optional


# ===============================================================================
# Language-aware Help Loader
# ===============================================================================

def _get_lang() -> str:
    """
    Read LANG from sys_const.yaml.
    Returns "kr" or "en" (default: "en").
    """
    try:
        from usekit.classes.common.utils.helper_const import get_const
        lang = get_const("LANG")
        return str(lang).lower().strip()
    except Exception:
        return "en"


def _load_help_kr():
    """Load Korean help content."""
    from usekit.help.index.topic.help_part1 import (
        HELP_TOPICS, HELP_OVERVIEW, HELP_ALIAS, HELP_ACTION,
    )
    from usekit.help.index.topic.help_part2 import (
        HELP_PATTERN, HELP_WALK, HELP_KEYDATA,
    )
    from usekit.help.index.topic.help_part3 import (
        HELP_EXAMPLES, HELP_QUICK,
    )
    return {
        "topics": HELP_TOPICS,
        "overview": HELP_OVERVIEW,
        "alias": HELP_ALIAS,
        "action": HELP_ACTION,
        "object": HELP_ALIAS,      # object = alias 내 FORMAT 섹션 참조
        "location": HELP_ALIAS,    # location = alias 내 LOCATION 섹션 참조
        "pattern": HELP_PATTERN,
        "walk": HELP_WALK,
        "keydata": HELP_KEYDATA,
        "examples": HELP_EXAMPLES,
        "quick": HELP_QUICK,
    }


def _load_help_en():
    """Load English help content."""
    from usekit.help.index.topic.help_part1_en import (
        HELP_TOPICS, HELP_OVERVIEW, HELP_ALIAS, HELP_ACTION,
    )
    from usekit.help.index.topic.help_part2_en import (
        HELP_PATTERN, HELP_WALK, HELP_KEYDATA,
    )
    from usekit.help.index.topic.help_part3_en import (
        HELP_EXAMPLES, HELP_QUICK,
    )
    return {
        "topics": HELP_TOPICS,
        "overview": HELP_OVERVIEW,
        "alias": HELP_ALIAS,
        "action": HELP_ACTION,
        "object": HELP_ALIAS,
        "location": HELP_ALIAS,
        "pattern": HELP_PATTERN,
        "walk": HELP_WALK,
        "keydata": HELP_KEYDATA,
        "examples": HELP_EXAMPLES,
        "quick": HELP_QUICK,
    }


# Cache per language
_help_cache = {}

def _get_help_data() -> dict:
    """Get help data for current language (cached)."""
    lang = _get_lang()
    if lang not in _help_cache:
        if lang == "kr":
            _help_cache[lang] = _load_help_kr()
        else:
            _help_cache[lang] = _load_help_en()
    return _help_cache[lang]


# ===============================================================================
# Help Display Function
# ===============================================================================

def show_help(topic: Optional[str] = None) -> None:
    """
    MOSA 도움말 표시 / Show MOSA help
    
    Args:
        topic: 도움말 주제 (없으면 전체 개요)
    """
    data = _get_help_data()
    topics = data["topics"]

    # ----------------------------------------
    # 1) topic 없으면 전체 개요 출력
    # ----------------------------------------
    if topic is None:
        print(data["overview"])
        
        lang = _get_lang()
        if lang == "kr":
            print("\n📚 사용 가능한 도움말 주제:")
        else:
            print("\n📚 Available help topics:")
        print("━" * 74)

        for key, desc in sorted(topics.items()):
            print(f"  u.help('{key:12s}')  # {desc}")
        return

    # ----------------------------------------
    # 2) topic 존재하는 경우
    # ----------------------------------------
    topic = topic.lower().strip()

    if topic in data and topic != "topics":
        print(data[topic])
    else:
        lang = _get_lang()
        if lang == "kr":
            print(f"❌ '{topic}' 주제를 찾을 수 없습니다.\n")
            print("📚 사용 가능한 주제:")
        else:
            print(f"❌ Topic '{topic}' not found.\n")
            print("📚 Available topics:")
        for key, desc in sorted(topics.items()):
            print(f"  • {key:12s} - {desc}")


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "show_help",
]
