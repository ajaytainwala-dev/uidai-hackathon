
import plotly.express as px
import plotly.graph_objects as go

def plot_trend(df, title="Trend Analysis", x_col='date', y_col='forecast', color_col='type'):
    """Line chart for trends."""
    if df.empty:
        return None
    fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title, markers=True)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_bar_metrics(df, x_col, y_cols, title="Metrics"):
    """Bar chart for comparing metrics."""
    if df.empty:
        return None
    # Melt if multiple Y columns
    if isinstance(y_cols, list) and len(y_cols) > 1:
        df_melt = df.melt(id_vars=[x_col], value_vars=y_cols, var_name='Metric', value_name='Count')
        fig = px.bar(df_melt, x=x_col, y='Count', color='Metric', title=title, barmode='group')
    else:
        y = y_cols[0] if isinstance(y_cols, list) else y_cols
        fig = px.bar(df, x=x_col, y=y, title=title)
        
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_heatmap(df, x_col, y_col, value_col, title="Heatmap"):
    """Heatmap for State/District vs Time or other dimensions."""
    if df.empty:
        return None
    # Pivot for heatmap matrix
    if len(df[x_col].unique()) > 50:
        top_districts = df.groupby(x_col)[value_col].sum().nlargest(20).index
        df = df[df[x_col].isin(top_districts)]

    matrix = df.pivot_table(index=y_col, columns=x_col, values=value_col, fill_value=0)
    fig = px.imshow(matrix, title=title, aspect='auto', color_continuous_scale='Viridis')
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_treemap(df, path_cols, value_col, title="Treemap Distribution"):
    """Hierarchical Treemap."""
    if df.empty:
        return None
    fig = px.treemap(df, path=path_cols, values=value_col, title=title)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_box_distribution(df, x_col, y_col, title="Distribution Analysis"):
    """Box plot for detecting outliers/distribution."""
    if df.empty:
        return None
    fig = px.box(df, x=x_col, y=y_col, title=title, points="outliers")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_correlation_heatmap(corr_matrix, title="Correlation Matrix"):
    """Specific heatmap for correlation matrices."""
    if corr_matrix.empty:
        return None
    fig = px.imshow(corr_matrix, text_auto=True, title=title, color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_stacked_area(df, x_col, y_col, color_col, title="Stacked Area"):
    """Stacked Area Chart."""
    if df.empty:
        return None
    fig = px.area(df, x=x_col, y=y_col, color=color_col, title=title)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_scatter(df, x_col, y_col, size_col=None, color_col=None, title="Scatter Plot"):
    """Scatter Plot for 3D multivariate analysis (X, Y, Size, Color)."""
    if df.empty:
        return None
    fig = px.scatter(df, x=x_col, y=y_col, size=size_col, color=color_col, title=title, hover_data=df.columns)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_radar(df, r_col, theta_col, title="Radar Chart"):
    """Radar Chart for multi-variable comparison."""
    if df.empty:
        return None
    fig = px.line_polar(df, r=r_col, theta=theta_col, line_close=True, title=title)
    fig.update_traces(fill='toself')
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_funnel(data_dict, title="Funnel Chart"):
    """Funnel Chart from dictionary {Stage: Value}."""
    if not data_dict:
        return None
    fig = px.funnel(x=list(data_dict.values()), y=list(data_dict.keys()), title=title)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_gauge(value, title="Gauge", min_val=0, max_val=100):
    """Gauge Indicator."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        gauge = {
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "#3b82f6"},
            'bgcolor': "#1f2937",
        }
    ))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_bullet(title, current_val, target_val, range_max):
    """Bullet Chart for KPI vs Target."""
    fig = go.Figure(go.Indicator(
        mode = "number+gauge+delta", value = current_val,
        delta = {'reference': target_val, 'increasing': {'color': '#10b981'}},
        domain = {'x': [0.1, 1], 'y': [0.2, 0.9]},
        title = {'text': title},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [None, range_max]},
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75,
                'value': target_val
            },
            'steps': [
                {'range': [0, range_max*0.5], 'color': "#374151"},
                {'range': [range_max*0.5, range_max*0.8], 'color': "#4b5563"}
            ],
            'bar': {'color': "#3b82f6"}
        }
    ))
    fig.update_layout(height=150, margin={'t':10, 'b':10, 'l':10, 'r':10}, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def plot_choropleth(df, geojson, locations_col, color_col, featureidkey, title="Geospatial Map"):
    """Choropleth Map for geospatial analysis."""
    if df.empty or not geojson:
        return None
    
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations=locations_col,
        featureidkey=featureidkey,
        color=color_col,
        title=title,
        color_continuous_scale="Viridis",
        projection="mercator"
    )
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin={"r":0,"t":40,"l":0,"b":0})
    return fig
