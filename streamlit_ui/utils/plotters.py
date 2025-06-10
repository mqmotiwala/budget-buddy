import config as c 
import pandas as pd
import plotly.graph_objects as go
import altair as alt
from utils.helpers import hex_to_rgba

def sankey(df):
    CUSTOM_NODES = {
        "Expenses": "Parent node for all expenses",
        "To Cash Reserve": "Node targeted when income-(savings+expenses) > 0",
        "From Cash Reserve": "Node sourced when income-(savings+expenses) < 0"
    }

    source, target, value = [], [], []

    # net values for all categories
    totals = {
        category: abs(df[df[c.CATEGORY_COLUMN] == category][c.AMOUNT_COLUMN].sum())
        for category in df[c.CATEGORY_COLUMN].unique()
    }

    # net values for primary nodes
    primary_nodes_net_values = {}
    for primary_node in c.CATEGORIES_BODY.keys():
        primary_node_categories = c.extract_categories(c.CATEGORIES_BODY[primary_node])
        primary_nodes_net_values[primary_node] = sum(totals.get(category, 0) for category in primary_node_categories)

    # Determine flow delta
    total_outflows = primary_nodes_net_values["Savings"] + primary_nodes_net_values["Expenses"]
    total_inflows = primary_nodes_net_values["Income"]
    delta = total_inflows - total_outflows

    # Compute value for custom nodes
    custom_node_values = {
        "To Cash Reserve": max(delta, 0),
        "From Cash Reserve": abs(min(delta, 0)),
        "Expenses": primary_nodes_net_values["Expenses"]
    }

    # Build labeled nodes with currency (includes both config + dynamic)
    raw_nodes = c.CATEGORIES + list(CUSTOM_NODES.keys())
    nodes = []
    node_values = []

    for category in raw_nodes:
        value_for_node = (
            primary_nodes_net_values.get(category) or
            totals.get(category) or
            custom_node_values.get(category, 0)
        )
        label = f"{category} (${value_for_node:,.2f})" if value_for_node else category
        nodes.append(label)
        node_values.append(value_for_node)

    # Create index mapping based on raw node names
    node_indices = {category: i for i, category in enumerate(raw_nodes)}

    # Income → Expenses
    source.append(node_indices["Income"])
    target.append(node_indices["Expenses"])
    value.append(primary_nodes_net_values["Expenses"])

    # Income → Savings
    source.append(node_indices["Income"])
    target.append(node_indices["Savings"])
    value.append(primary_nodes_net_values["Savings"])

    # Expenses → each expense category
    for category in c.EXPENSES_CATEGORIES:
        source.append(node_indices["Expenses"])
        target.append(node_indices[category])
        value.append(totals.get(category, 0))

    # Delta flow
    if delta > 0:
        source.append(node_indices["Income"])
        target.append(node_indices["To Cash Reserve"])
        value.append(delta)
    elif delta < 0:
        source.append(node_indices["From Cash Reserve"])
        target.append(node_indices["Income"])
        value.append(abs(delta))

    # colors
    colors = {
        "Income": "#014400",
        "Savings": "#72b772",
        "Expenses": "#d62728",
        "To Cash Reserve": "#17becf",
        "From Cash Reserve": "#ff7f0e"
    }

    # assign node colors in the same order as nodes
    # default color is used for general expense types
    node_colors = [colors.get(cat, "#da7878") for cat in raw_nodes]

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
