import dash
from dash import html, dcc, Input, Output, State
import requests
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta


app = dash.Dash(__name__, external_stylesheets=[
    'https://codepen.io/chriddyp/pen/bWLwgP.css'
])
server = app.server
API = "http://localhost:5000"


card_colors = {"temperature": "#E377C2", "humidity": "#17BECF", "light": "#2CA02C", "co2": "#FF7F0E"}
units = {"temperature": "°C", "humidity": "%", "light": "lx", "co2": "ppm"}
metrics = ["temperature", "humidity", "light", "co2"]
preset_choices = [
    ("Last 10 mins", 1/6),
    ("Last 30 mins", 0.5),
    ("Last 1 hour", 1),
    ("Last 3 hours", 3),
    ("Last 6 hours", 6),
    ("Last 12 hours", 12),
    ("Today", 24)
]


def fetch_rooms():
    try:
        return requests.get(f"{API}/api/rooms").json()
    except:
        return []


def fetch_thresholds():
    try:
        return requests.get(f"{API}/api/thresholds").json()
    except:
        return {}


def fetch_latest(room):
    try:
        return requests.get(f"{API}/api/latest", params={"room": room}).json()
    except:
        return []


import pytz


def fetch_history(room, metric, start_dt, end_dt):
    start_str = start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f"[DASH DEBUG] Fetching history for {room}, metric {metric}: {start_str} to {end_str}")
    try:
        resp = requests.get(
            f"{API}/api/history",
            params={"room": room, "metric": metric, "start_time": start_str, "end_time": end_str, "limit": 1000}
        )
        df = pd.DataFrame(resp.json())
        if not df.empty and "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            if df["time"].dt.tz is None:
                df["time"] = df["time"].dt.tz_localize('UTC')
            df["time"] = df["time"].dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
            return df.dropna(subset=["time"])
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Fetching history: {e}")
        return pd.DataFrame()


def fetch_alerts(page=1, per_page=15):
    try:
        return requests.get(f"{API}/api/alerts", params={"page": page, "per_page": per_page}).json()
    except:
        return []


app.layout = html.Div(style={"maxWidth": "1150px", "margin": "32px auto", "fontFamily": "Arial,sans-serif", "paddingBottom": 30}, children=[
    html.H1("SMARTGUARD", style={"color": "#222", "fontWeight": "700", "fontSize": "2.1rem", "margin": "12px 0 17px 5px"}),
    html.Div([
        html.Label("Room", style={"fontWeight": "bold", "marginRight": "8px"}),
        dcc.Dropdown(id="room-selector", options=[], placeholder="Select Room", style={"width": "200px", "display": "inline-block"}),
        html.Label("View Range", style={"fontWeight": "bold", "marginLeft": "18px", "marginRight": "8px"}),
        dcc.Dropdown(
            id="range-dropdown",
            options=[{"label": label, "value": hrs} for label, hrs in preset_choices],
            value=1,
            clearable=False,
            style={"width": "135px", "display": "inline-block"}
        ),
        dcc.DatePickerSingle(id="custom-date", placeholder="Pick date", style={"marginLeft": "12px"})
    ], style={"marginBottom": "18px"}),
    html.Div(id="live-metrics", style={"display": "flex", "gap": "24px", "margin": "18px 0 7px 0"}),
    html.Div([
        html.H2("Room Metrics Over Time", style={"color": "#555", "fontSize": "1.19rem", "margin": "0 0 7px 12px"}),
        dcc.Graph(id="metrics-graph", style={"height": "395px"})
    ], style={"backgroundColor": "#FFF", "padding": "16px", "borderRadius": "11px", "boxShadow": "0 2px 13px rgba(0,0,0,0.07)", "marginBottom": "14px"}),
    html.Div([
        html.H2("Individual Metrics (Past Trends)", style={"color": "#444", "fontWeight": "650", "fontSize": "1.15rem", "marginBottom": "12px", "marginLeft": 6}),
        html.Div([
            dcc.Graph(id="metric-plot-temperature", style={"height": "220px", "width": "47%", "display": "inline-block", "marginRight": "4%"}),
            dcc.Graph(id="metric-plot-humidity", style={"height": "220px", "width": "47%", "display": "inline-block"}),
        ], style={"marginBottom": "7px"}),
        html.Div([
            dcc.Graph(id="metric-plot-light", style={"height": "220px", "width": "47%", "display": "inline-block", "marginRight": "4%"}),
            dcc.Graph(id="metric-plot-co2", style={"height": "220px", "width": "47%", "display": "inline-block"})
        ])
    ], style={"backgroundColor": "#FFF", "padding": "12px", "borderRadius": "10px", "marginBottom": "18px", "boxShadow": "0 2px 7px rgba(0,0,0,0.07)"}),
    html.Div([
        html.H2(
            "Alert Logs",
            style={
                "color": "#B71C1C", 
                "fontSize": "2.1rem", 
                "fontWeight": 700,
                "fontFamily": "Segoe UI, Arial, sans-serif",
                "marginBottom": "10px", 
                "textAlign": "center",
                "letterSpacing": "1.5px",
                "textTransform": "uppercase"
            }
        ),
        html.Div([
            html.Label("Show only:", style={"fontWeight": "bold", "marginRight": "8px", "marginLeft": "5px"}),
            dcc.Dropdown(
                id="alert-type-filter",
                options=[{"label": "All", "value": "all"}] + [
                    {"label": m.title(), "value": m} for m in ["temperature", "humidity", "light", "co2"]
                ],
                value="all",
                clearable=False,
                style={"width": "135px", "display": "inline-block", "marginRight": "15px"}
            ),
            html.Label("Per page:", style={"fontWeight": "bold", "marginRight": "7px"}),
            dcc.Input(id="alerts-per-page", type="number", value=10, min=5, max=100, style={"width": "62px", "marginRight": "13px"}),
            html.Button("Reload", id="reload-alerts", n_clicks=0),
        ], style={"marginBottom": "14px"}),
        html.Div(
            id="alert-log-table",
            style={"overflowX": "auto", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 8px rgba(0,0,0,0.08)", "padding": "8px 2px"}
        ),
        html.Div([
            html.Button("Previous", id="prev-page", n_clicks=0, style={
                "width": "110px", "height": "44px", "fontSize": "1.09rem", "marginRight": "14px", "fontWeight": "bold", "borderRadius": "8px", "letterSpacing": "1.2px",
                "border": "1.5px solid #bbb", "background": "#fff", "transition": "background 0.17s"
            }),
            html.Div(
                html.Span(id="page-info", style={"fontSize": "1.11rem", "fontWeight": "600", "fontFamily": "Segoe UI, Arial, sans-serif"}),
                style={"display": "flex", "alignItems": "center", "justifyContent": "center", "height": "44px", "minWidth": "75px"}
            ),
            html.Button("Next", id="next-page", n_clicks=0, style={
                "width": "110px", "height": "44px", "fontSize": "1.09rem", "marginLeft": "14px", "fontWeight": "bold", "borderRadius": "8px", "letterSpacing": "1.2px",
                "border": "1.5px solid #bbb", "background": "#fff", "transition": "background 0.17s"
            }),
        ], style={
            "display": "flex", "justifyContent": "center", "alignItems": "center", "gap": "14px", "marginTop": "18px"
        })

    ], style={"backgroundColor": "#FFF", "padding": "16px 8px", "borderRadius": "10px", "marginBottom": "15px", "boxShadow": "0 2px 8px rgba(0,0,0,0.08)"}),
])


@app.callback(
    Output("room-selector", "options"), Output("room-selector", "value"),
    [Input("room-selector", "value")]
)
def populate_rooms(current_value):
    rooms = fetch_rooms()
    opts = [{"label": r, "value": r} for r in rooms]
    value = current_value if current_value in rooms else (rooms[0] if rooms else None)
    return opts, value


from datetime import datetime, timedelta


@app.callback(
    Output("live-metrics", "children"), Output("metrics-graph", "figure"),
    Output("metric-plot-temperature", "figure"), Output("metric-plot-humidity", "figure"),
    Output("metric-plot-light", "figure"), Output("metric-plot-co2", "figure"),
    Input("room-selector", "value"), Input("range-dropdown", "value"), Input("custom-date", "date")
)
def update_metrics(room, preset_hrs, custom_date):
    print(f"Inputs: room={room}, preset_hrs={preset_hrs}, custom_date={custom_date}")
    
    now = datetime.utcnow()
    print(f"DEBUG NOW (UTC): {now}")
    
    if custom_date:
        cd = pd.to_datetime(custom_date)
        start_dt = cd.replace(hour=0, minute=0, second=0)
        end_dt = start_dt + timedelta(days=1)
    else:
        
        end_dt = now
        start_dt = now - timedelta(hours=float(preset_hrs))
    
    print(f"[DASH CALLBACK] start_dt: {start_dt}, end_dt: {end_dt}")
    
    latest = fetch_latest(room)
    cards = []
    df = pd.DataFrame(latest)
    for m in metrics:
        part = df[df["type"] == m]
        if not part.empty:
            v = part.iloc[0]['value']
            t = pd.to_datetime(part.iloc[0]['time']) if 'time' in part.iloc[0] else ''
            if t != '':
                if t.tzinfo is None:
                    t = t.tz_localize('UTC')
                t = t.tz_convert('Asia/Kolkata').tz_localize(None)
            sid = part.iloc[0].get('sensor_id', '')
            color = card_colors[m]
            th = fetch_thresholds().get(m, {})
            lim = ""
            if th and (v < th['min'] or v > th['max']):
                lim = "ANOMALY!"
            cards.append(html.Div([
                html.Div(m.title(), style={"color": color, "fontWeight": "bold", "fontSize": "1.08rem"}),
                html.Div(f"{v:.1f} {units[m]}", style={"fontSize": "1.47rem", "fontWeight": "600"}),
                html.Div(f"Sensor: {sid}", style={"fontSize": "0.89rem"}),
                html.Div(f"Time: {t.strftime('%Y-%m-%d %H:%M:%S')}" if t != "" else "", style={"fontSize": "0.83rem", "color": "#444"}),
                html.Div(lim, style={"color": "red" if lim else "#333", "fontSize": "0.97rem", "fontWeight": "bold"})
            ], style={"background": "white", "borderRadius": "7px", "padding": "12px 17px", "boxShadow": "0 2px 5px rgba(0,0,0,0.09)", "minWidth": "145px", "minHeight": "116px", "marginRight": "8px"}))
    
    if not cards:
        cards = [html.Div("No live data", style={"background": "white", "padding": "9px 17px"})]
    
    traces = []
    metric_figs = {}
    for m in metrics:
        dfm = fetch_history(room, m, start_dt, end_dt)
        if not dfm.empty:
            ax = "y" if m in ["temperature", "humidity"] else "y2"
            traces.append(go.Scatter(
                x=dfm["time"], y=dfm["value"], mode="lines", name=m.title(), yaxis=ax,
                line={"color": card_colors[m], "width": 2},
                hovertemplate=f"{m.title()}: %{{y:.1f}} {units[m]}<br>Time: %{{x}}<extra></extra>"
            ))
        metric_figs[m] = go.Figure()
        if not dfm.empty:
            metric_figs[m].add_trace(go.Scatter(
                x=dfm["time"], y=dfm["value"], mode="lines", name=m.title(),
                line={"color": card_colors[m], "width": 2},
                hovertemplate=f"{m.title()}: %{{y:.1f}} {units[m]}<br>Time: %{{x}}<extra></extra>"
            ))
            metric_figs[m].update_layout(
                xaxis_title="Time", yaxis_title=f"{m.title()} ({units[m]})",
                font=dict(size=11), margin=dict(l=36, r=20, t=24, b=25), height=220, template="plotly_white",
                showlegend=False
            )
    
    layout = go.Layout(
        xaxis=dict(title="Time", showgrid=True, tickfont=dict(size=11)),
        yaxis=dict(title="Temp (°C)/Humidity (%)", showgrid=True, range=[0, 110], tickfont=dict(size=11)),
        yaxis2=dict(title="Light (lx)/CO₂ (ppm)", overlaying="y", side="right", showgrid=False, range=[0, 2000], tickfont=dict(size=11)),
        legend=dict(orientation="h", x=0, y=1.08, font=dict(size=10)),
        font=dict(size=13), margin=dict(l=42, r=56, t=35, b=33), height=397, template="plotly_white"
    )
    
    if not traces:
        traces.append(go.Scatter(x=[], y=[], mode="lines", name="No Data"))
    
    fig = go.Figure(traces, layout)
    
    return cards, fig, metric_figs.get("temperature"), metric_figs.get("humidity"), metric_figs.get("light"), metric_figs.get("co2")



@app.callback(
    Output("alert-log-table", "children"),
    Output("page-info", "children"),
    [Input("reload-alerts", "n_clicks"), Input("alerts-per-page", "value"),
     Input("prev-page", "n_clicks"), Input("next-page", "n_clicks"),
     Input("alert-type-filter", "value")],
    State("alerts-per-page", "value")
)
def update_alerts(_, per_page, prev, next, alert_type, alerts_per_page):
    page = (next or 0) - (prev or 0) + 1
    data = fetch_alerts(page=page, per_page=alerts_per_page or 10)
    if alert_type and alert_type != "all":
        data = [a for a in data if a.get("type", "") == alert_type]
    if not data:
        body = [html.Tr([html.Td("No alerts found.", colSpan=7, style={"textAlign": "center"})])]
    else:
        body = []
        for a in data:
            dt_raw = a.get('time','N/A')
            dt_local = pd.to_datetime(dt_raw)
            if dt_local.tzinfo is None:
                dt_local = dt_local.tz_localize('UTC')
            dt_local = dt_local.tz_convert('Asia/Kolkata').tz_localize(None)
            dt = dt_local.strftime('%Y-%m-%d %H:%M:%S')


            room = a.get('room', 'N/A')
            sensor = a.get('sensor_id', 'N/A')
            typ = a.get('type', 'N/A').title()
            val = a.get('value', 'N/A')
            sev = str(a.get('severity', '')).title()
            sev_color = {'High': '#E53935', 'Low': '#FFD600'}.get(sev, '#AAA')
            body.append(html.Tr([
                html.Td(dt, style={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "1.09rem", "padding": "4px 7px"}),
                html.Td(room, style={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "1.09rem", "padding": "4px 7px"}),
                html.Td(sensor, style={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "1.09rem", "padding": "4px 7px"}),
                html.Td(typ, style={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "1.09rem", "padding": "4px 7px"}),
                html.Td('{:.2f}'.format(float(val)) if isinstance(val, (float,int)) else val, style={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "1.09rem", "padding": "4px 7px"}),
                html.Td(sev, style={"fontWeight": "bold", "color": sev_color, "fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": "1.09rem", "padding": "4px 7px"}),
            ], style={"backgroundColor": "#FFEEEE" if sev == "High" else "#F0FFF5" if sev == "Low" else "#FFF", "borderBottom": "1px solid #F2F2F2", "transition": "background 0.2s"}))
    table = html.Table([
        html.Thead(html.Tr([
            html.Th("Alert Time", style={"fontWeight": "700", "background": "#E7EEF8", "fontSize": "1.18rem", "fontFamily": "Segoe UI, Arial, sans-serif"}),
            html.Th("Room", style={"fontWeight": "700", "background": "#E7EEF8", "fontSize": "1.18rem", "fontFamily": "Segoe UI, Arial, sans-serif"}),
            html.Th("Sensor ID", style={"fontWeight": "700", "background": "#E7EEF8", "fontSize": "1.18rem", "fontFamily": "Segoe UI, Arial, sans-serif"}),
            html.Th("Sensor Type", style={"fontWeight": "700", "background": "#E7EEF8", "fontSize": "1.18rem", "fontFamily": "Segoe UI, Arial, sans-serif"}),
            html.Th("Value", style={"fontWeight": "700", "background": "#E7EEF8", "fontSize": "1.18rem", "fontFamily": "Segoe UI, Arial, sans-serif"}),
            html.Th("Severity", style={"fontWeight": "700", "background": "#E7EEF8", "fontSize": "1.18rem", "fontFamily": "Segoe UI, Arial, sans-serif"})
        ])),
        html.Tbody(body)
    ], style={"width": "98%", "margin": "auto", "borderCollapse": "collapse"})
    return table, f"Page {page}"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
