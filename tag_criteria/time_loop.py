# -*- coding: utf-8 -*-
"""#time_loop - time loops. No generic phrases like 'again and again'."""
import re

import _common

TAG = "time_loop"

# Explicit time-loop phrases only. Forbidden: снова и снова, один и тот же день, опять тот же день.
PATTERNS = [
    r"временная петля", r"временной петле", r"в петле времени", r"попал в петлю",
    r"зациклен", r"зациклился", r"зацикливание", r"застрял в цикле",
    r"повторяет один день", r"один день повторяется", r"день сурка",
    r"повторяется один и тот же", r"цикл повторяется", r"вырваться из петли",
    r"выйти из петли", r"time loop", r"живет один день заново",
    r"проживает один день снова",
]
PAT = _common.compile_any(PATTERNS)


def check(text):
    return bool(text and PAT.search(text))
