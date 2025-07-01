import config as c
import streamlit as st
import utils.css as css

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

    # this defines the primary editing groups
    # note: expense categories are further categorizable
    editing_groups = {
        "expense_buckets": {
                GROUP_HEADER_KEY: "Expense Buckets",
                GROUP_DESCRIPTION_KEY: """
                    Define your expense buckets here.  
                    Note: Buckets are only used for organizing and analytics, you define the expense categories for each bucket below.
                """,
                GROUP_VALUES_KEY: st.session_state.user.EXPENSES_BUCKETS
            },
        "other": [        
            {
                GROUP_HEADER_KEY: "Income",
                GROUP_DESCRIPTION_KEY: "What income streams do you want to track?",
                GROUP_VALUES_KEY: st.session_state.user.INCOME_CATEGORIES,
            },
            {
                GROUP_HEADER_KEY: "Savings",
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
            disabled = disabled
        )

        return res

    # lock this feature behind premium tier
    disabled = not(st.session_state.user.is_premium)
    disabled = False # remove in prod
    if disabled:
        st.error(c.UPGRADE_NOTICE_TEXT_CUSTOMIZE_CATEGORIES_SECTION)
        css.divider()

    help_text = """
        Create new categories by adding them into the fields below.
    """
    st.info(help_text, icon="ℹ️")

    # render "other" editing_groups
    selections = {}
    cols = st.columns(len(editing_groups["other"]))
    for i, attrs in enumerate(editing_groups["other"]):
        with cols[i]:
            res = render_editing_group(attrs)
            selections[attrs[GROUP_HEADER_KEY]] = res

    # render expense_buckets editing_group
    attrs = editing_groups["expense_buckets"]
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
