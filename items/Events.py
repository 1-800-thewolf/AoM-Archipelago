all_events = set()


def event(name: str):
    all_events.add(name)
    return name


class Event:
    victory = event("Victory")
