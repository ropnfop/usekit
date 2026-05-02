# Path: usekit.classes.navi.base.init.wrap.pyp.nbi_simple_pyp.py
# -----------------------------------------------------------------------------------------------
#  Simple Pyp IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: p : pyp
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.pyp.nbi_wrap_pyp import (
    # path
    path_pyp_base, path_pyp_sub, path_pyp_dir, path_pyp_now,
    path_pyp_tmp, path_pyp_pre, path_pyp_cache,
    # find
    find_pyp_base, find_pyp_sub, find_pyp_dir, find_pyp_now,
    find_pyp_tmp, find_pyp_pre, find_pyp_cache,
    # list
    list_pyp_base, list_pyp_sub, list_pyp_dir, list_pyp_now,
    list_pyp_tmp, list_pyp_pre, list_pyp_cache,
    # get
    get_pyp_base, get_pyp_sub, get_pyp_dir, get_pyp_now,
    get_pyp_tmp, get_pyp_pre, get_pyp_cache,
    # set
    set_pyp_base, set_pyp_sub, set_pyp_dir, set_pyp_now,
    set_pyp_tmp, set_pyp_pre, set_pyp_cache,
)


class PypNaviSimple:
    """
    Ultra-short pyp navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: p(pyp)
            loc: b(base) / s(sub) / d(dir) / n(now) / t(tmp) / p(pre) / c(cache)

    Parameter rule (Small → Big):
        - Common logical names:
            name (nm), root (rt), dir_path (dp),      
            keydata (kd), cus (cus),  op (op), cp (cp)
            restore (rst)
                               
        - path / find / list:
            name, dir_path, keydata, cus            

        - get :
            name, dir_path, op, restore

        - set :
            data, name, root, dir_path, op, cp

    All methods delegate to wrap-layer functions via _wrap_simple_format, so positional,
    keyword, and alias parameters are all normalized before calling the underlying function.
    """

    # ------------------------------------------------------------------
    # PATH (pp*)
    # ------------------------------------------------------------------
    @staticmethod
    def ppb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path pyp base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pps(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path pyp sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ppd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path pyp dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ppn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path pyp now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ppt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path pyp tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ppp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path pyp pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ppc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path pyp cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fp*)
    # ------------------------------------------------------------------
    @staticmethod
    def fpb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find pyp base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fps(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find pyp sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fpd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find pyp dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fpn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find pyp now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fpt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find pyp tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fpp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find pyp pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fpc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find pyp cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (lp*)
    # ------------------------------------------------------------------
    @staticmethod
    def lpb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list pyp base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lps(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list pyp sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lpd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list pyp dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lpn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list pyp now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lpt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list pyp tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lpp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list pyp pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lpc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list pyp cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gp*)
    # ------------------------------------------------------------------
    @staticmethod
    def gpb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get pyp base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_pyp_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gps(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get pyp sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_pyp_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gpd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get pyp dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_pyp_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gpn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get pyp now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_pyp_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gpt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get pyp tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_pyp_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gpp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get pyp pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_pyp_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gpc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get pyp cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_pyp_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sp*)
    # ------------------------------------------------------------------
    @staticmethod
    def spb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set pyp base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_pyp_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sps(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set pyp sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_pyp_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def spd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set pyp dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_pyp_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def spn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set pyp now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_pyp_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def spt(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set pyp tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_pyp_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def spp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set pyp pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_pyp_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def spc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set pyp cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_pyp_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
PypNS = PypNaviSimple()

__all__ = [
    "PypNaviSimple",
    "PypNS",
]