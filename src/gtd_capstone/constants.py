from __future__ import annotations

CORE_COLUMNS = [
    "eventid",
    "iyear",
    "imonth",
    "iday",
    "country_txt",
    "region_txt",
    "provstate",
    "city",
    "latitude",
    "longitude",
    "summary",
    "success",
    "suicide",
    "attacktype1_txt",
    "targtype1_txt",
    "weaptype1_txt",
    "gname",
    "motive",
    "nkill",
    "nwound",
    "property",
    "ishostkid",
    "dbsource",
]

CATEGORICAL_COLUMNS = [
    "country_txt",
    "region_txt",
    "provstate",
    "city",
    "attacktype1_txt",
    "targtype1_txt",
    "weaptype1_txt",
    "gname",
]

NUMERIC_COLUMNS = [
    "iyear",
    "imonth",
    "iday",
    "latitude",
    "longitude",
    "success",
    "suicide",
    "nkill",
    "nwound",
    "property",
    "ishostkid",
]

UNSAFE_CHAT_TERMS = [
    "how to attack",
    "best target",
    "target selection",
    "make a bomb",
    "build a bomb",
    "weaponize",
    "evade police",
    "avoid detection",
    "maximize casualties",
    "plan an attack",
    "terrorist tactics",
]

