"""
Name: Quincy Ji
CS230: Section 6
Data: Fast Food Restaurant in the USA
URL: will be updated in presentation tomorrow

Description: This program allows users to explore fast food restaurant data in the USA through interactive visualizations, including bar charts, tables, and maps.
Users can filter data by state, city, and category to view the distribution of fast food restaurants and get detailed information.

Query 1:"Which fast-food categories are most common in each state?" -- Fast Food Categories by State
Visualizes the number of fast-food restaurants in each category by state.
Users can filter states and view results in a stacked bar chart for easy comparison.

Query 2:"Find all fast-food restaurants in city that belong to a specific category." -- Filtered Fast-Food Restaurants by City and Category
Allows filtering by state, city, and category, showing matching restaurants in a detailed table.

Query 3: "Show the geographic distribution of fast-food restaurant of selected states." -- Geographic Distribution of Fast-Food Restaurants:
Displays an interactive map of restaurant locations, with hover details including name, address, city, and state.

"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import os

#read the data
current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, 'fast_food_usa.csv')
data = pd.read_csv(file_path)
category_state_data = data[['categories', 'province']]

#[PY5] Dictionary
category_map = {
    "Asian": ["chinese", "asian", "japanese"],
    "American/Burger": ["american", "burger"],
    "Mexican/Taco": ["mexican", "taco"],
    "Italian/Pizza": ["italian", "pizza"],
    "Ice Cream": ["ice cream"],
}

def recategorize_category(category, custom_mapping=category_map):
    category_lower = category.lower()
    for recat, keywords in custom_mapping.items(): #where recat is key, keywords are the values
        if any(word in category_lower for word in keywords):
            return recat.capitalize()
    return "Uncategorized"

#[PY2]Function that returns more than one value
def get_filtered_data(cities, category, states):
    if cities and category:
        filtered_data = data[
            (data['city'].isin(cities))
            & (data['recategorized'] == category)
            & (data['province'].isin(states)) # Handle the situation that there are same name of cities in different state
        ]
        #[DA1]lamda function
        formatted_addresses = filtered_data.apply(lambda row: f"{row['address']}, {row['city']}, {row['province']}", axis=1)
        filtered_data['formatted_address'] = formatted_addresses
        return filtered_data, formatted_addresses
    else:
        return pd.DataFrame(), []
#[DA7]Add columns
data['recategorized'] = data['categories'].apply(recategorize_category)


#Query 1

st.title("Fast Food Categories by State")
#[ST]
st.markdown("""
Explore the most common fast-food categories by state, filter cities, and view detailed geographic locations of restaurants across the USA.

- Use filters in the sidebar to customize your view.
- Visualizations include bar charts, tables, and an interactive map to explore the data.
- You can also get detailed information about specific restaurants in selected cities and categories.
""")

#[ST1]text box
st.subheader("Instruction of Most Common Fast-Food Categories")
Instruction_text = """
1. Use the "State filter" in the sidebar to select specific states you are interested in. 
2. The “Category Distribution by State” bar chart will display the number of restaurants in each fast-food category for the selected states.
3. Scroll down to see the "Most Popular Fast-Food Category by State" table, showing which category has the most restaurants in each state.
4. Use the "City Filter" and "Category Dropdown" in the sidebar to further refine your search. The filtered results of fast-food restaurants will be shown in a detailed table.
5. The "Geographic Distribution Map" shows the locations of fast-food restaurants in the selected states, with detailed information available on hover.
"""
st.text_area("Instruction", Instruction_text, height=150)

#[ST4]Design -- Side bar
st.sidebar.header("Filter Options")
selected_states = st.sidebar.multiselect(
    "Select States",
    options=sorted(data['province'].unique()),  #[PY4][DA2] List Comprehension & sorted data -- used for filter states
)
#[DA4]Filter data by one condition
if selected_states:
    filtered_data = data[data['province'].isin(selected_states)]
else:
    filtered_data = data

#[DA7]Group the data
grouped_data = filtered_data.groupby(['province', 'recategorized']).size().unstack(fill_value=0)

#[VIZ1] stack bar charts using Matplot
st.subheader("Category Distribution by State")
fig, ax = plt.subplots(figsize=(10, 6))
grouped_data.plot(kind='bar', stacked=True, ax=ax, colormap='tab20c')
ax.set_title("Fast Food Category Distribution by State", fontsize=16)
ax.set_xlabel("State", fontsize=12)
ax.set_ylabel("Number of Restaurants", fontsize=12)
ax.legend(title="Categories", fontsize=10, title_fontsize=12)
st.pyplot(fig)

#Table for most popular categories

#[DA7]Drop columns
grouped_data_filtered = grouped_data.drop(columns=['Uncategorized'], errors='ignore')

#[DA3]Find the largest value of a column
largest_category = grouped_data_filtered.idxmax(axis=1)
largest_category_counts = grouped_data_filtered.max(axis=1)

#[DA6]Pivot Table
largest_category_table = pd.DataFrame({
    'State': largest_category.index,
    'Category': largest_category.values,
    'Counts': largest_category_counts.values
})
largest_category_pivot = largest_category_table.pivot_table(index='State', values=['Category', 'Counts'], aggfunc='first')
st.subheader("Most Popular Fast-Food Category by State (Excluding 'Uncategorized')")
st.table(largest_category_table)

#Query 2

#[ST2]Multiselect for cities in selected states
st.sidebar.subheader("City Filter")
if selected_states:
    cities_in_selected_states = sorted(data[(data['province'].isin(selected_states))]['city'].unique())
    selected_cities = st.sidebar.multiselect("Select Cities", options=cities_in_selected_states)

    #[ST3]Dropdown for selecting a category
    categories_available = sorted(data['recategorized'].unique()) #[DA2]sort data
    selected_category = st.sidebar.selectbox("Select a Category", options=categories_available)

#Filter data based on selected cities and category
#[PY3] Error checking
try:
    filtered_city_category_data, formatted_addresses = get_filtered_data(selected_cities, selected_category, selected_states)

    #[VIZ2]DataFrame
    st.subheader("Filtered Fast-Food Restaurants")
    if not filtered_city_category_data.empty:
        filtered_restaurants_df = filtered_city_category_data[['name', 'formatted_address']]
        st.dataframe(
            filtered_restaurants_df,
            column_config={
                "name":'Fast Food Restaurant',
                "formatted_address":'Address'
            },
            hide_index=True
        )
    else:
        st.write("No restaurants found for the selected criteria.")

except Exception as e:
    st.error(f"An error occurred while filtering data: {e}")

#Query 3

#[MAP]
st.subheader("Geographic Distribution of Fast Food Restaurant of Selected State")
if selected_states:
    geo_data = data[data['province'].isin(selected_states)]
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=geo_data,
        get_position="[longitude,latitude]",
        get_radius = 5000,
        get_color = [255, 0, 0],
        pickable = True
    )
    view_state = pdk.ViewState(
        latitude=geo_data['latitude'].mean(),
        longitude=geo_data['longitude'].mean(),
        zoom=4,
        pitch=0
    )
    #add restaurant details when hovering over a marker
    geo_map = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}\n{address}, {city}, {province}"}
    )

    st.pydeck_chart(geo_map)
else:
        st.write("No geographic data available for the selected states.")
