# DeskFlow — Helpdesk Ticketing on a Full DevOps Pipeline

**Vansh Dobhal — Roll No. 10099**
Session 21 · DevOps Final Capstone · GitHub: [v4xsh/devops](https://github.com/v4xsh/devops)

![CI/CD](https://github.com/v4xsh/devops/actions/workflows/ci-cd.yml/badge.svg)

---

## 1. Overview

DeskFlow is a small support-desk application. Customers raise **tickets**
(title, description, customer, priority, status) and support **agents** pick them up,
move them through `open → in_progress → resolved → closed`, and reassign them.
The dashboard shows live KPIs, a filterable ticket table and an activity feed.

The application is deliberately small. The point of the project is everything around it:
how a change goes from my laptop, through Git, automated tests, container builds, a security
scan and a registry, onto Kubernetes infrastructure described in code, with autoscaling,
monitoring and a rehearsed way to debug failures.

| Layer | What I used |
|---|---|
| Frontend | React 18 + Vite, hand-written responsive CSS, served by Nginx (non-root) |
| Backend | FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic migrations |
| Database | PostgreSQL 16 |
| Tests | pytest (30 tests, in-memory SQLite), bandit SAST |
| Containers | Multi-stage Dockerfiles, Docker Compose |
| CI/CD | GitHub Actions: test → build/scan/push → deploy |
| Security scanning | Trivy (images, dependencies, secrets, IaC), bandit |
| Registry | GitHub Container Registry (GHCR), images tagged with the commit SHA |
| Infrastructure as Code | Terraform: AWS VPC + EKS in `ap-south-1` |
| Orchestration | Kubernetes, Helm chart, ingress-nginx, HPA, metrics-server |
| Observability | Prometheus (kube-prometheus-stack), ServiceMonitor, Grafana dashboard |

## 2. Architecture

```mermaid
flowchart TD
    dev[Developer laptop] -->|git push| gh[GitHub repo]
    gh --> ci[GitHub Actions]
    subgraph pipeline [CI/CD pipeline]
      ci --> t[test: pytest + bandit + npm build]
      t --> b[build images]
      b --> s[Trivy scan]
      s --> p[push to GHCR :sha]
      p --> d[helm upgrade --install]
    end
    tf[Terraform] -->|creates| aws
    subgraph aws [AWS ap-south-1]
      vpc[VPC: 2 public + 2 private subnets, NAT gateway]
      vpc --> eks[EKS control plane + managed node group]
    end
    d --> eks
    subgraph k8s [Kubernetes namespace: deskflow]
      ing[Ingress deskflow.local] -->|/| fe[frontend Deployment x2<br/>Nginx + React]
      ing -->|/api, /docs| be[backend Deployment 2-6 pods<br/>FastAPI]
      fe -->|/api proxy| be
      be --> pg[(PostgreSQL StatefulSet + PVC)]
      hpa[HPA: CPU 60%] -.scales.-> be
    end
    prom[Prometheus] -->|ServiceMonitor scrapes /metrics| be
    graf[Grafana] --> prom
```

The same picture as plain text:

```text
Developer ──git push──▶ GitHub ──▶ GitHub Actions
                                     ├─ pytest + bandit + frontend build
                                     ├─ docker build (backend, frontend)
                                     ├─ Trivy scan  ──▶ Security tab (SARIF)
                                     └─ push ghcr.io/v4xsh/deskflow-*:<sha>
                                                  │
Terraform ──▶ AWS VPC + EKS ◀──── helm upgrade --install (image.tag=<sha>)
                                                  │
                        Ingress (deskflow.local)  ▼
                 /  ──▶ frontend (Nginx) ──/api──▶ backend (FastAPI) ──▶ PostgreSQL
              /api ───────────────────────────────▶      ▲  ▲
                                                HPA ─────┘  └──── Prometheus ──▶ Grafana
```

The browser only ever calls relative URLs such as `/api/tickets`. In Docker Compose the
frontend's Nginx proxies `/api` to the backend; in Kubernetes the Ingress routes `/api`
straight to the backend Service. The frontend never needs to know a backend hostname.

## 3. Repository layout

```text
.
├── frontend/              React + Vite app, Nginx runtime config, multi-stage Dockerfile
├── backend/
│   ├── app/               FastAPI app: models, schemas, routers, DB config
│   ├── alembic/           migrations: 0001 schema, 0002 seed data
│   ├── tests/             pytest suite (conftest.py uses in-memory SQLite)
│   ├── requirements.txt   pinned runtime deps (requirements-dev.txt adds pytest)
│   └── Dockerfile         python:3.12-slim, non-root, migrates then starts uvicorn
├── docker-compose.yml     postgres + backend + frontend with healthchecks
├── terraform/             VPC + EKS (terraform-aws-modules), ap-south-1
├── helm/deskflow/         Helm chart (Deployments, Services, StatefulSet, Ingress, HPA, ServiceMonitor)
├── k8s/                   namespace manifest
├── monitoring/            kube-prometheus-stack + metrics-server values, Grafana dashboard
├── troubleshooting/       two deliberately broken manifests + step-by-step fixes
├── scripts/               kind bootstrap, load test, screenshot helpers
├── .github/workflows/     ci-cd.yml
└── docs/                  DECISIONS.md, DEMO.md, SCREENSHOTS.md, screenshots/
```

## 4. Running locally

### Option A — Docker Compose (one command)

```bash
docker compose up --build -d
```

| URL | What |
|---|---|
| http://localhost:3000 | DeskFlow dashboard |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/health | liveness |
| http://localhost:8000/ready | readiness (checks the DB) |
| http://localhost:8000/metrics | Prometheus metrics |

The database is seeded with 4 agents and 10 tickets by the second Alembic migration.
Look at the table directly:

```bash
docker compose exec db psql -U deskflow -d deskflow -c 'SELECT id, title, status, priority FROM tickets;'
```

Start order is enforced with healthchecks: the backend waits for `pg_isready`, and the
frontend waits until the backend's `/ready` answers.

### Option B — Run the backend and frontend directly

```bash
# PostgreSQL (any instance works)
docker run -d --name deskflow-pg -p 5433:5432 \
  -e POSTGRES_USER=deskflow -e POSTGRES_PASSWORD=deskflow -e POSTGRES_DB=deskflow postgres:16-alpine

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://deskflow:deskflow@localhost:5433/deskflow'
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal) — Vite proxies /api to :8000
cd frontend
npm ci
npm run dev        # http://localhost:5173
```

## 5. API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | service info |
| GET | `/health` | liveness probe — process is up |
| GET | `/ready` | readiness probe — runs `SELECT 1`, returns **503** if the DB is unreachable |
| GET | `/metrics` | Prometheus metrics (request count, latency histograms, process stats) |
| GET | `/api/tickets` | list tickets; filters `status`, `priority`, `assignee_id`, `q` (search) |
| POST | `/api/tickets` | create a ticket |
| GET | `/api/tickets/{id}` | one ticket (404 if missing) |
| PUT | `/api/tickets/{id}` | partial update (status, priority, assignee, …) |
| DELETE | `/api/tickets/{id}` | delete (204) |
| GET | `/api/tickets/stats` | counts by status and priority, urgent open, unassigned, resolution rate |
| GET | `/api/agents` | list agents |
| POST | `/api/agents` | create an agent (409 on duplicate email) |
| GET | `/api/activity` | recent ticket events for the activity feed |

Swagger UI is at `/docs`; the OpenAPI schema is served at `/api/openapi.json` so that the
Ingress `/api` rule covers it.

## 6. Testing

```bash
cd backend
pytest -v
```

30 tests cover every route: health, readiness (including the 503 path, simulated with a
broken DB session), metrics, Swagger, full ticket CRUD, filters, stats, the activity feed,
agents, 404s and validation errors (bad status/priority values, too-short titles, missing
customer, unknown assignee, invalid e-mail, duplicate e-mail).

`tests/conftest.py` overrides FastAPI's `get_db` dependency with an **in-memory SQLite**
database and creates a fresh schema for every test, so tests never touch the real
PostgreSQL and do not depend on each other.

Why tests run first in the pipeline:

```text
bad code → pytest fails → pipeline stops → no image is built or pushed → nothing broken is deployed
```

## 7. Containers

**Backend** (`backend/Dockerfile`) — two stages. The build stage installs dependencies into
a virtualenv; the runtime stage copies only that virtualenv onto `python:3.12-slim`, applies
OS security updates, removes pip/setuptools (not needed at runtime and a source of scanner
findings), and runs as UID `10001`. On start it runs `alembic upgrade head` and then
`uvicorn` on port 8000. Several replicas can start at once safely: migrations take a
PostgreSQL advisory lock, so only one pod migrates at a time.

**Frontend** (`frontend/Dockerfile`) — multi-stage: `node:20-alpine` runs `npm ci && npm run build`,
then only the static `dist/` is copied into `nginxinc/nginx-unprivileged` (UID `101`, port 8080).
Node and all build tooling stay out of the final 60 MB image. `BACKEND_URL` is injected into
the Nginx config at container start, so the same image works in Compose and Kubernetes.

## 8. CI/CD — GitHub Actions

Workflow: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). It runs on every
push and pull request to `main`.

```text
test ──▶ build-scan-push ──▶ deploy
```

1. **test** — Python 3.12: install requirements, `pytest -q`, `bandit -r app -ll` (SAST).
   Node 20: `npm ci && npm run build`. If anything fails, the pipeline stops here.
2. **build-scan-push** — only on pushes to `main`. Logs in to GHCR with the built-in
   `GITHUB_TOKEN` (`permissions: packages: write`), builds both images, scans them with
   Trivy, and pushes:
   - `ghcr.io/v4xsh/deskflow-backend:<commit-sha>` and `:latest`
   - `ghcr.io/v4xsh/deskflow-frontend:<commit-sha>` and `:latest`
3. **deploy** — installs Helm and kubectl, writes the kubeconfig from the `KUBECONFIG_B64`
   secret and runs `helm upgrade --install ... --set image.tag=<commit-sha>`. When that secret
   is not configured the job is **skipped** (not failed), so the pipeline stays green without
   a cluster.

**Traceability.** Every image is tagged with the full Git commit SHA:

```text
commit d7520cb… → ghcr.io/v4xsh/deskflow-backend:d7520cb…  → Helm revision N
```

Given any running pod, `kubectl get pod -o jsonpath='{..image}'` gives the SHA, and
`git show <sha>` shows exactly which code is running. `latest` is pushed only for
convenience; deployments always use the SHA. The images also carry the
`org.opencontainers.image.revision` label.

To enable the deploy job against a real cluster:

```bash
# EKS example
aws eks update-kubeconfig --region ap-south-1 --name deskflow-eks
gh secret set KUBECONFIG_B64 --body "$(base64 -w0 ~/.kube/config)"
```

## 9. Security scanning layers

A scanner is one control, not a guarantee. Different tools catch different classes of problem:

| Layer | Question it answers | In this project |
|---|---|---|
| **SAST** | Is my own source code written unsafely? | `bandit -r app -ll` in the test job (fails the build on medium+ issues) |
| **Dependency scanning** | Do my libraries have known CVEs? | `trivy fs` scans `requirements.txt` and `package-lock.json`; Trivy image scan also checks installed Python packages |
| **Secret scanning** | Did someone commit a key or password? | `trivy fs --scanners secret` in CI; GitHub secret scanning (on by default for public repos); `.gitignore` blocks `.env`, `*.tfvars`, kubeconfigs |
| **Container scanning** | Does the image's OS or runtime have known CVEs? | `trivy image` on both images, HIGH/CRITICAL |
| **Runtime security** | Is the running workload locked down? | non-root containers, dropped capabilities, no privilege escalation, read-only root FS for the backend, seccomp `RuntimeDefault`, namespace enforces the Pod Security Standard **restricted** |

**How the Trivy steps are configured.** There are two kinds of step per image:

- a **report** step with `exit-code: 0` that sends every HIGH/CRITICAL finding (fixed or not)
  as SARIF to the repository's *Security → Code scanning* tab;
- a **gate** step with `--ignore-unfixed --exit-code 1` that fails the pipeline if any
  HIGH/CRITICAL vulnerability **with an available fix** is present.

The reason for the split: base images regularly contain CVEs for which the distribution has
not released a fix yet. Failing on those would block every release without making anything
safer — there is nothing to upgrade to. Anything that *can* be fixed still blocks the build.

**What the scan found.** The first scan of the backend flagged fixable CVEs in Starlette
(e.g. CVE-2025-62727, a denial-of-service via `Range` header merging) and in the copies of
`urllib3`/`setuptools` vendored inside pip. I fixed them by upgrading FastAPI/Starlette and
removing pip from the runtime image. The frontend image (Alpine + Nginx) scans clean.
The backend now has **0 fixable** HIGH/CRITICAL issues; the remaining 44 HIGH findings are in
Debian 13 base packages marked *affected* with no fixed version yet, for example
**CVE-2026-76642** in `util-linux` (a mount helper that keeps running privileged hooks after
failing). It matters on a host where unprivileged users can call `mount`; in this container
the app runs as an unprivileged user with all capabilities dropped and never calls `mount`,
so the practical risk is very low. It stays visible in the Security tab and will clear once
Debian ships the fix and the image is rebuilt.

## 10. Terraform — AWS infrastructure

Kubernetes manages workloads; it cannot create the network or the cluster it runs on.
Terraform describes that infrastructure as code (`terraform/`):

```text
AWS ap-south-1
 ├── VPC 10.20.0.0/16
 │    ├── 2 public subnets  (/24) — load balancers, NAT gateway   tag kubernetes.io/role/elb
 │    ├── 2 private subnets (/20) — worker nodes and pods          tag kubernetes.io/role/internal-elb
 │    └── NAT gateway (single by default; one per AZ with single_nat_gateway=false)
 └── EKS cluster deskflow-eks (Kubernetes 1.34)
      ├── add-ons: coredns, kube-proxy, vpc-cni, eks-pod-identity-agent
      └── managed node group: t3.medium × 2 (min 2, max 4), AL2023
```

Built with the community modules `terraform-aws-modules/vpc/aws` (~> 5.13) and
`terraform-aws-modules/eks/aws` (~> 20.24). Files: `versions.tf` (providers, and an S3
remote-state backend left commented out), `variables.tf`, `main.tf`, `outputs.tf`,
`terraform.tfvars.example`.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # optional — defaults work
terraform init
terraform plan
terraform apply                                  # ~15 min; costs money (EKS + NAT)
$(terraform output -raw configure_kubectl)       # aws eks update-kubeconfig --region ap-south-1 --name deskflow-eks
...
terraform destroy                                # always, after the demo
```

`terraform fmt -check`, `terraform init -backend=false` and `terraform validate` pass
(see `docs/screenshots/26-terraform-validate.png`). No credentials are stored in the repo;
authentication comes from the AWS CLI profile or environment.

## 11. Kubernetes, Helm, Ingress and HPA

The Helm chart in `helm/deskflow/` packages the whole application:

| Template | Purpose |
|---|---|
| `backend-deployment.yaml` | FastAPI pods; init container waits for Postgres; liveness `/health`, readiness `/ready`; requests/limits; `maxUnavailable: 0` rolling updates |
| `frontend-deployment.yaml` | Nginx pods (2 replicas); probes on `/healthz` |
| `backend-service.yaml`, `frontend-service.yaml` | stable ClusterIP Services in front of the pods |
| `postgres-statefulset.yaml` | PostgreSQL StatefulSet with a PersistentVolumeClaim + headless Service |
| `postgres-secret.yaml` | DB password (or use `postgres.existingSecret`) |
| `configmap.yaml` | non-secret config: environment, CORS, DB host/user, backend URL |
| `ingress.yaml` | `deskflow.local`: `/` → frontend, `/api` and `/docs` → backend |
| `hpa.yaml` | backend autoscaling 2–6 replicas at 60 % average CPU |
| `servicemonitor.yaml` | tells the Prometheus Operator to scrape backend `/metrics` (toggle `serviceMonitor.enabled`) |
| `NOTES.txt`, `_helpers.tpl` | post-install instructions; shared names, labels, image refs |

`values.yaml` holds production-like defaults; `values-dev.yaml` is for a local cluster.

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install deskflow ./helm/deskflow -n deskflow -f helm/deskflow/values-dev.yaml --set image.tag=<sha>
helm list -n deskflow
helm history deskflow -n deskflow
helm rollback deskflow <revision> -n deskflow
```

**Local cluster.** I used [kind](https://kind.sigs.k8s.io/) (3 nodes) as a stand-in for EKS.
`scripts/local-cluster.sh` creates it and installs ingress-nginx, metrics-server,
kube-prometheus-stack, the Grafana dashboard and the chart in one go:

```bash
./scripts/local-cluster.sh
echo "127.0.0.1 deskflow.local grafana.deskflow.local prometheus.deskflow.local" | sudo tee -a /etc/hosts
```

**Ingress.** An Ingress object is only configuration — ingress-nginx is the controller that
actually implements it. Verified with `curl -H "Host: deskflow.local" http://localhost/api/tickets/stats`
and in the browser.

**HPA.** The HPA needs two things: CPU *requests* on the pods (utilisation is measured as a
percentage of the request) and a metrics source (metrics-server). Under the load test
(`scripts/load_test.py`, ~300 req/s for 4 minutes) the backend scaled **2 → 4 → 6** pods,
then back to 2 after the load stopped:

```text
NAME               REFERENCE                     TARGETS         MINPODS   MAXPODS   REPLICAS
deskflow-backend   Deployment/deskflow-backend   cpu: 4%/60%     2         6         2
deskflow-backend   Deployment/deskflow-backend   cpu: 602%/60%   2         6         4
deskflow-backend   Deployment/deskflow-backend   cpu: 594%/60%   2         6         6
```

At 6 pods the bottleneck moved to PostgreSQL (at its 500m CPU limit) — a good illustration of
why the database tier is usually moved to a managed service such as Amazon RDS in production.

**PostgreSQL in Kubernetes vs RDS.** Running Postgres as a StatefulSet is fine for a demo:
it is self-contained and free. For production I would use RDS: managed backups, point-in-time
recovery, Multi-AZ failover and patching, at the cost of running outside the cluster. The chart
supports this by setting `postgres.enabled=false` and pointing the config at an external host.

## 12. Monitoring

- The backend exposes `/metrics` via `prometheus-fastapi-instrumentator`
  (`http_requests_total`, `http_request_duration_seconds`, latency histograms, process CPU/memory).
- `kube-prometheus-stack` installs Prometheus, Grafana, kube-state-metrics and node-exporter
  (`monitoring/kube-prometheus-stack-values.yaml`).
- The chart's **ServiceMonitor** makes Prometheus discover every backend pod automatically —
  all 6 pods showed as **UP** on the targets page during the load test.
- The **Grafana dashboard** (`monitoring/deskflow-dashboard.json`) is provisioned from a
  ConfigMap labelled `grafana_dashboard: "1"` (`kubectl apply -k monitoring/`), which Grafana's
  sidecar loads automatically. Panels: requests/sec, p50/p95/p99 latency, 5xx error rate,
  responses by status class, CPU per backend pod against the request, HPA current/desired/max
  replicas, and memory per pod.

## 13. Troubleshooting lab

| Lab | Break it | Symptom | Root cause | Guide |
|---|---|---|---|---|
| Broken image | `kubectl apply -f troubleshooting/broken-image.yaml` | Pod stuck in `ImagePullBackOff` | tag `v1.0.0-typo` does not exist in GHCR | [broken-image.FIX.md](troubleshooting/broken-image.FIX.md) |
| Broken Service | `kubectl apply -f troubleshooting/broken-service.yaml` | Service exists but `Connection refused`; endpoints `<none>` | selector `component=api` matches no pod (pods are `component=backend`) | [broken-service.FIX.md](troubleshooting/broken-service.FIX.md) |

Investigation path: `kubectl get pods` → `kubectl describe pod` → `kubectl get events --sort-by=.lastTimestamp`
for the image; `kubectl get svc` → `kubectl get endpoints` → `kubectl get pods --show-labels` for the
Service. Both were reproduced and fixed on the kind cluster; full output is in `docs/screenshots/5*` and `6*`.

I also rehearsed a failed release: `helm upgrade` with a non-existent image tag timed out,
the old pods kept serving traffic (HTTP 200) thanks to `maxUnavailable: 0`, and
`helm rollback deskflow 2` restored the previous revision.

## 14. Screenshot gallery

Full list with captions: [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md). Presentation script: [docs/DEMO.md](docs/DEMO.md).

| | |
|---|---|
| ![Dashboard](docs/screenshots/01-app-dashboard-desktop.png) Dashboard (desktop) | ![Mobile](docs/screenshots/05-app-dashboard-mobile.png) Dashboard (mobile) |
| ![Create ticket](docs/screenshots/02-app-create-ticket-modal.png) Create-ticket modal | ![Swagger](docs/screenshots/06-swagger-docs.png) Swagger UI |
| ![pytest](docs/screenshots/16-pytest.png) pytest — 30 passed | ![Trivy](docs/screenshots/17-trivy-backend.png) Trivy scan |
| ![Actions](docs/screenshots/22-github-actions-run.png) GitHub Actions run | ![GHCR](docs/screenshots/24-ghcr-packages.png) Images in GHCR |
| ![Pods](docs/screenshots/31-kubectl-get-pods.png) `kubectl get pods` | ![Ingress](docs/screenshots/38-app-via-ingress.png) App via Ingress |
| ![HPA](docs/screenshots/40-kubectl-get-hpa-watch.png) HPA scaling 2 → 6 | ![Prometheus](docs/screenshots/43-prometheus-targets.png) Prometheus targets UP |
| ![Grafana](docs/screenshots/45-grafana-dashboard.png) Grafana dashboard | ![Troubleshooting](docs/screenshots/52-lab1-describe-pod.png) ImagePullBackOff investigation |

## 15. Cleanup

```bash
docker compose down -v                  # stop Compose and delete the database volume
./scripts/local-cluster.sh down         # or: kind delete cluster --name deskflow
cd terraform && terraform destroy       # if the AWS stack was created
```

## 16. Further notes

Design decisions and trade-offs are recorded in [docs/DECISIONS.md](docs/DECISIONS.md).
