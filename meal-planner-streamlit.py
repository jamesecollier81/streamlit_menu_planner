import streamlit as st
import json
from typing import List, Dict, Optional
from collections import defaultdict
import random

# Initialize session state variables if they don't exist
if 'selected_lunch' not in st.session_state:
    st.session_state.selected_lunch = None
if 'selected_dinners' not in st.session_state:
    st.session_state.selected_dinners = []
if 'show_grocery_list' not in st.session_state:
    st.session_state.show_grocery_list = False
if 'locked_indices' not in st.session_state:
    st.session_state.locked_indices = []

class MealPlanner:
    def __init__(self, recipes_file: str):
        with open(recipes_file, 'r') as f:
            self.recipes = json.load(f)
        
        self.lunch_recipes = [r for r in self.recipes if r['name'].startswith('Lunch - ')]
        self.dinner_recipes = [r for r in self.recipes if not r['name'].startswith('Lunch - ')]
    
    def get_categories(self, meal_type: str = 'dinner') -> List[str]:
        recipes = self.lunch_recipes if meal_type == 'lunch' else self.dinner_recipes
        return sorted(set(r['category'] for r in recipes))
    
    def generate_lunch(self, category: Optional[str] = None) -> Dict:
        available = self.lunch_recipes
        if category:
            available = [r for r in available if r['category'] == category]
            if not available:
                st.error(f"No lunch recipes found for category: {category}")
                return None
        
        selected_lunch = random.choice(available)
        st.session_state.selected_lunch = selected_lunch
        return selected_lunch
    
    def generate_dinners(self, category_limits: Dict[str, int], locked_indices: List[int] = None) -> List[Dict]:
        if locked_indices is None:
            locked_indices = []
            
        new_dinners = [None] * 5
        remaining_slots = 5 - len(locked_indices)
        
        # Keep locked meals
        for idx in locked_indices:
            if 0 <= idx < len(st.session_state.selected_dinners):
                new_dinners[idx] = st.session_state.selected_dinners[idx]
                cat = st.session_state.selected_dinners[idx]['category']
                if cat in category_limits:
                    category_limits[cat] -= 1
        
        # Fill remaining slots
        empty_indices = [i for i in range(5) if new_dinners[i] is None]
        for idx in empty_indices:
            available_categories = [cat for cat, limit in category_limits.items() if limit > 0]
            if available_categories:
                category = random.choice(available_categories)
                available = [r for r in self.dinner_recipes 
                           if r['category'] == category and r not in new_dinners]
                if available:
                    new_dinners[idx] = random.choice(available)
                    category_limits[category] -= 1
        
        st.session_state.selected_dinners = new_dinners
        return new_dinners

    def generate_grocery_list(self) -> Dict[str, tuple]:
        grocery_list = defaultdict(lambda: [0, ""])
        
        if st.session_state.selected_lunch:
            for ingredient, amount in st.session_state.selected_lunch['ingredients'].items():
                unit = st.session_state.selected_lunch['units'].get(ingredient, "")
                grocery_list[ingredient][0] += amount
                grocery_list[ingredient][1] = unit

        for dinner in st.session_state.selected_dinners:
            if dinner:
                for ingredient, amount in dinner['ingredients'].items():
                    unit = dinner['units'].get(ingredient, "")
                    grocery_list[ingredient][0] += amount
                    grocery_list[ingredient][1] = unit

        return {k: tuple(v) for k, v in sorted(grocery_list.items())}

def main():
    st.title("Meal Planner")
    
    planner = MealPlanner('recipes.json')
    
    # Lunch Section
    st.header("Lunch Generator")
    use_category = st.checkbox("Use category for lunch generation")
    
    if use_category:
        lunch_categories = planner.get_categories('lunch')
        selected_lunch_category = st.selectbox(
            "Select lunch category",
            lunch_categories
        )
        if st.button("Generate Lunch with Category"):
            planner.generate_lunch(selected_lunch_category)
    else:
        if st.button("Generate Random Lunch"):
            planner.generate_lunch()
    
    # Display selected lunch
    if st.session_state.selected_lunch:
        st.write("Selected Lunch:", st.session_state.selected_lunch['name'])
        st.write("Category:", st.session_state.selected_lunch['category'])
    
    # Dinner Section
    st.header("Dinner Generator")
    
    # Category selection for dinners
    st.subheader("Select Dinner Categories")
    categories = planner.get_categories('dinner')
    category_counts = {}
    
    col1, col2 = st.columns(2)
    with col1:
        for i, category in enumerate(categories):
            count = st.number_input(
                f"{category}",
                min_value=0,
                max_value=5,
                value=0,
                key=f"category_{i}"
            )
            if count > 0:
                category_counts[category] = count
    
    # Lock dinners
    if st.session_state.selected_dinners:
        st.subheader("Lock Dinners")
        st.session_state.locked_indices = []
        for i, dinner in enumerate(st.session_state.selected_dinners):
            if dinner:
                if st.checkbox(f"Lock {dinner['name']}", key=f"lock_{i}"):
                    st.session_state.locked_indices.append(i)
    
    # Generate dinners button
    if st.button("Generate Dinners"):
        total_selected = sum(category_counts.values())
        remaining_slots = 5 - len(st.session_state.locked_indices)
        
        if total_selected != remaining_slots:
            st.error(f"Please select exactly {remaining_slots} meals total (selected: {total_selected})")
        else:
            planner.generate_dinners(category_counts, st.session_state.locked_indices)
    
    # Display selected dinners
    if st.session_state.selected_dinners:
        st.subheader("Selected Dinners")
        for i, dinner in enumerate(st.session_state.selected_dinners, 1):
            if dinner:
                st.write(f"{i}. {dinner['name']} ({dinner['category']})")
    
    # Grocery list
    st.header("Grocery List")
    if st.button("Generate Grocery List"):
        st.session_state.show_grocery_list = True
    
    if st.session_state.show_grocery_list:
        grocery_list = planner.generate_grocery_list()
        st.subheader("Shopping List")
        for ingredient, (amount, unit) in grocery_list.items():
            st.write(f"{ingredient}: {amount} {unit}")

if __name__ == "__main__":
    main()
