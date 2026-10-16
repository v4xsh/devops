#!/usr/bin/env bash
# Bring up the complete DeskFlow stack on a local kind cluster:
#   kind -> ingress-nginx -> metrics-server -> kube-prometheus-stack -> DeskFlow (Helm)
#
# Usage:  ./scripts/local-cluster.sh            # create everything
#         ./scripts/local-cluster.sh down       # delete the cluster
# Requires: docker, kind, kubectl, helm
set -euo pipefail

CLUSTER=deskflow
NAMESPACE=deskflow
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INGRESS_NGINX_VERSION=controller-v1.12.1
TAG="${IMAGE_TAG:-$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo dev)}"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

if [[ "${1:-}" == "down" ]]; then
  kind delete cluster --name "$CLUSTER"
  exit 0
fi

log "Creating kind cluster '$CLUSTER'"
if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --config "$ROOT/scripts/kind-config.yaml" --wait 120s
fi
kubectl config use-context "kind-$CLUSTER"

log "Installing ingress-nginx ($INGRESS_NGINX_VERSION)"
kubectl apply -f "https://raw.githubusercontent.com/kubernetes/ingress-nginx/$INGRESS_NGINX_VERSION/deploy/static/provider/kind/deploy.yaml"
kubectl wait -n ingress-nginx --for=condition=ready pod -l app.kubernetes.io/component=controller --timeout=180s

log "Installing metrics-server (needed by the HPA)"
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null 2>&1 || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
helm repo update >/dev/null
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system \
  -f "$ROOT/monitoring/metrics-server-values.yaml" --wait

log "Installing kube-prometheus-stack (Prometheus + Grafana)"
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f "$ROOT/monitoring/kube-prometheus-stack-values.yaml" --wait --timeout 10m
kubectl apply -k "$ROOT/monitoring/"

log "Building images (tag $TAG) and loading them into kind"
docker build -t "ghcr.io/v4xsh/deskflow-backend:$TAG" "$ROOT/backend"
docker build -t "ghcr.io/v4xsh/deskflow-frontend:$TAG" --build-arg "APP_VERSION=$TAG" "$ROOT/frontend"
kind load docker-image --name "$CLUSTER" "ghcr.io/v4xsh/deskflow-backend:$TAG" "ghcr.io/v4xsh/deskflow-frontend:$TAG"

log "Deploying DeskFlow with Helm"
kubectl apply -f "$ROOT/k8s/namespace.yaml"
helm upgrade --install deskflow "$ROOT/helm/deskflow" -n "$NAMESPACE" \
  -f "$ROOT/helm/deskflow/values-dev.yaml" --set image.tag="$TAG" --wait --timeout 5m

kubectl get pods,svc,ingress,hpa -n "$NAMESPACE"
cat <<MSG

Done. Add this line to /etc/hosts to use the hostnames in a browser:
  127.0.0.1 deskflow.local grafana.deskflow.local prometheus.deskflow.local

  App:        http://deskflow.local
  Swagger:    http://deskflow.local/docs
  Prometheus: http://prometheus.deskflow.local/targets
  Grafana:    http://grafana.deskflow.local   (admin / deskflow-admin)

Without /etc/hosts:  curl -H 'Host: deskflow.local' http://localhost/api/tickets/stats
MSG
