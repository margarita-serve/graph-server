import os

from bokeh.models import HoverTool, AjaxDataSource, DatetimeTickFormatter, Paragraph
from bokeh.plotting import figure
from bokeh.layouts import column, row

HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8',
           'http-equiv': "Content-Security-Policy", 'content': "upgrade-insecure-requests",
           'Access-Control-Allow-Origin': "*"}

KORESERVE_MAIN_REST_API_SERVER_ENDPOINT = os.environ.get('KORESERVE_MAIN_REST_API_SERVER_ENDPOINT')


def cpu(doc):
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')
    request_cpu = arg['request_cpu'][0].decode('utf8')
    host = arg['host'][0].decode('utf8')

    pod_name = "{" + f"pod=~'{inferenceName}-.*', container='kserve-container'" + "}"
    query = f"query=sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{pod_name}) by (container)"

    url = f"http://{host}" + f'/api/v1/deployments/graph-data/{inferenceName}'
    # url = KORESERVE_MAIN_REST_API_SERVER_ENDPOINT + f'/api/v1/deployments/graph-data/{inferenceName}'
    # url = "http://localhost:8080" + f'/api/v1/deployments/graph-data/{inferenceName}'

    source = AjaxDataSource(data_url=f"{url}?{query}", polling_interval=60000, mode='replace', method='GET',
                            http_headers=HEADERS, if_modified=True, max_size=32)
    source.data = dict(x=[], y=[])

    plot = figure(x_axis_type="datetime", sizing_mode='fixed', width=1500, max_width=2000, height=400)

    title_ = Paragraph(text="CPU(cores)", align="center", styles={"font-size": "16px"})
    layout = row([title_])

    plot.line(x='x', y='y', source=source)
    plot.xaxis.formatter = DatetimeTickFormatter(
        hours=["%H:%M"],
        minutes=["%H:%M"],
    )

    hover_tool = HoverTool(tooltips=[
        ("date", "@x{%T}"),
        ("value", "@y{0.0000}"),

    ],
        formatters={
            "@x": "datetime",
        },
        mode='vline',
        muted_policy="ignore",
        point_policy="snap_to_data",
        line_policy="nearest",
        show_arrow=False
    )
    plot.y_range.start = 0
    plot.y_range.end = float(request_cpu)
    plot.add_tools(hover_tool)
    plot.toolbar_location = None
    plot.toolbar.active_drag = None

    doc.add_root(column(layout, plot))


def memory(doc):
    arg = doc.session_context.request.arguments
    inferenceName = arg['inference_name'][0].decode('utf8')
    request_memory = arg['request_memory'][0].decode('utf8')
    host = arg['host'][0].decode('utf8')

    pod_name = "{" + f"pod=~'{inferenceName}-.*', container='kserve-container'" + "}"
    query = f"query=sum(container_memory_working_set_bytes{pod_name}) by (container) / (1024*1024)"

    url = f"http://{host}" + f'/api/v1/deployments/graph-data/{inferenceName}'
    # url = KORESERVE_MAIN_REST_API_SERVER_ENDPOINT + f'/api/v1/deployments/graph-data/{inferenceName}'
    # url = "http://localhost:8080" + f'/api/v1/deployments/graph-data/{inferenceName}'

    source = AjaxDataSource(data_url=f"{url}?{query}", polling_interval=60000, mode='replace', method='GET',
                            http_headers=HEADERS, if_modified=True, max_size=32)
    source.data = dict(x=[], y=[])

    plot = figure(x_axis_type="datetime", sizing_mode='fixed', width=1500, max_width=2000, height=400)
    title_ = Paragraph(text="Memory(Mi)", align="center", styles={"font-size": "16px"})
    layout = row([title_])

    plot.line(x='x', y='y', source=source)
    plot.xaxis.formatter = DatetimeTickFormatter(
        hours=["%H:%M"],
        minutes=["%H:%M"],
    )

    hover_tool = HoverTool(tooltips=[
        ("date", "@x{%T}"),
        ("value", "@y{0}"),

    ],
        formatters={
            "@x": "datetime",
        },
        mode='vline',
        muted_policy="ignore",
        point_policy="snap_to_data",
        line_policy="nearest",
        show_arrow=False
    )
    plot.y_range.start = 0
    plot.y_range.end = float(request_memory) * 1024
    plot.add_tools(hover_tool)
    plot.toolbar_location = None
    plot.toolbar.active_drag = None

    doc.add_root(column(layout, plot))
