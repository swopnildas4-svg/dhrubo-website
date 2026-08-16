import os

# Render/Hugging Face-এ এগুলো "Environment Variables" / "Secrets" হিসেবে সেট করবে,
# কখনো এই ফাইলে সরাসরি key লিখবে না (public repo হলে key leak হয়ে যাবে)
GROQ_API_KEY = os.environ.get("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", "")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6KhtU7na-nMH9TSNoYFww8Q7NqwjGnH_URU0oeO0tEtpg", "")
