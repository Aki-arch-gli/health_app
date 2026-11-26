from modules.meal_print import build_meal_card


def export_pdf(menu, shopping=()):
    sections = [
        (name, [menu.get(name, "")])
        for name in ("朝食", "昼食", "夕食")
    ]
    return build_meal_card("本日の献立", sections, shopping)
