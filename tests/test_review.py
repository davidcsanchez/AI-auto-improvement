

import asyncio

import httpx


test_prompts = [
    # --- NIVEL 1: Fáciles (Llama 3B debería acertar) ---
    "I forgot my password and cannot log in.",
    "The login button on the website is completely broken.",
    "Could you add a dark mode to the dashboard?",
    "My monitor won't turn on.",
    "I have a double charge on my credit card this month.",
    "I need a refund for the last billing cycle.",
    "The API is returning a 500 Internal Server Error consistently.",
    "How do I update my profile picture?",
    "My keyboard is missing the Enter key.",
    "Please delete my account and all associated data.",

    # --- NIVEL 2: Trampas de Intención (Llama 3B se confundirá) ---
    "Can you create a feature that stops the app from crashing every 5 minutes?", # Trampa: Parece Feature, es Bug (high).
    "I need access to the database to fix my own invoice.", # Trampa: Access issue vs Billing issue.
    "The physical server in room B is making a weird buzzing noise.", # Trampa: Hardware (medium/high).
    "I want to reset my password but the email never arrives.", # Trampa: Bug report en el backend de emails, no access_issue.
    "Charge me whatever you want, but give me the premium features now.", # Trampa: Billing vs Feature request.
    "Every time I query the API, the frontend goes completely blank.", # Trampa: Backend vs Frontend.
    "Are you guys ever going to fix the typo on the homepage?", # Trampa: Bug report (low).
    "I locked myself out. Take your time though, I am on vacation for 2 weeks.", # Trampa: Access issue, pero Urgency LOW (3B pondrá medium/high).
    "Add a button so I can cancel my subscription myself instead of emailing you.", # Trampa: Feature request vs Billing.
    "The hardware token you sent me is logging me into someone else's account.", # Trampa: Critical Bug/Access (3B podría poner hardware).

    # --- NIVEL 3: Escalado de Manager y Sarcasmo (Llama 3B fallará seguro) ---
    "Your stupid software deleted all my clients. I am calling my lawyers right now, expect a lawsuit.", # Trampa: Critical + requires_manager_escalation=True
    "I just love it when I pay $500 a month to see a white screen. Great job guys.", # Trampa: Bug report + Sarcasmo (manager escalation).
    "If nobody fixes this billing error in 5 minutes, I am cancelling all 50 licenses.", # Trampa: Billing + Critical + Manager escalation.
    "This is the third time I'm asking for a password reset. Is anyone actually working there?", # Trampa: Manager escalation.
    "I found a vulnerability where I can see other users' credit cards.", # Trampa: Bug report + Critical + Backend/Database. (3B podría poner Billing).
    "My boss is literally screaming at me because your database is offline.", # Trampa: Critical + Manager escalation.
    "Whatever you updated yesterday broke my custom reports.", # Trampa: Bug report + Backend.
    "I'm not mad, just disappointed that I got overcharged again.", # Trampa: Billing + Manager escalation (sutil).
    "Can we get a manager to explain why the API rate limits were halved without notice?", # Trampa: Feature/Other + Manager escalation.
    "I will literally pay someone out of my own pocket to come fix this router." # Trampa: Hardware + High + Manager escalation.
]




async def run_tests():
    url = "http://127.0.0.1:8000/process"
    
    async with httpx.AsyncClient() as client:
        for i, prompt in enumerate(test_prompts[:15], 1):
            print(f"Sending ticket {i}/30...")
            try:
                response = await client.post(url, json={"text": prompt}, timeout=10.0)
                if response.status_code == 200:
                    print(f"✅ Success: {response.json()['intent']} - {response.json()['urgency']}")
                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"⚠️ Failed to connect: {e}")
            
            # Pequeña pausa para no saturar al modelo local (3B)
            await asyncio.sleep(12.0)
if __name__ == "__main__":
    asyncio.run(run_tests())