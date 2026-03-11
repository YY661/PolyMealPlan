import argparse
import csv
import random

from food_item import FoodItem

TAG_COLS = ("VG", "V", "AG", "HALAL")
MEALS = ("Breakfast", "Lunch", "Dinner")
EVERYDAY = {"Every Day", "Everyday"}


# Convert a CSV string value into a float (or None if missing).
def to_float(value):
    if value is None:
        return None
    s = value.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# get dietary tag codes from a CSV row
def row_tags(row):
    return [t for t in TAG_COLS if row.get(t, "").strip() == "1"]


# Checks if food contains ALL required tags.
def includes_all_tags(item_tags, required_tags):
    return set(required_tags).issubset(set(item_tags))


# Read the CSV and return all rows as dictionaries.
def read_csv_rows(csv_path):
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# Build FoodItem objects and keep the original row data (NO date filtering).
def load_records(csv_path, date, required_tags, disallow_repeats):
    rows = read_csv_rows(csv_path)
    if not rows:
        raise SystemExit("CSV has no rows")

    records = []
    for r in rows:
        tags = row_tags(r)
        if not includes_all_tags(tags, required_tags):
            continue

        item = FoodItem(
            (r.get("item_name") or "").strip(),
            (r.get("restaurant_name") or "").strip(),
            to_float(r.get("calories")),
            to_float(r.get("total_fat_g")),
            to_float(r.get("total_carbs_g")),
            to_float(r.get("protein_g")),
            tags,
        )
        records.append((item, {**r, "tags": tags}))

    if not records:
        raise SystemExit("No rows found after filtering by tags")

    return records, "ALL"


# Split records into meal pools using period_name (breakfast, lunch dinner, and every Day items go into all meals).
def make_meal_pools(records):
    pools = {m: [] for m in MEALS}
    for item, meta in records:
        period = (meta.get("period_name") or "").strip()
        if period in EVERYDAY:
            for m in MEALS:
                pools[m].append((item, meta))
        elif period in pools:
            pools[period].append((item, meta))
    return pools


# Add up calories/fat/carbs/protein for a list of records.
def sum_macros(recs):
    cal = fat = carbs = prot = 0.0
    for item, _ in recs:
        if item.calories is None or item.fat is None or item.carbs is None or item.protein is None:
            continue
        cal += float(item.calories)
        fat += float(item.fat)
        carbs += float(item.carbs)
        prot += float(item.protein)
    return (cal, fat, carbs, prot)


# Score a macro total vs the target.
def score(totals, target, calorie_tolerance):
    cal, fat, carbs, prot = totals
    tcal, tfat, tcarb, tprot = target
    err = 3.0 * abs(cal - tcal) + 1.5 * abs(fat - tfat) + 1.0 * abs(carbs - tcarb) + 4.0 * abs(prot - tprot)
    if calorie_tolerance > 0:
        low, high = tcal - calorie_tolerance, tcal + calorie_tolerance
        if cal < low:
            err += (low - cal) * 5.0
        elif cal > high:
            err += (cal - high) * 8.0
    return err


# Randomly search for 3 items per meal that best matches the user's daily macro target.
def find_best_plan(pools, target, required_tags, trials, seed, meal_split, calorie_tolerance, allow_repeats):
    rng = random.Random(seed)

    def complete(item):
        return item.calories is not None and item.fat is not None and item.carbs is not None and item.protein is not None

    filtered = {}
    for meal in MEALS:
        filtered[meal] = [rec for rec in pools[meal] if complete(rec[0]) and includes_all_tags(rec[0].diet_restrictions, required_tags)]
        if len(filtered[meal]) < 3:
            raise SystemExit(f"Not enough candidates for {meal}. Need 3, found {len(filtered[meal])}.")

    s = sum(meal_split)
    b, l, d = (meal_split[0] / s, meal_split[1] / s, meal_split[2] / s)
    meal_targets = {
        "Breakfast": (target[0] * b, target[1] * b, target[2] * b, target[3] * b),
        "Lunch": (target[0] * l, target[1] * l, target[2] * l, target[3] * l),
        "Dinner": (target[0] * d, target[1] * d, target[2] * d, target[3] * d),
    }

    def rec_key(rec):
        meta = rec[1]
        return (
            meta.get("restaurant_name", ""),
            meta.get("period_name", ""),
            meta.get("menu_section", ""),
            meta.get("item_name", ""),
        )

    best_plan, best_err = None, float("inf")

    for _ in range(max(1, trials)):
        if allow_repeats:
            plan = {m: rng.sample(filtered[m], 3) for m in MEALS}
        else:
            used = set()
            b_plan = rng.sample(filtered["Breakfast"], 3)
            used |= {rec_key(r) for r in b_plan}

            l_pool = [r for r in filtered["Lunch"] if rec_key(r) not in used]
            if len(l_pool) < 3:
                continue
            l_plan = rng.sample(l_pool, 3)
            used |= {rec_key(r) for r in l_plan}

            d_pool = [r for r in filtered["Dinner"] if rec_key(r) not in used]
            if len(d_pool) < 3:
                continue
            d_plan = rng.sample(d_pool, 3)

            plan = {"Breakfast": b_plan, "Lunch": l_plan, "Dinner": d_plan}

        meal_err = sum(score(sum_macros(plan[m]), meal_targets[m], calorie_tolerance / 3.0) for m in MEALS)
        day_totals = sum_macros(plan["Breakfast"] + plan["Lunch"] + plan["Dinner"])
        day_err = score(day_totals, target, calorie_tolerance)
        total_err = day_err + 0.5 * meal_err

        if total_err < best_err:
            best_err, best_plan = total_err, plan

    if best_plan is None:
        raise SystemExit("Could not find a valid plan.")

    return best_plan


# Print the chosen foods plus meal totals and daily totals.
def print_plan(plan, target, date_used, required_tags):
    def fmt(t):
        return f"Calories={t[0]:.0f}  Fat={t[1]:.1f}g  Carbs={t[2]:.1f}g  Protein={t[3]:.1f}g"

    day = plan["Breakfast"] + plan["Lunch"] + plan["Dinner"]
    totals = sum_macros(day)

    print("\n Daily Meal Plan ")
    print("Menu:", "All rows (no date filter)")
    print("Required tags (must include):", required_tags if required_tags else "None")
    print("\nTarget:\n ", fmt(target))
    print("Actual:\n ", fmt(totals))
    print("Diff (Actual - Target):\n ", fmt((totals[0] - target[0], totals[1] - target[1], totals[2] - target[2], totals[3] - target[3])))

    for meal in MEALS:
        print(f"\n {meal} (3 items) ")
        print("Meal totals:", fmt(sum_macros(plan[meal])))
        for i, (_, meta) in enumerate(plan[meal], 1):
            print(f"\n[{meal} item {i}]")
            for k in sorted(meta.keys()):
                print(f"  {k}: {meta[k]}")


# Parse inputs user macro information into one object to use.
def parse_args():
    ap = argparse.ArgumentParser(description="Generate a 3-meal (3 items each) macro-matching plan from menu_dataset.csv (no date filter)")
    ap.add_argument("--csv", default="menu_dataset.csv")

    ap.add_argument("--calories", type=float, required=True)
    ap.add_argument("--fat", type=float, required=True)
    ap.add_argument("--carbs", type=float, required=True)
    ap.add_argument("--protein", type=float, required=True)

    ap.add_argument("--require-tag", action="append", default=[], help="Repeatable: VG, V, AG, HALAL")
    ap.add_argument("--trials", type=int, default=60000)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--meal-split", type=float, nargs=3, default=(0.30, 0.35, 0.35), metavar=("B", "L", "D"))
    ap.add_argument("--calorie-tolerance", type=float, default=150.0)
    ap.add_argument("--allow-repeats", action="store_true")

    return ap.parse_args()


# Run the full program: load data, build pools, search, and print the plan.
def main():
    args = parse_args()

    for t in args.require_tag:
        if t not in TAG_COLS:
            raise SystemExit(f"Unknown tag {t!r}. Expected one of: {', '.join(TAG_COLS)}")

    records, date_used = load_records(
        args.csv,
        None,
        args.require_tag,
        disallow_repeats=not args.allow_repeats,
    )

    pools = make_meal_pools(records)
    target = (args.calories, args.fat, args.carbs, args.protein)

    plan = find_best_plan(
        pools,
        target,
        args.require_tag,
        trials=args.trials,
        seed=args.seed,
        meal_split=tuple(args.meal_split),
        calorie_tolerance=args.calorie_tolerance,
        allow_repeats=args.allow_repeats,
    )

    print_plan(plan, target, date_used, args.require_tag)


if __name__ == "__main__":
    main()