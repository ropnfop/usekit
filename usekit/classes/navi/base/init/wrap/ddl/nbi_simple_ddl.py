# Path: usekit.classes.navi.base.init.wrap.ddl.nbi_simple_ddl.py
# -----------------------------------------------------------------------------------------------
#  Simple Ddl IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: d : ddl
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.ddl.nbi_wrap_ddl import (
    # path
    path_ddl_base, path_ddl_sub, path_ddl_dir, path_ddl_now,
    path_ddl_tmp, path_ddl_pre, path_ddl_cache,
    # find
    find_ddl_base, find_ddl_sub, find_ddl_dir, find_ddl_now,
    find_ddl_tmp, find_ddl_pre, find_ddl_cache,
    # list
    list_ddl_base, list_ddl_sub, list_ddl_dir, list_ddl_now,
    list_ddl_tmp, list_ddl_pre, list_ddl_cache,
    # get
    get_ddl_base, get_ddl_sub, get_ddl_dir, get_ddl_now,
    get_ddl_tmp, get_ddl_pre, get_ddl_cache,
    # set
    set_ddl_base, set_ddl_sub, set_ddl_dir, set_ddl_now,
    set_ddl_tmp, set_ddl_pre, set_ddl_cache,
)


class DdlNaviSimple:
    """
    Ultra-short ddl navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: d(ddl)
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
    # PATH (pd*)
    # ------------------------------------------------------------------
    @staticmethod
    def pdb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path ddl base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pds(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path ddl sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pdd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path ddl dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pdn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path ddl now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pdt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path ddl tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pdp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path ddl pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pdc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path ddl cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fd*)
    # ------------------------------------------------------------------
    @staticmethod
    def fdb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find ddl base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fds(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find ddl sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fdd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find ddl dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fdn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find ddl now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fdt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find ddl tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fdp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find ddl pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fdc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find ddl cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (ld*)
    # ------------------------------------------------------------------
    @staticmethod
    def ldb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list ddl base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lds(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list ddl sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ldd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list ddl dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ldn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list ddl now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ldt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list ddl tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ldp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list ddl pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ldc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list ddl cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gd*)
    # ------------------------------------------------------------------
    @staticmethod
    def gdb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get ddl base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_ddl_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gds(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get ddl sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_ddl_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gdd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get ddl dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_ddl_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gdn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get ddl now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_ddl_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gdt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get ddl tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_ddl_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gdp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get ddl pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_ddl_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gdc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get ddl cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_ddl_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sd*)
    # ------------------------------------------------------------------
    @staticmethod
    def sdb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set ddl base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_ddl_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sds(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set ddl sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_ddl_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sdd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set ddl dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_ddl_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sdn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set ddl now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_ddl_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sdt(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set ddl tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_ddl_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sdp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set ddl pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_ddl_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sdc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set ddl cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_ddl_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
DdlNS = DdlNaviSimple()

__all__ = [
    "DdlNaviSimple",
    "DdlNS",
]