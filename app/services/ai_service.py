"""
app/services/ai_service.py
─────────────────────────────────────────────────────────────────────────────
AI integration for transaction categorization using Azure OpenAI or GitHub Models.
"""

import json
import logging
from typing import Optional, Dict
from openai import AsyncAzureOpenAI, AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.enabled = settings.AI_ENABLED
        self.client = None
        self.model = None

        if not self.enabled:
            return

        # Priority 1: GitHub Models (using provided PAT)
        if settings.GITHUB_TOKEN:
            logger.info("AI Service: Initializing with GitHub Models")
            self.client = AsyncOpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=settings.GITHUB_TOKEN
            )
            self.model = settings.GITHUB_MODEL_NAME

        # Priority 2: Azure OpenAI
        elif settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            logger.info("AI Service: Initializing with Azure OpenAI")
            self.client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version="2024-02-15-preview"
            )
            self.model = settings.AZURE_OPENAI_DEPLOYMENT

        else:
            logger.warning("AI Service enabled but no credentials (GitHub or Azure) found.")
            self.enabled = False

    async def categorize_transaction(self, merchant: str, amount: float, raw_text: str) -> Optional[Dict[str, str]]:
        """
        Determines the best category for a transaction using LLM.
        Returns a dict with 'category' and 'reason'.
        """
        if not self.enabled or not self.client:
            return None

        prompt = f"""
        You are a financial expert. Categorize this Indian transaction into one of these EXACT categories:
        Food, Shopping, Bills, Transport, Entertainment, Health, Investment, or Others.

        Merchant: {merchant}
        Amount: ₹{amount}
        Full Text: "{raw_text}"

        Return ONLY a JSON object: {{"category": "category_name", "reason": "short_reason"}}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )

            content = response.choices[0].message.content.strip()
            # Clean possible markdown formatting if the model wraps JSON in ```json
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()

            result = json.loads(content)
            logger.info(f"AI Categorized '{merchant}' as {result.get('category')}")
            return result
        except Exception as e:
            logger.error(f"AI Service Error: {e}")
            return None

# Singleton instance
ai_service = AIService()
