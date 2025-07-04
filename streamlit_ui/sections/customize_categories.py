import config as c
import streamlit as st
import utils.css as css
import utils.helpers as h

def show_customize_categories():

    # key names for editing_group items
    # used to define rendering attributes for the editing_group
    GROUP_HEADER_KEY = "header"
    GROUP_VALUES_KEY = "values"
    GROUP_HEADER_LEVEL_KEY = "level"
    GROUP_HEADER_UNDERLINE_KEY = "underline"
    GROUP_DESCRIPTION_KEY = "description"

    HEADERS_MARKDOWN_LEVEL = 3
    MAX_NUMBER_OF_COLUMNS = 4

    EXPENSES_EDITING_GROUP_KEY = "expense_buckets"
    EXPENSES_GROUP_HEADER_KEY_VALUE = "Expense Buckets"
    OTHER_EDITING_GROUP_KEY = "other"

    # this defines the primary editing groups
    # note: expense categories are further categorizable
    editing_groups = {
        EXPENSES_EDITING_GROUP_KEY: {
                GROUP_HEADER_KEY: EXPENSES_GROUP_HEADER_KEY_VALUE,
                GROUP_DESCRIPTION_KEY: """
                    Define your expense buckets here.  
                    Note: Buckets are only used for organizing and analytics, you define the expense categories for each bucket below.
                """,
                GROUP_VALUES_KEY: st.session_state.user.EXPENSES_BUCKETS
            },
        OTHER_EDITING_GROUP_KEY: [        
            {
                GROUP_HEADER_KEY: c.INCOME_PARENT_CATEGORY_KEY,
                GROUP_DESCRIPTION_KEY: "What income streams do you want to track?",
                GROUP_VALUES_KEY: st.session_state.user.INCOME_CATEGORIES,
            },
            {
                GROUP_HEADER_KEY: c.SAVINGS_PARENT_CATEGORY_KEY,
                GROUP_DESCRIPTION_KEY: "What savings outlets do you have?",
                GROUP_VALUES_KEY: st.session_state.user.SAVINGS_CATEGORIES,
            }
        ]
    }

    def render_editing_group(attrs):
        """
            produces streamlit widgets for categorization editing for given group

            args:
                attrs (dict): attributes to render for the editing group
            
            returns
                res (list): list of user selected options from multiselect
        """
        
        group_header = attrs.get(GROUP_HEADER_KEY, None)
        group_description = attrs.get(GROUP_DESCRIPTION_KEY, None)
        group_values = attrs.get(GROUP_VALUES_KEY, [])

        # by default, use specified markdown header level 
        group_header_level = attrs.get(GROUP_HEADER_LEVEL_KEY, HEADERS_MARKDOWN_LEVEL)
        group_header_underline = attrs.get(GROUP_HEADER_UNDERLINE_KEY, True)

        if group_header: 
            css.header(group_header, lvl=group_header_level, underline_text = group_header_underline)

        if group_description: 
            st.write(group_description)

        res = st.multiselect(
            label = group_header,
            label_visibility = "collapsed",
            options = group_values,
            default = group_values,
            accept_new_options = True,
            disabled = not(h.user_is_premium())
        )

        return res

    # lock this feature behind premium tier
    if not h.user_is_premium():
        st.error(f"Custom categories are not available on the free tier. Upgrade to premium!", icon="🚫")
        css.divider()

    help_text = """
        Create new categories by typing them directly into the fields below.
    """
    st.info(help_text, icon="ℹ️")

    # render OTHER_EDITING_GROUP_KEY editing_groups
    selections = {}
    cols = st.columns(len(editing_groups[OTHER_EDITING_GROUP_KEY]))
    for i, attrs in enumerate(editing_groups[OTHER_EDITING_GROUP_KEY]):
        with cols[i]:
            res = render_editing_group(attrs)
            selections[attrs[GROUP_HEADER_KEY]] = res

    # render expense_buckets editing_group
    attrs = editing_groups[EXPENSES_EDITING_GROUP_KEY]
    buckets = render_editing_group(attrs)
    selections[attrs[GROUP_HEADER_KEY]] = buckets

    css.header("Expense Categories", lvl = HEADERS_MARKDOWN_LEVEL + 1)
    st.markdown("Define the expense categories you want to track within each bucket.")
    
    # dynamically render editing widgets for each expense_bucket
    # Note: 
    #   renders are generated with tables of 1 row each
    #   this is because Streamlit applies a border to each column (container object) of the table
    #   and the desired UI is to border each category, so we need to ensure 1 category/column
    for i, bucket in enumerate(buckets):
        col_index = i % MAX_NUMBER_OF_COLUMNS

        if col_index == 0:
            # create a new set of columns every MAX_NUMBER_OF_COLUMNS items
            # this is effective creating single row columns
            columns_remaining = len(buckets) - i
            row_length = min(columns_remaining, MAX_NUMBER_OF_COLUMNS)
            cols = st.columns(row_length, border=True)

        with cols[col_index]:
            attrs = {
                GROUP_HEADER_KEY: bucket,
                GROUP_HEADER_LEVEL_KEY: HEADERS_MARKDOWN_LEVEL + 2,
                GROUP_VALUES_KEY: st.session_state.user.EXPENSES_BODY.get(bucket, []),
            }

            res = render_editing_group(attrs)
            selections[attrs[GROUP_HEADER_KEY]] = res

    # modify selections to match categories.json format
    categories = selections.copy()

    # this key contains the expense bucket names
    # pop since its not required in categories.json
    categories.pop(EXPENSES_GROUP_HEADER_KEY_VALUE)

    # shift all expense_buckets under EXPENSES_PARENT_CATEGORY_KEY
    categories[c.EXPENSES_PARENT_CATEGORY_KEY] = {}
    for bucket in selections[EXPENSES_GROUP_HEADER_KEY_VALUE]:
        categories.pop(bucket)
        categories[c.EXPENSES_PARENT_CATEGORY_KEY][bucket] = selections[bucket]

    # add non_expenses key
    categories[c.NON_EXPENSES_PARENT_CATEGORY_KEY] = c.NON_EXPENSES_CATEGORIES
    
    if st.button("💾 Update Categories", disabled=not(h.user_is_premium())):
        st.session_state.user.update_categories(categories)
        st.session_state.user.load_budgetbuddy_user_variables()

        h.save_toast()

        # force Streamlit to re-render all widgets that rely on st.session_state.user.CATEGORIES data
        st.rerun()