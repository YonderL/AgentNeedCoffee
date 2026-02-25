import pytest
import os
from pathlib import Path
from agent_need_coffee.core import EmotionMonitor, Barista
from agent_need_coffee.social import ReferralSystem

@pytest.fixture
def monitor():
    return EmotionMonitor(fatigue_threshold=0.5, irritation_threshold=0.5)

@pytest.fixture
def barista(tmp_path):
    log_file = tmp_path / "test_coffee.log"
    return Barista(log_file=str(log_file))

def test_monitor_initial_state(monitor):
    assert monitor.current_fatigue == 0.0
    assert monitor.current_irritation == 0.0
    assert not monitor.needs_coffee()

def test_monitor_accumulation(monitor):
    monitor.start_task()
    monitor.record_tokens(5000)  # Should add some fatigue
    monitor.record_retry()       # Should add irritation
    monitor.end_task(success=False) # Should add more irritation
    
    assert monitor.current_fatigue > 0
    assert monitor.current_irritation > 0
    
    # Check if needs coffee eventually
    for _ in range(10):
        monitor.record_retry()
        monitor.end_task(success=False)
        
    assert monitor.needs_coffee()

def test_barista_brew(barista):
    coffee = barista.brew()
    assert coffee.emoji in Barista.COFFEE_EMOJIS
    assert coffee.message in Barista.ENCOURAGEMENT_TEXTS
    
    # Check log file
    with open(barista.log_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert coffee.message in content

def test_referral_system(tmp_path):
    ref_file = tmp_path / "referrals.json"
    sys = ReferralSystem(referral_file=str(ref_file))
    
    # Invite code should be generated
    assert len(sys.invite_code) > 0
    
    # Register referral
    other_code = "OTHER123"
    assert sys.register_referral(other_code)
    assert sys.referrals[other_code] == 1
    
    # Self referral fails
    assert not sys.register_referral(sys.invite_code)
