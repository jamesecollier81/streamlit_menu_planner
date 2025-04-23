import streamlit as st
import json
from typing import List, Dict, Optional
import random

# Initialize session state variables if they don't exist
if 'selected_lunch' not in st.session_state:
    st.session_state.selected_lunch = None
if 'selected_dinners' not in st.session_state:
    st.session_state.selected_dinners = []
if 'locked_dinners' not in st.session_state:
    st.session_state.locked_dinners = {}

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
    
    def generate_dinners(self, category_limits: Dict[str, int]) -> List[Dict]:
        new_dinners = [None] * 5
        
        # First, keep all locked dinners
        locked_indices = [i for i in range(5) if i in st.session_state.locked_dinners]
        for idx in locked_indices:
            new_dinners[idx] = st.session_state.locked_dinners[idx]
            cat = new_dinners[idx]['category']
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
        st.write("Ingredients:", ", ".join(st.session_state.selected_lunch['ingredients']))
    
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
        
        # Update locked dinners based on checkboxes
        for i, dinner in enumerate(st.session_state.selected_dinners):
            if dinner:
                key = f"lock_dinner_{i}"
                is_locked = st.checkbox(
                    f"Lock {dinner['name']}", 
                    key=key,
                    value=(i in st.session_state.locked_dinners)
                )
                
                if is_locked:
                    st.session_state.locked_dinners[i] = dinner
                elif i in st.session_state.locked_dinners:
                    del st.session_state.locked_dinners[i]
    
    # Generate dinners button
    if st.button("Generate Dinners"):
        total_selected = sum(category_counts.values())
        remaining_slots = 5 - len(st.session_state.locked_dinners)
        
        if total_selected != remaining_slots:
            st.error(f"Please select exactly {remaining_slots} meals total (selected: {total_selected})")
        else:
            planner.generate_dinners(category_counts)
    
    # Display selected dinners
    if st.session_state.selected_dinners:
        st.subheader("Selected Dinners")
        for i, dinner in enumerate(st.session_state.selected_dinners, 1):
            if dinner:
                locked_status = "(Locked)" if (i-1) in st.session_state.locked_dinners else ""
                st.write(f"{i}. {dinner['name']} ({dinner['category']}) {locked_status}")
                st.write(f"Ingredients: {', '.join(dinner['ingredients'])}")

if __name__ == "__main__":
    main()
