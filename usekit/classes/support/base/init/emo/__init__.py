# usekit.classes.support.base.init.emo
#
# Emotion/knowledge-decomposition subsystem (the `ue` namespace).
# Pure transform modules (data in -> data out): no DB, no timestamp, no
# previous-state, no auto-dispatch. Assembly/feedback lives in the app layer
# (SRSNOTE), keeping usekit's generic build() uncontaminated.
#
# Modules:
#   sbi_emo  - EmoHandler (the `ue` singleton, lazy-wrapped in use_support)
#   hslva    - HSL <-> 5-letter HSLVA code (STEP B)
#   ersdf    - knowledge address code (STEP C)
#   dhsl     - coordinate diff + flow gate (STEP D)
#   meta     - model-output normalization (STEP E)
