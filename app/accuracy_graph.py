import requests
import os

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool, Range1d, Select, NumeralTickFormatter, LinearAxis, Legend, \
    Paragraph, Plot, Text
from bokeh.plotting import figure

import pandas as pd
from datetime import datetime, timedelta
import json
import operator
import numpy as np

HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8',
           'http-equiv': "Content-Security-Policy", 'content': "upgrade-insecure-requests"}

ACCURACY_MONITOR_ENDPOINT = os.environ.get('ACCURACY_MONITOR_ENDPOINT')

global target_data


def accuracy_over_time(doc):
    global target_data
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')
    target_metric = arg['target_metric'][0].decode('utf8')

    info_url = ACCURACY_MONITOR_ENDPOINT + "/accuracy-monitor/monitor-info" + "/" + inferenceName
    info_params = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
    }

    info_response = requests.get(info_url, params=info_params, headers=HEADERS)
    if info_response.status_code >= 400:
        # todo 인포를 못받아올 경우
        info = False
        target = ""
    else:
        info_json = json.loads(info_response.text)
        info_data = eval(info_json['data'])
        model_type = info_data['model_type']
        info = True

        if model_type == 'Regression':
            target = 'rmse'
        elif model_type == 'Binary':
            target = 'tpr'
        else:
            # todo multiclass
            target = 'logloss'

        if target_metric != "":
            target = target_metric

    parse = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
        'start_time': arg['start_time'][0].decode('utf8'),
        'end_time': arg['end_time'][0].decode('utf8'),
        'type': 'timeline'
    }

    data_url = ACCURACY_MONITOR_ENDPOINT + "/accuracy-monitor/accuracy" + "/" + inferenceName
    response = requests.get(data_url, params=parse, headers=HEADERS)

    if response.status_code >= 400 or info is False or str(response.text).find("No data") >= 0:
        # plot = figure(sizing_mode="fixed",
        #               min_width=1200,
        #               max_width=2000,
        #               height=400, )
        # select = Select(value="metric", width=200)
        #
        # plot.toolbar_location = None
        # plot.toolbar.active_drag = None
        # plot.xaxis.axis_label = "Time of Prediction"
        # plot.yaxis.axis_label = target
        # plot.xgrid.grid_line_color = None
        #
        # title_ = Paragraph(text="Accuracy Over Time", align="center", styles={"font-size": "16px"})
        # layout = row([title_, select])
        #
        # doc.add_root(column(layout, plot))
        x = [0, 1, 2]
        y = [1, 0, 2]
        text = [
            "There are no predictions in the selected date range, update the range filter or click reset to return to the default date range.",
            "", ""]
        source = ColumnDataSource(dict(x=x, y=y, text=text))

        plot = Plot(title=None, toolbar_location=None, sizing_mode="fixed", min_width=1200, max_width=2000,
                    height=400)

        glyph = Text(x="x", y="y", text="text")
        plot.add_glyph(source, glyph)

        doc.add_root(plot)
    else:
        t = response.text
        response_df = eval(t)

        df_data = response_df['data']
        df = eval(df_data)

        actual_df = df['actual']

        base_df = df['base']

        x_list = list(df['date'])

        actual_df = pd.DataFrame(actual_df).replace("N/A", np.nan)
        metric_list = actual_df.keys().tolist()
        metric_list.remove('count')

        if model_type == "Regression":
            metric_list.remove('average_predicted')
            metric_list.remove('average_actual')
        elif model_type == "Binary":
            metric_list.remove('percentage_predicted')
            metric_list.remove('percentage_actual')

        x_list = [datetime.strptime(x_list[i], "%Y-%m-%dT%H:%M:%S.%fZ") for i in range(len(x_list))]
        if len(x_list) >= 2:
            term = x_list[1] - x_list[0]
        else:
            term = x_list[0] - x_list[0]
        delta_list = []
        for i in range(len(x_list)):
            delta_list.append(x_list[i] + term)

        actual_df.insert(0, "x_value", x_list)
        actual_df.insert(0, "delta_value", delta_list)

        data = get_data_source(actual_df, target)

        source = ColumnDataSource(data=data)

        base_source = ColumnDataSource(dict(x=[0], y=[base_df[target]]))

        def select_metric(value, old, new):
            global target_data
            target = new
            update_data = get_data_source(actual_df, target)
            base_update_data = get_base_data_source(base_df, target)

            t_l = plot.select_one({'name': 'circle'})
            s_l = plot.select_one({'name': 'line'})
            base_l = base_plot.select_one({'name': 'base_circle'})

            # t_l.data_source.data['y_value'] = target_data
            t_l.data_source.data = update_data
            s_l.data_source.data = update_data
            base_l.data_source.data = base_update_data
            # s_l.data_source.data['y_value'] = target_data
            base_plot.yaxis.axis_label = target
            base_plot.y_range = plot.y_range

        select = Select(value=target, options=metric_list, width=200)
        select.on_change("value", select_metric)

        plot = figure(
            # x_range=FactorRange(factors=x_list),
            x_axis_type="datetime",
            sizing_mode="stretch_width",
            min_width=1200,
            max_width=2000,
            height=400,
        )
        base_plot = figure(height=400, width=150)

        title_ = Paragraph(text="Accuracy Over Time", align="center", styles={"font-size": "16px"})
        layout = row([title_, select])
        layout2 = row([base_plot, plot])

        base_plot.yaxis[0].formatter = NumeralTickFormatter(format='0.000 a')

        plot.circle(x="x", y="y", source=source, size=8, color='green', fill_alpha=0.5, line_color="green",
                    name="circle")

        base_plot.circle(x="x", y="y", source=base_source, size=8, color='green', fill_alpha=0.5, line_color="green",
                         name="base_circle")

        line = plot.line(x="x", y="y", source=source, name='line', hover_alpha=1)
        plot.vbar_stack(['vbar1', 'vbar2'], x='x', source=source)  # 그래프 형태를위한 더미 그래프
        base_plot.vbar_stack(['vbar1', 'vbar2'], x='x', source=base_source, width=0)

        hover_tool = HoverTool(tooltips=[
            # ("date", "$x{%F} ~ $x{%F}"),
            ("date", "@x{%Y-%m-%d:%H} ~ @delta_x{%Y-%m-%d:%H}"),
            ("value", "@y{0.000 a}"),
            # ("value2", "@count")

        ],
            renderers=[line],
            formatters={
                "@x": "datetime",
                "@delta_x": "datetime"
            },
            mode='vline',
            # muted_policy="ignore",
            point_policy="snap_to_data",
            line_policy="nearest",
            show_arrow=False
        )

        base_hover_tool = HoverTool(tooltips=[
            ("value", "@y{0.000 a}")
        ])
        base_plot.y_range = plot.y_range

        # plot.xgrid.grid_line_color = None
        plot.toolbar_location = None
        plot.toolbar.active_drag = None
        # plot.xaxis.axis_label = "Scoring"
        # plot.yaxis.axis_label = target
        plot.xgrid.grid_line_color = None
        plot.yaxis.visible = False
        plot.add_tools(hover_tool)

        base_plot.toolbar_location = None
        base_plot.toolbar.active_drag = None
        # base_plot.xaxis.axis_label = "Training"
        base_plot.yaxis.axis_label = target
        base_plot.xgrid.grid_line_color = None
        # base_plot.xaxis.visible = False
        base_plot.xaxis.major_label_text_font_size = "0px"
        base_plot.xaxis.major_tick_line_color = "white"
        base_plot.xaxis.minor_tick_line_alpha = 0
        base_plot.add_tools(base_hover_tool)

        doc.add_root(column(layout, layout2))


def predicted_actual(doc):
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')

    info_url = ACCURACY_MONITOR_ENDPOINT + "/accuracy-monitor/monitor-info" + "/" + inferenceName
    info_params = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
    }

    info_response = requests.get(info_url, params=info_params, headers=HEADERS)
    if info_response.status_code >= 400:
        # todo 인포를 못받아올 경우
        info = False
    else:
        info_json = json.loads(info_response.text)
        info_data = eval(info_json['data'])
        model_type = info_data['model_type']
        info = True
        binary_thres = False
        if model_type == "Binary":
            if "binary_threshold" in info_data:
                binary_thres = True
                positive_class = info_data["positive_class"]
                negative_class = info_data["negative_class"]
                binary_threshold = info_data["binary_threshold"]

    parse = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
        'start_time': arg['start_time'][0].decode('utf8'),
        'end_time': arg['end_time'][0].decode('utf8'),
        'type': 'timeline'
    }

    data_url = ACCURACY_MONITOR_ENDPOINT + "/accuracy-monitor/predicted-actual" + "/" + inferenceName
    response = requests.get(data_url, params=parse, headers=HEADERS)
    if response.status_code >= 400 or info is False or str(response.text).find("No data") >= 0:
        # plot = figure(sizing_mode="fixed",
        #               min_width=1200,
        #               max_width=2000,
        #               height=400, )
        #
        # title_ = Paragraph(text="Predicted & Actual", align="center", styles={"font-size": "16px"})
        # layout = row([title_])
        #
        # plot.toolbar_location = None
        # plot.toolbar.active_drag = None
        # plot.xaxis.axis_label = "Time of Prediction"
        # plot.yaxis.axis_label = "Percentage of Records"
        # plot.xgrid.grid_line_color = None
        #
        # doc.add_root(column(layout, plot))
        x = [0, 1, 2]
        y = [1, 0, 2]
        text = [
            "There are no predictions in the selected date range, update the range filter or click reset to return to the default date range.",
            "", ""]
        source = ColumnDataSource(dict(x=x, y=y, text=text))

        plot = Plot(title=None, toolbar_location=None, sizing_mode="fixed", min_width=1200, max_width=2000,
                    height=400)

        glyph = Text(x="x", y="y", text="text")
        plot.add_glyph(source, glyph)

        doc.add_root(plot)
    else:
        t = response.text
        response_df = eval(t)

        df_data = response_df['data']
        df = eval(df_data)
        data = df['data']
        date = df['date']
        base = df['base']

        count = []
        total_count = []
        predicted = []
        actual = []

        for i in data:
            count.append(i['count'])
            total_count.append(i['total_count'])
            if model_type == "Regression":
                predicted.append(i['average_predicted'])
                actual.append(i['average_actual'])
                base_source = ColumnDataSource(
                    dict(x=[0], pre=[base["average_predicted"]], act=[base["average_actual"]]))
            elif model_type == "Binary":
                predicted.append(i['percentage_predicted'])
                actual.append(i['percentage_actual'])

                base_source = ColumnDataSource(
                    dict(x=[0], pre=[base["percentage_predicted"] / 100], act=[base["percentage_actual"] / 100]))
            else:
                pass
        date = [datetime.strptime(date[i], "%Y-%m-%dT%H:%M:%S.%fZ") for i in range(len(date))]
        if len(date) >= 2:
            delta = date[1] - date[0]
            delta_second = (date[1] - date[0]).total_seconds()
        else:
            delta = timedelta(hours=1)
            delta_second = 86400
        delta_list = []
        for i in range(len(date)):
            delta_list.append(date[i] + delta)

        x = date
        y = predicted
        y2 = actual

        y_min = np.nanmin(y)
        y_max = np.nanmax(y)
        y2_min = np.nanmin(y2)
        y2_max = np.nanmax(y2)

        vbar_y1 = count
        vbar_y2 = total_count

        max_value = np.nanmax(vbar_y2)

        gap = list(map(operator.sub, vbar_y2, vbar_y1))
        vbar_y2 = gap

        real_y1 = vbar_y1
        vbar_y1 = list(map(lambda x: x / max_value if max_value != 0 else 0, vbar_y1))
        real_y2 = vbar_y2
        vbar_y2 = list(map(lambda x: x / max_value if max_value != 0 else 0, vbar_y2))

        y = [np.nan if x == 0 else x for x in y]
        y2 = [np.nan if x == 0 else x for x in y2]

        source = ColumnDataSource(data=dict(
            x=x,
            delta_x=delta_list,
            vbar1=vbar_y1,
            vbar2=vbar_y2,
            r_vbar1=real_y1,
            r_vbar2=real_y2,
            circle1=y,
            circle2=y2,
        ))

        plot = figure(sizing_mode="fixed",
                      min_width=1200,
                      max_width=2000,
                      height=400, x_axis_type='datetime')

        base_plot = figure(height=400, width=150)

        title_ = Paragraph(text="Predicted & Actual", align="center", styles={"font-size": "16px"})
        layout = row([title_])
        layout2 = row([base_plot, plot])

        if model_type == "Regression":
            tick_max = y_max if y_max > y2_max else y2_max
            tick_min = y_min if y_min < y2_min else y2_min
            term = tick_max - tick_min
            gap = term / 5
            if tick_min == 0:
                tick_min = tick_max - (5 * gap)
            plot.yaxis.ticker = [tick_min, tick_max - (4 * gap), tick_max - (3 * gap), tick_max - (2 * gap),
                                 tick_max - gap, tick_max]
            plot.y_range.start = tick_min - gap
            plot.y_range.end = tick_max + gap
            plot.yaxis[0].formatter = NumeralTickFormatter(format='0.000 a')
            base_plot.yaxis[0].formatter = NumeralTickFormatter(format='0.000 a')

        elif model_type == "Binary":
            plot.yaxis.ticker = [0, 0.2, 0.4, 0.6, 0.8, 1]
            plot.yaxis[0].formatter = NumeralTickFormatter(format='0 %')
            base_plot.yaxis[0].formatter = NumeralTickFormatter(format='0 %')
            plot.y_range.start = -0.2
            plot.y_range.end = 1
        else:
            pass

        base_plot.y_range = plot.y_range
        base_plot.yaxis.ticker = plot.yaxis.ticker
        plot.extra_y_ranges['vbar'] = Range1d(start=0, end=10)
        plot.add_layout(LinearAxis(y_range_name='vbar'), 'right')

        circle1 = plot.circle(x="x", y="circle1", source=source, size=10, color='blue', fill_alpha=0.5)
        circle2 = plot.circle(x="x", y="circle2", source=source, size=10, line_color='red', fill_color="white",
                              fill_alpha=0)
        vbar = plot.vbar_stack(['vbar1', 'vbar2'], x='x', source=source, color=['black', 'black'], fill_alpha=[1, 0],
                               hatch_alpha=1, hatch_pattern='right_diagonal_line', line_color='white',
                               y_range_name='vbar', width=delta_second * 1000)

        base_plot.circle(x="x", y="pre", source=base_source, size=10, color='blue', fill_alpha=0.5)
        base_plot.circle(x="x", y="act", source=base_source, size=10, line_color='red', fill_color="white",
                         fill_alpha=0)

        legend = Legend(items=[
            ("predicted values", [circle1]),
            ("actual values", [circle2]),
            ("number of actuals", [vbar[0]]),
            ("number of preidctions without actuals", [vbar[1]])
        ], orientation='horizontal', location="top_left", background_fill_alpha=0, border_line_alpha=0,
        )
        if model_type == "Binary":
            if binary_thres is True:
                tooltips = [
                    ("date", "@x{%Y-%m-%d:%H} ~ @delta_x{%Y-%m-%d:%H}"),
                    (f"Percentage Predicted({positive_class})", "@circle1{0.00 %}"),
                    (f"Percnetage Actual({positive_class})", "@circle2{0.00 %}"),
                    ("Number of rows", "@r_vbar1{0.000 a}"),
                    ("Number of rows without actuals", "@r_vbar2{0.000 a}"),
                ]
            else:
                tooltips = [
                    ("date", "@x{%Y-%m-%d:%H} ~ @delta_x{%Y-%m-%d:%H}"),
                    (f"Percentage Predicted({positive_class})", "@circle1{0.00 %}"),
                    (f"Percnetage Actual({positive_class})", "@circle2{0.00 %}"),
                    ("Number of rows", "@r_vbar1{0.000 a}"),
                    ("Number of rows without actuals", "@r_vbar2{0.000 a}"),
                ]
            hover_tool = HoverTool(tooltips=tooltips,
                                   renderers=[vbar[0]],
                                   formatters={
                                       "@x": "datetime",
                                       "@delta_x": "datetime",
                                   },
                                   mode='vline',
                                   # muted_policy="ignore",
                                   point_policy="snap_to_data",
                                   line_policy="nearest",
                                   show_arrow=False
                                   )
            base_hover_tool = HoverTool(tooltips=[
                (f"Percentage Predicted({positive_class})", "@pre{0.00 %}"),
                (f"Percentage Actual({positive_class})", "@act{0.00 %}")
            ])
        elif model_type == "Regression":
            hover_tool = HoverTool(tooltips=[
                ("date", "@x{%Y-%m-%d:%H} ~ @delta_x{%Y-%m-%d:%H}"),
                ("Average Predicted", "@circle1{0.000 a}"),
                ("Average Actual", "@circle2{0.000 a}"),
                ("Number of rows", "@r_vbar1{0.000 a}"),
                ("Number of rows without actuals", "@r_vbar2{0.000 a}"),
            ],
                renderers=[vbar[0]],
                formatters={
                    "@x": "datetime",
                    "@delta_x": "datetime",
                },
                mode='vline',
                # muted_policy="ignore",
                point_policy="snap_to_data",
                line_policy="nearest",
                show_arrow=False
            )
            base_hover_tool = HoverTool(tooltips=[
                ("Average Predicted", "@pre{0.000 a}"),
                ("Average Actual", "@act{0.000 a}")
            ])
        else:
            hover_tool = HoverTool()

        plot.add_tools(hover_tool)
        plot.add_layout(legend)
        plot.yaxis[0].visible = False
        plot.yaxis[1].visible = False
        plot.xgrid.grid_line_color = None
        plot.toolbar_location = None
        plot.toolbar.active_drag = None
        plot.xaxis.axis_label = "Scoring \n Time of Prediction"

        base_plot.toolbar_location = None
        base_plot.toolbar.active_drag = None
        base_plot.xaxis.axis_label = "Training"
        base_plot.yaxis.axis_label = "Target value"
        base_plot.xgrid.grid_line_color = None
        # base_plot.xaxis.visible = False
        base_plot.xaxis.major_label_text_font_size = "0px"
        base_plot.xaxis.major_tick_line_color = "white"
        base_plot.xaxis.minor_tick_line_alpha = 0
        base_plot.add_tools(base_hover_tool)

        doc.add_root(column(layout, layout2))


def get_data_source(d, t):
    x_value = list(d['x_value'])
    y_value = list(d[t])
    delta_value = list(d['delta_value'])

    data = {
        'x': x_value,
        'y': y_value,
        'delta_x': delta_value
    }

    return data


def get_base_data_source(d, t):
    x_value = [0]
    if type(d[t]) == str:
        y_value = [np.nan]
    else:
        y_value = [d[t]]

    data = {
        "x": x_value,
        "y": y_value
    }

    return data
