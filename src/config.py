COLOR_PALETTE = [
    "D50000", "E67C73", "F4511E", "F6BF26",
    "33B679", "0B8043", "039BE5", "3F51B5",
    "7986CB", "8E24AA", "616161", "A79B8E"
]

DAYS_MAP = {
    "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
    "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"
}

DAYS_ABBR_LIST = list(DAYS_MAP.keys())

DAY_STR_TO_INT = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6
}

DAY_INT_TO_STR = {v: k for k, v in DAY_STR_TO_INT.items()}

AVAILABLE_LANGUAGES = {
    "en": "English",
    "tr": "Türkçe",
}
