import sqlite3
import sys
import argparse


class FoodBlog:
    data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
            "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
            "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}

    def __init__(self, name):
        self.conn = sqlite3.connect(name)
        self.conn.execute("PRAGMA foreign_keys = 1")
        self.c = self.conn.cursor()

    def create_tables(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS ingredients
                (ingredient_id INTEGER PRIMARY KEY, [ingredient_name] VARCHAR(50) UNIQUE NOT NULL)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS measures
                (measure_id INTEGER PRIMARY KEY, measure_name TEXT UNIQUE)''')
        self.conn.commit()
        self.c.execute('''CREATE TABLE IF NOT EXISTS serve
                (serve_id INTEGER PRIMARY KEY, recipe_id INTEGER NOT NULL, meal_id INTEGER NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id),
                FOREIGN KEY (meal_id) REFERENCES meals (meal_id))''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS meals
                (meal_id INTEGER PRIMARY KEY, meal_name TEXT UNIQUE NOT NULL)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS recipes
                (recipe_id INTEGER PRIMARY KEY, recipe_name TEXT NOT NULL, recipe_description TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS quantity
                (quantity_id INTEGER PRIMARY KEY, quantity INTEGER NOT NULL, measure_id INTEGER NOT NULL, 
                ingredient_id INTEGER NOT NULL, recipe_id INTEGER NOT NULL,
                FOREIGN KEY(recipe_id) REFERENCES recipes (recipe_id),
                FOREIGN KEY(measure_id) REFERENCES measures (measure_id),
                FOREIGN KEY(ingredient_id) REFERENCES ingredients (ingredient_id))''')
        self.conn.commit()

    def insert_ingredients(self):
        for value in self.data['ingredients']:
            self.c.execute("INSERT INTO ingredients (ingredient_name) VALUES (?);", (value,))
            self.conn.commit()

    def insert_measures(self):
        for value in self.data['measures']:
            self.c.execute("INSERT INTO measures (measure_name) VALUES (?);", (value,))
            self.conn.commit()

    def insert_meals(self):
        for value in self.data['meals']:
            self.c.execute("INSERT INTO meals (meal_name) VALUES (?);", (value,))
            self.conn.commit()

    def insert_recipe(self, name, desc):

        self.c.execute("INSERT INTO recipes (recipe_name, recipe_description) VALUES(?,?);", (name, desc,))
        self.conn.commit()

    def query_meals(self):
        meals = self.c.execute("SELECT meal_id, meal_name FROM meals")
        self.conn.commit()
        return meals

    def insert_serve(self, name, desc, serving):
        meals = []
        for s in serving:
            result = self.c.execute("SELECT meal_id FROM meals WHERE meal_id = (?)", (s,))
            meals.append(result.fetchone())
        recipes = self.c.execute("SELECT recipe_name FROM recipes WHERE recipe_name = (?)", (name,))
        recipes.fetchone()
        if recipes is None:
            self.insert_recipe(name, desc)
            self.conn.commit()
        recipe_id = self.c.execute("SELECT * FROM recipes").lastrowid
        for m in meals:
            self.c.execute("INSERT INTO serve (meal_id, recipe_id) VALUES(?, ?);", (m[0], recipe_id))
        self.conn.commit()

    def insert_quantity(self, _quantity, name, desc):
        recipes = self.c.execute("SELECT recipe_name FROM recipes WHERE recipe_name = (?)", (name,))
        recipes.fetchone()
        recipe_id = 0
        if recipes is None:
            self.insert_recipe(name, desc)
            self.conn.commit()
            recipe_id = self.c.execute("SELECT recipe_id FROM recipes").lastrowid
        else:
            recipe_ids = self.c.execute('''SELECT recipe_id FROM recipes WHERE recipe_name LIKE ?''',
                                         (f'{name}%',)).fetchall()
        lst = _quantity.split()
        if len(lst) == 3:
            quantity = int(lst[0])
            measure_name = lst[1]
            ingredient_name = lst[2]
            measure_ids = self.c.execute('''SELECT measure_id FROM measures WHERE measure_name LIKE ?''',
                                         (f'{measure_name}%',)).fetchall()
            ingredient_ids = self.c.execute(
                '''SELECT ingredient_id FROM ingredients WHERE ingredient_name LIKE ?''',
                (f'{ingredient_name}%',)).fetchall()
            if len(measure_ids) > 1:
                print('The measure is not conclusive!')
            elif len(ingredient_ids) > 1:
                print('The measure is not conclusive!')
            else:
                measure_id = int(measure_ids[0][0])
                ingredient_id = int(ingredient_ids[0][0])
                recipe_id = int(recipe_ids[0][0])
                print(f'ingredient_id: {ingredient_id}')
                print(f'measure_id: {measure_id}')
                print(f'recipe_id: {recipe_id}')
                self.c.execute("INSERT INTO quantity (quantity, recipe_id, measure_id, ingredient_id) VALUES (?, ?, ?, ?);",
                               (quantity, recipe_id, measure_id, ingredient_id))
                self.conn.commit()
        elif len(lst) == 2:
            quantity = int(lst[0])
            ingredient_name = lst[1]
            ingredient_ids = self.c.execute(
                '''SELECT ingredient_id FROM ingredients WHERE ingredient_name LIKE ?''',
                (f'{ingredient_name}%',)).fetchall()
            if len(ingredient_ids) > 1:
                print('The measure is not conclusive!')
            else:
                ingredient_id = ingredient_ids[0][0]
                recipe_id = int(recipe_ids[0][0])
                print(f'ingredient_id: {ingredient_id}')
                print(f'measure_id: {8}')
                print(f'recipe_id: {recipe_id}')
                self.c.execute('''INSERT INTO quantity 
                (quantity, recipe_id, measure_id, ingredient_id) 
                VALUES (?, ?, ?, ?);''', (quantity, recipe_id, 8, ingredient_id))
                self.conn.commit()
        self.conn.commit()

    def find_recipes(self, meals, ing):
        output = "Recipes selected for you: "
        ing = ing.split("=")
        ing = ing[1].strip('"')
        ing = ing.split(",")
        meals = meals.split("=")
        meals = meals[1].strip('"')
        meals = meals.split(",")
        ingredient_ids = []
        meal_ids = []
        recipe_ids = []
        available_recipe_ids = []
        for ingredient in ing:
            ingredient_id = self.c.execute('SELECT ingredient_id FROM ingredients WHERE ingredient_name LIKE ?', (ingredient,)).fetchone()
            if ingredient_id is not None:
                ingredient_id = ingredient_id[0]
            ingredient_ids.append(ingredient_id)
            recipes = self.c.execute('SELECT recipe_id FROM quantity WHERE ingredient_id=?', (ingredient_id,)).fetchall()
            for recipe in recipes:
                recipe_ids.append(recipe[0])
        ingredient_ids = set(ingredient_ids)
        for meal in meals:
            meal_id = self.c.execute('SELECT meal_id FROM meals WHERE meal_name=?', (meal,)).fetchone()[0]
            meal_ids.append(meal_id)
        for recipe_id in recipe_ids:
            ing_recipe = []
            ingredients = self.c.execute('SELECT ingredient_id FROM quantity WHERE recipe_id=?', (recipe_id,)).fetchall()
            for i in ingredients:
                ing_recipe.append(i[0])
            ing_recipe = set(ing_recipe)
            if ingredient_ids.issubset(ing_recipe):
                recipe = self.c.execute('SELECT recipe_name FROM recipes WHERE recipe_id=?', (recipe_id,)).fetchone()[0]
                available_recipe_ids.append(recipe)
        if len(available_recipe_ids) != 0:
            print("and ".join(available_recipe_ids))
        else:
            print('no such recipes')


def main():
    name = "food_blog.db"
    food_blog = FoodBlog(name)
    food_blog.create_tables()
    if len(sys.argv) == 4:
        ings = sys.argv[2]
        meals = sys.argv[3]
        food_blog.find_recipes(meals, ings)
        food_blog.conn.close()
        exit()
    food_blog.insert_ingredients()
    food_blog.insert_meals()
    food_blog.insert_measures()
    print("Pass the empty recipe name to exit.")
    while True:
        print(food_blog.query_meals())
        recipe_name = input("Recipe name:")
        if recipe_name == "":
            break
        else:
            recipe_desc = input("Recipe description:")
            food_blog.insert_recipe(recipe_name, recipe_desc)
            print("1) breakfast  2) brunch  3) lunch  4) supper ")
            serve = [int(i) for i in list(input("When the dish can be served: ").split(" "))]
            food_blog.insert_serve(recipe_name, recipe_desc, serve)
            while True:
                quantity = input("Input quantity of ingredient <press enter to stop")
                if quantity == "":
                    break
                else:
                    food_blog.insert_quantity(quantity, recipe_name, recipe_desc)

    food_blog.conn.close()


if __name__ == '__main__':
    main()
