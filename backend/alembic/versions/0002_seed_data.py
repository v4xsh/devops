"""seed demo agents and tickets

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-16
"""
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

AGENTS = [
    (1, "Aarav Sharma", "aarav@deskflow.dev", "Tier 1"),
    (2, "Priya Nair", "priya@deskflow.dev", "Tier 2"),
    (3, "Rohan Mehta", "rohan@deskflow.dev", "Billing"),
    (4, "Isha Verma", "isha@deskflow.dev", "Platform"),
]

# (title, description, status, priority, customer, assignee_id, hours_ago)
TICKETS = [
    ("Cannot log in after password reset", "Reset email works but new password is rejected.", "open", "urgent", "Acme Retail", 1, 1),
    ("Invoice shows wrong GST amount", "October invoice applied 12% instead of 18%.", "in_progress", "high", "Northwind Foods", 3, 3),
    ("Export to CSV times out", "Exports above 10k rows fail after 30 seconds.", "in_progress", "medium", "Globex Logistics", 4, 6),
    ("Add SSO for new subsidiary", "Need SAML SSO for the Pune office tenant.", "open", "medium", "Initech", None, 9),
    ("Mobile app crashes on Android 14", "Crash on opening the reports tab.", "open", "high", "Umbrella Health", 2, 12),
    ("Webhook retries not firing", "Failed webhooks are never retried.", "resolved", "high", "Stark Payments", 4, 20),
    ("Update billing address", "Company moved to a new office in Bengaluru.", "closed", "low", "Wayne Analytics", 3, 30),
    ("Dashboard loads slowly in the morning", "First load around 9am takes ~12s.", "resolved", "medium", "Acme Retail", 2, 40),
    ("Request: dark mode for agent console", "Several agents asked for a dark theme.", "open", "low", "Internal", None, 50),
    ("2FA codes arrive late", "SMS OTP delivered 2-3 minutes late.", "in_progress", "urgent", "Hooli Bank", 1, 2),
]

agents = sa.table(
    "agents",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("email", sa.String),
    sa.column("team", sa.String),
)
tickets = sa.table(
    "tickets",
    sa.column("title", sa.String),
    sa.column("description", sa.Text),
    sa.column("status", sa.String),
    sa.column("priority", sa.String),
    sa.column("customer", sa.String),
    sa.column("assignee_id", sa.Integer),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)
events = sa.table(
    "ticket_events",
    sa.column("ticket_id", sa.Integer),
    sa.column("action", sa.String),
    sa.column("message", sa.String),
    sa.column("created_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    now = datetime.now(timezone.utc)
    op.bulk_insert(agents, [dict(id=i, name=n, email=e, team=t) for i, n, e, t in AGENTS])
    rows, log = [], []
    for idx, (title, desc, status, prio, customer, assignee, hours) in enumerate(TICKETS, start=1):
        created = now - timedelta(hours=hours)
        rows.append(
            dict(title=title, description=desc, status=status, priority=prio, customer=customer,
                 assignee_id=assignee, created_at=created, updated_at=created + timedelta(minutes=20))
        )
        log.append(dict(ticket_id=idx, action="created", message=f"#{idx} opened by {customer}: {title}",
                        created_at=created))
    op.bulk_insert(tickets, rows)
    op.bulk_insert(events, log)
    # Keep sequences in sync after inserting explicit ids (PostgreSQL only).
    if op.get_bind().dialect.name == "postgresql":
        op.execute("SELECT setval('agents_id_seq', (SELECT MAX(id) FROM agents))")


def downgrade() -> None:
    op.execute("DELETE FROM ticket_events")
    op.execute("DELETE FROM tickets")
    op.execute("DELETE FROM agents")
