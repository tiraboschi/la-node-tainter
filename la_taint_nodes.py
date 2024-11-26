#!/usr/bin/python3
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
from openshift.dynamic import DynamicClient

import os
import requests


TAINT_KEY = "la-taint-psi-cpu"
PSI_CPU_QUERY = 'rate(node_pressure_cpu_waiting_seconds_total[1m])'


class BearerAuth(requests.auth.AuthBase):

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


def func(x):
    return x + 1


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

    k8s_client = client.ApiClient()
    dyn_client = DynamicClient(k8s_client)

    worker_nodes = {}
    v1 = client.CoreV1Api()
    ret = v1.list_node(label_selector='node-role.kubernetes.io/worker')
    for i in ret.items:
        worker_nodes[i.metadata.name] = {
            "existing_taint": None,
            "cpu_pressure": 0.0
        }
        if i.spec.taints is not None:
            for t in i.spec.taints:
                if t.key == TAINT_KEY:
                    worker_nodes[i.metadata.name]["existing_taint"] = t

    os.environ["REQUESTS_CA_BUNDLE"] = ca_crt

    v1_routes = dyn_client.resources.get(
        api_version='route.openshift.io/v1',
        kind='Route'
    )
    prometheus_route = v1_routes.get(
        name="prometheus-k8s",
        namespace="openshift-monitoring"
    )

    prometheus_url = f"https://{prometheus_route.status.ingress[0].host}"
    with open(token, 'r') as file:
        token_content = file.read()

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
    print(f"worker nodes: {worker_nodes}")


if __name__ == '__main__':
    main()
