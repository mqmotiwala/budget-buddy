import config as c
import pandas as pd
import streamlit as st
import utils.css as css
import utils.helpers as h
import utils.plotters as p
from datetime import timedelta as td

def show_analytics():
    # ensure master data is loaded
    if not hasattr(st.session_state.user, "master"):
        st.session_state.user.load_master()
    master = st.session_state.user.master

    if master is None or master.empty:
        return 
    
    css.divider()
    st.header("💡Review Analytics")

    time_range = st.pills(
        label="Select analysis time range",
        options = c.TIME_RANGES,
        default = "Trailing 3 Months"
    )

    min_date_in_master = master[c.DATE_COLUMN].min()
    max_date_in_master = master[c.DATE_COLUMN].max()

    start, end = None, None
    if time_range == "All Time":
        start, end = min_date_in_master, max_date_in_master
    elif time_range == "Custom":
        try:
            start, end = st.date_input(
                label = "date_input",
                label_visibility = "collapsed",
                value = [],
                min_value = min_date_in_master, 
                max_value = max_date_in_master
            )
        except ValueError:
            # user has not finished making a selection
            pass 
    elif time_range:
        start, end = h.get_time_range_dates(time_range)
    else:
        # no time_range selection has been made yet 
        st.info(c.SELECTION_PROMPT)

    if start and end:
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)

        # prepare analysis dataframe
        # copy to avoid modifying the original master DataFrame
        # without copy, Pandas raises a SettingWithCopyWarning 
        # and behavior can be unpredictable 
        analyze = master[
            master[c.DATE_COLUMN].between(start, end) &
            master[c.CATEGORY_COLUMN].notna() &
            ~master[c.CATEGORY_COLUMN].isin(st.session_state.user.NON_EXPENSES_CATEGORIES)
        ].copy()

        st.markdown(f"Analyzing :rainbow[{start.strftime(c.PREFERRED_UI_DATE_FORMAT_STRFTIME)} - {end.strftime(c.PREFERRED_UI_DATE_FORMAT_STRFTIME)}]")
        
        if analyze.empty:
            st.write("There is no categorized data for me to analyze. 😔")
            return 
        
        st.markdown("##### *Deep Dives by Category*")
        filtered_categories = st.multiselect(
            label = "Filter by category",
            options = [cat for cat in st.session_state.user.CATEGORIES if cat not in st.session_state.user.NON_EXPENSES_CATEGORIES], 
            default = None,
            placeholder = c.SELECTION_PROMPT,
            label_visibility ='collapsed'
        )

        if filtered_categories:
            if (end - start) > td(days=60):
                # group by month
                analyze[c.GROUP_BY_COLUMN] = analyze[c.DATE_COLUMN].values.astype("datetime64[M]")
            elif (end - start) > td(days=15):
                # group by week
                analyze[c.GROUP_BY_COLUMN] = analyze[c.DATE_COLUMN].apply(lambda x: x - td(days=x.weekday()))
            else:
                # group by day
                analyze[c.GROUP_BY_COLUMN] = analyze[c.DATE_COLUMN]

            x_values = sorted(analyze[c.GROUP_BY_COLUMN].unique())

            grouped = analyze.groupby([c.CATEGORY_COLUMN, c.GROUP_BY_COLUMN])[c.AMOUNT_COLUMN].sum().abs().reset_index()
            filtered = grouped[grouped[c.CATEGORY_COLUMN].isin(filtered_categories)]

            # build Python‐datetime tick list
            raw_vals = sorted(filtered[c.GROUP_BY_COLUMN].unique())
            x_values = [pd.to_datetime(val).to_pydatetime() for val in raw_vals]

            st.altair_chart(
                p.line_chart(filtered, x_values),
                use_container_width=True
            )

        st.markdown("##### *Cashflow At A Glance*")
        st.plotly_chart(p.sankey(analyze), use_container_width=True)

