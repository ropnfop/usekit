# Path: usekit.classes.navi.base.init.wrap.yaml.nbi_simple_yaml.py
# -----------------------------------------------------------------------------------------------
#  Simple Yaml IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.2: Aligned simple getter/setter signatures with wrap layer (Small → Big)
# -----------------------------------------------------------------------------------------------
#    act: p / f / l / g / s : path / find / list / get / set
#    obj: y : yaml
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
from usekit.classes.navi.base.init.wrap.yaml.nbi_wrap_yaml import (
    # path
    path_yaml_base, path_yaml_sub, path_yaml_dir, path_yaml_now,
    path_yaml_tmp, path_yaml_pre, path_yaml_cache,
    # find
    find_yaml_base, find_yaml_sub, find_yaml_dir, find_yaml_now,
    find_yaml_tmp, find_yaml_pre, find_yaml_cache,
    # list
    list_yaml_base, list_yaml_sub, list_yaml_dir, list_yaml_now,
    list_yaml_tmp, list_yaml_pre, list_yaml_cache,
    # get
    get_yaml_base, get_yaml_sub, get_yaml_dir, get_yaml_now,
    get_yaml_tmp, get_yaml_pre, get_yaml_cache,
    # set
    set_yaml_base, set_yaml_sub, set_yaml_dir, set_yaml_now,
    set_yaml_tmp, set_yaml_pre, set_yaml_cache,
)


class YamlNaviSimple:
    """
    Ultra-short yaml navigation wrapper with full alias support.

    Naming rule:
        act.obj.loc  →  3 letters
            act: p(path) / f(find) / l(list) / g(get) / s(set)
            obj: y(yaml)
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
    # PATH (py*)
    # ------------------------------------------------------------------
    @staticmethod
    def pyb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path yaml base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_yaml_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pys(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path yaml sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_yaml_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pyd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path yaml dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_yaml_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pyn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path yaml now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_yaml_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pyt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path yaml tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_yaml_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pyp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path yaml pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_yaml_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def pyc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """path yaml cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(path_yaml_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # FIND (fy*)
    # ------------------------------------------------------------------
    @staticmethod
    def fyb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find yaml base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_yaml_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fys(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find yaml sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_yaml_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fyd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find yaml dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_yaml_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fyn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find yaml now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_yaml_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fyt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find yaml tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_yaml_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fyp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find yaml pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_yaml_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def fyc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """find yaml cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(find_yaml_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # LIST (ly*)
    # ------------------------------------------------------------------
    @staticmethod
    def lyb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list yaml base : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_yaml_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lys(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list yaml sub : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_yaml_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lyd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list yaml dir : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_yaml_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lyn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list yaml now : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_yaml_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lyt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list yaml tmp : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_yaml_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lyp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list yaml pre : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_yaml_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def lyc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """list yaml cache : supports positional, keyword, and alias (nm, dp, kd, cs)"""
        return _wrap_simple_format(list_yaml_cache)(name, dir_path, keydata, cus, **kwargs)

    # ------------------------------------------------------------------
    # GET (gy*)
    # ------------------------------------------------------------------
    @staticmethod
    def gyb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get yaml base : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_yaml_base)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gys(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get yaml sub : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_yaml_sub)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gyd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get yaml dir : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_yaml_dir)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gyn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get yaml now : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_yaml_now)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gyt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get yaml tmp : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_yaml_tmp)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gyp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get yaml pre : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_yaml_pre)(name, dir_path, op, restore, **kwargs)

    @staticmethod
    def gyc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """get yaml cache : supports positional, keyword, and alias (nm, dp, op, rs)"""
        return _wrap_simple_format(get_yaml_cache)(name, dir_path, op, restore, **kwargs)

    # ------------------------------------------------------------------
    # SET (sy*)
    # ------------------------------------------------------------------
    @staticmethod
    def syb(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set yaml base : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_yaml_base)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def sys(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set yaml sub : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_yaml_sub)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def syd(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set yaml dir : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_yaml_dir)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def syn(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set yaml now : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_yaml_now)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def syt(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set yaml tmp : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_yaml_tmp)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def syp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set yaml pre : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_yaml_pre)(data, name, root, dir_path, op, cp, **kwargs)

    @staticmethod
    def syc(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
        """set yaml cache : supports positional, keyword, and alias (nm, rt, dp, op, cp)"""
        return _wrap_simple_format(set_yaml_cache)(data, name, root, dir_path, op, cp, **kwargs)

# Singleton-style export
YamlNS = YamlNaviSimple()

__all__ = [
    "YamlNaviSimple",
    "YamlNS",
]