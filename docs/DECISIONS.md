# Design Decisions

A record of the choices made while building DeskFlow and why. Newest-relevant first within each section.

## Application

| Decision | Reason |
|---|---|
| Domain: helpdesk / support tickets ("DeskFlow") instead of TaskBoard | The course requires an original domain. Tickets + agents map naturally onto the same CRUD + stats architecture. |
| Status and priority stored as strings with CHECK constraints, not PostgreSQL ENUM types | Same validation guarantee, but adding a value later is a one-line migration instead of an `ALTER TYPE` dance. Pydantic `Literal` types validate at the API edge too. |
| `assignee_id` foreign key to `agents` with `ON DELETE SET NULL` | Deleting an agent should unassign tickets, not delete them. The API returns `assignee_name` as well so the UI needs no extra lookup. |
| Extra `ticket_events` table + `GET /api/activity` | Gives the dashboard a real activity feed instead of a fake one, and an audit trail of status changes. |
| `/ready` returns HTTP 503 (not 200 with an error body) when `SELECT 1` fails | Kubernetes readiness probes and load balancers only look at the status code. |
| OpenAPI schema served at `/api/openapi.json` (Swagger stays at `/docs`) | ingress-nginx's path validation rejects `.` in Ingress paths, so `/openapi.json` cannot have its own rule. Under `/api` it is covered by the existing backend route. |
| Seed data in its own Alembic migration (`0002`) | The demo starts with realistic data, and `alembic downgrade 0001` removes it cleanly. |
| PostgreSQL advisory lock around migrations (`alembic/env.py`) | Each backend pod runs `alembic upgrade head` on start. With 2+ replicas starting together they would race to create the same tables. Tested with three concurrent migrators against one database: exactly one seed, no errors. |
| Frontend calls only relative `/api/...` URLs | Nginx (Compose) or the Ingress (Kubernetes) does the routing, so one frontend build works everywhere. |
| Nginx config rendered from a template with `BACKEND_URL` | Same image in Compose (`http://backend:8000`) and Kubernetes (`http://deskflow-backend:8000`). |

## Dependencies and images

| Decision | Reason |
|---|---|
| Upgraded to current releases (FastAPI 0.143, Starlette 1.8, SQLAlchemy 2.1, …) | The first Trivy scan flagged fixable HIGH CVEs in older Starlette. |
| Test-only packages moved to `requirements-dev.txt` | pytest/httpx have no business in the production image. CI installs the dev file. |
| Backend image is multi-stage and deletes pip/setuptools/wheel from the runtime | pip vendors its own copies of urllib3, msgpack etc. that were the remaining fixable scanner findings, and the app never installs anything at runtime. |
| `nginxinc/nginx-unprivileged` for the frontend | Runs as UID 101 on port 8080 out of the box; no root needed. |
| Docker Compose does **not** publish PostgreSQL's port | Port 5432 was already used by a local PostgreSQL on my machine, and the database does not need to be reachable from the host. Use `docker compose exec db psql ...`. |

## CI/CD

| Decision | Reason |
|---|---|
| Trivy installed from the official release tarball with a pinned version **and SHA-256 checksum**, rather than a third-party action tag | A mutable action tag can be re-pointed; a checksum-verified binary cannot. Supply-chain hygiene for the security tool itself. |
| Two Trivy steps per image: a report (`exit-code: 0`, SARIF to the Security tab) and a gate (`--ignore-unfixed --exit-code 1`) | Base images regularly carry CVEs with no fix released yet. Blocking on those would block every release without making anything safer. Every finding is still reported, and anything that *can* be fixed fails the build. |
| SARIF upload steps use `continue-on-error: true` | The Security tab upload is reporting, not a gate; a GitHub API hiccup should not fail a release. |
| `TRIVY_DB_REPOSITORY` points at `mirror.gcr.io` / `public.ecr.aws` | Avoids the GHCR rate limits that commonly hit Trivy DB downloads on shared runners. |
| Images built once with `load: true`, scanned locally, then pushed | Exactly the bytes that were scanned are the bytes that get pushed. |
| Tags: full commit SHA **and** `latest` | SHA for traceability and deployment; `latest` only for convenience. |
| Deploy job gated by a `deploy_enabled` output computed from the `KUBECONFIG_B64` secret | Job-level `if:` cannot read secrets directly. With no secret configured the job shows as *skipped*, not failed. |
| `bandit -r app -ll` added to the test job | Covers the SAST layer that Trivy does not. |
| Actions pinned to their current majors (checkout v7, setup-python v7, setup-node v7, docker/* v4/v7, codeql-action v4, …) | Older majors run on the deprecated Node 20 Actions runtime and CodeQL Action v3 is deprecated in December 2026; the first runs showed these as warnings. |
| `runs-on: ubuntu-24.04` instead of `ubuntu-latest` | `ubuntu-latest` moves to Ubuntu 26 on 19 Oct 2026; pinning keeps builds reproducible until I choose to move. |
| Frontend builds with Node 20 (CI and the Dockerfile build stage) | Matches the course specification. Node is only used at build time and is not in the shipped image; moving to Node 22/24 is a one-line change. |
| `concurrency` with `cancel-in-progress` | A newer push supersedes an older run on the same branch. |

## Infrastructure (Terraform)

| Decision | Reason |
|---|---|
| `terraform-aws-modules/vpc` ~> 5.13 and `/eks` ~> 20.24 with AWS provider ~> 5.70 | Mature, widely used module versions with a stable interface. |
| Kubernetes 1.34, AL2023 node AMI | Within EKS standard support; Amazon Linux 2 node images are not available for current Kubernetes versions. |
| Single NAT gateway by default (`single_nat_gateway = true`) | One NAT is ~⅓ the cost of one per AZ; acceptable for a course project. Flip the variable for HA. |
| 2 AZs, private /20 subnets for nodes, public /24 subnets for load balancers | Minimum EKS needs; subnets are tagged for the AWS Load Balancer Controller. |
| S3 backend block present but commented out | A fresh clone works with local state; a team would enable remote state with locking. |
| **`terraform apply` was not run** | No AWS credentials are configured on the build machine, and EKS + NAT cost real money. `fmt`, `init -backend=false` and `validate` all pass. |

## Kubernetes

| Decision | Reason |
|---|---|
| kind (1 control plane + 2 workers) as the stand-in for EKS | Free, runs in Docker, and supports ingress-nginx via host port mapping. The chart is the same; only values differ. |
| Images side-loaded into kind with the same `ghcr.io/v4xsh/...:<sha>` names | Exactly the naming CI uses; `IfNotPresent` means kind never needs to pull. |
| No `replicas` field on the backend Deployment when the HPA is enabled | Otherwise every `helm upgrade` would reset the replica count the HPA chose. |
| Low CPU request (50m in dev) | Utilisation is a percentage of the request, so a small request makes the HPA demo reachable on a laptop. |
| Namespace enforces Pod Security Standard **restricted**; all pods run non-root with capabilities dropped | Runtime security layer. Required adding pod/container security contexts everywhere (including the troubleshooting manifests). |
| Backend `readOnlyRootFilesystem: true` with an `emptyDir` on `/tmp` | The app writes nothing to disk. Nginx needs to write its rendered config, so the frontend is not read-only. |
| `maxUnavailable: 0` on the backend rollout | A bad release (e.g. wrong image tag) never takes healthy pods away — demonstrated in the Helm rollback rehearsal. |
| Prometheus `serviceMonitorSelectorNilUsesHelmValues: false` **and** the ServiceMonitor carries `release: kube-prometheus-stack` | Either alone is enough; both make discovery robust if one is changed. |
| Control-plane scrape jobs (etcd, scheduler, controller-manager, kube-proxy) disabled | Not reachable on kind or EKS; they would only show as DOWN on the targets page. |
| Grafana dashboard provisioned from a ConfigMap via kustomize `configMapGenerator` | The JSON stays a normal file that can be edited/imported; `kubectl apply -k monitoring/` creates the labelled ConfigMap the sidecar loads. |
| ingress-nginx `controller-v1.12.1` | Current kind-provider manifest. (Upstream ingress-nginx has been retired; for a long-lived EKS setup the AWS Load Balancer Controller or a Gateway API implementation would be the replacement.) |

## Tooling on the build machine

- `hey` could not be downloaded (its release bucket returned 403), so the load generator is a
  dependency-free Python script (`scripts/load_test.py`, thread pool + keep-alive connections).
- `/etc/hosts` could not be edited without sudo; browser screenshots via the Ingress use
  Chromium's `--host-resolver-rules` to map `*.deskflow.local` to 127.0.0.1, and terminal checks use
  `curl -H "Host: deskflow.local"`.
- The `gh` CLI is installed but not logged in on this machine, and the unauthenticated GitHub API
  was rate-limited at times. CI status was read from the public Actions API and pages instead;
  `gh run list` / `gh run view` outputs in `docs/screenshots/20-*`, `21-*` were produced from the same
  public API.

---

## What I still need to run myself

These steps need my AWS account, a browser session logged in to GitHub, or sudo.

### 1. Terraform plan / apply / destroy on AWS (rubric M7)

```bash
aws configure                       # or export AWS_PROFILE=...
cd terraform
terraform init
terraform plan -out tfplan | tee ../docs/terraform-plan.txt
terraform apply tfplan              # ~15-20 minutes
$(terraform output -raw configure_kubectl)
kubectl get nodes
```

Screenshots to take: `terraform plan` output, AWS Console → VPC (ap-south-1) and
AWS Console → EKS → `deskflow-eks` with its node group.

Optional — deploy the app on EKS:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system
kubectl apply -f k8s/namespace.yaml
helm upgrade --install deskflow ./helm/deskflow -n deskflow --set image.tag=<latest-commit-sha> \
  --set postgres.storageClass=gp2
kubectl get ingress -n deskflow     # use the ELB hostname
```

(EKS 1.34 needs the EBS CSI driver add-on for the Postgres PVC; add `aws-ebs-csi-driver = {}` to
`cluster_addons` with an IRSA/Pod Identity role, or set `postgres.enabled=false` and use RDS.)

Then **always**:

```bash
helm uninstall deskflow -n deskflow; helm uninstall ingress-nginx -n ingress-nginx   # removes the ELB first
terraform destroy                   # screenshot the "Destroy complete!" line
```

### 2. Enable the CD deploy job (optional)

```bash
gh secret set KUBECONFIG_B64 --repo v4xsh/devops --body "$(base64 -w0 ~/.kube/config)"
```

The next push to `main` will run the `deploy` job instead of skipping it. Only do this for a
cluster reachable from GitHub's runners (EKS with a public endpoint, not kind).

### 3. `/etc/hosts` for opening the kind Ingress in a normal browser

```bash
echo "127.0.0.1 deskflow.local grafana.deskflow.local prometheus.deskflow.local" | sudo tee -a /etc/hosts
```

### 4. `gh` CLI evidence from my own account (optional)

```bash
gh auth login
gh run list --repo v4xsh/devops --limit 5
gh run view --repo v4xsh/devops <run-id>
```
