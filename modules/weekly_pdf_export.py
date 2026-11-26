from modules.meal_print import build_meal_card


def export_weekly_pdf(week, shopping=()):
    sections = [
        (day, [f"{meal}　{menu.get(meal, '')}" for meal in ("朝食", "昼食", "夕食")])
        for day, menu in week.items()
    ]
    return build_meal_card("1週間の献立", sections, shopping)
