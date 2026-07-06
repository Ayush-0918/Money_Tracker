"""
app/services/ai_service.py
─────────────────────────────────────────────────────────────────────────────
Modular AI Service supporting GitHub Models and local fallbacks.
Responsible for categorization, insights, and saving tips.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# ── Provider Metrics & Circuit Breakers ──────────────────────────────────────

class ProviderMetrics:
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.total_latency_seconds = 0.0

    def record_success(self, latency: float):
        self.success_count += 1
        self.total_latency_seconds += latency

    def record_failure(self):
        self.failure_count += 1

    def get_summary(self) -> Dict[str, Any]:
        avg_latency = (self.total_latency_seconds / self.success_count) if self.success_count > 0 else 0.0
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_latency_seconds": avg_latency
        }

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_state_change = time.time()

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_state_change > self.cooldown_seconds:
                self.state = "HALF_OPEN"
                self.last_state_change = time.time()
                return True
            return False
        return True

# ── Provider Interface ──────────────────────────────────────────────────────

class AIProvider(ABC):
    def __init__(self):
        self.metrics = ProviderMetrics()
        self.circuit_breaker = CircuitBreaker()

    @abstractmethod
    async def get_completion(
        self, 
        prompt: str, 
        system_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        pass

    @abstractmethod
    async def is_healthy(self) -> bool:
        pass

class GitHubModelsProvider(AIProvider):
    def __init__(self):
        super().__init__()
        self.token = settings.GITHUB_TOKEN
        self.endpoint = settings.GITHUB_MODELS_ENDPOINT
        self.model = settings.GITHUB_MODEL
        self.timeout = settings.AI_TIMEOUT_GITHUB

        # Initializing client only if token is present to avoid crashes
        self.client = AsyncOpenAI(
            base_url=self.endpoint,
            api_key=self.token,
            max_retries=3,
            timeout=self.timeout
        ) if self.token else None

    async def get_completion(
        self, 
        prompt: str, 
        system_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not self.client:
            return None

        if not self.circuit_breaker.allow_request():
            logger.warning(json.dumps({
                "event": "circuit_breaker_blocked",
                "provider": "GitHubModelsProvider",
                "state": self.circuit_breaker.state
            }))
            return None

        start_time = time.time()
        request_id = f"ai_{int(start_time)}"
        logger.info(json.dumps({
            "event": "ai_request_start",
            "request_id": request_id,
            "provider": "GitHubModelsProvider",
            "model": self.model,
            "prompt_length": len(prompt)
        }))

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_completion_tokens=200,
                response_format={"type": "json_object"}
            )
            latency = time.time() - start_time
            self.metrics.record_success(latency)
            self.circuit_breaker.record_success()

            logger.info(json.dumps({
                "event": "ai_request_success",
                "request_id": request_id,
                "provider": "GitHubModelsProvider",
                "latency_seconds": latency
            }))
            return response.choices[0].message.content
        except Exception as e:
            latency = time.time() - start_time
            self.metrics.record_failure()
            self.circuit_breaker.record_failure()

            logger.error(json.dumps({
                "event": "ai_request_failure",
                "request_id": request_id,
                "provider": "GitHubModelsProvider",
                "error": type(e).__name__,
                "message": str(e),
                "latency_seconds": latency
            }))
            return None

    async def is_healthy(self) -> bool:
        if not self.client:
            return False
        return self.circuit_breaker.state != "OPEN"

class GroqProvider(AIProvider):
    def __init__(self):
        super().__init__()
        self.api_key = settings.GROQ_API_KEY
        self.endpoint = settings.GROQ_API_URL
        self.model = settings.GROQ_MODEL
        self.timeout = settings.AI_TIMEOUT_GROQ

        self.client = AsyncOpenAI(
            base_url=self.endpoint,
            api_key=self.api_key,
            max_retries=3,
            timeout=self.timeout
        ) if self.api_key else None

    async def get_completion(
        self, 
        prompt: str, 
        system_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not self.client:
            return None

        if not self.circuit_breaker.allow_request():
            logger.warning(json.dumps({
                "event": "circuit_breaker_blocked",
                "provider": "GroqProvider",
                "state": self.circuit_breaker.state
            }))
            return None

        start_time = time.time()
        request_id = f"groq_{int(start_time)}"
        logger.info(json.dumps({
            "event": "ai_request_start",
            "request_id": request_id,
            "provider": "GroqProvider",
            "model": self.model,
            "prompt_length": len(prompt)
        }))

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            latency = time.time() - start_time
            self.metrics.record_success(latency)
            self.circuit_breaker.record_success()

            logger.info(json.dumps({
                "event": "ai_request_success",
                "request_id": request_id,
                "provider": "GroqProvider",
                "latency_seconds": latency
            }))
            return response.choices[0].message.content
        except Exception as e:
            latency = time.time() - start_time
            self.metrics.record_failure()
            self.circuit_breaker.record_failure()

            logger.error(json.dumps({
                "event": "ai_request_failure",
                "request_id": request_id,
                "provider": "GroqProvider",
                "error": type(e).__name__,
                "message": str(e),
                "latency_seconds": latency
            }))
            return None

    async def is_healthy(self) -> bool:
        if not self.client:
            return False
        return self.circuit_breaker.state != "OPEN"

from sqlalchemy import select
from app.models.merchant import MerchantAlias, MerchantRule, UserOverride, AICategorizationCache
from app.models.category import Category

class RuleEngineProvider(AIProvider):
    def __init__(self):
        super().__init__()

    async def get_completion(
        self, 
        prompt: str, 
        system_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not context:
            return None

        db = context.get("db")
        merchant = context.get("merchant")
        user_id = context.get("user_id")

        if not db or not merchant:
            return None

        # Resolve Rule-based Fallback
        alias_stmt = select(MerchantAlias).where(MerchantAlias.alias == merchant.lower().strip())
        alias_result = await db.execute(alias_stmt)
        alias = alias_result.scalar_one_or_none()

        if alias:
            canonical_merchant_id = alias.merchant_id

            # 1. User Override check
            if user_id:
                override_stmt = select(UserOverride).where(
                    UserOverride.user_id == user_id,
                    UserOverride.merchant_id == canonical_merchant_id,
                    UserOverride.correction_count >= 2
                )
                override_res = await db.execute(override_stmt)
                override = override_res.scalar_one_or_none()
                if override:
                    cat_stmt = select(Category).where(Category.id == override.category_id)
                    cat_res = await db.execute(cat_stmt)
                    cat = cat_res.scalar_one_or_none()
                    if cat:
                        logger.info("RuleEngineProvider: resolved via UserOverride")
                        return f'{{"category": "{cat.name}"}}'

            # 2. Global Rule check
            rule_stmt = select(MerchantRule).where(
                MerchantRule.merchant_id == canonical_merchant_id
            )
            rule_res = await db.execute(rule_stmt)
            rule = rule_res.scalar_one_or_none()
            if rule:
                cat_stmt = select(Category).where(Category.id == rule.category_id)
                cat_res = await db.execute(cat_stmt)
                cat = cat_res.scalar_one_or_none()
                if cat:
                    logger.info("RuleEngineProvider: resolved via MerchantRule")
                    return f'{{"category": "{cat.name}"}}'

        return None

    async def is_healthy(self) -> bool:
        return True

class ProviderManager(AIProvider):
    def __init__(self, providers: List[AIProvider]):
        super().__init__()
        self.providers = providers

    async def get_completion(
        self, 
        prompt: str, 
        system_message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        for provider in self.providers:
            if not await provider.is_healthy():
                logger.warning(f"ProviderManager: Skipping unhealthy provider {provider.__class__.__name__}")
                continue

            retries = 2
            delay = 0.5
            for attempt in range(retries):
                try:
                    res = await provider.get_completion(prompt, system_message, context)
                    if res is not None:
                        return res
                except Exception as e:
                    logger.warning(
                        f"ProviderManager: Provider {provider.__class__.__name__} failed on attempt {attempt+1} - {str(e)}"
                    )
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
            
            logger.warning(f"ProviderManager: Provider {provider.__class__.__name__} failed completely. Falling back...")
        
        return None

    async def is_healthy(self) -> bool:
        return any([await p.is_healthy() for p in self.providers])

# ── AI Service Core ────────────────────────────────────────────────────────

class AIService:
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.enabled = settings.AI_ENABLED
        # Simple in-memory cache for merchant classifications
        self._merchant_cache: Dict[str, str] = {}

    async def categorize_transaction(
        self, 
        merchant: str, 
        amount: float, 
        raw_text: str,
        db: Optional[Any] = None,
        user_id: Optional[Any] = None
    ) -> Optional[str]:
        """Categorizes a transaction using AI with a rule-based fallback."""
        if not self.enabled:
            return None

        # 1. Check in-memory Cache
        cache_key = merchant.lower().strip()
        if cache_key in self._merchant_cache:
            return self._merchant_cache[cache_key]

        # 2. Check Database Cache
        if db is not None:
            try:
                db_cache_stmt = select(AICategorizationCache).where(
                    AICategorizationCache.merchant_name == cache_key
                )
                db_cache_res = await db.execute(db_cache_stmt)
                db_cache = db_cache_res.scalar_one_or_none()
                if db_cache:
                    self._merchant_cache[cache_key] = db_cache.category_name
                    logger.info(f"AI Cache Hit: {cache_key} -> {db_cache.category_name}")
                    return db_cache.category_name
            except Exception as e:
                logger.error(f"Failed to query AI categorization cache: {e}")

        # 3. Keyword-based deterministic pre-classification rules:
        merchant_lower = merchant.lower().strip()
        raw_lower = raw_text.lower()
        pre_category = None

        if any(kw in raw_lower for kw in ["salary", "payroll", "wages", "neft salary", "credited salary"]) or \
           any(kw in merchant_lower for kw in ["salary", "payroll", "wages"]):
            pre_category = "Income"
        elif any(kw in raw_lower for kw in ["cashback", "refund", "reversal"]):
            pre_category = "Income"
        elif any(kw in raw_lower for kw in ["emi", "loan repayment", "repayment of loan"]) or \
             any(kw in merchant_lower for kw in ["emi", "loan repayment"]):
            pre_category = "Loans/EMI"
        elif any(kw in raw_lower for kw in ["credit card payment", "credit card bill", "cc payment"]) or \
             "credit card" in merchant_lower:
            pre_category = "Credit Card Payment"

        if pre_category:
            self._merchant_cache[cache_key] = pre_category
            if db is not None:
                try:
                    db_cache = AICategorizationCache(
                        merchant_name=cache_key,
                        category_name=pre_category
                    )
                    await db.merge(db_cache)
                    await db.flush()
                    logger.info(f"Pre-classified Category Saved: {cache_key} -> {pre_category}")
                except Exception as e:
                    logger.error(f"Failed to save pre-classified category to cache: {e}")
            return pre_category

        # 4. AI Inference
        system_msg = (
            "You are a finance assistant. Categorize Indian transactions into one of these exact categories: "
            "Food, Shopping, Bills, Transport, Entertainment, Health, Investment, Income, Loans/EMI, "
            "Credit Card Payment, or Others."
        )
        prompt = f"Merchant: {merchant}, Amount: ₹{amount}, Text: {raw_text}. Return JSON: {{\"category\": \"name\"}}"

        context = {
            "merchant": merchant,
            "amount": amount,
            "raw_text": raw_text,
            "db": db,
            "user_id": user_id
        }
        result_json = await self.provider.get_completion(prompt, system_msg, context)

        if result_json:
            try:
                data = json.loads(result_json)
                category = data.get("category")
                if category:
                    self._merchant_cache[cache_key] = category
                    # Save to database cache persistently
                    if db is not None:
                        try:
                            db_cache = AICategorizationCache(
                                merchant_name=cache_key,
                                category_name=category
                            )
                            await db.merge(db_cache)
                            await db.flush()
                            logger.info(f"AI Cache Saved: {cache_key} -> {category}")
                        except Exception as e:
                            logger.error(f"Failed to save to AI categorization cache: {e}")
                    return category
            except json.JSONDecodeError:
                pass

        return None # Fallback logic is handled in transaction_service.py

    async def get_spending_insights(self, transactions: List[Dict[str, Any]]) -> Optional[str]:
        """Generates insights from a list of transactions."""
        system_msg = "Analyze the spending pattern and provide 2-3 bullet points of insights."
        prompt = f"Transactions: {json.dumps(transactions)}. Return JSON: {{\"insights\": \"string\"}}"

        result_json = await self.provider.get_completion(prompt, system_msg)
        return json.loads(result_json).get("insights") if result_json else None

    async def get_saving_tips(self, budget_status: Dict[str, Any]) -> Optional[str]:
        """Provides personalized saving tips based on current budget usage."""
        system_msg = "Provide 2 short, personalized saving tips based on the budget performance."
        prompt = f"Budget Status: {json.dumps(budget_status)}. Return JSON: {{\"tips\": \"string\"}}"

        result_json = await self.provider.get_completion(prompt, system_msg)
        return json.loads(result_json).get("tips") if result_json else None

    async def get_merchant_understanding(self, merchant_name: str) -> Optional[Dict[str, Any]]:
        """Deeply analyzes an unknown merchant name."""
        system_msg = "Analyze the merchant name and provide its business type and likely category."
        prompt = f"Merchant: {merchant_name}. Return JSON: {{\"business_type\": \"string\", \"category\": \"string\"}}"

        result_json = await self.provider.get_completion(prompt, system_msg)
        return json.loads(result_json) if result_json else None

    async def get_budget_recommendations(self, historical_spending: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Recommends budget limits based on historical data."""
        system_msg = "Suggest monthly budget limits for each category based on the spending history."
        prompt = f"History: {json.dumps(historical_spending)}. Return JSON: {{\"recommendations\": [ {{\"category\": \"string\", \"limit\": float}} ] }}"

        result_json = await self.provider.get_completion(prompt, system_msg)
        return json.loads(result_json).get("recommendations") if result_json else None

    async def get_monthly_summary(self, month_data: Dict[str, Any]) -> Optional[str]:
        """Generates a comprehensive monthly financial summary."""
        system_msg = "Generate a professional 3-sentence financial summary for the month."
        prompt = f"Month Data: {json.dumps(month_data)}. Return JSON: {{\"summary\": \"string\"}}"

        result_json = await self.provider.get_completion(prompt, system_msg)
        return json.loads(result_json).get("summary") if result_json else None

    async def get_coach_insights(self, summary_data: Dict[str, Any]) -> Optional[List[str]]:
        """Generates dynamic AI Financial Coach insights."""
        system_msg = (
            "You are a helpful and witty personal finance coach. Analyze the user's spending "
            "and budget details, and generate exactly 2 short, punchy coach tips. "
            "Highlight budget overruns, large category jumps (e.g. food vs last month), "
            "active subscriptions count, and recommendations to save money."
        )
        prompt = f"Data: {json.dumps(summary_data)}. Return JSON: {{\"insights\": [\"tip1\", \"tip2\"]}}"

        result_json = await self.provider.get_completion(prompt, system_msg)
        if result_json:
            try:
                data = json.loads(result_json)
                return data.get("insights")
            except json.JSONDecodeError:
                pass
        return None

# Dependency Injection helper
def get_ai_service() -> AIService:
    providers = []
    
    # 1. Groq (Primary)
    if settings.GROQ_API_KEY:
        providers.append(GroqProvider())
        
    # 2. GitHub Models (Secondary)
    if settings.GITHUB_TOKEN:
        providers.append(GitHubModelsProvider())
        
    # 3. Rule Engine (Offline Fallback)
    providers.append(RuleEngineProvider())
    
    manager = ProviderManager(providers)
    return AIService(manager)

# Global instance for legacy support (if needed)
ai_service = get_ai_service()
