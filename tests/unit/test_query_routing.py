"""P5.4 routing is deterministic, bounded, and does not invoke an Agent."""

from legal_research.application.query_routing import QueryRoute, RuleFirstQueryRouter


def test_router_prefers_supported_exact_section_references() -> None:
    assert RuleFirstQueryRouter().route("section 8.1.2").route is QueryRoute.EXACT_REFERENCE


def test_router_bounds_multi_part_decomposition_and_falls_back_safely() -> None:
    router = RuleFirstQueryRouter()
    plan = router.route("What are the elements of self defence and who bears the burden of proof?")
    assert plan.route is QueryRoute.MULTI_PART_QUESTION
    assert len(plan.queries) == 2
    assert router.route("self defence").route is QueryRoute.SEMANTIC_QUESTION


def test_router_does_not_expand_unbounded_or_ambiguous_requests() -> None:
    router = RuleFirstQueryRouter()

    plan = router.route("Explain actus reus and mens rea and causation and defences")

    assert plan.route is QueryRoute.SEMANTIC_QUESTION
    assert plan.queries == ("Explain actus reus and mens rea and causation and defences",)
