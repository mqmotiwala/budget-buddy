import config as c
import streamlit as st
import utils.helpers as h

def build_categorization_column(attrs):
    num_values = st.number_input(f"How many {attrs["parent_type"]} do you want to track?", min_value = 1, value = len(attrs["parent_values"]))

    with st.form(f"customize {attrs["parent_type"]}", enter_to_submit = False):
        st.subheader(attrs["parent_subheader"])
        st.text(attrs["definition_text"])

        for i in range(num_values):
            st.text_input(f"{attrs["parent_subheader"]} #{i+1} Label", value = h.get_index(attrs["parent_values"], i))

        if st.form_submit_button("💾 Save Changes"):
            st.write("ah ee")

def show_customize_categories_v1():
    cols = st.columns(3)

    with cols[0]:
        attrs = {
            "parent_type": "income sources",
            "parent_values": st.session_state.user.INCOME_CATEGORIES,
            "parent_subheader": "Income",
            "definition_text": "Define all your income streams here."
        }
        
        build_categorization_column(attrs)

    with cols[1]:
        attrs = {
            "parent_type": "savings outlets",
            "parent_values": st.session_state.user.SAVINGS_CATEGORIES,
            "parent_subheader": "Savings",
            "definition_text": "Define all your savings outlets here."
        }
        
        build_categorization_column(attrs)

    with cols[2]:
        attrs = {
            "parent_type": "expense categories",
            "parent_values": st.session_state.user.EXPENSES_CATEGORIES,
            "parent_subheader": "Expense Category",
            "definition_text": "Define all your expense categories here."
        }
        
        build_categorization_column(attrs)

    st.divider()

def show_customize_categories_v2():

    parents = [
        {
            "parent_type": "income sources",
            "parent_values": st.session_state.user.INCOME_CATEGORIES,
            "parent_subheader": c.INCOME_PARENT_CATEGORY_KEY,
            "definition_text": "Define all your income streams here."   
        },
        {
            "parent_type": "savings outlets",
            "parent_values": st.session_state.user.SAVINGS_CATEGORIES,
            "parent_subheader": c.SAVINGS_PARENT_CATEGORY_KEY,
            "definition_text": "Define all your savings outlets here."  
        },
        {
            "parent_type": "expense categories",
            "parent_values": st.session_state.user.EXPENSES_CATEGORIES,
            "parent_subheader": c.EXPENSES_PARENT_CATEGORY_KEY,
            "definition_text": "Define all your expense categories here."
        }
    ]

    cols = st.columns(3)
    for i, attrs in enumerate(parents):
        with cols[i]:
            attrs["user_submitted_num_items"] = st.number_input(f"How many {attrs["parent_type"]} do you want to track?", min_value = 1, value = len(attrs["parent_values"]))

    with st.form("categorization", border=False, enter_to_submit=False):
        cols = st.columns(3, border=True)
        form_values = {}
        for i, attrs in enumerate(parents):
            with cols[i]:
                st.subheader(attrs["parent_subheader"])
                st.text(attrs["definition_text"])
                form_values[attrs["parent_subheader"]] = []

                for i in range(attrs["user_submitted_num_items"]):
                    input = st.text_input(f"{attrs["parent_subheader"]} #{i+1} Label", value = h.get_index(attrs["parent_values"], i))
                    if input is not None and len(input) > 0:
                        form_values[attrs["parent_subheader"]].append(input)

        if st.form_submit_button("💾 Save Changes"):
            categories = {
                c.INCOME_PARENT_CATEGORY_KEY: [],
                c.SAVINGS_PARENT_CATEGORY_KEY: [],
                c.EXPENSES_PARENT_CATEGORY_KEY: [],
                c.NON_EXPENSES_PARENT_CATEGORY_KEY: c.NON_EXPENSES_CATEGORIES
            }

            for i, attrs in enumerate(parents):
                for i in range(attrs["user_submitted_num_items"]):
                    categories[attrs["parent_subheader"]] = form_values[attrs["parent_subheader"]]

            st.json(categories)

def show_customize_categories_v3():

    parents = [
        {
            "parent_type": "income sources",
            "parent_values": st.session_state.user.INCOME_CATEGORIES,
            "parent_subheader": "Income",
            "definition_text": "Define all your income streams here."   
        },
        {
            "parent_type": "savings outlets",
            "parent_values": st.session_state.user.SAVINGS_CATEGORIES,
            "parent_subheader": "Savings",
            "definition_text": "Define all your savings outlets here."  
        },
        {
            "parent_type": "expense categories",
            "parent_values": st.session_state.user.EXPENSES_CATEGORIES,
            "parent_subheader": "Expense Category",
            "definition_text": "Define all your expense categories here."
        }
    ]

    cols = st.columns(3)
    for i, attrs in enumerate(parents):
        with cols[i]:
            attrs["num_user_values"] = st.number_input(f"How many {attrs["parent_type"]} do you want to track?", min_value = 1, value = len(attrs["parent_values"]))

    with st.form("test", border=False):
        for i, attrs in enumerate(parents):
            st.subheader(attrs["parent_subheader"])
            st.text(attrs["definition_text"])

            for i in range(attrs["num_user_values"]):
                st.text_input(f"{attrs["parent_subheader"]} #{i+1} Label", value = h.get_index(attrs["parent_values"], i))

        if st.form_submit_button("💾 Save Changes"):
            st.write("ah ee")
    st.json(st.session_state.user.CATEGORIES_BODY)
    st.write(st.session_state.user.CATEGORIES)
    st.write(st.session_state.user.INCOME_CATEGORIES)
    st.write(st.session_state.user.SAVINGS_CATEGORIES)
    st.write(st.session_state.user.EXPENSES_CATEGORIES)
    st.write(st.session_state.user.NON_EXPENSES_CATEGORIES)
