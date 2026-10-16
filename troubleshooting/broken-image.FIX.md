# Lab 1 — ImagePullBackOff (broken image tag)

## Break it

```bash
kubectl apply -f troubleshooting/broken-image.yaml
```

## Investigate

**1. The Pod never becomes Ready**

```bash
kubectl get pods -n deskflow -l lab=broken-image
```
```text
NAME                              READY   STATUS             RESTARTS   AGE
deskflow-canary-f694757cf-6gxj9   0/1     ImagePullBackOff   0          45s
```

`ImagePullBackOff` means the kubelet tried to pull the image, failed, and is now waiting
longer and longer between retries. The container has never started, so there are no logs —
`kubectl logs` will not help here. Look at the Pod's events instead.

**2. Describe the Pod**

```bash
kubectl describe pod <pod-name> -n deskflow
```
```text
    Image:          ghcr.io/v4xsh/deskflow-frontend:v1.0.0-typo
    State:          Waiting
      Reason:       ImagePullBackOff
Events:
  Normal   Pulling  kubelet  Pulling image "ghcr.io/v4xsh/deskflow-frontend:v1.0.0-typo"
  Warning  Failed   kubelet  Failed to pull image "ghcr.io/v4xsh/deskflow-frontend:v1.0.0-typo":
           ... failed to resolve reference "ghcr.io/v4xsh/deskflow-frontend:v1.0.0-typo": not found
  Warning  Failed   kubelet  Error: ErrImagePull
  Warning  Failed   kubelet  Error: ImagePullBackOff
```

**3. Namespace events, newest last**

```bash
kubectl get events -n deskflow --sort-by=.lastTimestamp
```

## Diagnosis

The registry answered `not found`: the repository exists but the tag `v1.0.0-typo` was never
pushed. (Other messages point to other causes: `unauthorized` / `denied` = private image with no
`imagePullSecret`; `no such host` / `i/o timeout` = DNS or network problem on the node.)

Check which tags really exist — CI pushes every commit as `ghcr.io/v4xsh/deskflow-frontend:<git-sha>`
plus `latest`. See the package page on GitHub, or:

```bash
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:v4xsh/deskflow-frontend:pull" | jq -r .token)
curl -s -H "Authorization: Bearer $TOKEN" https://ghcr.io/v2/v4xsh/deskflow-frontend/tags/list
```

## Fix

Point the Deployment at a tag that exists (a commit SHA built by CI):

```bash
kubectl set image deployment/deskflow-canary \
  frontend=ghcr.io/v4xsh/deskflow-frontend:d7520cb8e0e8f8323c7c64e713e0e29256bd3287 -n deskflow
kubectl rollout status deployment/deskflow-canary -n deskflow
```
```text
deployment.apps/deskflow-canary image updated
deployment "deskflow-canary" successfully rolled out
```
```bash
kubectl get pods -n deskflow -l lab=broken-image
```
```text
NAME                               READY   STATUS        RESTARTS   AGE
deskflow-canary-57d557d9d7-slbsx   1/1     Running       0          4s
deskflow-canary-f694757cf-6gxj9    0/1     Terminating   0          57s
```

`kubectl set image` is the quick live fix. The permanent fix is to correct the tag in
`broken-image.yaml` (or in Helm values) and re-apply, so Git stays the source of truth.

## Clean up

```bash
kubectl delete -f troubleshooting/broken-image.yaml
```

**Lesson:** pin images to tags that CI actually produced (the commit SHA), never hand-typed versions.
