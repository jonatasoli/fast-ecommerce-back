from datetime import datetime, timedelta, timezone

from app.cart.retry import BACKOFF_SCHEDULE, get_backoff_delay, is_job_expired


class CheckoutJobsHelpersTest:
    def test_get_backoff_delay_sequence(self):
        assert get_backoff_delay(0) == BACKOFF_SCHEDULE[0]
        assert get_backoff_delay(1) == BACKOFF_SCHEDULE[1]
        assert get_backoff_delay(2) == BACKOFF_SCHEDULE[2]
        assert get_backoff_delay(3) is None

    def test_is_job_expired_helper(self):
        now = datetime.now(timezone.utc)
        older = now - timedelta(days=8)
        recent = now - timedelta(days=1)

        assert is_job_expired(older, now=now) is True
        assert is_job_expired(recent, now=now) is False


if __name__ == '__main__':
    suite = CheckoutJobsHelpersTest()
    suite.test_get_backoff_delay_sequence()
    suite.test_is_job_expired_helper()
