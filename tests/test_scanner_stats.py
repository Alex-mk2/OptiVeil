"""Tests del cálculo de métricas de calidad del escaneo (función pura)."""
import pytest

from modules.stealth.scanner import build_scan_stats


def test_todos_responden_sin_perdida():
    s = build_scan_stats(total=100, open_count=10, responded_count=100,
                         attempts=1, recovered_on_retry=0)
    assert s["response_rate"] == 1.0
    assert s["loss_rate"] == 0.0
    assert s["unanswered"] == 0


def test_perdida_parcial():
    s = build_scan_stats(total=100, open_count=5, responded_count=75,
                         attempts=2, recovered_on_retry=2)
    assert s["unanswered"] == 25
    assert s["response_rate"] == 0.75
    assert s["loss_rate"] == 0.25
    assert s["recovered_on_retry"] == 2


def test_cero_puertos_no_divide_por_cero():
    s = build_scan_stats(total=0, open_count=0, responded_count=0,
                         attempts=0, recovered_on_retry=0)
    assert s["response_rate"] == 0.0
    assert s["loss_rate"] == 0.0


def test_responded_no_supera_total():
    s = build_scan_stats(total=10, open_count=0, responded_count=999,
                         attempts=1, recovered_on_retry=0)
    assert s["responded"] == 10
    assert s["unanswered"] == 0
