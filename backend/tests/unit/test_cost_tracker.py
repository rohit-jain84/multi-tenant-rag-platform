from app.services.generation.cost_tracker import estimate_cost


class TestEstimateCost:
    def test_basic_cost(self):
        cost = estimate_cost(prompt_tokens=1000, completion_tokens=500)
        # With defaults: 0.00015 * 1 + 0.0006 * 0.5 = 0.00015 + 0.0003 = 0.00045
        assert cost == 0.00045

    def test_zero_tokens(self):
        cost = estimate_cost(prompt_tokens=0, completion_tokens=0)
        assert cost == 0.0

    def test_large_tokens(self):
        cost = estimate_cost(prompt_tokens=100000, completion_tokens=50000)
        assert cost > 0
        assert isinstance(cost, float)
