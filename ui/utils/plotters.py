import random
import config as c
import altair as alt
import streamlit as st
import utils.helpers as h
import plotly.graph_objects as go
from utils.helpers import hex_to_rgba

def sankey(df):
    """
        Generate Sankey diagram for user spending data

        Note:
            This avoids self-loops if a parent and child share the same name
            so, under such situations, those links are not rendered.
    """

    OVERSPENT_CUSTOM_NODE_NAME = "From Cash Reserve"    # Node targeted when income-(savings+expenses) > 0
    UNDERSPENT_CUSTOM_NODE_NAME = "To Cash Reserve"     # Node sourced when income-(savings+expenses) < 0

    source, target, value = [], [], []

    # net values for all categories
    totals = {
        category: abs(df[df[c.CATEGORY_COLUMN] == category][c.AMOUNT_COLUMN].sum())
        for category in st.session_state.user.CATEGORIES
    }

    # add primary nodes to totals
    # primary nodes are the top-level keys in the categories model
    for primary_node in st.session_state.user.CATEGORIES_BODY.keys():
        primary_node_categories = h.extract_categories(st.session_state.user.CATEGORIES_BODY.get(primary_node, []))
        totals[primary_node] = sum(totals.get(category, 0) for category in primary_node_categories)

    # add expense buckets to totals
    for bucket in st.session_state.user.EXPENSES_BODY.keys():
        bucket_categories = h.extract_categories(st.session_state.user.EXPENSES_BODY.get(bucket, []))
        totals[bucket] = sum(totals.get(category, 0) for category in bucket_categories)

    # add custom node values to totals
    total_outflows = totals[c.SAVINGS_PARENT_CATEGORY_KEY] + totals[c.EXPENSES_PARENT_CATEGORY_KEY]
    total_inflows = totals[c.INCOME_PARENT_CATEGORY_KEY]
    delta = total_inflows - total_outflows
    totals[UNDERSPENT_CUSTOM_NODE_NAME] = max(delta, 0)
    totals[OVERSPENT_CUSTOM_NODE_NAME] = abs(min(delta, 0))

    # Build labeled nodes with currency (includes both config + dynamic)
    raw_nodes = totals.keys()
    nodes = []
    node_values = []

    for category in raw_nodes:
        value_for_node = totals.get(category)
        label = f"{category} (${value_for_node:,.2f})" if value_for_node else category
        nodes.append(label)
        node_values.append(value_for_node)

    # Create index mapping based on raw node names
    node_indices = {category: i for i, category in enumerate(raw_nodes)}

    # INCOME_CATEGORIES -> INCOME
    for category in st.session_state.user.INCOME_CATEGORIES:
        if category != c.INCOME_PARENT_CATEGORY_KEY:
            source.append(node_indices[category])
            target.append(node_indices[c.INCOME_PARENT_CATEGORY_KEY])
            value.append(totals.get(category, 0))

    # INCOME → EXPENSES
    source.append(node_indices[c.INCOME_PARENT_CATEGORY_KEY])
    target.append(node_indices[c.EXPENSES_PARENT_CATEGORY_KEY])
    value.append(totals[c.EXPENSES_PARENT_CATEGORY_KEY])

    # INCOME → SAVINGS
    source.append(node_indices[c.INCOME_PARENT_CATEGORY_KEY])
    target.append(node_indices[c.SAVINGS_PARENT_CATEGORY_KEY])
    value.append(totals[c.SAVINGS_PARENT_CATEGORY_KEY])

    # EXPENSES → EXPENSES_BUCKETS → EXPENSES_CATEGORIES 
    for bucket in st.session_state.user.EXPENSES_BUCKETS:
        if bucket != c.EXPENSES_PARENT_CATEGORY_KEY:
            source.append(node_indices[c.EXPENSES_PARENT_CATEGORY_KEY])
            target.append(node_indices[bucket])
            value.append(totals.get(bucket, 0))

        for category in st.session_state.user.EXPENSES_BODY.get(bucket, []):
            if category != bucket and category in totals.keys():
                source.append(node_indices[bucket])
                target.append(node_indices[category])
                value.append(totals.get(category, 0))       

    # SAVINGS → SAVINGS_CATEGORIES
    for category in st.session_state.user.SAVINGS_CATEGORIES:
        if category != c.SAVINGS_PARENT_CATEGORY_KEY:
            source.append(node_indices[c.SAVINGS_PARENT_CATEGORY_KEY])
            target.append(node_indices[category])
            value.append(totals.get(category, 0))

    # Delta flow
    if delta > 0:
        source.append(node_indices[c.INCOME_PARENT_CATEGORY_KEY])
        target.append(node_indices[UNDERSPENT_CUSTOM_NODE_NAME])
        value.append(delta)
    elif delta < 0:
        source.append(node_indices[OVERSPENT_CUSTOM_NODE_NAME])
        target.append(node_indices[c.INCOME_PARENT_CATEGORY_KEY])
        value.append(abs(delta))

    # colors
    colors_map = {
        # tuple elements are ordered in hierarchy of categories.json keys
        c.INCOME_PARENT_CATEGORY_KEY: ("#014400", "#158013"),
        c.SAVINGS_PARENT_CATEGORY_KEY: ("#72b772", "#bae7ba"),
        c.EXPENSES_PARENT_CATEGORY_KEY: ("#d62728", "#f75d5d", "#ffcccc"),
        UNDERSPENT_CUSTOM_NODE_NAME: ("#17becf", "#7fdbff"),
        OVERSPENT_CUSTOM_NODE_NAME: ("#ff7f0e", "#ffbb78")
    }

    # assign node colors in the same order as nodes
    node_colors = []
    for cat in raw_nodes:
        node_color = colors_map.get(cat, None)
        if node_color:
            node_colors.append(node_color[0])
        else:
            if cat in st.session_state.user.INCOME_CATEGORIES:
                node_colors.append(colors_map[c.INCOME_PARENT_CATEGORY_KEY][1])
            elif cat in st.session_state.user.SAVINGS_CATEGORIES:
                node_colors.append(colors_map[c.SAVINGS_PARENT_CATEGORY_KEY][1])
            elif cat in st.session_state.user.EXPENSES_BUCKETS:
                node_colors.append(colors_map[c.EXPENSES_PARENT_CATEGORY_KEY][1])
            elif cat in st.session_state.user.EXPENSES_CATEGORIES:
                node_colors.append(colors_map[c.EXPENSES_PARENT_CATEGORY_KEY][2])
            else:
                # non-expenses colors; these are not rendered 
                # but to avoid index out of range errors, we still add to node_colors 
                node_colors.append("#000000")

    # color links by the target node
    link_colors = [hex_to_rgba(node_colors[t]) for t in target]

    # Build Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="black", width=1),
            label=nodes,
            color=node_colors,
            hovertemplate='%{label}<br><extra></extra>'
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br>"
        )
    )])

    fig.update_layout(
        # override any Streamlit theming injections
        # without this, I have observed major formatting issues with node annotation labels
        template=None,
        height=450,
        margin=dict(l=0, r=0, t=30, b=10),
        font=dict(size=14, weight=1000, family="Courier New"),
    )

    return fig

def sankey_json(data):
    """
    Builds a hierarchical Sankey diagram for Categories model,
    Avoids self-loops when a parent and child share the same name.

    Args:
        data (dict): categories.json as dict
    """

    if not isinstance(data, dict):
        raise TypeError("Input data must be of type dict.")
    
    source, target, value = [], [], []

    # INCOME_CATEGORIES -> INCOME
    for category in st.session_state.user.INCOME_CATEGORIES:
        if category != c.INCOME_PARENT_CATEGORY_KEY:
            source.append(category)
            target.append(c.INCOME_PARENT_CATEGORY_KEY)
            value.append(1)

    # INCOME → EXPENSES
    source.append(c.INCOME_PARENT_CATEGORY_KEY)
    target.append(c.EXPENSES_PARENT_CATEGORY_KEY)
    value.append(1)

    # INCOME → SAVINGS
    source.append(c.INCOME_PARENT_CATEGORY_KEY)
    target.append(c.SAVINGS_PARENT_CATEGORY_KEY)
    value.append(1)

    # EXPENSES → EXPENSES_BUCKETS → EXPENSES_CATEGORIES 
    for bucket in st.session_state.user.EXPENSES_BUCKETS:
        if bucket != c.EXPENSES_PARENT_CATEGORY_KEY:
            source.append(c.EXPENSES_PARENT_CATEGORY_KEY)
            target.append(bucket)
            value.append(1)

        for category in st.session_state.user.EXPENSES_BODY.get(bucket, []):
            if category != bucket and category in st.session_state.user.EXPENSES_CATEGORIES:
                source.append(bucket)
                target.append(category)
                value.append(1)      

    # SAVINGS → SAVINGS_CATEGORIES
    for category in st.session_state.user.SAVINGS_CATEGORIES:
        if category != c.SAVINGS_PARENT_CATEGORY_KEY:
            source.append(c.SAVINGS_PARENT_CATEGORY_KEY)
            target.append(category)
            value.append(1)

    # Build the ordered, deduplicated node list
    all_nodes = list(dict.fromkeys(source + target))
    idx_map   = { name:i for i, name in enumerate(all_nodes) }

    # colors
    colors = {
        c.INCOME_PARENT_CATEGORY_KEY: "#014400",
        c.SAVINGS_PARENT_CATEGORY_KEY: "#72b772",
        c.EXPENSES_PARENT_CATEGORY_KEY: "#d62728",
    }

    # assign node colors in the same order as nodes
    # for general expense categories, a random red shade is assigned
    red_variants = [
        "#B71414",  # dark red
        "#E51919",  # rich mid-dark red
        "#EA4747",  # medium red
        "#EF7575",  # soft mid-light red
        "#F4A3A3",  # light red
    ]

    # assign node colors in the same order as nodes
    # default color is used for general expense types
    node_colors = [colors.get(cat, random.choice(red_variants)) for cat in all_nodes]

    # # color links by the target node
    link_colors = [hex_to_rgba(node_colors[t]) for t in [idx_map[t] for t in target]]

    # Build Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=30,
            line=dict(color="black", width=1),
            label=all_nodes,
            color=node_colors,
            hovertemplate='%{label}<br><extra></extra>'
        ),
        link=dict(
            source=[idx_map[s] for s in source],
            target=[idx_map[t] for t in target],
            value=value,
            color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br><extra></extra>"
        )
    )])

    fig.update_layout(
        # override any Streamlit theming injections
        # without this, I have observed major formatting issues with node annotation labels
        template=None,
        height=450,
        margin=dict(l=0, r=0, t=30, b=10),
        font=dict(size=14, weight=1000, family="Courier New"),
    )

    return fig

def line_chart(df, x_values):
    """
    df: a DataFrame already grouped and filtered
    x_values: list of Python datetime objects for your ticks
    """

    # Base line + point chart
    base = alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(filled=True, size=40),
        strokeWidth=2.5
    ).encode(
        x=alt.X(
            c.GROUP_BY_COLUMN,
            type='temporal',
            title="Date",
            scale=alt.Scale(domain=x_values),
            axis=alt.Axis(
                values=x_values,
                labelAngle=0,
                labelOverlap=True,
                format="%b %Y"
            )
        ),
        y=alt.Y(
            c.AMOUNT_COLUMN,
            title="Amount",
            axis=alt.Axis(format="$,.0f")
        ),
        color=c.CATEGORY_COLUMN,
        tooltip=[
            alt.Tooltip(c.GROUP_BY_COLUMN, type="temporal", title="Date", format="%b %d, %Y"),
            alt.Tooltip(c.CATEGORY_COLUMN, type="nominal", title="Category"),
            alt.Tooltip(c.AMOUNT_COLUMN, type="quantitative", title="Amount", format="$,.0f"),
        ]
    )

    # Text labels on each point
    labels = alt.Chart(df).mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        size=14
    ).encode(
        x=alt.X(c.GROUP_BY_COLUMN, type='temporal', scale=alt.Scale(domain=x_values)),
        y=c.AMOUNT_COLUMN,
        text=alt.Text(c.AMOUNT_COLUMN, format="$,.0f"),
        color=c.CATEGORY_COLUMN,  # keep labels same color as line
        tooltip=alt.value(None)
    )

    # Layer them and set size
    return (base + labels).properties(
        width='container',
        height=400
    )
