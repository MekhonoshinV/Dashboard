import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd

# Загрузка данных
# Пока просто загружаем локально, позже сделаем загрузку через интерфейс
df = pd.read_csv('data/financial_data.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Инициализация приложения
app = dash.Dash(__name__)

# Макет (Layout) дашборда
app.layout = html.Div([
    html.H1("Финансовый дашборд", style={'textAlign': 'center'}),
    
    # 1. Выпадающий список (Dropdown) для выбора категории
    html.Label("Выберите категорию:"),
    dcc.Dropdown(
        id='category-dropdown',
        options=[{'label': 'Все', 'value': 'All'}] + 
                [{'label': cat, 'value': cat} for cat in df['Category'].unique()],
        value='All'
    ),
    
    # 2. График временного ряда (Линейный график доходов и расходов)
    dcc.Graph(id='time-series'),
    
    # 3. Круговая диаграмма расходов
    dcc.Graph(id='pie-chart'),
    
    # 4. Гистограмма распределения прибыли
    dcc.Graph(id='histogram'),
    
    # 5. Таблица данных
    dash_table.DataTable(id='data-table'),
    
    # 6. График рассеяния (Корреляция)
    dcc.Graph(id='scatter-plot')
])

# Калбэки для интерактивности
@app.callback(
    [Output('time-series', 'figure'),
     Output('pie-chart', 'figure'),
     Output('histogram', 'figure'),
     Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('scatter-plot', 'figure')],
    [Input('category-dropdown', 'value')]
)
def update_dashboard(selected_category):
    # Фильтрация данных
    if selected_category == 'All':
        dff = df
    else:
        dff = df[df['Category'] == selected_category]
    
    # 1. Временной ряд
    fig_line = px.line(dff, x='Date', y=['Income', 'Expense'], 
                       title="Динамика доходов и расходов")
    
    # 2. Круговая диаграмма (расходы по категориям)
    expense_by_cat = dff.groupby('Category')['Expense'].sum().reset_index()
    fig_pie = px.pie(expense_by_cat, values='Expense', names='Category', 
                     title="Структура расходов")
    
    # 3. Гистограмма прибыли
    fig_hist = px.histogram(dff, x='Profit', nbins=20, 
                            title="Распределение прибыли")
    
    # 4. Таблица (первые 5 строк для примера)
    columns = [{"name": i, "id": i} for i in dff.columns]
    data = dff.head(10).to_dict('records')
    
    # 5. График рассеяния (Прибыль vs Доход)
    fig_scatter = px.scatter(dff, x='Income', y='Profit', color='Category',
                             title="Корреляция: Доход vs Прибыль")
    
    return fig_line, fig_pie, fig_hist, data, columns, fig_scatter

if __name__ == '__main__':
    app.run_server(debug=True)