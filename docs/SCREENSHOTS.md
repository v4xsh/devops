# Screenshots and Evidence

**DeskFlow · Vansh Dobhal — Roll No. 10099**

Everything lives in [`screenshots/`](screenshots/). Every terminal capture exists twice:
the full raw output as `.txt` and a rendered terminal image as `.png` with the same name.
Browser screenshots were taken with headless Chromium (Playwright).

Captured on 16 Oct 2026 against: Docker Compose (local), a 3-node kind cluster
(stand-in for EKS), GitHub Actions run [#5](https://github.com/v4xsh/devops/actions/runs/38867226880) and GHCR.

## Mapped to the 15 Final Demo steps

### 1. Application

| File | Caption |
|---|---|
| `01-app-dashboard-desktop.png` | Dashboard at 1440 px: dark sidebar, KPI cards, ticket table with status filters and priority badges, pipeline card, activity feed |
| `02-app-create-ticket-modal.png` | Create-ticket modal filled in (urgent, assigned to an agent) |
| `03-app-ticket-created.png` | New ticket #11 at the top of the table, KPIs and activity feed updated, success toast |
| `04-app-status-filter.png` | Status filter "Open" applied |
| `05-app-dashboard-mobile.png` | Same dashboard at 390 px (phone): collapsed nav, KPI grid, table rows as cards |
| `05b-app-dashboard-mobile-full.png` | Full-length mobile page |
| `08-compose-up.png` / `.txt` | `docker compose up --build -d`: db → backend → frontend start in order once each is healthy |
| `09-compose-ps.png` / `.txt` | All three Compose services up and healthy, frontend on :3000, backend on :8000 |
| `13-frontend-proxy.png` / `.txt` | Frontend on :3000 serves the app and proxies `/api` to the backend |

### 2. API

| File | Caption |
|---|---|
| `06-swagger-docs.png` | Swagger UI at `/docs` with all ticket, agent and health endpoints |
| `10-curl-health-ready.png` / `.txt` | `/health` (liveness), `/ready` (DB check), `/` service info |
| `12-api-crud.png` / `.txt` | Create → read → update → stats → delete → 404 on a ticket with curl |
| `07-metrics-endpoint.png` | Raw Prometheus metrics at `/metrics` in the browser |
| `11-curl-metrics.png` / `.txt` | `curl /metrics` filtered to request counters and histograms |

### 3. Database

| File | Caption |
|---|---|
| `14-psql-tickets-table.png` / `.txt` | `psql` inside the db container: tables, the `tickets` rows, and Alembic version `0002` |

### 4. Git

| File | Caption |
|---|---|
| `19-git-log.png` / `.txt` | Commit history: small, descriptive commits, all authored by v4xsh |
| `19b-github-commit-history.png` | The same history on GitHub |

### 5. CI

| File | Caption |
|---|---|
| `16-pytest.png` / `.txt` | `pytest -v` on Python 3.12: 30 passed |
| `20-gh-run-list.png` / `.txt` | Recent workflow runs, all successful |
| `21-gh-run-view.png` / `.txt` | Run #5 in detail: test → build-scan-push green, deploy skipped cleanly (no cluster secret), no annotations |
| `22-github-actions-run.png` | Run #5 summary page with the three-job graph |
| `23-github-actions-build-job.png` | Build, scan & push job: every step green, including both Trivy gates and the GHCR push |

### 6. Docker

| File | Caption |
|---|---|
| `15-docker-images.png` / `.txt` | Backend (217 MB) and frontend (60 MB) images, tagged by commit SHA; backend runs as UID 10001, frontend as UID 101 |

### 7. Security

| File | Caption |
|---|---|
| `17-trivy-backend.png` / `.txt` | Backend: gate passes (0 fixable HIGH/CRITICAL); report lists unfixed Debian findings such as CVE-2026-76642 |
| `18-trivy-frontend.png` / `.txt` | Frontend (Alpine + Nginx): 0 HIGH/CRITICAL |
| `23-github-actions-build-job.png` | Trivy report, SARIF upload and gate steps in the pipeline |

### 8. Registry

| File | Caption |
|---|---|
| `24-ghcr-packages.png` | `deskflow-backend` and `deskflow-frontend` packages on GHCR, linked to v4xsh/devops |
| `25-ghcr-backend-package.png` | Backend package versions: one tag per commit SHA plus `latest`, public |

### 9. Terraform

| File | Caption |
|---|---|
| `26-terraform-validate.png` / `.txt` | `terraform fmt -check`, `terraform init -backend=false` (vpc + eks modules, AWS provider) and `terraform validate` → Success |

### 10. Kubernetes

| File | Caption |
|---|---|
| `30-kubectl-get-nodes.png` / `.txt` | 3-node kind cluster, all Ready |
| `31-kubectl-get-pods.png` / `.txt` | DeskFlow pods all Running (backend ×2, frontend ×3 after the Helm upgrade, postgres-0) |
| `32-kubectl-get-svc.png` / `.txt` | ClusterIP Services for backend and frontend, headless Service for Postgres |
| `36-kubectl-get-all.png` / `.txt` | Deployments, StatefulSet, bound PVC, ConfigMap, Secret, ServiceMonitor |
| `37-endpoints.png` / `.txt` | Endpoints behind each Service |

### 11. Helm

| File | Caption |
|---|---|
| `33-helm-list.png` / `.txt` | `helm list`: deskflow, kube-prometheus-stack, metrics-server releases |
| `70-helm-upgrade.png` / `.txt` | Upgrade to a new image SHA and 3 frontend replicas (revision 2) |
| `71-helm-bad-upgrade.png` / `.txt` | Upgrade with a non-existent tag fails; old pods keep serving (HTTP 200) |
| `72-helm-history-before-rollback.png` / `.txt` | History showing the failed revision 3 |
| `73-helm-rollback.png` / `.txt` | `helm rollback deskflow 2` succeeds; broken pods terminate |
| `74-helm-history.png` / `.txt` | Final history: install → upgrade → failed → "Rollback to 2" |

### 12. Ingress

| File | Caption |
|---|---|
| `34-kubectl-get-ingress.png` / `.txt` | Ingresses for deskflow.local, grafana and prometheus; curl through the Ingress |
| `38-app-via-ingress.png` | The app opened at http://deskflow.local through ingress-nginx |
| `38b-swagger-via-ingress.png` | Swagger at http://deskflow.local/docs (Ingress `/docs` → backend) |

### 13. HPA

| File | Caption |
|---|---|
| `35-kubectl-get-hpa.png` / `.txt` | HPA at rest: 2 replicas, CPU well under the 60 % target |
| `39-load-test.png` / `.txt` | Load test: 64 workers, ~300 req/s for 4 minutes, 72 k requests |
| `40-kubectl-get-hpa-watch.png` / `.txt` | `kubectl get hpa -w`: 2 → 4 → 6 replicas as CPU passes 600 % of request, back to idle after the load |
| `41-backend-pods-watch.png` / `.txt` | New backend pods created by the HPA going Pending → Running |
| `42-hpa-after-load.png` / `.txt` | `kubectl top pods` with 6 backend pods, and the HPA's SuccessfulRescale events |

### 14. Monitoring

| File | Caption |
|---|---|
| `43-prometheus-targets.png` | Prometheus targets: `serviceMonitor/deskflow/deskflow-backend` 6/6 UP |
| `44-prometheus-query.png` | PromQL graph of request rate per endpoint during the load test |
| `45-grafana-dashboard.png` | Grafana "DeskFlow — Service Overview": req/s, p95 latency, 5xx rate, HPA pods, per-endpoint rate, latency percentiles, status classes, CPU per pod vs request |

### 15. Failure simulation

| File | Caption |
|---|---|
| `50-lab1-apply.png` / `.txt` | Apply `broken-image.yaml` |
| `51-lab1-get-pods.png` / `.txt` | Pod stuck in `ImagePullBackOff` |
| `52-lab1-describe-pod.png` / `.txt` | `kubectl describe pod`: registry says the tag `v1.0.0-typo` is not found |
| `53-lab1-events.png` / `.txt` | Events sorted by time: Pulling → Failed → BackOff |
| `54-lab1-fix.png` / `.txt` | `kubectl set image` to a real SHA tag from GHCR; rollout succeeds |
| `55-lab1-fixed-pods.png` / `.txt` | New pod Running, broken pod terminating |
| `60-lab2-apply.png` / `.txt` | Apply `broken-service.yaml` |
| `61-lab2-get-svc.png` / `.txt` | The broken Service looks normal in `kubectl get svc` |
| `62-lab2-get-endpoints.png` / `.txt` | Its endpoints are `<none>`; selector is `component=api` |
| `63-lab2-pods-show-labels.png` / `.txt` | Pods are labelled `component=backend` — mismatch found |
| `64-lab2-test-traffic.png` / `.txt` | Traffic to the Service: connection refused |
| `65-lab2-fix.png` / `.txt` | Patch the selector |
| `66-lab2-fixed.png` / `.txt` | Endpoints populated, `{"status":"ok"}` through the Service |

## Still to capture manually

These need my AWS account, a signed-in GitHub session or a live audience:

- [ ] **`terraform plan` output** against a real AWS account (`terraform plan | tee docs/terraform-plan.txt`) — no AWS credentials on the build machine.
- [ ] **AWS Console**: VPC with its subnets/NAT gateway, and the EKS cluster `deskflow-eks` with its node group, in ap-south-1 (only after `terraform apply`).
- [ ] **`terraform destroy`** completion ("Destroy complete!").
- [ ] **Trivy log inside the pipeline**: open the *Build, scan & push images* job while signed in to GitHub and screenshot the expanded "Trivy gate" / "Trivy report" steps (raw logs are hidden from signed-out visitors).
- [ ] **Security → Code scanning** tab showing the uploaded Trivy findings (visible to repository admins).
- [ ] **Live demo** of a commit flowing through the pipeline (see [DEMO.md](DEMO.md)).
- [ ] Optional: the app running on a real EKS cluster through an AWS load balancer.

Exact commands for the AWS steps are in [DECISIONS.md → What I still need to run myself](DECISIONS.md#what-i-still-need-to-run-myself).
