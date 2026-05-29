import asyncio

from src.config.settings import get_settings
from src.core.sqlite_storage import SQLiteTicketStorage
from src.models.golden_sample import GoldenSample
from src.models.prompt_version import PromptVersion
from src.models.schemas import SupportTicketResponse


async def seed_database() -> None:
    settings = get_settings()
    storage = SQLiteTicketStorage()

    prompt = PromptVersion(
        parent_prompt_id=None,
        content=settings.INITIAL_PROMPT,
        version_number=1,
        is_active=True,
        triggering_sample_ids="[]",
        regression_passed=None,
        base_passed=None,
        base_total=None,
        failed_cases="[]",
    )

    await storage.save_prompt(prompt)

    samples = [
        (
            "I forgot my password and cannot log in.",
            SupportTicketResponse(
                intent="access_issue",
                urgency="medium",
                affected_component="frontend",
                requires_manager_escalation=False,
            ),
        ),
        (
            "My laptop screen is cracked after a fall.",
            SupportTicketResponse(
                intent="other",
                urgency="high",
                affected_component="hardware",
                requires_manager_escalation=False,
            ),
        ),
        (
            "The app crashes when I upload a PDF.",
            SupportTicketResponse(
                intent="bug_report",
                urgency="high",
                affected_component="backend_api",
                requires_manager_escalation=False,
            ),
        ),
        (
            "Please add two-factor authentication to my account.",
            SupportTicketResponse(
                intent="feature_request",
                urgency="low",
                affected_component="backend_api",
                requires_manager_escalation=False,
            ),
        ),
        (
            "I've been charged twice and I will sue if this isn't fixed NOW!",
            SupportTicketResponse(
                intent="billing_issue",
                urgency="critical",
                affected_component="database",
                requires_manager_escalation=True,
            ),
        ),
    ]

    for input_text, response in samples:
        golden_sample = GoldenSample(
            input_text=input_text,
            output_json=response.model_dump_json(),
            is_base_case=True,
        )
        await storage.save_golden_sample(golden_sample)

    print("Database seeded successfully with 1 prompt and 5 golden samples.")


def initialize_database() -> None:
    asyncio.run(seed_database())
