from __future__ import annotations

import html
import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path


SUMMARY_PATH = Path("reports/latest_summary.md")
DASHBOARD_URL = os.getenv(
    "DASHBOARD_URL",
    "https://balkissoc.github.io/contrarian-investing-monitor/",
)
EMAIL_TO = os.getenv("EMAIL_TO", "balkissoc@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM") or os.getenv("SMTP_USERNAME")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
# Google displays App Passwords in grouped form. Remove all whitespace, including
# non-breaking spaces that can be introduced when copying from a phone/browser.
SMTP_PASSWORD = re.sub(r"\s+", "", os.getenv("SMTP_PASSWORD", ""))


def extract(text: str, label: str, default: str = "—") -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, flags=re.M)
    return match.group(1).strip() if match else default


def first_near_miss(text: str) -> str:
    section = re.search(r"## Near Misses\s*(.*?)(?:\n## |\Z)", text, flags=re.S)
    if not section or "_None._" in section.group(1):
        return "None"

    rows = [line for line in section.group(1).splitlines() if line.strip().startswith("|")]
    if len(rows) < 3:
        return "See dashboard"
    cells = [cell.strip() for cell in rows[2].strip("|").split("|")]
    if len(cells) >= 8:
        ticker = cells[1]
        company = cells[2]
        one_day = cells[5]
        return f"{ticker} — {company} ({one_day}% 1-day)"
    return "See dashboard"


def main() -> None:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"Missing summary: {SUMMARY_PATH}")
    if not SMTP_USERNAME or not SMTP_PASSWORD or not EMAIL_FROM or not EMAIL_TO:
        raise RuntimeError("Missing SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM or EMAIL_TO.")

    text = SUMMARY_PATH.read_text(encoding="utf-8")
    run_time = extract(text, "Run time")
    scanned = extract(text, "Watchlist scanned")
    candidates = extract(text, "Candidates found")
    near_misses = extract(text, "Near misses found")
    top_near = first_near_miss(text)

    subject = f"Contrarian Monitor — {candidates} candidate(s), {near_misses} near miss(es)"

    plain = f"""Contrarian Investing Monitor

Latest scan: {run_time}
Universe scanned: {scanned}
Candidates: {candidates}
Near misses: {near_misses}
Top near miss: {top_near}

Open the graphical dashboard:
{DASHBOARD_URL}

Research aide only. Review ASX announcements, balance sheet, debt, liquidity, earnings quality and the cause of any sell-off before making an investment decision.
"""

    safe_url = html.escape(DASHBOARD_URL, quote=True)
    html_body = f"""<!doctype html>
<html><body style="font-family:Arial,sans-serif;color:#102033;line-height:1.5">
  <div style="max-width:620px;margin:auto;padding:24px">
    <h2 style="margin:0 0 16px">Contrarian Investing Monitor</h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
      <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb">Universe scanned</td><td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right"><strong>{html.escape(scanned)}</strong></td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb">Candidates</td><td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right"><strong>{html.escape(candidates)}</strong></td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb">Near misses</td><td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right"><strong>{html.escape(near_misses)}</strong></td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb">Top near miss</td><td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right">{html.escape(top_near)}</td></tr>
    </table>
    <p><a href="{safe_url}" style="display:inline-block;background:#24599c;color:white;text-decoration:none;font-weight:bold;padding:12px 18px;border-radius:8px">Open graphical dashboard</a></p>
    <p style="font-size:12px;color:#64748b">Latest scan: {html.escape(run_time)}</p>
    <p style="font-size:11px;color:#64748b">Research aide only. Review ASX announcements, balance sheet, debt, liquidity, earnings quality and the cause of any sell-off before making an investment decision.</p>
  </div>
</body></html>"""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    message.set_content(plain)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)

    print(f"Dashboard-link email sent to {EMAIL_TO}: {DASHBOARD_URL}")


if __name__ == "__main__":
    main()
