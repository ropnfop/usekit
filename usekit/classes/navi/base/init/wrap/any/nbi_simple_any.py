# Path: usekit.classes.navi.base.init.wrap.any.nbi_simple_any.py
# -----------------------------------------------------------------------------------------------
#  Simple Any IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: a : any
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.any.nbi_wrap_any import (
    # path
    path_any_base, path_any_sub, path_any_dir, path_any_now,
    path_any_tmp, path_any_pre, path_any_cache,
    # find
    find_any_base, find_any_sub, find_any_dir, find_any_now,
    find_any_tmp, find_any_pre, find_any_cache,
    # list
    list_any_base, list_any_sub, list_any_dir, list_any_now,
    list_any_tmp, list_any_pre, list_any_cache,
    # get
    get_any_base, get_any_sub, get_any_dir, get_any_now,
    get_any_tmp, get_any_pre, get_any_cache,
    # set
    set_any_base, set_any_sub, set_any_dir, set_any_now,
    set_any_tmp, set_any_pre, set_any_cache,
)


class AnyNaviSimple:
    """
    Ultra-short any navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: a(any)
            loc: b(base) / s(sub) / d(dir) / n(now) / t(tmp) / p(pre) / c(cache)

    Parameter rule (Small → Big):
        - Common logical names:
            name (nm), root (rt), dir_path (dp),      
            keydata (kd), cus (cus),  op (op), cp (cp)
            restore (rst)
                               
        - path / find / list:
            name, mod, dir_path, keydata, cus            

        - get :
            name, mod, dir_path, op, restore

        - set :
            data, name, mod, root, dir_path, op, cp

    All methods delegate to wrap-layer functions via _wrap_simple_format, so positional,
    keyword, and alias parameters are all normalized before calling the underlying function.
    """

    # ------------------------------------------------------------------
    # PATH (pa*)
    # ------------------------------------------------------------------
    @staticmethod
    def pab(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path any base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_any_base)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pas(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path any sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_any_sub)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pad(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path any dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_any_dir)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pan(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path any now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_any_now)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pat(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path any tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_any_tmp)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pap(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path any pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_any_pre)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pac(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path any cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_any_cache)(name, mod, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fa*)
    # ------------------------------------------------------------------
    @staticmethod
    def fab(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find any base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_any_base)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fas(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find any sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_any_sub)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fad(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find any dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_any_dir)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fan(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find any now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_any_now)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fat(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find any tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_any_tmp)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fap(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find any pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_any_pre)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fac(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find any cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_any_cache)(name, mod, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (la*)
    # ------------------------------------------------------------------
    @staticmethod
    def lab(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list any base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_any_base)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def las(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list any sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_any_sub)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lad(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list any dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_any_dir)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lan(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list any now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_any_now)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lat(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list any tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_any_tmp)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lap(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list any pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_any_pre)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lac(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list any cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_any_cache)(name, mod, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (ga*)
    # ------------------------------------------------------------------
    @staticmethod
    def gab(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
        """get any base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_any_base)(name, mod, dir_path, op, restore, **kwargs)

    @staticmethod
    def gas(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
        """get any sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_any_sub)(name, mod, dir_path, op, restore, **kwargs)

    @staticmethod
    def gad(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
        """get any dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_any_dir)(name, mod, dir_path, op, restore, **kwargs)

    @staticmethod
    def gan(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
        """get any now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_any_now)(name, mod, dir_path, op, restore, **kwargs)

    @staticmethod
    def gat(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
        """get any tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_any_tmp)(name, mod, dir_path, op, restore, **kwargs)

    @staticmethod
    def gap(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
        """get any pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_any_pre)(name, mod, dir_path, op, restore, **kwargs)

    @staticmethod
    def gac(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
        """get any cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_any_cache)(name, mod, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sa*)
    # ------------------------------------------------------------------
    @staticmethod
    def sab(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set any base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_any_base)(data, name, mod, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sas(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set any sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_any_sub)(data, name, mod, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sad(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set any dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_any_dir)(data, name, mod, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def san(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set any now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_any_now)(data, name, mod, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sat(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set any tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_any_tmp)(data, name, mod, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sap(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set any pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_any_pre)(data, name, mod, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sac(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set any cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_any_cache)(data, name, mod, root, dir_path, op, cp, **kwargs)

# Singleton-style export
AnyNS = AnyNaviSimple()

__all__ = [
    "AnyNaviSimple",
    "AnyNS",
]