import traceback
import pandas as pd
import streamlit as st
import utils.helpers as h
import config_general as c

def show_categorize():
    # ensure master data is loaded
    if "master" not in st.session_state:
        st.session_state.master = h.load_master()
    master = st.session_state.master

    st.divider()
    st.header("🏷️Categorize Expenses")

    if master is None or master.empty:
        st.write("No categorized expenses found. Start by uploading some statements.")
        return 
    
    try:
        uncategorized = master[master[c.CATEGORY_COLUMN].isna()]
        TBD = master[(master[c.CATEGORY_COLUMN] == "TBD")]

        with st.expander("Apply filters", icon=":material/tune:"):
            # date filter
            prompt_text = "Filter by transaction dates"
            st.text(prompt_text)

            min_date_in_master = master[c.DATE_COLUMN].min()
            max_date_in_master = master[c.DATE_COLUMN].max()
            res = st.date_input(
                label = "date_input",
                label_visibility = "collapsed",
                value = [min_date_in_master, max_date_in_master],
                min_value = min_date_in_master, 
                max_value = max_date_in_master
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
            description_filter_setting = h.create_text_filter(prompt_text="Filter by description")

            # amount filter
            st.divider()
            prompt_text = "Filter by transaction amount"
            st.text(prompt_text)
            min_amount_in_master = int(master[c.AMOUNT_COLUMN].min())
            max_amount_in_master = int(master[c.AMOUNT_COLUMN].max())
            range_step = 10

            # needed to ensure default values are rounded to the nearest range step
            # as they must be within the options, which are multiples of range_step
            mround = lambda x: range_step * round(x / range_step)
            min_amount, max_amount = st.select_slider(
                label=prompt_text, 
                options=range(min_amount_in_master, max_amount_in_master + range_step, range_step),
                value=(mround(min_amount_in_master), mround(max_amount_in_master)),
                format_func=lambda x: f"-${abs(x):,}" if x < 0 else f"${x:,}",
                label_visibility='collapsed'
            )
            
            # issuer filter
            filtered_issuers = h.create_multiselect_filter(prompt_text="Filter by statement issuer", options=st.session_state.EXISTING_ISSUERS, default=st.session_state.EXISTING_ISSUERS)

            # category filter            
            st.divider()
            prompt_text = "Filter by category"
            st.text(prompt_text)

            # if there are uncategorized expenses, filter only for them by default
            show_uncategorized_only = st.toggle("Show uncategorized only", value=not(uncategorized.empty))

            # otherwise, let user decide which categories to review
            filtered_categories = h.create_multiselect_filter(
                prompt_text = "Filter by category", 
                options = st.session_state.CATEGORIES, 
                # if there are no more uncategorized transactions, except for those marked as "TBD", then default to showing those.
                default = ["TBD"] if uncategorized.empty and not(TBD.empty) else None,
                disabled = show_uncategorized_only,
                include_aesthetics_boilerplate=False
            )

            # notes filter
            notes_filter_setting = h.create_text_filter("Filter by notes")

        date_filter = master[c.DATE_COLUMN].between(min_date, max_date)
        description_filter = master[c.DESCRIPTION_COLUMN].str.contains(description_filter_setting, case=False, na=False) if description_filter_setting else True
        amount_filter = master[c.AMOUNT_COLUMN].between(min_amount, max_amount)
        issuer_filter = master[c.ISSUER_COLUMN].isin(filtered_issuers) if filtered_issuers else True
        category_filter = master[c.CATEGORY_COLUMN].isna() if show_uncategorized_only else master[c.CATEGORY_COLUMN].isin(filtered_categories) if filtered_categories and len(filtered_categories) != len(c.CATEGORIES) else True
        notes_filter = master[c.NOTES_COLUMN].str.contains(notes_filter_setting, case=False, na=False) if notes_filter_setting else True

        display_df = master[date_filter & description_filter & amount_filter & issuer_filter & category_filter & notes_filter]

        if uncategorized.empty and TBD.empty:
            st.markdown(":rainbow[Nice!] All expenses are categorized.")
            st.text("You can still edit existing categories below.")
        else:
            st.markdown(f":rainbow[{len(uncategorized) + len(TBD)}/{len(master)}] expenses are uncategorized!")

        # category column config is handled separately
        # since it relies on user specific data
        c.column_configs[c.CATEGORY_COLUMN] = st.column_config.SelectboxColumn(
            label="Category",
            width="medium",
            options=st.session_state.CATEGORIES
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
            h.update_master(master)
            
            st.success("Categorized data synced to cloud.")

            # force reload master data
            st.session_state.master = h.load_master()
            st.rerun()

    except Exception as e:
        st.error(f"Failed to handle master data: {e}")
        st.text("Detailed traceback:")
        st.code(traceback.format_exc())
