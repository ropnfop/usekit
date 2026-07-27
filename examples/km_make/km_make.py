from usekit import u, uw
from usekit.classes.common.utils.helper_km_system import clear_km_cache

# km 파일을 usekit
km = r'''# _jb.km
@test    = @JB.test
@card    = @JB.srs.cards
@session = @JB.ai.session
@config  = @JB.ai.config
@ai_data = [@session | @config]
'''
u.wjb(km, "_jb", ext=".km", wrap=False)
clear_km_cache()

# alias
uw.p(u.rjb("@card.math_001"))
uw.p(u.rjb("@session.today"))
uw.p(u.rjb("@config.groq"))