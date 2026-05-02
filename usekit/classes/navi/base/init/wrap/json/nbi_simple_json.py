# Path: usekit.classes.navi.base.init.wrap.json.nbi_simple_json.py
# -----------------------------------------------------------------------------------------------
#  Simple Json IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: j : json
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.json.nbi_wrap_json import (
    # path
    path_json_base, path_json_sub, path_json_dir, path_json_now,
    path_json_tmp, path_json_pre, path_json_cache,
    # find
    find_json_base, find_json_sub, find_json_dir, find_json_now,
    find_json_tmp, find_json_pre, find_json_cache,
    # list
    list_json_base, list_json_sub, list_json_dir, list_json_now,
    list_json_tmp, list_json_pre, list_json_cache,
    # get
    get_json_base, get_json_sub, get_json_dir, get_json_now,
    get_json_tmp, get_json_pre, get_json_cache,
    # set
    set_json_base, set_json_sub, set_json_dir, set_json_now,
    set_json_tmp, set_json_pre, set_json_cache,
)


class JsonNaviSimple:
    """
    Ultra-short json navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: j(json)
            loc: b(base) / s(sub) / d(dir) / n(now) / t(tmp) / p(pre) / c(cache)

    Parameter rule (Small → Big):
        - Common logical names:
            name      (nm)
            root      (rt)
            dir_path  (dp)
            keydata   (kd)
            cus       (cs)
            op        (op)
            restore   (rs)
            cp        (cp)

        - path:
            name, dir_path, keydata, cus

        - find / list:
            data, name, dir_path, keydata, cus

        - get (wrap: get_json_*):
            name, dir_path, op, restore

        - set (wrap: set_json_*):
            data, name, root, dir_path, op, cp

    All methods delegate to wrap-layer functions via _wrap_simple_format, so positional,
    keyword, and alias parameters are all normalized before calling the underlying function.
    """

    # ------------------------------------------------------------------
    # PATH (pj*)
    # ------------------------------------------------------------------
    @staticmethod
    def pjb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path json base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_json_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pjs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path json sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_json_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pjd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path json dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_json_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pjn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path json now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_json_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pjt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path json tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_json_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pjp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path json pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_json_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pjc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path json cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_json_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fj*)
    # ------------------------------------------------------------------
    @staticmethod
    def fjb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find json base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_json_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fjs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find json sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_json_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fjd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find json dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_json_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fjn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find json now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_json_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fjt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find json tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_json_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fjp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find json pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_json_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fjc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find json cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_json_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (lj*)
    # ------------------------------------------------------------------
    @staticmethod
    def ljb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list json base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_json_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ljs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list json sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_json_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ljd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list json dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_json_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ljn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list json now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_json_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ljt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list json tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_json_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ljp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list json pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_json_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ljc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list json cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_json_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gj*)
    # ------------------------------------------------------------------
    @staticmethod
    def gjb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get json base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_json_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gjs(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get json sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_json_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gjd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get json dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_json_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gjn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get json now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_json_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gjt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get json tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_json_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gjp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get json pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_json_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gjc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get json cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_json_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sj*)
    # ------------------------------------------------------------------
    @staticmethod
    def sjb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set json base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_json_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sjs(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set json sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_json_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sjd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set json dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_json_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sjn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set json now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_json_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sjt(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set json tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_json_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sjp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set json pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_json_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sjc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set json cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_json_cache)(data, name, root, dir_path, op, cp, **kwargs)


# Singleton-style export
JsonNS = JsonNaviSimple()

__all__ = [
    "JsonNaviSimple",
    "JsonNS",
]