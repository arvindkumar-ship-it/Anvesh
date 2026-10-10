from types import SimpleNamespace
import pytest
import llm_config


def test_provider_exhaustion_is_bounded(monkeypatch):
    calls = []
    def fail(**kwargs):
        calls.append(kwargs['model'])
        raise RuntimeError('503 unavailable fixture')
    monkeypatch.setattr(llm_config, 'completion', fail)
    with pytest.raises(RuntimeError, match='All configured'):
        llm_config.get_llm_response('fixture')
    assert calls == [llm_config.M1, llm_config.M2, llm_config.M3, llm_config.M4]


def test_fallback_returns_success_and_preserves_input(monkeypatch):
    calls = []
    def complete(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1: raise RuntimeError('429 quota fixture')
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='fixture output'))])
    monkeypatch.setattr(llm_config, 'completion', complete)
    assert llm_config.get_llm_response('fixture') == 'fixture output'
    assert calls[1]['messages'] == [{'role': 'user', 'content': 'fixture'}]
    assert calls[1]['timeout'] == 30


def test_nonretryable_error_does_not_call_other_providers(monkeypatch):
    calls = []
    def fail(**kwargs):
        calls.append(kwargs); raise ValueError('invalid input')
    monkeypatch.setattr(llm_config, 'completion', fail)
    with pytest.raises(ValueError): llm_config.get_llm_response('fixture')
    assert len(calls) == 1


def test_attempt_limit(monkeypatch):
    with pytest.raises(ValueError): llm_config.get_llm_response('fixture', max_attempts=0)
