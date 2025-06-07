import config as c 
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
        "To Cash Reserve": delta if delta > 0 else 0,
        "From Cash Reserve": abs(delta) if delta < 0 else 0,
        "Expenses": primary_nodes_net_values["Expenses"]
    }

    # Build labeled nodes with currency (includes both config + dynamic)
    raw_nodes = c.CATEGORIES + list(CUSTOM_NODES.keys())
    nodes = []
    node_customdata = []
    node_values = []

    for category in raw_nodes:
        value_for_node = (
            primary_nodes_net_values.get(category) or
            totals.get(category) or
            custom_node_values.get(category, 0)
        )
        label = f"{category} (${value_for_node:,.2f})" if value_for_node else category
        nodes.append(label)
        node_customdata.append(f"${value_for_node:,.2f}")
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

    # Delta-based flow
    if delta > 0:
        source.append(node_indices["Income"])
        target.append(node_indices["To Cash Reserve"])
        value.append(delta)
    elif delta < 0:
        source.append(node_indices["From Cash Reserve"])
        target.append(node_indices["Income"])
        value.append(abs(delta))

    # Build Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            customdata=node_customdata,
            hovertemplate='%{label}<br>Total: %{customdata}<extra></extra>',
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
        )
    )])

    fig.update_layout(height=450)
    return fig

def sunburst_pie(df):
    # Aggregate absolute costs by category
    grouped = df.groupby(c.CATEGORY_COLUMN, as_index=False)[c.AMOUNT_COLUMN].sum()
    grouped[c.AMOUNT_COLUMN] = grouped[c.AMOUNT_COLUMN].abs()

    grouped["category_group"] = grouped["category"].apply(lambda x: x if x in ["Savings, Income"] else "Expenses")

    fig = px.sunburst(grouped, path=["category_group", "category"], values='amount')
    
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Amount: %{value}<br>Percent of %{parent}: %{percentParent:.1%}<br>Percent of total: %{percentRoot:.1%}<extra></extra>'
    )

    return fig
