import pytest
from app.services.ai_service import AIProvider, ProviderManager, RuleEngineProvider
from app.models.category import Category
from app.models.merchant import Merchant, MerchantAlias, MerchantRule
import uuid


class DummyHealthyProvider(AIProvider):
    def __init__(self, value=None, healthy=True):
        self.value = value
        self.healthy = healthy
        self.call_count = 0

    async def get_completion(self, prompt, system_message, context=None):
        self.call_count += 1
        if self.value is None:
            raise Exception("Failure")
        return self.value

    async def is_healthy(self):
        return self.healthy


@pytest.mark.asyncio
async def test_provider_manager_sequential_fallback():
    # Primary fails, Secondary succeeds
    p1 = DummyHealthyProvider(value=None)
    p2 = DummyHealthyProvider(value='{"category": "Bills"}')
    p3 = DummyHealthyProvider(value='{"category": "Shopping"}')

    manager = ProviderManager([p1, p2, p3])
    res = await manager.get_completion("prompt", "sys")

    assert res == '{"category": "Bills"}'
    assert p1.call_count == 2  # 2 retries
    assert p2.call_count == 1
    assert p3.call_count == 0


@pytest.mark.asyncio
async def test_provider_manager_unhealthy_skipped():
    p1 = DummyHealthyProvider(value='{"category": "Bills"}', healthy=False)
    p2 = DummyHealthyProvider(value='{"category": "Shopping"}', healthy=True)

    manager = ProviderManager([p1, p2])
    res = await manager.get_completion("prompt", "sys")

    assert res == '{"category": "Shopping"}'
    assert p1.call_count == 0
    assert p2.call_count == 1


@pytest.mark.asyncio
async def test_rule_engine_provider_fallback(db_session):
    # Setup database rules
    cat_id = uuid.uuid4()
    cat = Category(id=cat_id, name="Investment", slug="investment", display_name="Investment", system=True)
    merchant = Merchant(id=uuid.uuid4(), name="Zerodha", is_verified=True)
    alias = MerchantAlias(alias="zerodha", merchant_id=merchant.id)
    rule = MerchantRule(merchant_id=merchant.id, category_id=cat_id)

    db_session.add_all([cat, merchant, alias, rule])
    await db_session.commit()

    # Rule Engine Provider
    provider = RuleEngineProvider()
    context = {"db": db_session, "merchant": "Zerodha", "user_id": uuid.uuid4()}
    res = await provider.get_completion("prompt", "sys", context)
    assert res == '{"category": "Investment"}'
