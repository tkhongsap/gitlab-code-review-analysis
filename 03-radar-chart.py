#!/usr/bin/env python3
import json
import plotly.graph_objects as go
import numpy as np

# Path to the summary average scores JSON file.
JSON_FILE = "docs/extracted_scores/summary_average_scores.json"
# Output HTML file for the radar chart.
OUTPUT_HTML = "docs/extracted_scores/summary_radar_chart.html"

def load_scores(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def create_radar_chart(data):
    # Exclude "Overall Score" and "Metadata" from the data so only the seven score dimensions are used.
    filtered_data = {k: v for k, v in data.items() 
                    if k not in ["Overall Score", "Metadata"]}
    categories = list(filtered_data.keys())
    values = list(filtered_data.values())

    # Calculate angles for heptagon (7 points)
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False)
    # Rotate to start from the top
    angles = np.roll(angles, -2)
    
    # Convert to degrees and create labels list
    angles_deg = np.degrees(angles)
    labels = ['' for _ in range(len(categories))]
    # Create hover text and display text
    hover_text = []
    display_text = []
    # Calculate text positions slightly outside the points
    text_r = []  # Slightly larger than the actual values for text positioning
    for i, cat in enumerate(categories):
        labels[i] = cat
        hover_text.append(f"{cat}<br>Score: {values[i]:.1f}/10")
        display_text.append(f"{values[i]:.1f}")
        # Add 0.5 to push text outside the points
        text_r.append(values[i] + 0.5)
    
    fig = go.Figure(
        data=[
        # The filled radar chart
        go.Scatterpolar(
            r=values,
            theta=angles_deg,
            hovertext=hover_text,
            hoverinfo="text",
            fill='toself',
            name='Average Scores',
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=8),
            mode='lines+markers'  # Show lines and markers only
        ),
        # Separate trace for the text labels
        go.Scatterpolar(
            r=text_r,
            theta=angles_deg,
            text=display_text,
            textposition="middle center",
            textfont=dict(size=14, color="#1f77b4", weight="bold"),
            mode="text",
            showlegend=False,
            hoverinfo="none"
        )
        ]
    )
    
    # Customize the layout for a professional look.
    fig.update_layout(
        polar=dict(
            bgcolor="#f6f6f6",
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=14, color="#333333"),
                gridcolor="#BFBFBF",
                gridwidth=1
            ),
            angularaxis=dict(
                tickfont=dict(size=16, color="#333333"),  # Bigger font for dimension labels
                gridcolor="#BFBFBF",
                gridwidth=1,
                ticktext=labels,
                tickvals=angles_deg,
                direction='clockwise'
            )
        ),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial, sans-serif", color="#333333"),
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False
    )
    
    return fig

def create_dashboard(data, metadata):
    # Get the radar chart HTML
    fig = create_radar_chart(data)
    chart_html = fig.to_html(full_html=False, include_plotlyjs=True)

    # Create the HTML template with Shadcn-like styling
    dashboard_html = f"""
    <html>
    <head>
        <title>Code Review Dashboard</title>
        <style>
            body {{
                margin: 0;
                padding: 2rem;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
                background-color: #f9fafb;
                color: #111827;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                margin-bottom: 2rem;
            }}
            .title {{
                font-size: 2rem;
                font-weight: 600;
                color: #111827;
                margin-bottom: 1rem;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                margin-bottom: 2rem;
            }}
            .metric-card {{
                background: white;
                border-radius: 0.5rem;
                padding: 1.5rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s;
            }}
            .metric-card:hover {{
                transform: translateY(-2px);
            }}
            .metric-title {{
                font-size: 0.875rem;
                font-weight: 500;
                color: #6b7280;
                margin-bottom: 0.5rem;
            }}
            .metric-value {{
                font-size: 1.875rem;
                font-weight: 600;
                color: #111827;
            }}
            .chart-container {{
                background: white;
                border-radius: 0.5rem;
                padding: 2rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">Code Review Analytics</h1>
            </div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">Total Files Reviewed</div>
                    <div class="metric-value">{metadata["Total Files Processed"]}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Total Projects</div>
                    <div class="metric-value">{metadata["Total Projects"]}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Overall Score</div>
                    <div class="metric-value">{data["Overall Score"]}/10</div>
                </div>
            </div>
            <div class="chart-container">
                {chart_html}
            </div>
        </div>
    </body>
    </html>
    """
    return dashboard_html

def main():
    data = load_scores(JSON_FILE)
    metadata = data.get("Metadata", {})
    
    # Create the full dashboard HTML
    dashboard_html = create_dashboard(data, metadata)
    
    # Save as an interactive HTML file.
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    print(f"Radar chart saved to: {OUTPUT_HTML}")

if __name__ == "__main__":
    main() 