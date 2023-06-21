import toolz as to

PALETTE = {
    "grey": "#4c545e",
    "white": "#ffffff",
    "anti-flash-white":"#f4f4f5",
    "alabaster": "#e5e0d7",
    "melon": "#f1a496",
    "french-grey": "#aeb1cb",
    "1-alice-blue": "#b1cfec", # "#dbe9f6",
    "2-light-sky-blue": "#94caf5",
    "3-air-blue": "#63a4cb",
    "4-cerulean": "#277ca6",
}

ORDINAL = list(to.keyfilter(
    lambda x: x in [
        "melon",
        "french-grey",
        "1-alice-blue",
        "2-light-sky-blue",
        "3-air-blue",
        "4-cerulean",
    ], PALETTE
).values())
