# Path: usekit.classes.navi.base.init.wrap.csv.nbi_simple_csv.py
# -----------------------------------------------------------------------------------------------
#  Simple Csv IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: c : csv
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.csv.nbi_wrap_csv import (
    # path
    path_csv_base, path_csv_sub, path_csv_dir, path_csv_now,
    path_csv_tmp, path_csv_pre, path_csv_cache,
    # find
    find_csv_base, find_csv_sub, find_csv_dir, find_csv_now,
    find_csv_tmp, find_csv_pre, find_csv_cache,
    # list
    list_csv_base, list_csv_sub, list_csv_dir, list_csv_now,
    list_csv_tmp, list_csv_pre, list_csv_cache,
    # get
    get_csv_base, get_csv_sub, get_csv_dir, get_csv_now,
    get_csv_tmp, get_csv_pre, get_csv_cache,
    # set
    set_csv_base, set_csv_sub, set_csv_dir, set_csv_now,
    set_csv_tmp, set_csv_pre, set_csv_cache,
)


class CsvNaviSimple:
    """
    Ultra-short csv navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: c(csv)
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
    # PATH (pc*)
    # ------------------------------------------------------------------
    @staticmethod
    def pcb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path csv base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_csv_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pcs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path csv sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_csv_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pcd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path csv dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_csv_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pcn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path csv now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_csv_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pct(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path csv tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_csv_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pcp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path csv pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_csv_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pcc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path csv cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_csv_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fc*)
    # ------------------------------------------------------------------
    @staticmethod
    def fcb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find csv base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_csv_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fcs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find csv sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_csv_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fcd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find csv dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_csv_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fcn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find csv now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_csv_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fct(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find csv tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_csv_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fcp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find csv pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_csv_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fcc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find csv cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_csv_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (lc*)
    # ------------------------------------------------------------------
    @staticmethod
    def lcb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list csv base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_csv_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lcs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list csv sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_csv_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lcd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list csv dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_csv_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lcn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list csv now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_csv_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lct(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list csv tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_csv_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lcp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list csv pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_csv_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lcc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list csv cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_csv_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gc*)
    # ------------------------------------------------------------------
    @staticmethod
    def gcb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get csv base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_csv_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gcs(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get csv sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_csv_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gcd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get csv dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_csv_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gcn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get csv now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_csv_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gct(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get csv tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_csv_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gcp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get csv pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_csv_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gcc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get csv cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_csv_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sc*)
    # ------------------------------------------------------------------
    @staticmethod
    def scb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set csv base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_csv_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def scs(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set csv sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_csv_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def scd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set csv dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_csv_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def scn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set csv now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_csv_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sct(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set csv tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_csv_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def scp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set csv pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_csv_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def scc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set csv cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_csv_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
CsvNS = CsvNaviSimple()

__all__ = [
    "CsvNaviSimple",
    "CsvNS",
]