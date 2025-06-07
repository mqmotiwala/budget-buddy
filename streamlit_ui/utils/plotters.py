import config as c 
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def sankey(df):
    CUSTOM_NODES = {
        # node_label: explanation
        "Expenses": "Parent node for all expenses",
        "To Cash Reserve": "Node targeted when income-(savings+expenses) > 0",
        "From Cash Reserve": "Node sourced when income-(savings+expenses) < 0"
    }
    
    source, target, value = [], [], []

    # define nodes 
    nodes = c.CATEGORIES + list(CUSTOM_NODES.keys())
    node_indices = {category: i for i, category in enumerate(nodes)}

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

    # link Income → Expenses
    source.append(node_indices["Income"])
    target.append(node_indices["Expenses"])
    value.append(primary_nodes_net_values["Expenses"])

    # link Income → Savings
    source.append(node_indices["Income"])
    target.append(node_indices["Savings"])
    value.append(primary_nodes_net_values["Savings"])

    # link Expenses → each expense category
    for category in c.EXPENSES_CATEGORIES:
        source.append(node_indices["Expenses"])
        target.append(node_indices[category])
        value.append(totals.get(category, 0))

    # Handle overspending/underspending
    total_outflows = primary_nodes_net_values["Savings"] + primary_nodes_net_values["Expenses"]
    total_inflows = primary_nodes_net_values["Income"]
    delta = total_inflows - total_outflows
    if delta > 0:
        source.append(node_indices["Income"])
        target.append(node_indices["To Cash Reserve"])
        value.append(delta)
    else:
        source.append(node_indices["From Cash Reserve"])
        target.append(node_indices["Income"])
        value.append(abs(delta))

    # Build Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
        )
    )])

    fig.update_layout(title="Income vs Spending Sankey", font_size=12)
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
