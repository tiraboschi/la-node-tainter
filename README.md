# la-node-tainter
LoadAware Node Tainter

## Motivation
This is a POC of a subset of what is actually proposed in [KEP-4205: PSI Based Node Conditions](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/4205-psi-metric).

PSI metric provides a quantifiable way to see resource pressure increases as they develop, with a new pressure metric for three major resources (memory, CPU, IO). These pressure metrics are useful for detecting resource shortages and provide nodes the opportunity to respond intelligently - by updating the node condition.

In short, PSI metrics are like barometers that provide fair warning of impending resource shortages on the node, and enable nodes to take more proactive, granular and nuanced steps when major resources (memory, CPU, IO) start becoming scarce.

The idea of this POC is to have a `CronJob` inspecting PSI metrics for the worker nodes
and then eventually set or remove taints on the nodes based on the value of PSI metrics.

## Deployment

1. [Reconfigure master and worker machine pools](manifests/mc-psi-*.yaml) to provide PSI metrics via the `node_exporter`.
```bash
  $ oc apply -f manifests/mc-psi-worker.yaml
  $ oc wait mcp worker --for condition=Updated=False --timeout=10s
  $ oc wait mcp worker --for condition=Updated=True  --timeout=15m
  $ oc apply -f manifests/mc-psi-master.yaml
  $ oc wait mcp master --for condition=Updated=False --timeout=10s
  $ oc wait mcp master --for condition=Updated=True  --timeout=15m
```

2. Deploy LoadAware Node Tainter
```bash
  $ oc apply -f manifests/la-node-tainter.yaml
```
