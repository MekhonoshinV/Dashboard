import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import base64
import io
import plotly.graph_objects as go

# Загрузка данных (начальные, до загрузки пользовательского файла)
df_initial = pd.read_csv('data/financial_data.csv')
df_initial['Date'] = pd.to_datetime(df_initial['Date'])

# Инициализация приложения
app = dash.Dash(__name__)

# Макет (Layout) дашборда
app.layout = html.Div([
    html.H1("Финансовый дашборд", style={'textAlign': 'center', 'color': '#2c3e50'}),
    dcc.Upload(...),
    html.Div([
        html.Div([dcc.Graph(id='indicator-gauge')], className='four columns'),
        html.Div([dcc.Graph(id='time-series')], className='eight columns')
    ], className='row'),
    # ... и так далее
], style={'font-family': 'Arial'})
app.layout = html.Div([
    html.H1("Финансовый дашборд", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # Компонент загрузки файла
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
        multiple=False
    ),
    
    # Хранилище для загруженных данных
    dcc.Store(id='stored-data'),
    
    # Индикатор (полоска состояния)
    html.Div([
        html.H3("Текущие показатели", style={'textAlign': 'center'}),
        dcc.Graph(id='indicator-gauge')
    ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
    
    # Выпадающий список для выбора категории
    html.Div([
        html.Label("Выберите категорию:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': 'Все', 'value': 'All'}] + 
                    [{'label': cat, 'value': cat} for cat in df_initial['Category'].unique()],
            value='All'
        )
    ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
    
    # Графики
    dcc.Graph(id='time-series'),
    
    html.Div([
        html.Div([dcc.Graph(id='pie-chart')], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='histogram')], style={'width': '48%', 'display': 'inline-block'})
    ]),
    
    dcc.Graph(id='scatter-plot'),
    
    html.H3("Таблица данных (первые 10 записей)", style={'marginTop': '20px'}),
    dash_table.DataTable(id='data-table')
])

# Калбэк для загрузки данных из файла
@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def load_data(contents, filename):
    if contents is None:
        # Если файл не загружен, используем начальные данные
        return df_initial.to_dict('records')
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        df['Date'] = pd.to_datetime(df['Date'])
        return df.to_dict('records')
    except Exception as e:
        print(f'Ошибка загрузки: {e}')
        return df_initial.to_dict('records')

# Калбэк для обновления всех графиков
@app.callback(
    [Output('time-series', 'figure'),
     Output('pie-chart', 'figure'),
     Output('histogram', 'figure'),
     Output('scatter-plot', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('indicator-gauge', 'figure')],
    [Input('category-dropdown', 'value'),
     Input('stored-data', 'data')]
)
def update_dashboard(selected_category, stored_data):
    # Преобразуем хранилище обратно в DataFrame
    if stored_data is None:
        df = df_initial.copy()
    else:
        df = pd.DataFrame(stored_data)
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Фильтрация данных по категории
    if selected_category == 'All':
        dff = df
    else:
        dff = df[df['Category'] == selected_category]
    
    # 1. Линейный график временного ряда
    fig_line = px.line(dff, x='Date', y=['Income', 'Expense'], 
                       title="Динамика доходов и расходов",
                       labels={'value': 'Сумма (руб)', 'variable': 'Показатель'})
    
    # 2. Круговая диаграмма расходов
    expense_by_cat = dff.groupby('Category')['Expense'].sum().reset_index()
    fig_pie = px.pie(expense_by_cat, values='Expense', names='Category', 
                     title="Структура расходов по категориям")
    
    # 3. Гистограмма распределения прибыли
    fig_hist = px.histogram(dff, x='Profit', nbins=20, 
                            title="Распределение прибыли",
                            labels={'Profit': 'Прибыль (руб)', 'count': 'Частота'})
    
    # 4. График рассеяния (корреляция)
    fig_scatter = px.scatter(dff, x='Income', y='Profit', color='Category',
                             title="Корреляция: Доход vs Прибыль",
                             labels={'Income': 'Доход (руб)', 'Profit': 'Прибыль (руб)'})
    
    # 5. Таблица данных
    columns = [{"name": i, "id": i} for i in dff.columns]
    data = dff.head(10).to_dict('records')
    
    # 6. Индикатор (средняя прибыль)
    avg_profit = dff['Profit'].mean()
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_profit,
        title={'text': "Средняя прибыль (руб)"},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [None, dff['Profit'].max() if len(dff) > 0 else 100000]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, avg_profit/2], 'color': "lightgray"},
                {'range': [avg_profit/2, avg_profit], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': avg_profit
            }
        }
    ))
    
    fig_gauge.update_layout(height=300)
    
    return fig_line, fig_pie, fig_hist, fig_scatter, data, columns, fig_gauge

if __name__ == '__main__':
    app.run(debug=True)