import plotly.graph_objs as go
import plotly.io as pio

def create_question_pie_chart(question_text, mean_score, frequencies, total_responses):
    """
    Google Forms‑style donut chart for a single Likert question.
    Uses Google's official colors: red → yellow → green → blue.
    """
    labels = ['1 - Strongly\nDisagree', '2 - Disagree', '3 - Neutral', '4 - Agree', '5 - Strongly\nAgree']
    values = [frequencies.get(i, 0) for i in range(1, 6)]
    
    # Google Forms official colors
    colors = ['#db4437', '#f4b400', '#4285f4', '#0f9d58', '#673ab7']
    
    # Remove zero-value slices
    filtered_labels = []
    filtered_values = []
    filtered_colors = []
    for i, v in enumerate(values):
        if v > 0:
            filtered_labels.append(labels[i])
            filtered_values.append(v)
            filtered_colors.append(colors[i])
    
    if not filtered_values:
        filtered_labels = ['No responses']
        filtered_values = [1]
        filtered_colors = ['#dadce0']
    
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=filtered_labels,
        values=filtered_values,
        hole=0.6,
        marker=dict(colors=filtered_colors, line=dict(color='white', width=2)),
        textinfo='percent',
        textposition='outside',
        sort=False,
        hovertemplate='%{label}: %{value} responses<extra></extra>'
    ))
    
    # Center annotation with average score
    fig.add_annotation(
        text=f"<b style='font-size:26px;'>{mean_score:.1f}</b><br><span style='font-size:10px;color:#5f6368;'>Average</span>",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(color='#202124'),
        bgcolor='rgba(255,255,255,0)'
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{question_text}</b><br><span style='font-size:12px;color:#5f6368;'>{total_responses} responses</span>",
            x=0.5,
            xanchor='center',
            font=dict(size=14, color='#202124')
        ),
        height=420,
        margin=dict(t=80, b=10, l=10, r=10),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return pio.to_html(fig, full_html=False)

def create_overall_pie_chart(labels, values, title):
    """Pie chart for overall satisfaction."""
    colors = ['#db4437', '#f4b400', '#4285f4', '#0f9d58', '#673ab7']
    
    filtered_labels = []
    filtered_values = []
    filtered_colors = []
    for i, v in enumerate(values):
        if v > 0:
            filtered_labels.append(labels[i])
            filtered_values.append(v)
            filtered_colors.append(colors[i])
    
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=filtered_labels,
        values=filtered_values,
        hole=0.55,
        marker=dict(colors=filtered_colors, line=dict(color='white', width=2)),
        textinfo='label+percent',
        textposition='outside',
        sort=False
    ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=14, color='#202124')
        ),
        height=420,
        margin=dict(t=60, b=10, l=10, r=10),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return pio.to_html(fig, full_html=False)

def create_text_response_card(question_text, responses):
    """HTML card for open‑ended text responses – Google Forms style."""
    html = f"""
    <div class="gf-text-card">
        <div class="gf-text-title">{question_text}</div>
        <div class="gf-text-count">{len(responses)} responses</div>
        <div class="gf-text-list">
    """
    if responses:
        for resp in responses[:15]:
            html += f'<div class="gf-text-item">"{resp}"</div>'
        if len(responses) > 15:
            html += f'<div class="gf-text-more">+ {len(responses) - 15} more responses</div>'
    else:
        html += '<div class="gf-text-empty">No responses yet.</div>'
    html += '</div></div>'
    return html

def create_multiple_choice_chart(question_text, options, counts, total_responses):
    """Horizontal bar chart for multiple choice questions – Google Forms style."""
    filtered_options = []
    filtered_counts = []
    for opt in options:
        cnt = counts.get(opt, 0)
        if cnt > 0:
            filtered_options.append(opt)
            filtered_counts.append(cnt)
    
    if not filtered_options:
        filtered_options = ['No responses']
        filtered_counts = [1]
    
    colors = ['#673ab7', '#9575cd', '#b39ddb', '#d1c4e9', '#ede7f6',
              '#7e57c2', '#5e35b1', '#4527a0', '#311b92', '#b388ff']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=filtered_counts,
        y=filtered_options,
        orientation='h',
        marker_color=colors[:len(filtered_options)],
        text=filtered_counts,
        textposition='outside',
        hovertemplate='%{y}: %{x} responses<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>{question_text}</b><br><span style='font-size:12px;color:#5f6368;'>{total_responses} responses</span>",
            x=0.5,
            xanchor='center',
            font=dict(size=14, color='#202124')
        ),
        xaxis_title='Number of responses',
        height=250,
        margin=dict(t=80, b=10, l=10, r=30),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False
    )
    
    return pio.to_html(fig, full_html=False)