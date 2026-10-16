# Final Presentation — Demo Script

**DeskFlow · Vansh Dobhal — Roll No. 10099**

Order: Application → Git commit → CI pipeline → Docker image → Security scan → Registry →
Terraform → Kubernetes → Helm → Ingress → Autoscaling → Monitoring → Troubleshooting.
Allow ~20 minutes. Commands assume the repo root.

> **Scope:** the AWS VPC + EKS infrastructure in ap-south-1 is defined as code. To avoid cloud
> cost, the Kubernetes deployment is demonstrated on a local kind cluster using the same Helm
> chart. The EKS deploy path is wired in CI behind the `KUBECONFIG_B64` secret.

## Before the session (15 min earlier)

```bash
docker compose up --build -d                 # app on :3000 / :8000
./scripts/local-cluster.sh                   # kind + ingress + metrics-server + Prometheus/Grafana + DeskFlow (~6 min)
grep deskflow.local /etc/hosts || echo "127.0.0.1 deskflow.local grafana.deskflow.local prometheus.deskflow.local" | sudo tee -a /etc/hosts
```

Open browser tabs: http://localhost:3000 · http://localhost:8000/docs ·
https://github.com/v4xsh/devops/actions · https://github.com/v4xsh?tab=packages ·
http://deskflow.local · http://prometheus.deskflow.local/targets ·
http://grafana.deskflow.local/d/deskflow-overview (admin / deskflow-admin).
Have three terminals ready.

---

## 1. Application (2 min)

**Show:** http://localhost:3000

**Say:** "DeskFlow is a support-desk app: customers raise tickets, agents work them. React
frontend, FastAPI backend, PostgreSQL."

- Point at the dark sidebar, KPI cards, status filter chips, priority badges, activity feed,
  and the delivery-pipeline card (it shows whether the API is ready and which build is running).
- Click **New ticket** → fill in title/customer, priority *Urgent*, assign an agent → **Create**.
  Point at the new row, the updated KPIs and the new activity entry.
- Change a ticket's status from the dropdown in the table.
- Narrow the browser window → sidebar collapses, table turns into cards (responsive).

**API:** http://localhost:8000/docs — run `POST /api/tickets`, `GET /api/tickets/{id}`,
`PUT`, `DELETE`. Mention `/health` vs `/ready`:

```bash
curl -s localhost:8000/health; echo
curl -s localhost:8000/ready; echo
curl -s localhost:8000/metrics | grep http_requests_total | head -5
```

"`/health` = is the process alive. `/ready` = can it serve traffic now — it runs `SELECT 1`
against Postgres and returns 503 if that fails."

**Database:**

```bash
docker compose exec db psql -U deskflow -d deskflow -c '\dt' \
  -c 'SELECT id, title, status, priority, customer FROM tickets ORDER BY id DESC LIMIT 5;'
```

"The schema comes from Alembic migrations — `0001` creates the tables, `0002` seeds demo data."

## 2. Git commit (1 min)

Make a small visible change, e.g. the subtitle under the logo:

```bash
sed -i 's/Support workspace/Support workspace · live demo/' frontend/src/components/Sidebar.jsx
git add frontend/src/components/Sidebar.jsx
git commit -m "update sidebar subtitle for demo"
git push origin main
git log --oneline -5
```

**Say:** "A commit is an immutable checkpoint. The SHA I just created is what will end up as
the image tag in the registry."

## 3. CI pipeline (2 min, runs ~3 min in the background)

**Show:** https://github.com/v4xsh/devops/actions → the run for the new commit.

**Say:** "Three jobs. **test** runs pytest, bandit and the frontend build — if any test fails,
the pipeline stops and no image is produced. **build-scan-push** builds both images, scans
them, pushes them. **deploy** runs Helm against a cluster — it's skipped here because no
cluster secret is configured, and it's designed to skip cleanly rather than fail."

From the terminal:

```bash
gh run list -R v4xsh/devops -L 5
gh run watch -R v4xsh/devops          # live view of the run for the new commit
```

Optional, to prove the gate: show `backend/tests/` and run locally

```bash
cd backend && pytest -q && cd ..
```

## 4. Docker image (1 min)

```bash
docker images | grep deskflow
docker image inspect deskflow-backend:local --format 'user={{.Config.User}}'
cat frontend/Dockerfile
```

**Say:** "The frontend is multi-stage: Node builds the static files, then only `dist/` goes
into an unprivileged Nginx image — 60 MB, no Node inside. Both images run as non-root users."

## 5. Security scan (1.5 min)

**Show:** the `build-scan-push` job log → *Trivy report* and *Trivy gate* steps, then the repo's
**Security → Code scanning** tab.

```bash
gh run view <run-id> -R v4xsh/devops --log | grep -A12 'Trivy gate (frontend'
gh api repos/v4xsh/devops/code-scanning/alerts --paginate \
  -q '.[] | "\(.rule.security_severity_level) \(.state) \(.most_recent_instance.category)"' | sort | uniq -c
trivy image --severity HIGH,CRITICAL --ignore-unfixed deskflow-backend:local
trivy image --severity HIGH,CRITICAL deskflow-frontend:local
```

Expected: both gates pass; code scanning shows 44 *high* / *open* alerts, all `trivy-backend`.

**Say:** "Two steps per image. The report step uploads every HIGH/CRITICAL finding to the
Security tab. The gate fails the pipeline if any of those has a fix available. The first scan
found fixable Starlette CVEs — I upgraded FastAPI and removed pip from the runtime image, and
the gate went green. The remaining backend findings are in Debian packages with no fix yet,
e.g. CVE-2026-76642 in util-linux's mount helper — not reachable here because the app runs as
an unprivileged user with all capabilities dropped."

"Scanning is one layer: bandit is SAST, Trivy fs covers dependencies and secrets, Trivy image
covers containers, and Pod Security 'restricted' covers runtime."

## 6. Registry (1 min)

**Show:** https://github.com/v4xsh?tab=packages → `deskflow-backend` → versions.

```bash
gh api /users/v4xsh/packages/container/deskflow-backend/versions \
  -q '.[] | [(.metadata.container.tags | join(",")), .created_at] | @tsv' | head -5
```

**Say:** "Every image is tagged with the full commit SHA plus `latest`. Deployments always use
the SHA, so from any running pod I can trace back to the exact commit."

```bash
kubectl get pods -n deskflow -o jsonpath='{range .items[*]}{.spec.containers[0].image}{"\n"}{end}' | sort -u
```

## 7. Terraform — Final Demo step 9 (3 min)

**Say first:** "The AWS infrastructure is defined as code. To avoid cloud cost I demonstrate the
Kubernetes part on a local kind cluster with the same Helm chart; the EKS deploy path is wired
into CI behind the `KUBECONFIG_B64` secret."

```bash
cd terraform
ls                          # versions.tf variables.tf main.tf outputs.tf terraform.tfvars.example
terraform fmt -check && terraform validate
```

Walk through the files in this order:

1. **`versions.tf`** — Terraform ≥ 1.5 and the AWS provider ~> 5.70. Point at the S3 remote-state
   block: "commented out so a fresh clone works; a team would enable it for shared, locked state."
2. **`variables.tf`** — region `ap-south-1`, cluster name `deskflow-eks`, Kubernetes 1.34,
   VPC CIDR `10.20.0.0/16`, node instance type `t3.medium`, node group min 2 / desired 2 / max 4,
   `single_nat_gateway`. "Everything environment-specific is a variable;
   `terraform.tfvars.example` shows how to override it without committing secrets."
3. **`main.tf` → provider** — `default_tags` put Project / Environment / Owner on every resource.
4. **`main.tf` → `module "vpc"`** (terraform-aws-modules/vpc):
   - **VPC** `10.20.0.0/16` across 2 availability zones.
   - **Public subnets** (two /24): internet-facing load balancers and the NAT gateway; tagged
     `kubernetes.io/role/elb` so AWS load balancers find them.
   - **Private subnets** (two /20): worker nodes and pods, not directly reachable from the
     internet; tagged `kubernetes.io/role/internal-elb`.
   - **NAT gateway**: lets private nodes reach out (pull images from GHCR, call AWS APIs) without
     being exposed. One shared NAT by default to save cost; one per AZ for high availability.
5. **`main.tf` → `module "eks"`** (terraform-aws-modules/eks):
   - **EKS cluster** `deskflow-eks`: AWS runs the control plane; nodes live in the private subnets.
   - Add-ons: CoreDNS, kube-proxy, VPC CNI (pods get VPC IPs), Pod Identity agent.
   - **Managed node group**: `t3.medium`, AL2023, min 2 / max 4 — AWS handles node patching and
     replacement.
6. **`outputs.tf`** — VPC and subnet IDs, NAT IPs, cluster name/endpoint/version, and
   `configure_kubectl`, which prints the exact
   `aws eks update-kubeconfig --region ap-south-1 --name deskflow-eks` command.

**Say:** "Kubernetes runs workloads but can't create its own network or cluster — Terraform does.
`terraform plan` shows the diff, `apply` creates it, `destroy` removes everything, so the
infrastructure is reviewable and repeatable instead of clicked together in the console."

```bash
cd ..
```

## 8. Kubernetes (1.5 min)

```bash
kubectl get nodes
kubectl get pods -n deskflow -o wide
kubectl get svc -n deskflow
kubectl get pvc -n deskflow
```

**Say:** "Deployments for the frontend and backend, a StatefulSet with a PersistentVolumeClaim
for Postgres. Services give pods a stable name — the frontend talks to `deskflow-backend`, not
to pod IPs."

Delete a pod and watch it come back:

```bash
kubectl delete pod -n deskflow -l app.kubernetes.io/component=frontend --wait=false | head -1
kubectl get pods -n deskflow -w      # Ctrl-C once the replacement is Running
```

## 9. Helm (1.5 min)

```bash
helm list -n deskflow
helm history deskflow -n deskflow
ls helm/deskflow/templates
```

**Say:** "The chart packages everything; `values-dev.yaml` vs `values.yaml` is the only
difference between my laptop and EKS. Upgrades are revisions, and I can roll back."

Live rollback (optional):

```bash
helm upgrade deskflow ./helm/deskflow -n deskflow -f helm/deskflow/values-dev.yaml \
  --reuse-values --set image.tag=does-not-exist --wait --timeout 60s   # fails
kubectl get pods -n deskflow          # old pods still Running (maxUnavailable: 0)
helm history deskflow -n deskflow
helm rollback deskflow <last-good-revision> -n deskflow
```

## 10. Ingress (1 min)

**Show:** http://deskflow.local and http://deskflow.local/docs

```bash
kubectl get ingress -n deskflow
curl -s -H "Host: deskflow.local" http://localhost/api/tickets/stats; echo
```

**Say:** "One hostname: `/` goes to the frontend, `/api` and `/docs` to the backend. The
Ingress object is just rules — ingress-nginx is the controller that actually does the routing."

## 11. Autoscaling (2 min)

Terminal 1:

```bash
kubectl get hpa -n deskflow -w
```

Terminal 2:

```bash
python3 scripts/load_test.py --url http://localhost --host deskflow.local --duration 180 --workers 64
```

**Say:** "The HPA targets 60 % of the CPU request, between 2 and 6 pods. It needs CPU requests
on the pods and metrics-server to read usage." Watch REPLICAS go 2 → 4 → 6. "After the load
stops it scales back down after the stabilisation window." (Previous run: `docs/screenshots/40-kubectl-get-hpa-watch.png`.)

## 12. Monitoring (2 min) — while the load test runs

**Show:** http://prometheus.deskflow.local/targets?search=deskflow — every backend pod **UP**.

**Say:** "The ServiceMonitor in my chart tells the Prometheus Operator to scrape `/metrics` on
every backend pod — new pods from the HPA are picked up automatically."

**Show:** Grafana → *DeskFlow — Service Overview*: requests/sec, p95 latency, 5xx error rate,
CPU per pod vs the request line, HPA replicas climbing.

## 13. Troubleshooting (3 min)

**Broken image:**

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n deskflow -l lab=broken-image          # ImagePullBackOff
kubectl describe pod -n deskflow -l lab=broken-image | tail -12
kubectl get events -n deskflow --sort-by=.lastTimestamp | tail -5
```

"`not found` from the registry → the tag doesn't exist. Fix: use a tag CI really pushed."

```bash
kubectl set image deployment/deskflow-canary -n deskflow \
  frontend=ghcr.io/v4xsh/deskflow-frontend:$(git rev-parse HEAD)
kubectl get pods -n deskflow -l lab=broken-image          # Running
kubectl delete -f troubleshooting/broken-image.yaml
```

(If the newest commit's images are not pushed yet, use any SHA from the GHCR package page.)

**Broken Service:**

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get svc -n deskflow                                # looks fine
kubectl exec -n deskflow deploy/deskflow-frontend -- wget -qO- -T 5 http://deskflow-api:8000/health   # refused
kubectl get endpoints deskflow-api -n deskflow             # <none>
kubectl describe svc deskflow-api -n deskflow | grep Selector
kubectl get pods -n deskflow --show-labels                 # pods say component=backend
kubectl patch svc deskflow-api -n deskflow --type merge \
  -p '{"spec":{"selector":{"app.kubernetes.io/name":"deskflow","app.kubernetes.io/component":"backend"}}}'
kubectl get endpoints deskflow-api -n deskflow             # pod IPs appear
kubectl exec -n deskflow deploy/deskflow-frontend -- wget -qO- -T 5 http://deskflow-api:8000/health   # {"status":"ok"}
kubectl delete -f troubleshooting/broken-service.yaml
```

"A Service finds pods only by labels. No match → no endpoints → no traffic. `kubectl get
endpoints` is the first thing to check."

## Close (30 s)

Return to the Actions tab — the run from step 2 should be green with new SHA-tagged images
in GHCR. "From a commit on my laptop to a tested, scanned, versioned image, deployed by Helm
onto Kubernetes, autoscaled and monitored."

## After the session

```bash
docker compose down -v
./scripts/local-cluster.sh down
```
