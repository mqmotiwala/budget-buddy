import config as c
import streamlit as st
import utils.helpers as h
import utils.css as css

def show_customize_categories():

    # parents list is used downstream by the frontend to allow edits for each section
    # in the non-detailed categorization model, Expenses are the only supported editable section
    # this is because Income and Savings only have one element each, i.e. Income and Savings
    # 
    # as such, parents list is adjusted to only include Expenses at the moment
    # consequently, we use columns in this code downstream but its not required at this stage since we only support edits for one section
    #
    # see commit f2d382b3dc6749fae0ff00ec3dae0b13eb1e49c9 for how the full list may look like after detailed categories are supported

    PARENT_TYPE_KEY_NAME = "parent_type"
    PARENT_VALUES_KEY_NAME = "parent_values"
    PARENT_SUBHEADER_KEY_NAME = "parent_subheader"
    PARENT_DEFINITION_TEXT_KEY_NAME = "definition_text"
    USER_INPUT_NUM_ITEMS_KEY_NAME = "user_input_num_items"

    parents = [
        {
            "parent_type": "expense categories",
            "parent_values": st.session_state.user.EXPENSES_CATEGORIES,
            "parent_subheader": c.EXPENSES_PARENT_CATEGORY_KEY,
            "definition_text": "Note: empty categories are automatically deleted!"
        }
    ]

    # create number_input widgets outside of the form
    # this is required so that text_input widgets inside the form can update in real-time when user interacts with the number_input widgets
    cols = st.columns(len(parents))
    for i, attrs in enumerate(parents):
        with cols[i]:
            st.subheader(attrs[PARENT_SUBHEADER_KEY_NAME])
            prompt_text = f"How many {attrs[PARENT_TYPE_KEY_NAME]} do you want to track?"
            st.info(attrs[PARENT_DEFINITION_TEXT_KEY_NAME], icon=":material/info:")
            st.text(prompt_text)

            attrs[USER_INPUT_NUM_ITEMS_KEY_NAME] = st.number_input(prompt_text, min_value = 1, value = len(attrs[PARENT_VALUES_KEY_NAME]), label_visibility="collapsed")
            
            css.divider()

    with st.form("categorization_form", border=False, enter_to_submit=False):
        cols = st.columns(len(parents), border=False)
        form_values = {}
        for i, attrs in enumerate(parents):
            with cols[i]:
                form_values[attrs[PARENT_SUBHEADER_KEY_NAME]] = []

                for i in range(attrs[USER_INPUT_NUM_ITEMS_KEY_NAME]):
                    input = st.text_input(f"{attrs[PARENT_SUBHEADER_KEY_NAME]} #{i+1} Label", value = h.get_index(attrs[PARENT_VALUES_KEY_NAME], i))
                    if input is not None and len(input) > 0:
                        form_values[attrs[PARENT_SUBHEADER_KEY_NAME]].append(input)

        if st.form_submit_button("💾 Save Changes"):
            categories = {
                c.INCOME_PARENT_CATEGORY_KEY: [c.INCOME_PARENT_CATEGORY_KEY],
                c.SAVINGS_PARENT_CATEGORY_KEY: [c.SAVINGS_PARENT_CATEGORY_KEY],
                c.EXPENSES_PARENT_CATEGORY_KEY: [],
                c.NON_EXPENSES_PARENT_CATEGORY_KEY: c.NON_EXPENSES_CATEGORIES
            }

            for i, attrs in enumerate(parents):
                for i in range(attrs[USER_INPUT_NUM_ITEMS_KEY_NAME]):
                    categories[attrs[PARENT_SUBHEADER_KEY_NAME]] = form_values[attrs[PARENT_SUBHEADER_KEY_NAME]]

            st.json(categories)