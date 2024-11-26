FROM quay.io/fedora/fedora:41

USER root

RUN dnf install -y \
    procps \
    python3 \
    python3-pip \
    python3-kubernetes \
    python3-prometheus_client &&\
    dnf clean all -y

RUN pip3 install openshift prometheus-api-client

USER 1001

COPY la_taint_nodes.py /
ENTRYPOINT ["/la_taint_nodes.py"]
