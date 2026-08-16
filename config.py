import os

# Render/Hugging Face-এ এগুলো "Environment Variables" / "Secrets" হিসেবে সেট করবে,
# কখনো এই ফাইলে সরাসরি key লিখবে না (public repo হলে key leak হয়ে যাবে)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
