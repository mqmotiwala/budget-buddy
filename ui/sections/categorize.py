import traceback
import config as c
import pandas as pd
import streamlit as st
import utils.css as css
import utils.helpers as h

def show_categorize():
    # ensure master data is loaded
    if not hasattr(st.session_state.user, "master"):
        st.session_state.user.load_master()
    master = st.session_state.user.master

    css.divider()
    st.header("🏷️Categorize Expenses")

    if master is None or master.empty:
        st.write("No categorized expenses found. Start by uploading some statements.")
        return 
    
    try:
        uncategorized = master[master[c.CATEGORY_COLUMN].isna()]
        TBD = master[(master[c.CATEGORY_COLUMN] == "TBD")]

        with st.expander("Apply filters", icon=":material/tune:"):
            # date filter
            css.markdown(css.underline("*Transaction Dates*", thickness="1px"))

            min_date_in_master = master[c.DATE_COLUMN].min()
            max_date_in_master = master[c.DATE_COLUMN].max()
            res = st.date_input(
                value = [min_date_in_master, max_date_in_master],
                min_value = min_date_in_master, 
                max_value = max_date_in_master,
                label = "Transaction Dates",
                label_visibility = "collapsed",
            )

            # streamlit enforces at least one date selection
            # so if user selects a single date, the second date is taken as the max date
            if len(res) == 1:
                min_date = res[0]
                max_date = max_date_in_master

                st.badge(f"Filtering for all dates since {min_date}", icon=":material/info:", color="orange")
            else:
                min_date, max_date = res
                
            # convert to datetime for pandas
            min_date = pd.to_datetime(min_date)
            max_date = pd.to_datetime(max_date)

            # description filter
            st.divider()
            css.markdown(css.underline("*Description*", thickness="1px"))
            description_filter_setting = st.text_input(
                placeholder = c.FILTER_PLACEHOLDER_TEXT,
                label_visibility = 'collapsed',
                label = "Description", 
            ) 

            # amount filter
            st.divider()
            css.markdown(css.underline("*Amount*", thickness="1px"))
            min_amount_in_master = int(master[c.AMOUNT_COLUMN].min())
            max_amount_in_master = int(master[c.AMOUNT_COLUMN].max())
            range_step = 10

            css.empty_space()

            # needed to ensure default values are rounded to the nearest range step
            # as they must be within the options, which are multiples of range_step
            mround = lambda x: range_step * round(x / range_step)
            min_amount, max_amount = st.select_slider(
                options=range(min_amount_in_master, max_amount_in_master + range_step, range_step),
                value=(mround(min_amount_in_master), mround(max_amount_in_master)),
                format_func=lambda x: f"-${abs(x):,}" if x < 0 else f"${x:,}",
                label="Amount", 
                label_visibility='collapsed'
            )
            
            # issuer filter
            st.divider()
            css.markdown(css.underline("*Statement Issuer*", thickness="1px"))
            filtered_issuers = st.multiselect(
                options = st.session_state.user.EXISTING_ISSUERS,
                default = st.session_state.user.EXISTING_ISSUERS,
                placeholder = c.FILTER_PLACEHOLDER_TEXT,
                label = "Statement Issuer",
                label_visibility ='collapsed',
            )

            # category filter            
            st.divider()
            css.markdown(css.underline("*Category*", thickness="1px"))

            # identify outdated categories; dropna() is used to exclude None
            outdated_categories = list(set(master[c.CATEGORY_COLUMN].dropna().unique()) - set(st.session_state.user.CATEGORIES))
            categories_including_outdated = st.session_state.user.CATEGORIES + outdated_categories

            UNCATEGORIZED_PILL_NAME = "Show Uncategorized Only"
            OUTDATED_CATEGORIES_PILL_NAME = "Filter by Outdated Categories"

            # Pill default priority order:
            # 1. OUTDATED_CATEGORIES_PILL_NAME
            # 2. UNCATEGORIZED_PILL_NAME 
            # 3. None
            default = OUTDATED_CATEGORIES_PILL_NAME if outdated_categories else UNCATEGORIZED_PILL_NAME if not(uncategorized.empty) else None
            
            # show quick filter pills, if applicable
            options = []
            category_pill = None
            options += [UNCATEGORIZED_PILL_NAME] if not(uncategorized.empty) else [] 
            options += [OUTDATED_CATEGORIES_PILL_NAME] if outdated_categories else []
            if options:
                category_pill = st.pills(
                    options = options,
                    default = default,
                    label = "Category", 
                    label_visibility='collapsed'
                )

            if category_pill == UNCATEGORIZED_PILL_NAME:
                # technically no options are required since the widget is disabled
                # but Streamlit has a minor bug where the passed placeholder str is not used if len(options) == 0
                options = st.session_state.user.CATEGORIES
                default = None
                disabled = True
                placeholder = "Filtering for uncategorized expenses."

            elif category_pill == OUTDATED_CATEGORIES_PILL_NAME:
                options = outdated_categories
                default = outdated_categories
                disabled = False
                placeholder = c.FILTER_PLACEHOLDER_TEXT

            else:
                options = st.session_state.user.CATEGORIES
                default = ["TBD"] if not(TBD.empty) else None
                disabled = False
                placeholder = c.FILTER_PLACEHOLDER_TEXT

            filtered_categories = st.multiselect(
                options = options,
                default = default,
                placeholder = placeholder,
                disabled = disabled,
                label = "Category",
                label_visibility ='collapsed',
            )

            # notes filter
            st.divider()
            css.markdown(css.underline("*Notes*", thickness="1px"))
            notes_filter_setting = st.text_input(
                placeholder = c.FILTER_PLACEHOLDER_TEXT,
                label_visibility = 'collapsed',
                label = "notes", 
            ) 

        date_filter = master[c.DATE_COLUMN].between(min_date, max_date)
        description_filter = master[c.DESCRIPTION_COLUMN].str.contains(description_filter_setting, case=False, na=False) if description_filter_setting else True
        amount_filter = master[c.AMOUNT_COLUMN].between(min_amount, max_amount)
        issuer_filter = master[c.ISSUER_COLUMN].isin(filtered_issuers) if filtered_issuers else True
        notes_filter = master[c.NOTES_COLUMN].str.contains(notes_filter_setting, case=False, na=False) if notes_filter_setting else True

        # this logic controls category_filter for the st.data_editor() widget
        if category_pill == UNCATEGORIZED_PILL_NAME:
            # if user explicitly filters for UNCATEGORIZED_PILL_NAME, respond accordingly
            category_filter = master[c.CATEGORY_COLUMN].isna()
        else:
            if filtered_categories:
                # if the user provided filtered_categories,
                # or, filter category section logic injected default values, then apply filters.
                category_filter = master[c.CATEGORY_COLUMN].isin(filtered_categories)
            else:
                # this is the path where no category filters have been applied
                # however, no selection == no filter
                category_filter = True         

        display_df = master[date_filter & description_filter & amount_filter & issuer_filter & category_filter & notes_filter]
        
        n1 = len(uncategorized)
        n2 = len(TBD)
        n3 = len(master[master[c.CATEGORY_COLUMN].isin(outdated_categories)])
        if n1 or n2 or n3:
            msg = f"""
                {f"{n1} transaction{'s' if n1 > 1 else ''} need{'s' if n1 == 1 else ''} to be categorized.  " if n1 > 0 else ""}
                {f"{n2} transaction{'s' if n2 > 1 else ''} marked for later.  " if n2 > 0 else ""}
                {f"{n3} transaction{'s' if n3 > 1 else ''} with outdated categories.  " if n3 > 0 else ""}
            """
            
            # removes empty lines
            clean = "\n".join(line for line in msg.splitlines() if line.strip())
            st.info(clean)
        else:
            msg = """
                You're all caught up! 🎉
            """
            st.success(msg)

        if outdated_categories:
            bullets = "\n".join(f"- {cat}" for cat in outdated_categories)
            error_msg = """
                Your data contains outdated categories that no longer exist in your categories model.  
                This data will not be used for analytics, until either the expenses are re-categorized or your categories model is updated.  
            """

            error_msg = f"{error_msg}\n\nOutdated categories:\n{bullets}"
            st.error(error_msg, icon="🚨")


        # category column config is handled separately
        # since it relies on user specific data
        c.column_configs[c.CATEGORY_COLUMN] = st.column_config.SelectboxColumn(
            label="Category",
            width="medium",
            # include outdated options in SelectboxColumn 
            # otherwise, Streamlit shows outdated category cells as empty
            options=categories_including_outdated
        )

        edited = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            column_config=c.column_configs
        )

        if st.button("💾 Save Changes"):
            # Update original master with edited categories
            for col in edited.columns:
                master.loc[edited.index, col] = edited[col]

            # upload updated master to S3
            st.session_state.user.update_master(master)
            
            h.save_toast()

            # force reload master data
            st.session_state.user.load_master()
            st.rerun()

    except Exception as e:
        st.error(f"Failed to handle master data: {e}")
        st.text("Detailed traceback:")
        st.code(traceback.format_exc())
