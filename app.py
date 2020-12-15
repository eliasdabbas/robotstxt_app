import advertools as adv
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_table import DataTable
import logging
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.YETI])

server = app.server

app.layout = html.Div([
    dbc.Row([
        dbc.Col(lg=2),
        dbc.Col([
            dbc.Label('URLs to test, one per line:'),
            dbc.Textarea(id='urls_to_check',
                         placeholder='/relative/path\n# OR\nhttps://www.example.com/full/path.html',
                         rows=10),
            html.Br(),
            dbc.Label('robots.txt URL:'),
            dbc.Row([
                dbc.Col([
                    dbc.Input(id='robotstxt_url', type='url'),
                ], lg=6),
                dbc.Col([
                    dbc.Button(id='submit', children='Submit', color='dark'),
                ]),
            ]),
            html.Br(), html.Br(), html.Br(),
            dbc.Tabs([
                dbc.Tab([
                    html.Br(),
                    dcc.Loading([
                        DataTable(id='robots_test_table',
                                  export_format='csv',
                                  sort_action='native',
                                  filter_action='native'),
                    ]),
                ], label='Test Results'),
                dbc.Tab([
                    html.Br(),
                    dcc.Loading([
                        html.Div(id='robotstxt_table'),
                    ])
                ], label='robots.txt file')
            ]),
        ], lg=8)
    ]),
] + [html.Br() for i in range(20)], style={'backgroundColor': '#eeeeee'})


@app.callback([Output('robots_test_table', 'data'),
               Output('robots_test_table', 'columns')],
              [Input('submit', 'n_clicks')],
              [State('robotstxt_url', 'value'),
               State('urls_to_check', 'value')])
def populate_test_table(n_clicks, robotstxt_url, urls):
    if not n_clicks:
        raise PreventUpdate
    if not urls:
        raise PreventUpdate

    robots_df = adv.robotstxt_to_df(robotstxt_url)
    user_agents = (robots_df[robots_df['directive'].str.contains('^user-agent$', case=False)]
                   ['content']
                   .drop_duplicates().tolist())
    urls = [url.strip() for url in urls.split()]
    logging.log(level=10, msg='@@'.join(urls))
    test_df = adv.robotstxt_test(robotstxt_url, user_agents, urls)
    test_df = test_df.sort_values(['user_agent', 'url_path'])
    columns = [{"name": i, "id": i} for i in test_df.columns]
    return test_df.to_dict('records'), columns


@app.callback([Output('robotstxt_table', 'children')],
              [Input('submit', 'n_clicks')],
              [State('robotstxt_url', 'value')])
def populate_robotstxt_table(n_clicks, robotstxt_url):
    if not n_clicks:
        raise PreventUpdate
    robots_df = adv.robotstxt_to_df(robotstxt_url)
    columns = [{"name": i, "id": i} for i in robots_df.columns]
    table = DataTable(columns=[{"name": i, "id": i} for i in ['directive', 'content', 'robotstxt_url', 'file_downloaded']],
                      data=robots_df.to_dict('records'),
                      export_format='csv',
                      sort_action='native',
                      filter_action='native',
                      style_data={'minWidth': '140px'},
                      style_table={'overflowX': 'auto'}),
    return table


if __name__ == '__main__':
    app.run_server(debug=True)
