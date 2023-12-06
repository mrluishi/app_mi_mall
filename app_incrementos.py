import dash
from dash import html, dcc, Input, Output
from dash.exceptions import PreventUpdate
import sqlalchemy
import pandas as pd
from datetime import datetime
from dash_table import DataTable
import pyodbc
import json

# Link these to Azure Key Vault secrets
DB_USER = 'testLogin1'
DB_PASSWORD = 'Prueba1&'
DB_HOST = 'srvsqlmallaventura.database.windows.net'
DB_NAME = 'your_database_name'

# Create a connection to the database
#engine = create_engine(f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
engine = sqlalchemy.create_engine(
    'mssql+pyodbc://' + 
    'testLogin1' + ':' + 
    'Prueba1&' + '@'+ 
    'srvsqlmallaventura.database.windows.net' + ':1433/' + 
    'dbsqlmallaventura' + 
    '?DRIVER=' + 'ODBC Driver 17 for SQL Server')


# Read data from SQL table
def read_data():
    query = "SELECT TOP 10 * FROM prod.MI_H_Reporte_1"
    df = pd.read_sql(query, engine)
    return df

# Create Dash app
app = dash.Dash(__name__)

# Initial data load
df = read_data()

#Copy of the original, without further modification by user
df_original = df.copy()

# Define layout
app.layout = html.Div([
    DataTable(
        id='table',
        columns=[
            {'name': col, 'id': col, 'editable': True} for col in df.columns
        ],
        data=df.to_dict('records'),
        editable=True
    ),
    
    html.Button('Save Changes', id='save-btn', n_clicks=0),
])

# Callback to update SQL table when button is clicked
@app.callback(
    Output('table', 'data'),
    [Input('save-btn', 'n_clicks')],
    prevent_initial_call=True
)
def save_changes(n_clicks):
    if n_clicks == 0:
        raise PreventUpdate
    
    # Get the updated table from the callback context
    ctx = dash.callback_context
    if not ctx.triggered_id:
        raise PreventUpdate

    triggered_component = ctx.triggered_id.split('.')[0]
    
    if triggered_component == 'save-btn':
        # Get the updated data from the DataTable
        modified_data = ctx.inputs[0]['value']['data']
        
        # Convert the JSON string to a Python object
        modified_data_dict = json.loads(modified_data)
        
        # Create a DataFrame from the modified data
        modified_df = pd.DataFrame(modified_data_dict)
        
        # Update the timestamp in your main table
        modified_df['TIMESTAMP'] = datetime.now()
        cols_filtered = ['NOMBREMALL','CODCONTRATO','NOMBRELOCATARIO','INCREMENTOSUGERIDO','TAMSUGERIDA','TIMESTAMP']
        modified_df = modified_df[cols_filtered]

        # Append the modified data to the destination table in SQL
        modified_df.to_sql('MI_H_IncrementoManual', engine, schema='prod', if_exists='append', index=False)

        # Read and return the updated data
        return modified_df.to_dict('records')

if __name__ == '__main__':
    app.run_server(debug=True)




