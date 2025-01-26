from flask import Flask, render_template, url_for
import os
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import numpy as np
from scipy import stats

app = Flask(__name__)

HOMES = [
    {"id": 1, "name": "André Loyer, 1276"},
    {"id": 2, "name": "Jair Abranches Mella, 1868"}
]

graph_dir = "static/graphs"
os.makedirs(graph_dir, exist_ok=True)

def generate_data(home_id):
    if home_id == 1:
        production_daily = [12, 15, 14, 13, 15, 16, 14, 15, 13, 12, 14, 15, 16, 13, 14, 15, 13, 14, 15, 16, 12, 14, 15, 13, 14, 15, 16, 12, 14, 15]
        consumption_daily = [10, 9, 11, 12, 10, 9, 8, 11, 10, 9, 8, 10, 9, 11, 12, 10, 9, 8, 11, 10, 9, 8, 10, 9, 11, 12, 10, 9, 8, 11]
    else:
        production_daily = [20, 19, 18, 21, 18, 17, 25, 22, 24, 18, 21, 19, 21, 17, 18, 22, 19, 25, 21, 21, 19, 18, 19, 20, 23, 18, 19, 24, 22, 20]
        consumption_daily = [8, 9, 10, 11, 10, 9, 11, 10, 9, 8, 10, 9, 12, 10, 9, 8, 11, 10, 9, 8, 10, 9, 11, 12, 10, 9, 11, 10, 9, 8]
    
    production_total = sum(production_daily)
    consumption_total = sum(consumption_daily)
    storage = max(production_total - consumption_total, 0)
    avg_daily_consumption = sum(consumption_daily) / len(consumption_daily)
    avg_daily_production = sum(production_daily) / len(production_daily)
    daily_ratio = [c / p if p > 0 else 0 for c, p in zip(consumption_daily, production_daily)]
    monthly_ratio = consumption_total / production_total if production_total > 0 else 0

    median_production = np.median(production_daily)
    median_consumption = np.median(consumption_daily)
    
    production_std = np.std(production_daily)
    consumption_std = np.std(consumption_daily)
    normal_distribution_production = stats.norm.pdf(production_daily, avg_daily_production, production_std)
    normal_distribution_consumption = stats.norm.pdf(consumption_daily, avg_daily_consumption, consumption_std)
    
    used_percentage = (consumption_total / production_total) * 100 if production_total > 0 else 0
    stored_percentage = (storage / production_total) * 100 if production_total > 0 else 0

    slope, intercept, r_value, p_value, std_err = stats.linregress(production_daily, consumption_daily)
    correlation = np.corrcoef(production_daily, consumption_daily)[0, 1]
    
    return {
        "consumption_daily": consumption_daily,
        "production_daily": production_daily,
        "production_total": production_total,
        "consumption_total": consumption_total,
        "storage": storage,
        "avg_daily_consumption": avg_daily_consumption,
        "avg_daily_production": avg_daily_production,
        "daily_ratio": daily_ratio,
        "monthly_ratio": monthly_ratio,
        "slope": slope,
        "intercept": intercept,
        "r_value": r_value,
        "p_value": p_value,
        "std_err": std_err,
        "correlation": correlation,
        "median_production": median_production,
        "median_consumption": median_consumption,
        "normal_distribution_production": normal_distribution_production,
        "normal_distribution_consumption": normal_distribution_consumption,
        "used_percentage": used_percentage,
        "stored_percentage": stored_percentage
    }


def generate_graphs(data, home_id):
    days = list(range(1, 31))
    
    fig_production = go.Figure(go.Bar(x=days, y=data["production_daily"], name='Produção Diária', marker_color='green'))
    fig_production.update_layout(title='Produção Diária')
    
    fig_consumption = go.Figure(go.Bar(x=days, y=data["consumption_daily"], name='Consumo Diário', marker_color='red'))
    fig_consumption.update_layout(title='Consumo Diário')
    
    fig_stacked = go.Figure(data=[
        go.Bar(name='Produção Diária', x=days, y=data["production_daily"], marker_color='green'),
        go.Bar(name='Consumo Diário', x=days, y=data["consumption_daily"], marker_color='red')
    ])
    fig_stacked.update_layout(barmode='stack', title='Produção e Consumo Diários')
    
    fig_scatter = px.scatter(x=data["production_daily"], y=data["consumption_daily"], labels={'x': 'Produção Diária (kWh)', 'y': 'Consumo Diário (kWh)'}, title='Dispersão: Produção vs Consumo')
    
    fig_pie = go.Figure(data=[go.Pie(labels=['Usada', 'Armazenada'], values=[data["used_percentage"], data["stored_percentage"]], hole=.3)])
    fig_pie.update_traces(marker=dict(colors=['red', 'blue']))  # Ajuste as cores aqui
    fig_pie.update_layout(title='Porcentagem de Energia Usada vs Armazenada')
    
    production_graph_path = os.path.join(graph_dir, f"production_graph_{home_id}.html")
    consumption_graph_path = os.path.join(graph_dir, f"consumption_graph_{home_id}.html")
    stacked_graph_path = os.path.join(graph_dir, f"stacked_graph_{home_id}.html")
    scatter_graph_path = os.path.join(graph_dir, f"scatter_graph_{home_id}.html")
    pie_graph_path = os.path.join(graph_dir, f"pie_graph_{home_id}.html")
    
    pio.write_html(fig_production, file=production_graph_path, auto_open=False)
    pio.write_html(fig_consumption, file=consumption_graph_path, auto_open=False)
    pio.write_html(fig_stacked, file=stacked_graph_path, auto_open=False)
    pio.write_html(fig_scatter, file=scatter_graph_path, auto_open=False)
    pio.write_html(fig_pie, file=pie_graph_path, auto_open=False)
    
    return production_graph_path, consumption_graph_path, stacked_graph_path, scatter_graph_path, pie_graph_path

@app.route("/")
def index():
    return render_template("index.html", homes=HOMES)

@app.route("/home/<int:home_id>")
def dashboard(home_id):
    home = next((home for home in HOMES if home["id"] == home_id), None)
    if not home:
        return "Residência não encontrada", 404
    data = generate_data(home_id)
    production_graph_path, consumption_graph_path, stacked_graph_path, scatter_graph_path, pie_graph_path = generate_graphs(data, home_id)
    graph_url = url_for('static', filename=f'graphs/energy_graph_{home_id}.html')
    pie_graph_url = url_for('static', filename=f'graphs/pie_graph_{home_id}.html')
    return render_template("dashboard.html", home=home, data=data, graph_url=graph_url, pie_graph_url=pie_graph_url)

@app.route("/details/<int:home_id>")
def details(home_id):
    home = next((home for home in HOMES if home["id"] == home_id), None)
    if not home:
        return "Residência não encontrada", 404
    data = generate_data(home_id)
    production_graph_path, consumption_graph_path, stacked_graph_path, scatter_graph_path, pie_graph_path = generate_graphs(data, home_id)
    production_graph_url = url_for('static', filename=f'graphs/production_graph_{home_id}.html')
    consumption_graph_url = url_for('static', filename=f'graphs/consumption_graph_{home_id}.html')
    stacked_graph_url = url_for('static', filename=f'graphs/stacked_graph_{home_id}.html')
    scatter_graph_url = url_for('static', filename=f'graphs/scatter_graph_{home_id}.html')
    pie_graph_url = url_for('static', filename=f'graphs/pie_graph_{home_id}.html')

    return render_template("details.html", home=home, data=data, production_graph_url=production_graph_url, consumption_graph_url=consumption_graph_url, stacked_graph_url=stacked_graph_url, scatter_graph_url=scatter_graph_url, pie_graph_url=pie_graph_url)


if __name__ == "__main__":
    app.run(debug=True)
