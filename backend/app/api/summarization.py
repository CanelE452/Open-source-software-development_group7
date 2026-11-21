from backend.app.api.backends import SummaryBackend
from backend.app.schemas.issues import IssueDetailResponse
from backend.app.schemas.summary import (
    Evidence as ResponseEvidence,
    SummaryResponse,
    SummarySection as ResponseSummarySection,
    SummaryStatus,
)
from backend.app.schemas.summarization_schema import IssueComment, IssueInput
from backend.app.summarization.summarize import SummaryGenerationError, summarize_issue


class OllamaSummaryBackend(SummaryBackend):
    available = True

    def summarize(self, issue: IssueDetailResponse) -> SummaryResponse:
        summary_input = IssueInput(
            number=issue.number,
            title=issue.title,
            body=issue.body,
            html_url=issue.html_url,
            comments=[
                IssueComment(
                    id=comment.id,
                    html_url=comment.html_url,
                    body=comment.body,
                )
                for comment in issue.comments
            ],
        )

        try:
            result = summarize_issue(summary_input)
        except SummaryGenerationError:
            return SummaryResponse(
                repository=issue.repository,
                number=issue.number,
                html_url=issue.html_url,
                status=SummaryStatus.failed,
                partial_collection=issue.partial_collection,
            )

        return SummaryResponse(
            repository=issue.repository,
            number=issue.number,
            html_url=issue.html_url,
            problem=self._to_response_section(result.problem),
            conditions=self._to_response_section(result.conditions),
            solution=self._to_response_section(result.solution),
            discussion=self._to_response_section(result.discussion),
            follow_up=self._to_response_section(result.follow_up),
            unknowns=self._to_response_section(result.unknowns),
            status=SummaryStatus(result.status),
            partial_collection=issue.partial_collection,
        )

    @staticmethod
    def _to_response_section(section) -> ResponseSummarySection:
        return ResponseSummarySection(
            text=section.text,
            evidence=[
                ResponseEvidence.model_validate(item.model_dump())
                for item in section.evidence
            ],
        )
