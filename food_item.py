import typing

class FoodItem:
    def __init__(self,
                 item_name:str,
                 restaurant:str,
                 calories:float | None,
                 fat:float | None,
                 carbs:float | None,
                 protein:float | None,
                 diet_restrictions:list[str]):
        self.item_name = item_name
        self.restaurant = restaurant
        self.calories = calories
        self.fat = fat
        self.carbs = carbs
        self.protein = protein
        self.diet_restrictions = diet_restrictions

    def __repr__(self):
        return ("{}:/nRestaurant: {}/nCalories: {}/nFat(g): {}/nCarbs(g): {}/n"
                "Protein(g): {}/nDietRestrictions(g): {}/n").format(
                                    self.item_name,self.restaurant,self.calories,
                                          self.fat,self.carbs,self.protein,
                                          self.diet_restrictions)


    def __eq__(self, other):
        return (other is self or
                type(self) is type(other) and
                self.item_name == other.item_name and
                self.restaurant == other.restaurant and
                self.calories == other.calories and
                self.fat == other.fat and
                self.carbs == other.carbs and
                self.protein == other.protein and
                self.diet_restrictions == other.diet_restrictions
                )