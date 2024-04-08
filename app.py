import pandas as pd
import plotly.graph_objects as go
import plotly
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

df = pd.read_excel("S&P500 Top 100 Companies.xlsx")
df['date'] = pd.to_datetime(df['date'])

@app.route("/")
@app.route("/<compare_type>/<graph_type>/<int:year_input>/<string:company_1>/<string:company_2>")
@app.route("/<compare_type>/<graph_type>/<string:company>/<int:year_1>/<int:year_2>")
def get_input(compare_type=None, graph_type=None, year_input=None, company=None, year_1=None, year_2=None, company_1=None, company_2=None):
    
    unique_symbols=[]
    unique_years=[]
    symbols = df['symbol'].values
    for name in symbols:
        if name not in unique_symbols:
            unique_symbols.append(name)
    
    for year in df['date'].dt.year:
        if year not in unique_years:
            unique_years.append(year)



    return render_template('index.html', symbol_dropdown=unique_symbols, year_dropdown=unique_years, year_selected=year_input, company_selected=company, year1_selected=year_1, year2_selected=year_2, company1_selected=company_1, company2_selected=company_2, selected_compare_type=compare_type,selected_graph_type=graph_type)

@app.route("/result")
def show_graph():
    compareType = request.args.get('compare_type')
    graphType = request.args.get('graph_type')

    if request.args.get('main_input').isdigit():
        input= int(request.args.get('main_input'))
        company1 = request.args.get('company1')
        company2 = request.args.get('company2')
        compiled_list=[company1, company2]
    else:
        input=request.args.get('main_input')
        year1 = int(request.args.get('year1'))
        year2 = int(request.args.get('year2'))
        compiled_list=[year1, year2]

    print(compareType, graphType, input, compiled_list)
    # Function to filter data by symbol and year (with input validation)
    i = 1

    for item in compiled_list:
        print(item)
        def filter_by_symbol_and_year(df):
            if type(input) is int:
                return df[(df['symbol'] == item) & (df['date'].dt.year == input)]
            else:
                return df[(df['symbol'] == input) & (df['date'].dt.year == item)]
        
        def check_scenario(result):
            scenario = None
            
            if not result.empty:
                if (result['grossProfit'].iloc[0] <= 0):
                    scenario = "Scenario 1: Negative Gross Profit"
                elif (result['operatingIncome'].iloc[0] <= 0):
                    scenario = "Scenario 2: Negative Operating Income"
                elif (result['incomeBeforeTax'].iloc[0] <= 0):
                    scenario = "Scenario 3: Negative Income Before Tax"
                else:
                    if (result['totalOtherIncomeExpensesNet'].iloc[0] <= 0):
                        scenario = "Scenario 4: Negative Total Other Income/Expenses (Net)"
                    else:
                        scenario = "Scenario 5: Positive Total Other Income/Expenses (Net)"
                    
            return scenario

        def match_scenario(scenario):
            # Load data from JSON file
            with open("scenario_data.json", "r") as infile:
                data = json.load(infile)

            # Retrieve data based on scenario
            if scenario in data:
                labels = data[scenario]["labels"]
                source = data[scenario]["source"]
                target = data[scenario]["target"]
                
                color_for_nodes = data[scenario]["color_for_nodes"]
                color_for_links = data[scenario]["color_for_links"]

                x = data[scenario]["x"]
                y = data[scenario]["y"]
            else:
                print("Matching Error: No scenario")
                labels, source, target = [], [], []
                color_for_nodes, color_for_links = [], []
                x, y = [], []

            return {
                "labels": labels,
                "source": source,
                "target": target,
                "color_for_nodes": color_for_nodes,
                "color_for_links": color_for_links,
                "x": x,
                "y": y
            }
        
        def generate_link_data(result):
            if not result.empty:
                scenario = check_scenario(result)
                scenario_data = match_scenario(scenario)
                
                labels = scenario_data['labels']
                source = scenario_data['source']
                target = scenario_data['target']
            else:
                return False

            revenue = result['revenue'].iloc[0]
            costOfRevenue = result['costOfRevenue'].iloc[0]
            grossProfit = result['grossProfit'].iloc[0]
            
            operatingExpenses = result['operatingExpenses'].iloc[0]
            operatingIncome = result['operatingIncome'].iloc[0]
            
            totalOtherIncomeExpensesNet = result['totalOtherIncomeExpensesNet'].iloc[0]
            incomeBeforeTax = result['incomeBeforeTax'].iloc[0]

            incomeTaxExpense = result['incomeTaxExpense'].iloc[0]
            netIncome = result['netIncome'].iloc[0]

            match scenario:
                case "Scenario 1: Negative Gross Profit":
                    value = [
                        revenue, 
                        costOfRevenue, -grossProfit
                    ]

                case "Scenario 2: Negative Operating Income":
                    value = [
                        costOfRevenue, grossProfit, 
                        grossProfit, -operatingIncome, 
                    ]
                
                case "Scenario 3: Negative Income Before Tax":
                    value = [ 
                        costOfRevenue, grossProfit, 
                        grossProfit, operatingIncome,
                        -totalOtherIncomeExpensesNet, -incomeBeforeTax
                    ]

                case "Scenario 4: Negative Total Other Income/Expenses (Net)":
                    value = [
                        costOfRevenue, grossProfit, 
                        operatingExpenses, operatingIncome, 
                        -totalOtherIncomeExpensesNet, incomeBeforeTax,
                        incomeTaxExpense, netIncome
                    ]

                case "Scenario 4: Negative Total Other Income/Expenses (Net)":
                    value = [
                        costOfRevenue, grossProfit, 
                        operatingExpenses, operatingIncome, 
                        -totalOtherIncomeExpensesNet, incomeBeforeTax,
                        incomeTaxExpense, netIncome
                    ]
                    
                case "Scenario 5: Positive Total Other Income/Expenses (Net)":
                    value = [
                        costOfRevenue, grossProfit, 
                        operatingExpenses, operatingIncome, 
                        totalOtherIncomeExpensesNet, operatingIncome,
                        incomeTaxExpense, netIncome if netIncome < operatingIncome else (operatingIncome - incomeTaxExpense)
                    ]
                case _:
                    value = None
            return dict(
                source = source,
                target = target,
                value = [0.001 if v == 0 else v for v in value],
                # "customdata": customdata,
                hovertemplate = "%{target.label} Ratio: <br> %{customdata:.2f}%"
            )
        

        def generate_node_data(result):
            if not result.empty:
                scenario = check_scenario(result)
                scenario_data = match_scenario(scenario)
                
                labels = scenario_data['labels']
                x = scenario_data['x']
                y = scenario_data['y']

                x = [0.001 if v == 0 else 0.999 if v == 1 else v for v in x]
                y = [0.001 if v == 0 else 0.999 if v == 1 else v for v in y]
            else:
                return False
                
            return dict(
                label = labels, 
                pad = 20, 
                thickness = 20, 
                x = x, 
                y = y
            )
        
        def generate_colour_data(result):
            if not result.empty:
                scenario = check_scenario(result)
                scenario_data = match_scenario(scenario)

                return dict(
                color_for_nodes = scenario_data['color_for_nodes'],
                color_for_links = scenario_data['color_for_links']
                )
                
            else:
                return False
        
        # TRY OUT
        result = filter_by_symbol_and_year(df)
        # link_data = generate_link_data(result)
        # node_data = generate_node_data(result)

        data = go.Sankey(
            link=generate_link_data(result),
            node=generate_node_data(result),
        )
        fig = go.Figure(data)

        company_name = result['symbol'].iloc[0]
        date = result['date'].iloc[0].to_period('Y')

        # Update our chart
        fig.update_layout(
            title=f"Income Statement for {company_name} as of {date}", font=dict(size=10), hovermode="x"  # Show values on hover
        )

        fig.update_traces(node_color=generate_colour_data(result)['color_for_nodes'], link_color=generate_colour_data(result)['color_for_links'])

        plotly.offline.plot(fig, filename=f'./static/sankey{i}.html', auto_open=False)

    ####################################################################################################

        # Filter Relevant Columns
        relevant_columns = ['date', 'symbol', 'revenue', 'costOfRevenue', 'grossProfit', 'operatingExpenses', 'operatingIncome', 'totalOtherIncomeExpensesNet', 'incomeBeforeTax', 'incomeTaxExpense', 'netIncome']
        df_relevant = df[relevant_columns]

        # Convert 'date' column to datetime format
        df_relevant['date'] = pd.to_datetime(df_relevant['date'])

        # Filter Data Based on Input Symbol and Year
        if type(input) is int:
            df_filtered = df_relevant[(df_relevant['symbol'] == item) & (df_relevant['date'].dt.year == input)]
        else:
            df_filtered = df_relevant[(df_relevant['symbol'] == input) & (df_relevant['date'].dt.year == item)]

        # Prepare Data for Waterfall Chart
        data = df_filtered.iloc[0].tolist()[2:]  # Exclude 'date' and 'symbol' columns
        categories = ['Revenue', 'Cost of Revenue', 'Gross Profit', 'Operating Expenses',
                    'Operating Income', 'Other Income/Expenses', 'Income Before Tax',
                    'Income Tax Expense', 'Net Income']

        # Calculate incremental values for the waterfall chart
        #increments = [data[0]] + [data[i] - data[i - 1] for i in range(1, len(data))]
        increments = [
            data[0],    # Revenue
            -data[1],   # Cost of Revenue (negative)
            data[2],    # Gross Profit
            -data[3],   # Operating Expenses (negative)
            data[4],    # Operating Income
            data[5],    # Other Income/Expenses
            data[6],    # Income Before Tax
            -data[7],   # Income Tax Expense (negative)
            data[8]     # Net Income
        ]

        # Define the figure for the waterfall chart
        fig = go.Figure(go.Waterfall(
            name="",
            orientation="h",  # Set orientation to horizontal for downward flow
            measure=["relative", "relative", "total", "relative", "total", "relative",
                                                    "total", "relative", "total"],
            y=categories,  # Keep categories in the original order
            textposition="outside",
            text=[f"{value:,.2f}" for value in increments],
            #text=[str(value) for value in data],  # Use data in the original order
            x=increments, # Use increments in the original order
            connector={"mode":"between", "line":{"width":4, "color":"rgb(0, 0, 0)", "dash":"solid"}},
        ))

        # Update layout settings for the chart
        fig.update_layout(
            title=f"Profit and Loss Statement of {item} ({input})",
            xaxis_title="Amount (in USD)",
            yaxis_title="Categories",
            yaxis_autorange='reversed'  # Reverse the y-axis
        )

        plotly.offline.plot(fig, filename=f'./static/waterfall{i}.html', auto_open=False)

        i+=1

    if type(input) is int:
        return redirect(url_for('get_input', year_input=input, company_1=company1, company_2=company2, compare_type=compareType, graph_type=graphType))
    else:
        return redirect(url_for('get_input', company=input, year_1=year1, year_2=year2, compare_type=compareType, graph_type=graphType))

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)