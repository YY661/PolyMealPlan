
# Prompts the user for macros + dietary tags, then runs the meal planner

import mealplan_yy as planner
import build_menu_data_tests as tests


# Ask the user for a number
def ask_float(prompt: str) -> float:
    while True:
        s = input(prompt).strip()
        try:
            return float(s)
        except ValueError:
            print("Please enter a valid number.")


# Ask the user for dietary tags (comma-separated) and validate them against TAG_COLS.
def ask_tags(prompt: str) -> list[str]:
    raw = input(prompt).strip()
    if not raw:
        return []
    tags = [t.strip().upper() for t in raw.split(",") if t.strip()]
    for t in tags:
        if t not in planner.TAG_COLS:
            print(f"Unknown tag: {t}. Valid tags are: {', '.join(planner.TAG_COLS)}")
            return ask_tags(prompt)
    return tags


# Collect user inputs and run the planner using reduced test data
def main():
    print("Meal Planner")

    calories = ask_float("Enter your daily calories: ")
    fat = ask_float("Enter your daily fat (grams): ")
    carbs = ask_float("Enter your daily carbs (grams): ")
    protein = ask_float("Enter your daily protein (grams): ")

    tags = ask_tags("Enter dietary tags (comma-separated: VG,V,AG,HALAL) or press Enter for none: ")

    target = (calories, fat, carbs, protein)

    # Convert reduced_data into the record format
    # set period_name="Every Day" so every item can be used for Breakfast/Lunch/Dinner
    records = []
    for item in tests.reduced_data:
        meta = {
            "date": "TEST",
            "restaurant_name": item.restaurant,
            "period_name": "Every Day",
            "menu_section": "TEST",
            "item_name": item.item_name,
            "tags": item.diet_restrictions,
        }
        records.append((item, meta))

    pools = planner.make_meal_pools(records)


    plan = planner.find_best_plan(
        pools,
        target,
        tags,
        trials=60000,
        seed=None,
        meal_split=(0.30, 0.35, 0.35),
        calorie_tolerance=150.0,
        allow_repeats=True,
    )

    planner.print_plan(plan, target, "TEST", tags)



if __name__ == "__main__":
    main()