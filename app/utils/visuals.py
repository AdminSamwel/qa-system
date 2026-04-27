import plotly.graph_objs as go
import plotly.io as pio
import numpy as np

def create_bar_chart(x_data, y_data, title, errors=None):
    """Bar chart with optional error bars (standard deviation)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_data,
        marker_color='#009EDB',
        error_y=dict(type='data', array=errors, visible=True) if errors else None
    ))
    fig.update_layout(title=title, xaxis_tickangle=-45, margin=dict(b=100), height=400)
    return pio.to_html(fig, full_html=False)

def create_pie_chart(labels, values, title):
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3,
                                 marker=dict(colors=['#009EDB', '#2E3192', '#6c757d', '#17a2b8', '#28a745']))])
    fig.update_layout(title=title)
    return pio.to_html(fig, full_html=False)

def create_radar_chart(categories, values, title, fill='toself'):
    """Spider/radar chart for multi-dimensional comparison."""
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill=fill,
        marker=dict(color='#009EDB')
    ))
    fig.update_layout(title=title, polar=dict(radialaxis=dict(visible=True, range=[0,5])), height=400)
    return pio.to_html(fig, full_html=False)

def create_heatmap(x_labels, y_labels, z_data, title):
    """Heatmap for question-by-section mean scores."""
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        colorscale='Blues',
        hoverongaps=False
    ))
    fig.update_layout(title=title, xaxis_title='Question', yaxis_title='Section')
    return pio.to_html(fig, full_html=False)

def create_line_chart(x_data, y_data, title):
    fig = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='lines+markers', marker=dict(color='#009EDB')))
    fig.update_layout(title=title)
    return pio.to_html(fig, full_html=False)