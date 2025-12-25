#!/usr/bin/env python3
"""Populate the project's SQLite database with test Message records.

Usage:
  python scripts/populate_test_db.py --database sqlite:////tmp/virtual_card.db
Or set the `DATABASE_URL` environment variable and run without args.
"""
from __future__ import annotations
import argparse
import os
import uuid
from datetime import datetime, timedelta

import sys
import os
# Ensure repo root is on sys.path so `shared` package can be imported when
# running this script from any CWD.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from shared.models import init_db, Message


def make_sample_messages():
    now = datetime.utcnow()
    msgs = []
    for i in range(1, 80):
        m = Message(
            uuid=str(uuid.uuid4()),
            name=f"Test User {i}",
            initials=(f"TU{i}" if i < 10 else f"T{i}")[:5],
            content=f"This is a sample message number {i}. Greetings from test data!",
            image_path=None if i % 3 != 0 else f"/tmp/media/image_{i}.jpg",
            thumb_path=None if i % 3 != 0 else f"/tmp/media/thumb_{i}.jpg",
            status="approved" if i % 2 == 0 else "pending",
            created_at=now - timedelta(days=i),
            approved_at=now - timedelta(days=i-1),
            ip_address=f"192.0.2.{i}",
            color_hint=None,
            order_index=i
        )
        msgs.append(m)
    return msgs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', '-d', help='Database URL (SQLAlchemy)', default=os.environ.get('DATABASE_URL', 'sqlite:////srv/coll-card/kun/data/virtual_card.db'))
    parser.add_argument('--drop', action='store_true', help='Drop and recreate tables before inserting (WARNING: destructive)')
    args = parser.parse_args()

    db_url = args.database
    print(f"Using database: {db_url}")

    Session, engine = init_db(db_url)

    if args.drop:
        print("Dropping and recreating tables...")
        from shared.models import Base
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    session = Session()
    samples = make_sample_messages()

    print(f"Inserting {len(samples)} sample messages...")
    session.add_all(samples)
    session.commit()

    # Print inserted ids and a count
    count = session.query(Message).count()
    print(f"Total messages in DB: {count}")

    for m in session.query(Message).order_by(Message.id).all():
        print(f"{m.id}: {m.uuid[:8]}.. {m.name} [{m.status}] created={m.created_at.isoformat()} image={bool(m.image_path)}")

    session.close()


if __name__ == '__main__':
    main()
