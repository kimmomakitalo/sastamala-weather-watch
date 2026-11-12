from datetime import datetime, timezone

from weather_watch.scheduling import is_scheduled_local_hour


def test_summer_utc_schedule_hits_target_helsinki_hour() -> None:
    summer_utc = datetime(2026, 7, 10, 13, 17, tzinfo=timezone.utc)

    assert is_scheduled_local_hour(summer_utc)


def test_winter_utc_schedule_hits_target_helsinki_hour() -> None:
    winter_utc = datetime(2026, 1, 10, 14, 17, tzinfo=timezone.utc)

    assert is_scheduled_local_hour(winter_utc)


def test_wrong_dst_schedule_is_skipped() -> None:
    wrong_summer_utc = datetime(2026, 7, 10, 14, 17, tzinfo=timezone.utc)
    wrong_winter_utc = datetime(2026, 1, 10, 13, 17, tzinfo=timezone.utc)

    assert not is_scheduled_local_hour(wrong_summer_utc)
    assert not is_scheduled_local_hour(wrong_winter_utc)
