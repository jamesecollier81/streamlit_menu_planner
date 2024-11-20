import streamlit as st
import json
from typing import List, Dict, Optional
from collections import defaultdict
import random

class MealPlanner:
    def __init__(self, recipes_file: str):
        with open(recipes_file, 'r') as f:
            self.recipes = json.load(f)
        
        self.lunch_recipes = [r for r in self.recipes if r['name'].startswith('Lunch - ')]
        self.dinner_recipes = [r for r in self.recipes if not r['name'].startswith('Lunch - ')]
        self.selected_lunch = None
        self.selected_dinners = []
        
    # ... [keeping the existing methods unchanged] ...
    def get_categories(self, meal_type: str = 'dinner') -> List[str]:
        recipes = self.lunch_recipes if meal_type == 'lunch' else self.dinner_recipes
        return sorted(set(r['category'] for r in recipes))
    
    def generate_lunch(self, category: Optional[str] = None) -> Dict:
        available = self.lunch_recipes
        if category:
            available = [r for r in available if r['category'] == category]
            if not available:
                raise ValueError(f"No lunch recipes found for category: {category}")
            
        self.selected_lunch = random.choice(available)
        return self.selected_lunch
    
    def generate_dinners(self, category_limits: Dict[str, int], locked_indices: List[int] = None) -> List[Dict]:
        if locked_indices is None:
            locked_indices = []
            
        new_dinners = [None] * 5
        remaining_slots = 5 - len(locked_indices)
        
        # Validate total requested meals matches available slots
        total_requested = sum(category_limits.values())
        if total_requested != remaining_slots:
            raise ValueError(f"Total category counts must equal {remaining_slots} (requested: {total_requested})")
            
        # Keep locked meals
        for idx in locked_indices:
            if 0 <= idx < len(self.selected_dinners) and self.selected_dinners:
                new_dinners[idx] = self.selected_dinners[idx]
                cat = self.selected_dinners[idx]['category']
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
                    
        self.selected_dinners = new_dinners
        return new_dinners

    def generate_grocery_list(self) -> Dict[str, tuple]:
        grocery_list = defaultdict(lambda: [0, ""])
        
        if self.selected_lunch:
            for ingredient, amount in self.selected_lunch['ingredients'].items():
                unit = self.selected_lunch['units'].get(ingredient, "")
                grocery_list[ingredient][0] += amount
                grocery_list[ingredient][1] = unit

        for dinner in self.selected_dinners:
            if dinner:
                for ingredient, amount in dinner['ingredients'].items():
                    unit = dinner['units'].get(ingredient, "")
                    grocery_list[ingredient][0] += amount
                    grocery_list[ingredient][1] = unit

        return {k: tuple(v) for k, v in sorted(grocery_list.items())}

def main():
    st.set_page_config(page_title="Meal Planner", layout="wide")
    st.title("Weekly Meal Planner")

    # Initialize session state
    if 'planner' not in st.session_state:
        st.session_state.planner = MealPlanner('recipes.json')
    if 'show_grocery_list' not in st.session_state:
        st.session_state.show_grocery_list = False

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Lunch Section
        st.subheader("Lunch Generator")
        use_lunch_category = st.checkbox("Use specific lunch category")
        if use_lunch_category:
            lunch_categories = st.session_state.planner.get_categories('lunch')
            selected_lunch_category = st.selectbox("Select lunch category", lunch_categories)
            if st.button("Generate Lunch"):
                st.session_state.planner.generate_lunch(selected_lunch_category)
        else:
            if st.button("Generate Random Lunch"):
                st.session_state.planner.generate_lunch()

        # Dinner Section
        st.subheader("Dinner Generator")
        
        # Display current dinners and lock controls
        if st.session_state.planner.selected_dinners:
            st.write("Lock dinners to keep:")
            locked_dinners = []
            for i, dinner in enumerate(st.session_state.planner.selected_dinners):
                if dinner:
                    if st.checkbox(f"Keep dinner #{i+1}", key=f"lock_{i}"):
                        locked_dinners.append(i)

        # Category selection
        st.write("Select dinner categories:")
        dinner_categories = st.session_state.planner.get_categories('dinner')
        remaining_slots = 5 - len(locked_dinners) if 'locked_dinners' in locals() else 5
        
        category_counts = {}
        total_selected = 0
        
        for category in dinner_categories:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(category)
            with col2:
                count = st.number_input(
                    f"Count for {category}",
                    min_value=0,
                    max_value=remaining_slots - total_selected,
                    value=0,
                    key=f"count_{category}",
                    label_visibility="collapsed"
                )
                if count > 0:
                    category_counts[category] = count
                    total_selected += count

        st.write(f"Selected: {total_selected}/{remaining_slots} slots")
        
        if st.button("Generate Dinners") and total_selected == remaining_slots:
            st.session_state.planner.generate_dinners(
                category_counts,
                locked_dinners if 'locked_dinners' in locals() else None
            )

        if st.button("Show/Hide Grocery List"):
            st.session_state.show_grocery_list = not st.session_state.show_grocery_list

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Meal Plan")
        
        # Display Lunch
        st.subheader("Lunch")
        if st.session_state.planner.selected_lunch:
            st.write(
                f"{st.session_state.planner.selected_lunch['name']} "
                f"({st.session_state.planner.selected_lunch['category']})"
            )
        else:
            st.write("No lunch selected")

        # Display Dinners
        st.subheader("Dinners")
        for i, dinner in enumerate(st.session_state.planner.selected_dinners, 1):
            if dinner:
                st.write(f"{i}. {dinner['name']} ({dinner['category']})")
            else:
                st.write(f"{i}. Not generated yet")

    with col2:
        if st.session_state.show_grocery_list:
            st.header("Grocery List")
            grocery_list = st.session_state.planner.generate_grocery_list()
            for ingredient, (amount, unit) in grocery_list.items():
                st.write(f"{ingredient}: {amount} {unit}")

if __name__ == "__main__":
    main()
