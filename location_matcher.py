from difflib import get_close_matches

POPULAR_LOCATIONS = [
    # Алматы
    "Парк 1-президента", "Ботанический сад", "Арбат", "Кок Тобе", "Центральный стадион", "Медеу",
    # Астана
    "Центральный парк", "Триатлон-парк", "Жетысу", "EXPO", "Байтерек", "Арбат Астаны"
]

def normalize_location(name: str) -> str:
    name = name.lower().strip()
    name = name.replace("ё", "е")
    return name

def suggest_location(input_text: str) -> str | None:
    input_norm = normalize_location(input_text)
    matches = get_close_matches(input_norm, [normalize_location(loc) for loc in POPULAR_LOCATIONS], n=1, cutoff=0.6)
    if matches:
        # Находим оригинальное имя по нормализованному
        for loc in POPULAR_LOCATIONS:
            if normalize_location(loc) == matches[0]:
                return loc
    return None
