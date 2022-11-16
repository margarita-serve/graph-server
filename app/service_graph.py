import requests
import os

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool, Range1d, Select, Plot, Text, NumeralTickFormatter
from bokeh.plotting import figure

import pandas as pd
from datetime import datetime, timedelta
import math

HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8',
           'http-equiv': "Content-Security-Policy", 'content': "upgrade-insecure-requests"}

SERVICE_MONITOR_ENDPOINT = os.environ.get('SERVICE_MONITOR_ENDPOINT')


def service_health(doc):
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')
    target_metric = arg['target_metric'][0].decode('utf8')

    parse = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
        'start_time': arg['start_time'][0].decode('utf8'),
        'end_time': arg['end_time'][0].decode('utf8'),
        'type': 'timeline'
    }

    data_url = SERVICE_MONITOR_ENDPOINT + "/servicehealth-monitor/servicehealth" + "/" + inferenceName
    response = requests.get(data_url, params=parse, headers=HEADERS)
    if response.status_code >= 400:
        # plot = figure()
        # select = Select(value="metric", width=200)
        # layout = row([select])
        #
        # plot.toolbar_location = None
        # plot.toolbar.active_drag = None
        # plot.xaxis.axis_label = "Time of Prediction"
        # plot.yaxis.axis_label = "Total Predictions"
        # plot.xgrid.grid_line_color = None
        #
        # doc.add_root(column(layout, plot))
        x = [0, 1, 2]
        y = [1, 0, 2]
        text = [
            "There are no predictions in the selected date range, update the range filter or click reset to return to the default date range.",
            "", ""]
        source = ColumnDataSource(dict(x=x, y=y, text=text))

        plot = Plot(title=None, toolbar_location=None, sizing_mode="stretch_width", min_width=1200, max_width=2000,
                    height=400)

        glyph = Text(x="x", y="y", text="text")
        plot.add_glyph(source, glyph)

        doc.add_root(plot)
    else:
        t = response.text
        response_df = eval(t)

        df_data = response_df['data']
        df = eval(df_data)
        metric_list = list(df.keys())
        if target_metric != "":
            target = target_metric
        else:
            target = metric_list[0]
        target_data = df[target]['value']

        x_list = list(target_data.keys())
        if len(x_list[0]) == 10:
            date_type = 'day'
        else:
            date_type = 'hour'

        if date_type == 'day':
            x_list = [datetime.strptime(x_list[i], "%Y-%m-%d") for i in range(len(x_list))]
        else:
            x_list = [datetime.strptime(x_list[i], "%Y-%m-%d %H:%M") - timedelta(hours=1) for i in range(len(x_list))]

        if len(x_list) >= 2:
            term = x_list[1] - x_list[0]
        else:
            term = x_list[0] - x_list[0]

        delta_list = []

        for i in range(len(x_list)):
            delta_list.append(x_list[i] + term)

        target_df = pd.DataFrame(list(target_data.items()), columns=['x_value', 'y_value'])
        target_df.pop('x_value')
        target_df.insert(0, "x_value", x_list)
        target_df.insert(0, "delta_value", delta_list)

        source = ColumnDataSource(data=target_df)
        source2 = ColumnDataSource(data=target_df)

        if target_df['y_value'].max() > 1:
            digit_len = int(math.log10(target_df['y_value'].max()))
            if digit_len == 0:
                max_value = 10
            else:
                max_value = 10 ** (digit_len + 1)
        else:
            max_value = 1.2

        def select_metric(value, old, new):
            target = new
            update_data, other = get_data(target_df, df, target)

            if target == "median_peak_load":
                if max(other['y_value']) > 1:
                    digit_len = int(math.log10(max(other['y_value'])))
                    if digit_len == 0:
                        max_value = 10
                    else:
                        max_value = 10 ** (digit_len + 1)
                else:
                    max_value = 1.2
                t_l2 = plot.select_one({'name': 'circle2'})
                s_l2 = plot.select_one({'name': 'line2'})

            else:
                if max(update_data['y_value']) > 1:
                    digit_len = int(math.log10(max(update_data['y_value'])))
                    if digit_len == 0:
                        max_value = 10
                    else:
                        max_value = 10 ** (digit_len + 1)
                else:
                    max_value = 1.2

                t_l2 = plot.select_one({'name': 'circle2'})
                s_l2 = plot.select_one({'name': 'line2'})
                t_l2.visible = False
                s_l2.visible = False
                plot.legend.items[0].visible = False
                plot.legend.items[1].visible = False

            t_l = plot.select_one({'name': 'circle'})
            s_l = plot.select_one({'name': "line"})

            t_l.visible = False
            s_l.visible = False
            plot.y_range.end = max_value
            t_l.data_source.data = update_data
            s_l.data_source.data = update_data
            t_l.visible = True
            s_l.visible = True
            # setattr(plot.legend.items[0].label, value, target)
            # plot.legend.items[0].label['value'] = target
            if target == "median_peak_load":
                t_l2.data_source.data = other
                s_l2.data_source.data = other
                t_l2.visible = True
                s_l2.visible = True
                # setattr(plot.legend.items[0].label, value, "median load")
                # setattr(plot.legend.items[1].label, value, "peak load")
                # plot.legend.items[0].label['value'] = "median load"
                # plot.legend.items[1].label['value'] = "peak load"
                plot.legend.items[0].visible = True
                plot.legend.items[1].visible = True

            if target == "median_peak_load":
                plot.yaxis.axis_label = target + "(per/min)"
            elif target == "response_time":
                plot.yaxis.axis_label = target + "(ms)"
            else:
                plot.yaxis.axis_label = target

        select = Select(value=target, options=metric_list, width=200)
        select.on_change("value", select_metric)

        plot = figure(
            x_axis_type='datetime',
            sizing_mode='fixed',
            width=1500,
            max_width=2000,
            height=400
        )

        layout = row([select])

        plot.circle(x="x_value", y="y_value", source=source, size=5, color='green', fill_alpha=0.5, name='circle')
        plot.circle(x="x_value", y="y_value", source=source2, size=5, color='red', fill_alpha=0.5, name='circle2',
                    visible=False)
        r1 = plot.line(x="x_value", y="y_value", source=source, name='line', hover_alpha=1, color='green',
                       legend_label="median load")
        r2 = plot.line(x="x_value", y="y_value", source=source2, name='line2', hover_alpha=1, color='red',
                       visible=False, legend_label="peak load")

        hover_tool = HoverTool(tooltips=[
            # ("date", "$x{%F} ~ $x{%F}"),
            ("date", "@x_value{%Y-%m-%d %H} ~ @delta_value{%Y-%m-%d %H}"),
            ("value", "@y_value{0.000 a}"),
            # ("value2", "@count")

        ],
            renderers=[r1, r2],
            formatters={
                "@x_value": "datetime",
                "@delta_value": "datetime"
            },
            mode='vline',
            muted_policy="ignore",
            point_policy="snap_to_data",
            line_policy="nearest",
            show_arrow=False
        )

        plot.y_range = Range1d(-0.0025, max_value)
        plot.yaxis[0].formatter = NumeralTickFormatter(format='0.000 a')
        plot.toolbar_location = None
        plot.toolbar.active_drag = None
        plot.xaxis.axis_label = "Time of Prediction"
        plot.yaxis.axis_label = target
        plot.xgrid.grid_line_color = None
        plot.add_tools(hover_tool)
        plot.legend.items[0].visible = False
        plot.legend.items[1].visible = False

        doc.add_root(column(layout, plot))


def get_data(target_df, df, target):
    if target == 'median_peak_load':
        y_value = list(df[target]['median']['value'].values())
        peak_value = list(df[target]['peak']['value'].values())
    else:
        y_value = list(df[target]['value'].values())
        peak_value = []

    x_value = list(target_df['x_value'])
    delta_value = list(target_df['delta_value'])

    data = {
        'x_value': x_value,
        'y_value': y_value,
        'delta_value': delta_value
    }
    other = {
        'x_value': x_value,
        'y_value': peak_value,
        'delta_value': delta_value
    }

    return data, other
