import json, httpx, pytest
from fastapi import FastAPI

from backend.app.api import summarization as summary_backend_module
from backend.app.api.backends import UnavailableSummaryBackend
from backend.app.api.dependencies import init_app_state
from backend.app.api.summarization import OllamaSummaryBackend
from backend.app.integrations import ollama
from backend.app.schemas.collection import CollectedComment
from backend.app.schemas.issues import IssueDetailResponse
from backend.app.schemas.summarization_schema import Evidence, IssueComment, IssueInput, IssueSummary, SummarySection
from backend.app.schemas.summary import SummaryStatus
from backend.app.summarization.summarize import SummaryGenerationError, parse_json_response, summarize_issue, validate_summary_evidence
from backend.tests.conftest import make_settings


ISSUE_URL = "https://github.com/huggingface/transformers/issues/47752"
COMMENT_URL_1001 = f"{ISSUE_URL}#issuecomment-1001"
COMMENT_URL_1002 = f"{ISSUE_URL}#issuecomment-1002"


def make_issue() -> IssueInput:
    return IssueInput(
        number=47752,
        title="incorrect precedence of generation_config values in pipeline",
        body=(
            'When calling pipeline("text-generation"), setting max_new_tokens '
            "in generation_config gets overridden by default parameters."
        ),
        html_url=ISSUE_URL,
        comments=[
            IssueComment(
                id=1001,
                html_url=COMMENT_URL_1001,
                body=(
                    "Confirmed. Setting max_new_tokens inside generation_config "
                    "is ignored if kwargs are passed."
                ),
            ),
            IssueComment(
                id=1002,
                html_url=COMMENT_URL_1002,
                body=(
                    "Workaround: Pass max_new_tokens directly as a keyword "
                    "argument to pipeline() instead of inside generation_config."
                ),
            ),
        ],
    )


def make_detail() -> IssueDetailResponse:
    return IssueDetailResponse(
        repository="huggingface/transformers",
        number=47752,
        title="incorrect precedence of generation_config values in pipeline",
        html_url=ISSUE_URL,
        body=(
            'When calling pipeline("text-generation"), setting max_new_tokens '
            "in generation_config gets overridden by default parameters."
        ),
        comments=[
            CollectedComment(
                id=1001,
                html_url=COMMENT_URL_1001,
                body=(
                    "Confirmed. Setting max_new_tokens inside generation_config "
                    "is ignored if kwargs are passed."
                ),
                author="maintainer-a",
            )
        ],
        comment_count=1,
        collected_at="2026-11-18T00:00:00+00:00",
    )


def make_summary() -> IssueSummary:
    return IssueSummary(
        problem=SummarySection(
            text="generation_config의 생성 길이 설정이 기본값보다 낮은 우선순위로 적용되지 않습니다.",
            evidence=[
                Evidence(
                    url=ISSUE_URL,
                    excerpt="setting max_new_tokens in generation_config gets overridden",
                    source_type="issue_body",
                )
            ],
        ),
        conditions=SummarySection(),
        solution=SummarySection(),
        discussion=SummarySection(),
        follow_up=SummarySection(),
        unknowns=SummarySection(),
        status="completed",
    )


def test_ollama_chat_request_and_response(monkeypatch) -> None:
    requests = []
    settings = make_settings(
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="qwen3:4b-q4_K_M",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"message": {"content": "요약 결과"}},
        )

    original_client = httpx.Client

    def mock_client(**kwargs):
        return original_client(
            transport=httpx.MockTransport(handler),
            **kwargs,
        )

    monkeypatch.setattr(ollama, "get_settings", lambda: settings)
    monkeypatch.setattr(ollama.httpx, "Client", mock_client)

    client = ollama.OllamaClient()
    try:
        assert client.chat("요약해줘") == "요약 결과"
    finally:
        client.close()

    assert len(requests) == 1
    request = requests[0]
    assert str(request.url) == "http://127.0.0.1:11434/api/chat"
    assert "Authorization" not in request.headers

    payload = json.loads(request.content)
    assert payload["model"] == "qwen3:4b-q4_K_M"
    assert payload["format"] == "json"
    assert payload["think"] is False
    assert payload["stream"] is False
    assert payload["options"]["num_ctx"] == 8192
    assert payload["options"]["num_predict"] == 1800


def test_parse_json_response_accepts_json_object() -> None:
    parsed = parse_json_response(
        '{"problem":{"text":"테스트 문제","evidence":[]} '
        ',"conditions":{"text":null,"evidence":[]}'
        ',"solution":{"text":null,"evidence":[]}'
        ',"discussion":{"text":null,"evidence":[]}'
        ',"follow_up":{"text":null,"evidence":[]}'
        ',"unknowns":{"text":null,"evidence":[]}}'
    )

    assert parsed["problem"]["text"] == "테스트 문제"


def test_parse_json_response_rejects_extra_text() -> None:
    with pytest.raises(ValueError):
        parse_json_response('{"problem": "ok"} trailing text')


def test_summary_evidence_accepts_exact_issue_excerpt() -> None:
    summary = IssueSummary(
        problem=SummarySection(
            text="generation_config의 생성 길이 설정이 기본값보다 낮은 우선순위로 적용되지 않습니다.",
            evidence=[
                Evidence(
                    url=ISSUE_URL,
                    excerpt="setting max_new_tokens in generation_config gets overridden",
                    source_type="issue_body",
                )
            ],
        ),
        conditions=SummarySection(),
        solution=SummarySection(),
        discussion=SummarySection(),
        follow_up=SummarySection(),
        unknowns=SummarySection(),
    )

    result = validate_summary_evidence(make_issue(), summary)

    assert result.status == "completed"
    assert result.problem.evidence[0].url == ISSUE_URL


def test_summary_evidence_rejects_unmatched_excerpt() -> None:
    summary = IssueSummary(
        problem=SummarySection(
            text="존재하지 않는 증상입니다.",
            evidence=[
                Evidence(
                    url=ISSUE_URL,
                    excerpt="This sentence is not in the issue",
                    source_type="issue_body",
                )
            ],
        ),
        conditions=SummarySection(),
        solution=SummarySection(),
        discussion=SummarySection(),
        follow_up=SummarySection(),
        unknowns=SummarySection(),
    )

    result = validate_summary_evidence(make_issue(), summary)

    assert result.status == "insufficient_evidence"
    assert result.problem.text is None
    assert result.problem.evidence == []


def test_summary_backend_maps_input_and_returns_result(monkeypatch) -> None:
    received = []

    def fake_summarize_issue(issue):
        received.append(issue)
        return make_summary()

    monkeypatch.setattr(
        summary_backend_module,
        "summarize_issue",
        fake_summarize_issue,
    )

    result = OllamaSummaryBackend().summarize(make_detail())

    assert result.repository == "huggingface/transformers"
    assert result.number == 47752
    assert result.status == SummaryStatus.completed
    assert result.problem.text == "generation_config의 생성 길이 설정이 기본값보다 낮은 우선순위로 적용되지 않습니다."
    assert result.problem.evidence[0].url == ISSUE_URL
    assert "Setting max_new_tokens" in received[0].comments[0].body


def test_summary_backend_returns_failed_when_ollama_fails(monkeypatch) -> None:
    def fail_summarize_issue(issue):
        raise SummaryGenerationError("local Ollama is unavailable")

    monkeypatch.setattr(
        summary_backend_module,
        "summarize_issue",
        fail_summarize_issue,
    )

    result = OllamaSummaryBackend().summarize(make_detail())

    assert result.status == SummaryStatus.failed
    assert result.problem.text is None


def test_app_registers_local_ollama_backend_and_preserves_override() -> None:
    app = FastAPI()
    init_app_state(app, make_settings())
    assert isinstance(app.state.summary_backend, OllamaSummaryBackend)

    unavailable_app = FastAPI()
    unavailable_app.state.summary_backend = UnavailableSummaryBackend()
    init_app_state(unavailable_app, make_settings())
    assert isinstance(
        unavailable_app.state.summary_backend,
        UnavailableSummaryBackend,
    )


def test_live_local_ollama_summary() -> None:
    try:
        response = httpx.get(
            "http://127.0.0.1:11434/api/ps",
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        pytest.fail(f"Local Ollama is unavailable: {exc}")

    loaded_models = response.json().get("models", [])
    print("Loaded Ollama models:", [model["name"] for model in loaded_models])

    result = summarize_issue(make_issue())

    print("Summary status:", result.status)
    print("Problem summary:", result.problem.text)
    print("Problem evidence:", [item.model_dump() for item in result.problem.evidence])

    assert result.status in {"completed", "insufficient_evidence"}
    assert result.status != "failed"
