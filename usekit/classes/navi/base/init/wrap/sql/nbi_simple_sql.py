# Path: usekit.classes.navi.base.init.wrap.sql.nbi_simple_sql.py
# -----------------------------------------------------------------------------------------------
#  Simple Sql IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: s : sql
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.sql.nbi_wrap_sql import (
    # path
    path_sql_base, path_sql_sub, path_sql_dir, path_sql_now,
    path_sql_tmp, path_sql_pre, path_sql_cache,
    # find
    find_sql_base, find_sql_sub, find_sql_dir, find_sql_now,
    find_sql_tmp, find_sql_pre, find_sql_cache,
    # list
    list_sql_base, list_sql_sub, list_sql_dir, list_sql_now,
    list_sql_tmp, list_sql_pre, list_sql_cache,
    # get
    get_sql_base, get_sql_sub, get_sql_dir, get_sql_now,
    get_sql_tmp, get_sql_pre, get_sql_cache,
    # set
    set_sql_base, set_sql_sub, set_sql_dir, set_sql_now,
    set_sql_tmp, set_sql_pre, set_sql_cache,
)


class SqlNaviSimple:
    """
    Ultra-short sql navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: s(sql)
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
    # PATH (ps*)
    # ------------------------------------------------------------------
    @staticmethod
    def psb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path sql base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path sql sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def psd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path sql dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def psn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path sql now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pst(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path sql tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def psp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path sql pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def psc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path sql cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_sql_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fs*)
    # ------------------------------------------------------------------
    @staticmethod
    def fsb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find sql base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find sql sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fsd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find sql dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fsn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find sql now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fst(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find sql tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fsp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find sql pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fsc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find sql cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_sql_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (ls*)
    # ------------------------------------------------------------------
    @staticmethod
    def lsb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list sql base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list sql sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lsd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list sql dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lsn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list sql now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lst(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list sql tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lsp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list sql pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lsc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list sql cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_sql_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gs*)
    # ------------------------------------------------------------------
    @staticmethod
    def gsb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get sql base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_sql_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gss(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get sql sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_sql_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gsd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get sql dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_sql_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gsn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get sql now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_sql_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gst(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get sql tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_sql_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gsp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get sql pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_sql_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gsc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get sql cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_sql_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (ss*)
    # ------------------------------------------------------------------
    @staticmethod
    def ssb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set sql base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_sql_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sss(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set sql sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_sql_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def ssd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set sql dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_sql_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def ssn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set sql now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_sql_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sst(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set sql tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_sql_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def ssp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set sql pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_sql_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def ssc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set sql cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_sql_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
SqlNS = SqlNaviSimple()

__all__ = [
    "SqlNaviSimple",
    "SqlNS",
]