import requests
import os
import logging

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool, Span, Range1d, CDSView, BooleanFilter, Select, \
    NumericInput, NumeralTickFormatter, LinearAxis, Legend, Paragraph, Label, Text, Plot
from bokeh.models.ranges import FactorRange
from bokeh.plotting import figure
from bokeh.transform import dodge
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import math

HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8',
           'http-equiv': "Content-Security-Policy", 'content': "upgrade-insecure-requests"}

DRIFT_MONITOR_ENDPOINT = os.environ.get('DRIFT_MONITOR_ENDPOINT')

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s]: {} %(levelname)s %(message)s'.format(os.getpid()),
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger()

global target_feature
global target_data


def feature_detail(doc):
    global target_feature
    global target_data
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')
    parse = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
        'start_time': arg['start_time'][0].decode('utf8'),
        'end_time': arg['end_time'][0].decode('utf8')
    }
    url = DRIFT_MONITOR_ENDPOINT + "/drift-monitor/feature-detail" + "/" + inferenceName
    response = requests.get(url, params=parse, headers=HEADERS)

    if response.status_code >= 400 or str(response.text).find("No data") >= 0:

        # plot = figure(x_range=(0, 1))
        # plot.xaxis.axis_label = 'Feature'
        # plot.yaxis.axis_label = 'Percentage of Records'
        # select = Select(value="feature", width=200)
        # title_ = Paragraph(text="Feature Details", align="center", styles={"font-size": "16px"})
        # layout = row([title_, select])
        #
        # plot.vbar(x=dodge('Label', -0.25, range=plot.x_range), top='Training', width=0.25, color='green',
        #           legend_label='Training', name='training')
        # plot.vbar(x=dodge('Label', 0.0, range=plot.x_range), top='Scoring', width=0.25, color='blue',
        #           legend_label='Scoring', name='scoring')
        #
        # plot.xgrid.grid_line_color = None
        # plot.legend.location = "top_right"
        # plot.legend.orientation = "horizontal"
        # plot.toolbar_location = None
        # plot.toolbar.active_drag = None

        x = [0, 1, 2]
        y = [1, 0, 2]
        text = ["In the selected time range there are no predictions.", "", ""]
        source = ColumnDataSource(dict(x=x, y=y, text=text))

        plot = Plot(title=None, toolbar_location=None)

        glyph = Text(x="x", y="y", text="text")
        plot.add_glyph(source, glyph)

        doc.add_root(plot)

    else:
        t = response.text
        response_df = eval(t)

        df_data = response_df['data']
        df = eval(df_data)
        feature_list = list(df['Label'].values())

        target_feature = feature_list[0]
        target_data = df['features'][target_feature]

        def select_feature(value, old, new):
            global target_feature
            global target_data
            target_feature = new
            target_data = df['features'][target_feature]
            update_data = get_target_data(target_data)

            plot.x_range.factors = update_data['Label']
            plot.xaxis.axis_label = target_feature
            t_l = plot.select_one({'name': 'training'})
            s_l = plot.select_one({'name': 'scoring'})
            t_l.data_source.data = update_data
            s_l.data_source.data = update_data

        select = Select(value=target_feature, options=feature_list, width=200)
        select.on_change("value", select_feature)

        title_ = Paragraph(text="Feature Details", align="center", styles={"font-size": "16px"})
        layout = row([title_, select])

        data = get_target_data(target_data)

        hover_tool = HoverTool(tooltips=[
            ("label", "@Delta_Label"),
            ("training", "@Training{0.0 %}"),
            ("scoring", "@Scoring{0.0 %}")
        ],
            mode='vline'
        )

        source = ColumnDataSource(data=data)

        plot = figure(x_range=FactorRange(factors=data['Label']))
        plot.xaxis.axis_label = target_feature
        plot.yaxis.axis_label = 'Percentage of Records'
        plot.yaxis[0].formatter = NumeralTickFormatter(format='0 %')
        plot.add_tools(hover_tool)

        plot.vbar(x=dodge('Label', -0.25, range=plot.x_range), top='Training', width=0.25, source=source, color='green',
                  legend_label='Training', name='training')
        plot.vbar(x=dodge('Label', 0.0, range=plot.x_range), top='Scoring', width=0.25, source=source, color='blue',
                  legend_label='Scoring', name='scoring')

        plot.x_range.range_padding = 0.1
        plot.xgrid.grid_line_color = None
        plot.toolbar_location = None
        plot.toolbar.active_drag = None

        doc.add_root(column(layout, plot))


global drift_line
global importance_line


def feature_drift(doc):
    global drift_line
    global importance_line
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')
    parse = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
        'start_time': arg['start_time'][0].decode('utf8'),
        'end_time': arg['end_time'][0].decode('utf8')
    }
    url = DRIFT_MONITOR_ENDPOINT + "/drift-monitor/feature-drift" + "/" + inferenceName
    response = requests.get(url, params=parse, headers=HEADERS)
    if response.status_code >= 400 or str(response.text).find("No data") >= 0:
        # importance_thres = 0.5
        # dri_thres = 0.15
        # plot = figure()
        # plot.xaxis.axis_label = 'Importance'
        # plot.yaxis.axis_label = 'Drift'
        # plot.x_range = Range1d(-0.01, 1.1)
        # plot.y_range = Range1d(-0.0025, 0.25)
        # importance_line = float(importance_thres)
        # drift_line = float(dri_thres)
        # draw_threshold(plot, drift_line, importance_line)
        # drift_input = NumericInput(value=dri_thres, title="Drift Line :", width=60, mode='float', low=0.01,
        #                            high=0.99, placeholder="0.01")
        # import_input = NumericInput(value=importance_thres, title="Importance Line :", width=60, mode='float',
        #                             low=0.01, high=0.99, placeholder="0.01")
        # plot.toolbar_location = None
        # plot.toolbar.active_drag = None
        # title_ = Paragraph(text="Feature Drift vs. Feature Importance  ", align="center", styles={"font-size": "16px"})
        # drift_ = Paragraph(text="Drift Line :", align="center", styles={"font-size": "12px"})
        # importance_ = Paragraph(text="Importance Line :", align="center", styles={"font-size": "12px"})
        # layout = row([title_, drift_, drift_input, importance_, import_input])
        #
        # doc.add_root(column(layout, plot))
        x = [0, 1, 2]
        y = [1, 0, 2]
        text = ["In the selected time range there are no predictions.", "", ""]
        source = ColumnDataSource(dict(x=x, y=y, text=text))

        plot = Plot(title=None, toolbar_location=None)

        glyph = Text(x="x", y="y", text="text")
        plot.add_glyph(source, glyph)

        doc.add_root(plot)
    else:
        t = response.text
        response_df = eval(t)

        df_data = response_df['data']

        df = eval(df_data)
        threshold = df.pop('threshold')
        dri_thres = threshold['drift']
        importance_thres = threshold['importance']

        data = pd.DataFrame(df)

        data['trans value'] = 0
        sco = data['drift score'].copy()
        tra = data['trans value'].copy()

        for i in range(len(data['drift score'])):
            if sco[i] > 1:
                tra[i] = 1
            else:
                tra[i] = sco[i]

        data['drift score'] = tra
        data['trans value'] = sco

        source = ColumnDataSource(data=data)
        # hover tool로 tooltips 와 formatters를 지정
        hover_tool = HoverTool(tooltips=[
            ("Name", "@{Label}"),
            ("Drift", "@{trans value}{0.000}"),
            ("Improtance", "@{feature importance}{0.000}")
        ],
            mode='mouse'
        )
        importance_line = float(importance_thres)
        drift_line = float(dri_thres)
        # 드리프트와 중요도 임계치를 넘는 항목 체크
        danger, warning, passing = drift_check(drift_line, importance_line,
                                               data['drift score'], data['feature importance'])

        danger_group, warning_group, passing_group = set_group(source, danger, warning, passing)

        if data['drift score'].max() > 0.25:
            if data['drift score'].max() < 1:
                y_range = data['drift score'].max() + 0.1
            else:
                y_range = 1.1
        else:
            y_range = 0.25

        plot = figure()
        plot.xaxis.axis_label = 'Importance'
        plot.yaxis.axis_label = 'Drift'
        plot.x_range = Range1d(-0.01, 1.1)
        plot.y_range = Range1d(-0.0025, y_range)

        draw_graph(plot, source, danger_group, warning_group, passing_group)

        # hover tool 추가
        plot.add_tools(hover_tool)
        draw_threshold(plot, drift_line, importance_line)

        def change_drift(value, old, new):
            global drift_line
            global importance_line
            if new is not None:
                drift_line = float(new)
                if drift_line >= 1:
                    drift_line = 0.99
                elif drift_line < 0:
                    drift_line = 0.01
                plot.renderers = []
                dangers, warnings, passings = drift_check(drift_line, importance_line, source.data['drift score'],
                                                          source.data['feature importance'])
                danger_groups, warning_groups, passing_groups = set_group(source, dangers, warnings, passings)
                draw_graph(plot, source, danger_groups, warning_groups, passing_groups)
                draw_threshold(plot, drift_line, importance_line)

        def change_import(value, old, new):
            global drift_line
            global importance_line
            if new is not None:
                importance_line = float(new)
                if importance_line >= 1:
                    importance_line = 0.99
                elif importance_line < 0:
                    importance_line = 0.01
                plot.renderers = []
                dangers, warnings, passings = drift_check(drift_line, importance_line, source.data['drift score'],
                                                          source.data['feature importance'])
                danger_groups, warning_groups, passing_groups = set_group(source, dangers, warnings, passings)
                draw_graph(plot, source, danger_groups, warning_groups, passing_groups)
                draw_threshold(plot, drift_line, importance_line)

        drift_input = NumericInput(value=dri_thres, width=60, mode='float', low=0.01,
                                   high=0.99, placeholder="0.01")
        drift_input.on_change('value', change_drift)

        import_input = NumericInput(value=importance_thres, width=60,
                                    mode='float', low=0.01, high=0.99, placeholder="0.01")
        import_input.on_change('value', change_import)

        title_ = Paragraph(text="Feature Drift vs. Feature Importance ", align="center", styles={"font-size": "16px"})
        drift_ = Paragraph(text="Drift Line :", align="center", styles={"font-size": "12px"})
        importance_ = Paragraph(text="Importance Line :", align="center", styles={"font-size": "12px"})
        layout = row([title_, drift_, drift_input, importance_, import_input])

        plot.toolbar_location = None
        plot.toolbar.active_drag = None

        doc.add_root(column(layout, plot))


def prediction_over_time(doc):
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')
    parse = {
        'model_history_id': arg['model_history_id'][0].decode('utf8'),
        'start_time': arg['start_time'][0].decode('utf8'),
        'end_time': arg['end_time'][0].decode('utf8')
    }
    url = DRIFT_MONITOR_ENDPOINT + "/drift-monitor/prediction-over-time" + "/" + inferenceName
    response = requests.get(url, params=parse, headers=HEADERS)

    logger.info(parse['start_time'])
    logger.info(parse['end_time'])

    if response.status_code >= 400 or str(response.text).find("No data") >= 0:
        # plot = figure(sizing_mode="stretch_width",
        #               min_width=1200,
        #               max_width=2000,
        #               height=400, )
        # plot.toolbar_location = None
        # plot.toolbar.active_drag = None
        # plot.xaxis.axis_label = "Time of Prediction"
        # plot.yaxis.axis_label = "Average Predicted Value"
        # plot.xgrid.grid_line_color = None
        #
        # title_ = Paragraph(text="Predictions Over Time", align="center", styles={"font-size": "16px"})
        # layout = row([title_])
        #
        # doc.add_root(column(layout, plot))
        x = [0, 1, 2]
        y = [1, 0, 2]
        text = ["In the selected time range there are no predictions.", "", ""]
        source = ColumnDataSource(dict(x=x, y=y, text=text))

        plot = Plot(title=None, toolbar_location=None, sizing_mode="stretch_width", min_width=1200, max_width=2000,
                    height=400)

        glyph = Text(x="x", y="y", text="text")
        plot.add_glyph(source, glyph)

        doc.add_root(plot)
    else:
        t = response.text
        response_df = eval(t)
        nan = np.nan
        df_data = response_df['data']
        df = eval(df_data)
        data = df['data']
        date = df['date']

        count = []
        avg = []
        tenth = []
        ninth = []

        for i in data:
            count.append(i['count'] if math.isnan(i['count']) is False else 0)
            avg.append(i['avg'])
            tenth.append(i['10th'])
            ninth.append(i['90th'])

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

        max_value = np.nanmax(count)
        real_count = count
        count = list(map(lambda x: x / max_value if max_value != 0 else 0, count))

        source = ColumnDataSource(data=dict(
            x=date,
            delta_x=delta_list,
            tenth=tenth,
            ninth=ninth,
            avg=avg,
            count_percent=count,
            count_value=real_count
        ))

        plot = figure(x_axis_type="datetime",
                      sizing_mode="fixed",
                      min_width=1200,
                      max_width=2000,
                      height=400, )

        range_vbar = plot.vbar(x="x", bottom='tenth', top='ninth', source=source, color='dodgerblue',
                               fill_alpha=0.3, line_color="white", width=delta_second * 1000)

        avg_circle = plot.circle(x="x", y="avg", source=source, size=10, line_color='blue', fill_color="white",
                                 fill_alpha=0)

        count_vbar = plot.vbar(x='x', top='count_percent', source=source, color='black', fill_alpha=0.7,
                               line_color='white', y_range_name='vbar', width=delta_second * 1000)

        tick_max = np.nanmax(ninth)
        tick_min = np.nanmin(tenth)
        if tick_max == tick_min:
            tick_min = 0
        term = tick_max - tick_min
        gap = term / 5
        if tick_min == 0:
            tick_min = tick_max - (5 * gap)
        plot.yaxis.ticker = [tick_min, tick_max - (4 * gap), tick_max - (3 * gap), tick_max - (2 * gap),
                             tick_max - gap, tick_max]
        plot.y_range.start = tick_min - gap
        plot.y_range.end = tick_max + gap
        plot.yaxis[0].formatter = NumeralTickFormatter(format='0.000 a')

        plot.extra_y_ranges['vbar'] = Range1d(start=0, end=10)
        plot.add_layout(LinearAxis(y_range_name='vbar'), 'right')

        legend = Legend(items=[
            ("Avg. Predicted Value", [avg_circle]),
            ("10th-90th Percentile", [range_vbar]),
            ("number of predictions", [count_vbar]),
        ], orientation='horizontal', location="top_left", background_fill_alpha=0, border_line_alpha=0,
        )

        hover_tool = HoverTool(tooltips=[
            ("date", "@x{%Y-%m-%d:%H} ~ @delta_x{%Y-%m-%d:%H}"),
            ("Average Predicted Value", "@avg{0.000 a}"),
            ("10th-90th Percentile", "@tenth{0.000 a} - @ninth{0.000 a}"),
            ("Predictions", "@count_value{0.000 a}")
        ],
            renderers=[count_vbar],
            formatters={
                "@x": "datetime",
                "@delta_x": "datetime",
            },
            mode='vline',
            muted_policy="ignore",
            point_policy="snap_to_data",
            line_policy="nearest",
            show_arrow=False
        )

        plot.add_tools(hover_tool)
        plot.add_layout(legend)
        # plot.legend.location = "top_left"
        plot.yaxis[1].visible = False

        plot.ygrid.grid_line_color = None
        plot.xaxis.axis_label = "Time of Prediction"
        plot.outline_line_color = None
        plot.toolbar_location = None
        plot.toolbar.active_drag = None

        title_ = Paragraph(text="Predictions Over Time", align="center", styles={"font-size": "16px"})
        layout = row([title_])
        doc.add_root(column(layout, plot))


def drift_check(drift, importance, drift_source, importance_source):
    booleans1 = [bool(driftscore >= drift) for driftscore in drift_source]
    booleans2 = [bool(importancescore >= importance) for importancescore in importance_source]

    # 드리프트와 중요치 둘다 임계치를 넘은 경우 (위험)
    danger = [(booleans1[i] is True and booleans2[i] is True) for i in range(len(booleans1))]
    # 드리프트만 임계치를 넘은 경우 (경고)
    warning = [(booleans1[i] is True and booleans2[i] is False) for i in range(len(booleans1))]
    # 드리프트 되지 않은 일반 항목
    passing = [booleans1[i] is False for i in range(len(booleans1))]

    return danger, warning, passing


def set_group(source, danger, warning, passing):
    # 위험 그룹
    danger_group = CDSView(source=source, filters=[BooleanFilter(danger)])
    # 경고 그룹
    warning_group = CDSView(source=source, filters=[BooleanFilter(warning)])
    # 일반 그룹
    passing_group = CDSView(source=source, filters=[BooleanFilter(passing)])

    return danger_group, warning_group, passing_group


def draw_graph(plot, source, danger_group, warning_group, passing_group):
    plot.scatter("feature importance", "drift score", source=source, fill_alpha=0.2, size=10, view=danger_group,
                 color='red')
    plot.scatter("feature importance", "drift score", source=source, fill_alpha=0.2, size=10, view=warning_group,
                 color='orange')
    plot.scatter("feature importance", "drift score", source=source, fill_alpha=0.2, size=10, view=passing_group,
                 color='blue')


def draw_threshold(plot, drift, importance):
    x = Span(location=importance, dimension='height', line_color='gray', line_width=1)
    y = Span(location=drift, dimension='width', line_color='gray', line_width=1)
    plot.renderers.extend([x, y])


def get_target_data(gtarget_data):
    labels = list(gtarget_data['Training']['Label'].values())
    delta_labels = make_label(labels)

    train_data = list(gtarget_data['Training']['Percentage'].values())
    sco_data = list(gtarget_data['Scoring']['Percentage'].values())

    data = {'Label': labels,
            'Delta_Label': delta_labels,
            'Training': train_data,
            'Scoring': sco_data
            }
    return data


def make_label(labels):
    temp = [None] * 13
    for i in range(len(labels)):
        if i == 0 or i == 11 or i == 12:
            temp[i] = labels[i]
        elif i == 10:
            temp[i] = f"{labels[i]} ~ {labels[i + 1][1:]}"
        else:
            temp[i] = f"{labels[i]} ~ {labels[i + 1]}"

    return temp
