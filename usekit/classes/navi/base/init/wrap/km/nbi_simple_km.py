# Path: usekit.classes.navi.base.init.wrap.km.nbi_simple_km.py
# -----------------------------------------------------------------------------------------------
#  Simple Km IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: k : km
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.km.nbi_wrap_km import (
    # path
    path_km_base, path_km_sub, path_km_dir, path_km_now,
    path_km_tmp, path_km_pre, path_km_cache,
    # find
    find_km_base, find_km_sub, find_km_dir, find_km_now,
    find_km_tmp, find_km_pre, find_km_cache,
    # list
    list_km_base, list_km_sub, list_km_dir, list_km_now,
    list_km_tmp, list_km_pre, list_km_cache,
    # get
    get_km_base, get_km_sub, get_km_dir, get_km_now,
    get_km_tmp, get_km_pre, get_km_cache,
    # set
    set_km_base, set_km_sub, set_km_dir, set_km_now,
    set_km_tmp, set_km_pre, set_km_cache,
)


class KmNaviSimple:
    """
    Ultra-short km navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: k(km)
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
    # PATH (pk*)
    # ------------------------------------------------------------------
    @staticmethod
    def pkb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path km base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_km_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pks(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path km sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_km_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pkd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path km dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_km_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pkn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path km now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_km_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pkt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path km tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_km_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pkp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path km pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_km_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pkc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path km cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_km_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fk*)
    # ------------------------------------------------------------------
    @staticmethod
    def fkb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find km base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_km_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fks(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find km sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_km_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fkd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find km dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_km_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fkn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find km now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_km_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fkt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find km tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_km_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fkp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find km pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_km_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fkc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find km cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_km_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (lk*)
    # ------------------------------------------------------------------
    @staticmethod
    def lkb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list km base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_km_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lks(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list km sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_km_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lkd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list km dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_km_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lkn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list km now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_km_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lkt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list km tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_km_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lkp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list km pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_km_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lkc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list km cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_km_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gk*)
    # ------------------------------------------------------------------
    @staticmethod
    def gkb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get km base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_km_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gks(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get km sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_km_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gkd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get km dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_km_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gkn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get km now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_km_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gkt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get km tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_km_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gkp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get km pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_km_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gkc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get km cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_km_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sk*)
    # ------------------------------------------------------------------
    @staticmethod
    def skb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set km base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_km_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sks(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set km sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_km_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def skd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set km dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_km_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def skn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set km now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_km_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def skt(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set km tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_km_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def skp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set km pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_km_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def skc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set km cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_km_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
KmNS = KmNaviSimple()

__all__ = [
    "KmNaviSimple",
    "KmNS",
]