from food_item import FoodItem
import csv

#csv values are read as strings, so we need to convert many of them (calories,fat,carbs,etc.) to floats
def convert_csv_to_float(value:str) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None

#the dietary restrictions are stored as indicator variables in csv. We need to convert them to strings
def convert_diet_restrictions(row:dict[str,str]) -> list[str]:
    tags = []
    csv_tags = ["VG","V","AG","HALAL"]
    for tag in csv_tags:
        if tag in row:
            value = row[tag].strip()
            if value == "1":
                tags.append(tag)
    return tags

#convert each csv row, which is input as a dictionary, into FoodItem objects
def convert_food_items(row:dict[str,str]) -> FoodItem:
    item_name = row["item_name"].strip()
    restaurant = row["restaurant_name"].strip()
    calories = convert_csv_to_float(row["calories"])
    fat = convert_csv_to_float(row["total_fat_g"])
    carbs = convert_csv_to_float(row["total_carbs_g"])
    protein = convert_csv_to_float(row["protein_g"])
    diet_restrictions = convert_diet_restrictions(row)
    return FoodItem(item_name,restaurant,calories,fat,carbs,protein,diet_restrictions)


_converted = None

#now, with helper functions, read csv dataset and convert each row into a FoodItem object in a list
def get_data() -> list[FoodItem]:
    global _converted
    if _converted is None:
        # Try the original filename first, then fall back to the common .csv name.
        try:
            dataset = open("menu_dataset", "r", encoding="utf-8", newline="")
        except FileNotFoundError:
            dataset = open("menu_dataset.csv", "r", encoding="utf-8", newline="")
        with dataset:
            reader = csv.DictReader(dataset)
            _converted = [convert_food_items(row) for row in reader]
    return _converted