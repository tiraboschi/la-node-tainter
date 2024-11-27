#!/usr/bin/python3
import logging
import math
import os
import sys
from collections import OrderedDict

import requests
from kubernetes import client, config
from openshift.dynamic import DynamicClient
from prometheus_api_client import PrometheusConnect

loglevel = os.environ.get('LOGLEVEL', 'INFO').upper()
logger = logging.getLogger("la_taint_nodes")
logger.setLevel(loglevel)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(loglevel)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


TAINT_KEY = "la-taint-psi-cpu"
PSI_CPU_QUERY = 'rate(node_pressure_cpu_waiting_seconds_total[1m])'
MAX_TAINTS_RATIO = 0.50
HARD_TAINT = 'NoSchedule'
SOFT_TAINT = 'PreferNoSchedule'
HARD_TAINT_THRESHOLD = 50.0
SOFT_TAINT_THRESHOLD = 20.0


class BearerAuth(requests.auth.AuthBase):

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


def get_max_hard_taints(wnode_num):
    return int(math.floor(wnode_num*MAX_TAINTS_RATIO))


def get_max_soft_taints(wnode_num, htaints_num):
    return int(math.floor(wnode_num*MAX_TAINTS_RATIO))-htaints_num


def get_hard_taint():
    return {'effect': HARD_TAINT, 'key': TAINT_KEY, 'value': HARD_TAINT}


def get_soft_taint():
    return {'effect': SOFT_TAINT, 'key': TAINT_KEY, 'value': SOFT_TAINT}


def get_worker_nodes():
    worker_nodes = {}
    v1 = client.CoreV1Api()
    ret = v1.list_node(label_selector='node-role.kubernetes.io/worker')
    for i in ret.items:
        worker_nodes[i.metadata.name] = {
            "existing_taint": None,
            "cpu_pressure": 0.0,
            "proposed_taint": None
        }
        if i.spec.taints is not None:
            for t in i.spec.taints:
                if t.key == TAINT_KEY:
                    worker_nodes[i.metadata.name]["existing_taint"] = t
    logger.debug(f"get_worker_nodes: {worker_nodes}")
    return worker_nodes


def get_prom_url(dyn_client):
    v1_routes = dyn_client.resources.get(
        api_version='route.openshift.io/v1',
        kind='Route'
    )
    prometheus_route = v1_routes.get(
        name="prometheus-k8s",
        namespace="openshift-monitoring"
    )

    return f"https://{prometheus_route.status.ingress[0].host}"


def get_metric_for_nodes(prometheus_url, token_content, worker_nodes):
    prom = PrometheusConnect(
        url=prometheus_url,
        disable_ssl=False,
        auth=BearerAuth(token_content)
    )
    cm = prom.custom_query(query=PSI_CPU_QUERY)
    for m in cm:
        node = m.get('metric').get('instance')
        if node in worker_nodes:
            worker_nodes[node]["cpu_pressure"] = float(m.get('value')[1]) * 100
    logger.debug(f"get_metric_for_nodes: {worker_nodes}")
    return worker_nodes


def sort_nodes_by_metric(worker_nodes):
    return OrderedDict(
        sorted(
            worker_nodes.items(),
            key=lambda x: x[1]['cpu_pressure'],
            reverse=True
        )
    )


def set_expected_taints(worker_nodes_sorted):
    wnode_num = len(worker_nodes_sorted)
    max_hard_taints = get_max_hard_taints(wnode_num)
    max_soft_taints = max_hard_taints
    hard_taints = 0
    soft_taints = 0
    for node_name in worker_nodes_sorted:
        metric_value = worker_nodes_sorted[node_name]['cpu_pressure']
        if (metric_value >= HARD_TAINT_THRESHOLD
                and hard_taints < max_hard_taints):
            worker_nodes_sorted[node_name]['proposed_taint'] = get_hard_taint()
            hard_taints = hard_taints + 1
            max_soft_taints = get_max_soft_taints(wnode_num, hard_taints)
            if hard_taints >= max_hard_taints:
                break
        elif (metric_value >= SOFT_TAINT_THRESHOLD
              and soft_taints < max_soft_taints):
            worker_nodes_sorted[node_name]['proposed_taint'] = get_soft_taint()
            soft_taints = soft_taints + 1
            if soft_taints >= max_soft_taints:
                break
        else:
            break


def apply_taint(node_name, proposed_taint):
    # TODO: implement me
    logger.info("apply")


def remove_taint(node_name, proposed_taint):
    # TODO: implement me
    logger.info("remove")


def update_taint(node_name, proposed_taint):
    # TODO: implement me
    logger.info("update")


def compute_apply_patches(worker_nodes_sorted):
    for node_name in worker_nodes_sorted:
        existing_taint = worker_nodes_sorted[node_name]['existing_taint']
        proposed_taint = worker_nodes_sorted[node_name]['proposed_taint']
        if existing_taint is None and proposed_taint is not None:
            apply_taint(node_name, proposed_taint)
        elif existing_taint is not None and proposed_taint is None:
            remove_taint(node_name, proposed_taint)
        elif (existing_taint is not None and proposed_taint is not None
              and existing_taint['effect'] != proposed_taint['effect']):
            update_taint(node_name, proposed_taint)


def main():
    try:
        config.load_incluster_config()
        token = '/var/run/secrets/kubernetes.io/serviceaccount/token'
        ca_crt = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
    except config.ConfigException:
        config.load_kube_config()
        # oc create token -n openshift-la-node-tainter la-node-tainter > token
        token = 'token'
        # oc get configmap -n openshift kube-root-ca.crt -o json \
        # | jq -r '.data["ca.crt"]' > ca.crt
        ca_crt = 'ca.crt'

    os.environ["REQUESTS_CA_BUNDLE"] = ca_crt
    with open(token, 'r') as file:
        token_content = file.read()

    k8s_client = client.ApiClient()
    dyn_client = DynamicClient(k8s_client)

    worker_nodes = get_worker_nodes()

    prometheus_url = get_prom_url(dyn_client)
    get_metric_for_nodes(prometheus_url, token_content, worker_nodes)

    worker_nodes_sorted = sort_nodes_by_metric(worker_nodes)
    set_expected_taints(worker_nodes_sorted)
    compute_apply_patches(worker_nodes_sorted)


if __name__ == '__main__':
    main()
