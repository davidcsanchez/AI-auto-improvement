import asyncio

from src.core.sqlite_storage import SQLiteTicketStorage
from src.models.golden_sample import GoldenSample
from src.models.prompt_version import PromptVersion
from src.models.schemas import SupportTicketResponse


async def seed_database() -> None:
    storage = SQLiteTicketStorage()

    prompt = PromptVersion(
        parent_prompt_id=None,
        content = (
            "You are an IT support ticket classifier.\n\n"
            
            "1. INTENT Classification: Choose exactly one:\n"
            "   [bug_report, feature_request, access_issue, billing_issue, other]\n\n"
            
            "2. URGENCY Classification: Choose exactly one:\n"
            "   [low, medium, high, critical]\n\n"
            
            "3. AFFECTED COMPONENT: Choose exactly one:\n"
            "   [frontend, backend_api, database, hardware, unknown]\n\n"
            
            "4. ESCALATION RULE (requires_manager_escalation):\n"
            "   - DEFAULT VALUE: false\n"
            "   - Set to true IF AND ONLY IF the text contains explicit anger, insults, "
            "threats to leave the company, or mentions of legal action.\n"
            "   - CRITICAL: Do NOT set to true for severe technical bugs, broken hardware, "
            "or critical system outages unless the tone itself is angry or threatening. "
            "A PC not turning on is high urgency, but requires_manager_escalation must remain false.\n\n"
            
            "Return only JSON matching the requested schema."
        ),
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


def main() -> None:
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()