"""Capture browser screenshots of the running app with headless Chromium.

Usage: python scripts/capture_ui.py <frontend_url> <backend_url> <out_dir> [prefix]
"""
import sys
import time

from playwright.sync_api import sync_playwright

frontend, backend, out = sys.argv[1], sys.argv[2], sys.argv[3]
prefix = sys.argv[4] if len(sys.argv) > 4 else "ui"


def shot(page, name):
    path = f"{out}/{name}.png"
    page.screenshot(path=path, full_page=False)
    print("saved", path)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page.goto(frontend, wait_until="networkidle")
    page.wait_for_selector("table.tickets")
    shot(page, f"{prefix}-01-dashboard-desktop")

    page.click("text=New ticket")
    page.fill("input[placeholder='Short summary of the issue']", "Payment page shows 502 error")
    page.fill("input[placeholder='Company or contact name']", "Contoso Pharma")
    page.fill("textarea", "Checkout fails for all EU customers since 10:05 IST.")
    page.select_option(".modal select >> nth=0", "urgent")
    page.select_option(".modal select >> nth=2", index=2)
    page.wait_for_timeout(500)  # let the open animation finish
    shot(page, f"{prefix}-02-create-ticket-modal")
    page.click("button[type=submit]")
    page.wait_for_selector("text=Payment page shows 502 error")
    time.sleep(0.5)
    shot(page, f"{prefix}-03-ticket-created")

    page.click("button.chip:has-text('Open')")
    page.wait_for_timeout(600)
    shot(page, f"{prefix}-04-status-filter-open")

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
    mobile.goto(frontend, wait_until="networkidle")
    mobile.wait_for_selector("table.tickets")
    mobile.screenshot(path=f"{out}/{prefix}-05-dashboard-mobile.png")
    mobile.screenshot(path=f"{out}/{prefix}-05b-dashboard-mobile-full.png", full_page=True)
    print("saved mobile")

    if backend != "-":
        page.goto(f"{backend}/docs", wait_until="networkidle")
        page.wait_for_selector(".opblock")
        shot(page, f"{prefix}-06-swagger-docs")
        page.goto(f"{backend}/metrics")
        shot(page, f"{prefix}-07-metrics-endpoint")
    browser.close()
