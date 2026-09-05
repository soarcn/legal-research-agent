from legal_research.application.query_focus import FactPatternQueryFocuser


def test_focuser_uses_final_question_for_a_long_single_question_fact_pattern() -> None:
    question = " ".join(["A detailed fact is provided."] * 12) + " What must the prosecution prove?"

    focused = FactPatternQueryFocuser().focus(question)

    assert focused.applied is True
    assert focused.retrieval_query == "What must the prosecution prove?"


def test_focuser_keeps_short_and_multi_question_requests_unchanged() -> None:
    focuser = FactPatternQueryFocuser()

    assert focuser.focus("What is self defence?").applied is False
    multi = " ".join(["Detailed background."] * 25) + " What is self defence? Who bears the burden?"
    assert focuser.focus(multi).applied is False


def test_focuser_preserves_trailing_context() -> None:
    question = (
        " ".join(["Detailed background."] * 25) + " What must be proved? Consider both parties."
    )
    assert FactPatternQueryFocuser().focus(question).retrieval_query == question
