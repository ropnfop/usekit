# Path: usekit.classes.navi.base.init.wrap.txt.nbi_simple_txt.py
# -----------------------------------------------------------------------------------------------
#  Simple Txt IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: t : txt
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.txt.nbi_wrap_txt import (
    # path
    path_txt_base, path_txt_sub, path_txt_dir, path_txt_now,
    path_txt_tmp, path_txt_pre, path_txt_cache,
    # find
    find_txt_base, find_txt_sub, find_txt_dir, find_txt_now,
    find_txt_tmp, find_txt_pre, find_txt_cache,
    # list
    list_txt_base, list_txt_sub, list_txt_dir, list_txt_now,
    list_txt_tmp, list_txt_pre, list_txt_cache,
    # get
    get_txt_base, get_txt_sub, get_txt_dir, get_txt_now,
    get_txt_tmp, get_txt_pre, get_txt_cache,
    # set
    set_txt_base, set_txt_sub, set_txt_dir, set_txt_now,
    set_txt_tmp, set_txt_pre, set_txt_cache,
)


class TxtNaviSimple:
    """
    Ultra-short txt navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: t(txt)
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
    # PATH (pt*)
    # ------------------------------------------------------------------
    @staticmethod
    def ptb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path txt base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_txt_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pts(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path txt sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_txt_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ptd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path txt dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_txt_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ptn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path txt now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_txt_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ptt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path txt tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_txt_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ptp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path txt pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_txt_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ptc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path txt cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_txt_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (ft*)
    # ------------------------------------------------------------------
    @staticmethod
    def ftb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find txt base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_txt_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fts(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find txt sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_txt_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ftd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find txt dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_txt_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ftn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find txt now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_txt_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ftt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find txt tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_txt_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ftp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find txt pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_txt_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ftc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find txt cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_txt_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (lt*)
    # ------------------------------------------------------------------
    @staticmethod
    def ltb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list txt base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_txt_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lts(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list txt sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_txt_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ltd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list txt dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_txt_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ltn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list txt now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_txt_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ltt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list txt tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_txt_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ltp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list txt pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_txt_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ltc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list txt cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_txt_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gt*)
    # ------------------------------------------------------------------
    @staticmethod
    def gtb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get txt base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_txt_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gts(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get txt sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_txt_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gtd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get txt dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_txt_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gtn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get txt now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_txt_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gtt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get txt tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_txt_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gtp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get txt pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_txt_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gtc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get txt cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_txt_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (st*)
    # ------------------------------------------------------------------
    @staticmethod
    def stb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set txt base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_txt_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sts(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set txt sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_txt_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def std(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set txt dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_txt_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def stn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set txt now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_txt_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def stt(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set txt tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_txt_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def stp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set txt pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_txt_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def stc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set txt cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_txt_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
TxtNS = TxtNaviSimple()

__all__ = [
    "TxtNaviSimple",
    "TxtNS",
]