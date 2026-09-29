from dash import Dash, dcc, html, dash_table
import plotly.express as px
import pandas as pd

app = Dash(__name__)
app.title = "DataFlow360 - Test frontend"

# Données fictives pour tester l'affichage uniquement
transactions = pd.DataFrame({
    "Heure": ["08:10", "08:25", "09:00", "09:15", "09:40"],
    "Client": ["CL001", "CL002", "CL003", "CL004", "CL005"],
    "Montant (FCFA)": [15000, 250000, 8000, 175000, 42000],
    "Risque": ["Faible", "Élevé", "Faible", "Moyen", "Élevé"],
})

activite = pd.DataFrame({
    "Heure": ["08h", "09h", "10h", "11h", "12h"],
    "Transactions": [35, 52, 44, 68, 57],
})

graphique = px.line(
    activite,
    x="Heure",
    y="Transactions",
    markers=True,
    title="Activité des transactions (données fictives)",
)

graphique.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=50, b=20),
)

def carte_kpi(titre, valeur, couleur):
    return html.Div(
        [
            html.P(titre, style={"margin": "0", "color": "#555"}),
            html.H2(valeur, style={"margin": "8px 0 0", "color": couleur}),
        ],
        style={
            "backgroundColor": "white",
            "padding": "20px",
            "borderRadius": "12px",
            "boxShadow": "0 2px 8px #00000012",
            "flex": "1",
            "minWidth": "160px",
        },
    )


app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f6f9",
        "minHeight": "100vh",
        "padding": "24px",
    },
    children=[
        html.H1("DataFlow360", style={"color": "#183b66"}),
        html.P(
            "Plateforme de test — détection de fraude et risque de crédit",
            style={"color": "#555"},
        ),
        html.Div(
            "DONNÉES DE DÉMONSTRATION — PAS DE VRAIES TRANSACTIONS",
            style={
                "backgroundColor": "#fff3cd",
                "color": "#765b00",
                "padding": "10px",
                "borderRadius": "8px",
                "fontWeight": "bold",
                "marginBottom": "20px",
            },
        ),
        html.Div(
            [
                carte_kpi("Transactions", "256", "#183b66"),
                carte_kpi("Alertes fictives", "12", "#c0392b"),
                carte_kpi("Demandes de crédit", "38", "#2471a3"),
                carte_kpi("Risque élevé", "7", "#b9770e"),
            ],
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "16px",
                "marginBottom": "24px",
            },
        ),
        html.Div(
            dcc.Graph(figure=graphique),
            style={
                "backgroundColor": "white",
                "padding": "12px",
                "borderRadius": "12px",
                "marginBottom": "24px",
            },
        ),
        html.H2("Transactions récentes", style={"color": "#183b66"}),
        dash_table.DataTable(
            data=transactions.to_dict("records"),
            columns=[{"name": col, "id": col} for col in transactions.columns],
            style_table={"overflowX": "auto"},
            style_cell={
                "padding": "12px",
                "textAlign": "left",
                "fontFamily": "Arial",
            },
            style_header={
                "backgroundColor": "#183b66",
                "color": "white",
                "fontWeight": "bold",
            },
            style_data_conditional=[
                {
                    "if": {"filter_query": '{Risque} = "Élevé"'},
                    "backgroundColor": "#fdecea",
                    "color": "#a93226",
                },
                {
                    "if": {"filter_query": '{Risque} = "Moyen"'},
                    "backgroundColor": "#fff4d6",
                    "color": "#8a6100",
                },
            ],
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)