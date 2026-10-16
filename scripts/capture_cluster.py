"""Screenshot the app, Prometheus and Grafana through the kind ingress.

Maps *.deskflow.local to 127.0.0.1 inside Chromium, so /etc/hosts is not needed.
Usage: python scripts/capture_cluster.py <out_dir>
"""
import sys

from playwright.sync_api import sync_playwright

out = sys.argv[1]
RULES = "MAP deskflow.local 127.0.0.1, MAP grafana.deskflow.local 127.0.0.1, MAP prometheus.deskflow.local 127.0.0.1"

with sync_playwright() as p:
    browser = p.chromium.launch(args=[f"--host-resolver-rules={RULES}"])

    app = browser.new_page(viewport={"width": 1440, "height": 900})
    app.goto("http://deskflow.local/", wait_until="networkidle")
    app.wait_for_selector("table.tickets")
    app.screenshot(path=f"{out}/k8s-01-app-via-ingress.png")
    app.goto("http://deskflow.local/docs", wait_until="networkidle")
    app.wait_for_selector(".opblock")
    app.screenshot(path=f"{out}/k8s-02-swagger-via-ingress.png")

    prom = browser.new_page(viewport={"width": 1440, "height": 900})
    prom.goto("http://prometheus.deskflow.local/targets?search=deskflow", wait_until="load")
    prom.wait_for_timeout(2500)
    prom.screenshot(path=f"{out}/k8s-03-prometheus-targets.png")
    query = "sum by (handler) (rate(http_requests_total{namespace=\"deskflow\"}[1m]))"
    prom.goto(
        "http://prometheus.deskflow.local/query?g0.expr=" + query.replace(" ", "%20").replace('"', "%22")
        + "&g0.tab=graph&g0.range_input=30m",
        wait_until="load",
    )
    prom.wait_for_timeout(2500)
    prom.screenshot(path=f"{out}/k8s-04-prometheus-query.png")

    graf = browser.new_page(viewport={"width": 1600, "height": 1000})
    graf.goto("http://grafana.deskflow.local/login", wait_until="load")
    graf.fill("input[name=user]", "admin")
    graf.fill("input[name=password]", "deskflow-admin")
    graf.click("button[type=submit]")
    graf.wait_for_url(lambda url: "/login" not in url)
    graf.goto("http://grafana.deskflow.local/d/deskflow-overview/?orgId=1&from=now-20m&to=now&refresh=",
              wait_until="load")
    graf.wait_for_timeout(8000)
    graf.screenshot(path=f"{out}/k8s-05-grafana-dashboard.png")
    browser.close()
    print("done")
