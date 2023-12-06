
import dash
from dash import dcc, html, dash_table, ctx
#from dash import Dash, Input, Output, ctx, html, dcc, callback
from dash.dependencies import Input, Output, State
import sqlalchemy
import pandas as pd
from datetime import *
import numpy as np
import itertools
import pyodbc

#app = dash.Dash(__name__)

external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Create a connection to the database
print(datetime.now())
engine = sqlalchemy.create_engine(
    'mssql+pyodbc://' + 
    'testLogin1' + ':' + 
    'Prueba1&' + '@'+ 
    'srvsqlmallaventura.database.windows.net' + ':1433/' + 
    'dbsqlmallaventura' + 
    '?DRIVER=' + 'ODBC Driver 17 for SQL Server')

# Read data from SQL table
query = """SELECT NOMBREMALL,NOMBRESUBGERENTE,CODCONTRATO,NOMBRELOCATARIO,TAMACTUAL,INCREMENTOSUGERIDO,TAMSUGERIDA,NULL TAMPROPUESTA
            FROM prod.MI_H_Reporte_1 WITH(NOLOCK)
            WHERE PERIODO=(SELECT MAX(PERIODO) FROM prod.MI_H_Reporte_1)
            AND INCREMENTOSUGERIDO>0
            AND DIFTAM_TAMGRUPO<=0
            """
df = pd.read_sql(query, engine)
df.columns = ['MALL','SUBGERENTE','CONTRATO','LOCATARIO','TAM ACTUAL','INCREMENTO SUGERIDO','TAM SUGERIDA','TAM PROPUESTA']
df_original = df.copy()

list_contratos = df['CONTRATO'].sort_values().unique()
list_locatarios = df['LOCATARIO'].sort_values().unique()
list_malls = df['MALL'].sort_values().unique()

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                #html.P(children="🥑", className="header-emoji"),
                html.H1(
                    children="Comité Casos Especiales: TAM Renovación Locatarios", className="header-title"
                ),
                #html.P(
                #    children=(
                #        "Casos faltantes por definir incremento TAM por renovación"
                #    ),
                #    className="header-description",
                #),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Mall", className="menu-title"),
                        dcc.Dropdown(
                            id="mall-filter",
                            options=[
                                {"label": mall, "value": mall}
                                for mall in list_malls
                            ],
                            clearable=True,
                            searchable=True,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Contrato", className="menu-title"),
                        dcc.Dropdown(
                            id="contrato-filter",
                            options=[
                                {
                                    "label": contrato.title(),
                                    "value": contrato,
                                }
                                for contrato in list_contratos
                            ],
                            clearable=True,
                            searchable=True,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(children="Locatario", className="menu-title"),
                        dcc.Dropdown(
                            id="locatario-filter",
                            options=[
                                {
                                    "label": locatario.title(),
                                    "value": locatario,
                                }
                                for locatario in list_locatarios
                            ],
                            clearable=True,
                            searchable=True,
                            className="dropdown",
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dash_table.DataTable(
                                id='editable-table',
                                columns=[
                                    {'name': col, 'id': col, 'editable': True} for col in df.columns
                                ],
                                editable=True,
                                row_deletable=False,
                    ),
                    className="card",
                ),
                html.Div(
                    children=html.Button('Guardar cambios', id='save-button', n_clicks=0),
                ),
                html.Div(id='output-message'),
            ],
            className="wrapper",
        ),
    ]
)

# One callback to update same displayed table
@app.callback(
    Output('output-message', 'children'),
    Output("editable-table", "data"),
    [Input("mall-filter", "value"),
    Input("contrato-filter", "value"),
    Input("locatario-filter", "value"),
    Input('save-button', 'n_clicks',),
    Input('editable-table', 'data')],
    prevent_initial_call=True
)
def filter_update_and_save_table(mall, contrato_number, locatario_name, n_clicks, data):
    
    #Identify which trigger fired the callback
    triggered_id = ctx.triggered_id
    print(triggered_id)
    if triggered_id=='mall-filter' or triggered_id=='contrato-filter' or triggered_id=='locatario-filter':
        
        # Filtering table
        df_filtered = filter_table(mall, contrato_number, locatario_name)

        # Updating table
            
        return html.Div('Successful filter table'), df_filtered 
        
    elif triggered_id=='editable-table':
        
        i = 0
        print(len(data))
        for row in data:
            # Check if the value has changed
            print(row['CONTRATO'])
            df_comparison = df_original[df_original['CONTRATO']==row['CONTRATO']]
            db_value = df_comparison['INCREMENTO SUGERIDO'].item()
            print(db_value)
            print(row['INCREMENTO SUGERIDO'])
            if row['INCREMENTO SUGERIDO'] != db_value:
                
                df_row = df_original[df_original['CONTRATO']==row['CONTRATO']].reset_index(drop=True)
                df_row['INCREMENTO SUGERIDO'] = row['INCREMENTO SUGERIDO']
                df_row['TAM PROPUESTA'] = (1 + float(row['INCREMENTO SUGERIDO']))*row['TAM ACTUAL']
                data[i]['TAM PROPUESTA'] = df_row['TAM PROPUESTA'].item()
                print(data[i]['TAM PROPUESTA'])

            i += 1
        return html.Div('Successful updated table'), data 

    elif triggered_id=='save-button':
         
         return save_table(n_clicks, data)

def filter_table(mall, contrato_number, locatario_name):
    if not mall and not contrato_number and not locatario_name:
        print("Sin filtros")
    else:
        if not mall:
            print("Sin filtro mall")
            if not contrato_number and not locatario_name:
                print("Sin filtros adicionales")
                filtered_data = pd.DataFrame()
            else:
                print("Filtro contrato")
                filtered_data = df[(df['CONTRATO']==contrato_number) | (df['LOCATARIO']==locatario_name)]
        else:
            print("Filtro Mall")
            filtered_data = df[df['MALL']==mall]
            if not contrato_number and not locatario_name:
                print("Sin filtros adicionales")
            else:
                print("Filtro contrato")
                filtered_data = filtered_data[(filtered_data['CONTRATO']==contrato_number) | (filtered_data['LOCATARIO']==locatario_name)]

    try:
        data = filtered_data.to_dict('records')
    except:
        data = df[df['MALL']=='XX'].to_dict('records')
        
    return data

def save_table(n_clicks, data):

    if n_clicks > 0:
        print('click')
        #df_change.reset_index(inplace=True)
        df_change = pd.DataFrame(data)
        df_change['TIMESTAMP'] = datetime.now()
        df_change['MAIL_USER'] = np.nan 
        cols_filtered = ['MALL','CONTRATO','LOCATARIO','INCREMENTO SUGERIDO','TAM SUGERIDA','TAM PROPUESTA','MAIL_USER','TIMESTAMP']
        df_change = df_change[cols_filtered]
        df_change.columns = ['MALL','CONTRATO','LOCATARIO','INCREMENTO_SUGERIDO','TAM_SUGERIDA','TAM_PROPUESTA','MAIL_USER','TIMESTAMP']
        df_change.to_sql('MI_H_IncrementoManual', engine, schema='prod', if_exists='append', index=False, method='multi')

        return html.Div('Changes saved to the database'), data
    else:
        return html.Div(), data

if __name__ == '__main__':
    app.run_server(debug=True)


