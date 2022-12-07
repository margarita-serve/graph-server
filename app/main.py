from jinja2 import Environment, FileSystemLoader
from tornado.web import RequestHandler

import logging
import os

from bokeh.embed import server_document
from bokeh.server.server import Server

from drift_graph import feature_drift, feature_detail, prediction_over_time
from accuracy_graph import accuracy_over_time, predicted_actual
from service_graph import service_health
from resource import cpu, memory

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s]: {} %(levelname)s %(message)s'.format(os.getpid()),
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger()

MODE = os.environ.get('MODE')
if MODE == "dev":
    env = Environment(loader=FileSystemLoader('templates'))
else:
    env = Environment(loader=FileSystemLoader('app/templates'))


############################################################
# Domain Logic
############################################################


class DriftHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        model_history_id = args.get('modelHistoryID')[0].decode('utf8')
        start_time = args.get('startTime')[0].decode('utf8')
        end_time = args.get('endTime')[0].decode('utf8')
        arg = {
            "inference_name": deploymentID,
            "model_history_id": model_history_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        template = env.get_template('embed.html')
        script = server_document(f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/featuredrift",
                                 arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


class DetailHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        model_history_id = args.get('modelHistoryID')[0].decode('utf8')
        start_time = args.get('startTime')[0].decode('utf8')
        end_time = args.get('endTime')[0].decode('utf8')
        arg = {
            "inference_name": deploymentID,
            "model_history_id": model_history_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        template = env.get_template('embed.html')
        script = server_document(
            f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/featuredetail", arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


class POTHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        model_history_id = args.get('modelHistoryID')[0].decode('utf8')
        start_time = args.get('startTime')[0].decode('utf8')
        end_time = args.get('endTime')[0].decode('utf8')
        arg = {
            "inference_name": deploymentID,
            "model_history_id": model_history_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        template = env.get_template('embed.html')
        script = server_document(
            f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/pot", arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


class AccuracyHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        model_history_id = args.get('modelHistoryID')[0].decode('utf8')
        start_time = args.get('startTime')[0].decode('utf8')
        end_time = args.get('endTime')[0].decode('utf8')

        if args.get('targetMetric') is not None:
            target_metric = args.get('targetMetric')[0].decode('utf8')
        else:
            target_metric = ""
        arg = {
            "inference_name": deploymentID,
            "model_history_id": model_history_id,
            "start_time": start_time,
            "end_time": end_time,
            "target_metric": target_metric
        }

        template = env.get_template('embed.html')
        script = server_document(
            f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/aot", arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


class PAHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        model_history_id = args.get('modelHistoryID')[0].decode('utf8')
        start_time = args.get('startTime')[0].decode('utf8')
        end_time = args.get('endTime')[0].decode('utf8')
        arg = {
            "inference_name": deploymentID,
            "model_history_id": model_history_id,
            "start_time": start_time,
            "end_time": end_time,
        }

        template = env.get_template('embed.html')
        script = server_document(
            f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/pa", arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


class ServiceHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        model_history_id = args.get('modelHistoryID')[0].decode('utf8')
        start_time = args.get('startTime')[0].decode('utf8')
        end_time = args.get('endTime')[0].decode('utf8')

        if args.get('targetMetric') is not None:
            target_metric = args.get('targetMetric')[0].decode('utf8')
        else:
            target_metric = ""

        arg = {
            "inference_name": deploymentID,
            "model_history_id": model_history_id,
            "start_time": start_time,
            "end_time": end_time,
            "target_metric": target_metric
        }

        template = env.get_template('embed.html')
        script = server_document(
            f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/servicehealth", arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


class CpuHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        request_cpu = args.get('requestCPU')[0].decode('utf8')

        arg = {
            "inference_name": deploymentID,
            "request_cpu": request_cpu,
            "host": host_endpoint,
            "xProto": xProto
        }

        template = env.get_template('embed.html')
        script = server_document(
            f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/cpu-graph", arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


class MemoryHandler(RequestHandler):
    def get(self, deploymentID):
        args = self.request.arguments
        host_endpoint = self.request.host
        xProto = self.request.headers.get_list("X-Forwarded-Proto")
        if len(xProto) == 0:
            xProto = "http"
        else:
            xProto = xProto[0]

        request_memory = args.get('requestMemory')[0].decode('utf8')

        arg = {
            "inference_name": deploymentID,
            "request_memory": request_memory,
            "host": host_endpoint,
            "xProto": xProto
        }

        template = env.get_template('embed.html')
        script = server_document(
            f"{xProto}://{host_endpoint}/api/v1/deployments/graph-svr/{deploymentID}/memory-graph", arguments=arg)
        temp = template.render(script=script, template="Tornado")
        self.write(temp)


############################################################
# Main
############################################################


server = Server({
    # drift graph
    '/.*/featuredrift': feature_drift,
    '/.*/featuredetail': feature_detail,
    '/.*/pot': prediction_over_time,
    # accuracy graph
    '/.*/aot': accuracy_over_time,
    '/.*/pa': predicted_actual,
    # servicehealth graph
    '/.*/servicehealth': service_health,
    # resource graph
    '/.*/cpu-graph': cpu,
    '/.*/memory-graph': memory,

},
    num_procs=5,
    extra_patterns=[
        (r'/(?P<deploymentID>\w+)/drift', DriftHandler),
        (r'/(?P<deploymentID>\w+)/detail', DetailHandler),
        (r'/(?P<deploymentID>\w+)/prediction-over-time', POTHandler),
        (r'/(?P<deploymentID>\w+)/accuracy', AccuracyHandler),
        (r'/(?P<deploymentID>\w+)/predicted-actual', PAHandler),
        (r'/(?P<deploymentID>\w+)/service', ServiceHandler),
        (r'/(?P<deploymentID>\w+)/cpu', CpuHandler),
        (r'/(?P<deploymentID>\w+)/memory', MemoryHandler)
    ],
    allow_websocket_origin=["*"],
    prefix="/api/v1/deployments/graph-svr",
    # http_server_kwargs=dict({"xheaders": True})
)
# server.start()

if __name__ == '__main__':
    server.io_loop.start()
