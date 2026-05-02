# Path: usekit.classes.navi.base.init.wrap.md.nbi_simple_md.py
# -----------------------------------------------------------------------------------------------
#  Simple Md IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: m : md
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.md.nbi_wrap_md import (
    # path
    path_md_base, path_md_sub, path_md_dir, path_md_now,
    path_md_tmp, path_md_pre, path_md_cache,
    # find
    find_md_base, find_md_sub, find_md_dir, find_md_now,
    find_md_tmp, find_md_pre, find_md_cache,
    # list
    list_md_base, list_md_sub, list_md_dir, list_md_now,
    list_md_tmp, list_md_pre, list_md_cache,
    # get
    get_md_base, get_md_sub, get_md_dir, get_md_now,
    get_md_tmp, get_md_pre, get_md_cache,
    # set
    set_md_base, set_md_sub, set_md_dir, set_md_now,
    set_md_tmp, set_md_pre, set_md_cache,
)


class MdNaviSimple:
    """
    Ultra-short md navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: m(md)
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
    # PATH (pm*)
    # ------------------------------------------------------------------
    @staticmethod
    def pmb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path md base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_md_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pms(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path md sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_md_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pmd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path md dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_md_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pmn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path md now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_md_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pmt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path md tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_md_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path md pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_md_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pmc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path md cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_md_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fm*)
    # ------------------------------------------------------------------
    @staticmethod
    def fmb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find md base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_md_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fms(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find md sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_md_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fmd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find md dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_md_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fmn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find md now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_md_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fmt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find md tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_md_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find md pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_md_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fmc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find md cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_md_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (lm*)
    # ------------------------------------------------------------------
    @staticmethod
    def lmb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list md base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_md_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lms(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list md sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_md_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lmd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list md dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_md_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lmn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list md now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_md_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lmt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list md tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_md_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list md pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_md_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lmc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list md cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_md_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gm*)
    # ------------------------------------------------------------------
    @staticmethod
    def gmb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get md base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_md_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gms(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get md sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_md_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gmd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get md dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_md_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gmn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get md now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_md_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gmt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get md tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_md_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gmp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get md pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_md_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gmc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get md cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_md_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sm*)
    # ------------------------------------------------------------------
    @staticmethod
    def smb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set md base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_md_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sms(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set md sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_md_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def smd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set md dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_md_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def smn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set md now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_md_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def smt(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set md tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_md_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def smp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set md pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_md_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def smc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set md cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_md_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
MdNS = MdNaviSimple()

__all__ = [
    "MdNaviSimple",
    "MdNS",
]