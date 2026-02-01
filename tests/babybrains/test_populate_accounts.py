"""Tests for S0.1: bb_accounts populate command."""

from datetime import date, timedelta

import pytest

from atlas.babybrains import db


class TestPopulateAccounts:
    """Test populate_accounts function."""

    def test_inserts_4_accounts(self, bb_conn):
        results = db.populate_accounts(bb_conn)
        assert len(results) == 4

        accounts = db.get_accounts(bb_conn)
        assert len(accounts) == 4

    def test_correct_platforms(self, bb_conn):
        db.populate_accounts(bb_conn)
        accounts = db.get_accounts(bb_conn)
        platforms = {a.platform for a in accounts}
        assert platforms == {"youtube", "tiktok", "instagram", "facebook"}

    def test_correct_handles(self, bb_conn):
        db.populate_accounts(bb_conn)
        accounts = db.get_accounts(bb_conn)
        handles = {a.platform: a.handle for a in accounts}
        assert handles["youtube"] == "@babybrains-app"
        assert handles["tiktok"] == "babybrains.app"
        assert handles["instagram"] == "babybrains.app"
        assert handles["facebook"] == "Baby Brains"

    def test_youtube_is_incubating(self, bb_conn):
        db.populate_accounts(bb_conn)
        accounts = db.get_accounts(bb_conn, platform="youtube")
        assert len(accounts) == 1
        assert accounts[0].status == "incubating"

    def test_youtube_incubation_end_date_is_today_plus_7(self, bb_conn):
        db.populate_accounts(bb_conn)
        accounts = db.get_accounts(bb_conn, platform="youtube")
        expected = (date.today() + timedelta(days=7)).isoformat()
        assert accounts[0].incubation_end_date == expected

    def test_non_youtube_accounts_are_warming(self, bb_conn):
        db.populate_accounts(bb_conn)
        accounts = db.get_accounts(bb_conn)
        for a in accounts:
            if a.platform != "youtube":
                assert a.status == "warming", f"{a.platform} should be warming"

    def test_non_youtube_no_incubation_date(self, bb_conn):
        db.populate_accounts(bb_conn)
        accounts = db.get_accounts(bb_conn)
        for a in accounts:
            if a.platform != "youtube":
                assert a.incubation_end_date is None, (
                    f"{a.platform} should not have incubation_end_date"
                )

    def test_idempotent_no_duplicates(self, bb_conn):
        """Running populate twice should not create duplicate accounts."""
        db.populate_accounts(bb_conn)
        db.populate_accounts(bb_conn)

        accounts = db.get_accounts(bb_conn)
        assert len(accounts) == 4

    def test_idempotent_returns_updated(self, bb_conn):
        """Second run should report 'updated' not 'inserted'."""
        results1 = db.populate_accounts(bb_conn)
        results2 = db.populate_accounts(bb_conn)

        assert all(r["action"] == "inserted" for r in results1)
        assert all(r["action"] == "updated" for r in results2)

    def test_status_dashboard_shows_accounts(self, bb_conn):
        """Acceptance: bb status shows all 4 accounts."""
        db.populate_accounts(bb_conn)
        status = db.get_bb_status(bb_conn)
        assert len(status["accounts"]) == 4

        platforms = {a["platform"] for a in status["accounts"]}
        assert platforms == {"youtube", "tiktok", "instagram", "facebook"}

    def test_status_dashboard_includes_incubation_date(self, bb_conn):
        """Status dashboard includes incubation_end_date field."""
        db.populate_accounts(bb_conn)
        status = db.get_bb_status(bb_conn)

        yt = next(a for a in status["accounts"] if a["platform"] == "youtube")
        assert yt["incubation_end_date"] is not None
        assert yt["status"] == "incubating"
