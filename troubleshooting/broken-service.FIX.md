# Lab 2 — Service with no endpoints (selector mismatch)

## Break it

```bash
kubectl apply -f troubleshooting/broken-service.yaml
```

## Investigate

**1. The Service looks healthy at first glance**

```bash
kubectl get svc -n deskflow
```
```text
NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
deskflow-api        ClusterIP   10.96.245.77    <none>        8000/TCP   3s
deskflow-backend    ClusterIP   10.96.163.82    <none>        8000/TCP   12m
...
```

It has a ClusterIP and a port. Nothing here says it is broken.

**2. But traffic fails**

```bash
kubectl exec -n deskflow deploy/deskflow-frontend -- wget -qO- -T 5 http://deskflow-api:8000/health
```
```text
wget: can't connect to remote host (10.96.245.77): Connection refused
command terminated with exit code 1
```

**3. Check the endpoints — the list of Pod IPs behind the Service**

```bash
kubectl get endpoints deskflow-api deskflow-backend -n deskflow
kubectl describe svc deskflow-api -n deskflow | grep -E 'Selector|Endpoints'
```
```text
NAME               ENDPOINTS                          AGE
deskflow-api       <none>                             3s
deskflow-backend   10.244.1.15:8000,10.244.2.9:8000   12m

Selector:   app.kubernetes.io/component=api,app.kubernetes.io/name=deskflow
Endpoints:
```

`<none>` means no Ready Pod matches the Service selector.

**4. Compare the selector with the real Pod labels**

```bash
kubectl get pods -n deskflow --show-labels
```
```text
deskflow-backend-...   app.kubernetes.io/component=backend,app.kubernetes.io/instance=deskflow,app.kubernetes.io/name=deskflow
deskflow-frontend-...  app.kubernetes.io/component=frontend,...
```

## Diagnosis

The Service selects `component=api`, but the backend Pods are labelled `component=backend`.
A Service finds its Pods **only** through labels: no matching labels → no endpoints → no traffic.
(If the labels matched but endpoints were still empty, the next suspect would be failing
readiness probes — only Ready Pods are added to endpoints.)

## Fix

```bash
kubectl patch svc deskflow-api -n deskflow --type merge \
  -p '{"spec":{"selector":{"app.kubernetes.io/name":"deskflow","app.kubernetes.io/component":"backend"}}}'
```
```text
service/deskflow-api patched
```

Verify:

```bash
kubectl get endpoints deskflow-api -n deskflow
kubectl exec -n deskflow deploy/deskflow-frontend -- wget -qO- -T 5 http://deskflow-api:8000/health
```
```text
NAME           ENDPOINTS                          AGE
deskflow-api   10.244.1.15:8000,10.244.2.9:8000   13s

{"status":"ok"}
```

As with Lab 1, the lasting fix is to correct the selector in the YAML and re-apply it.

## Clean up

```bash
kubectl delete -f troubleshooting/broken-service.yaml
```

**Lesson:** when a Service "does nothing", run `kubectl get endpoints` first.
