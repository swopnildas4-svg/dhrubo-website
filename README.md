# Dhrubo Website - Deploy guide (Render.com, no credit card)

## 1. Put this on GitHub
Create a new GitHub repo, upload this whole `webapp` folder's contents (app.py, assistant_chat.py,
config.py, requirements.txt, templates/, static/).

## 2. Create a Render account
[render.com](https://render.com) → sign up with GitHub. No credit card needed for the free tier.

## 3. New Web Service
- Dashboard → **New +** → **Web Service**
- Connect your GitHub repo
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Instance Type:** Free

## 4. Add environment variables (Render → your service → Environment)
| Key | Value |
|---|---|
| `GROQ_API_KEY` | your Groq key |
| `GEMINI_API_KEY` | your Gemini key |
| `FLASK_SECRET_KEY` | any random long string |
| `ADMIN_API_KEY` | any random long string (this is what the desktop Settings window uses - keep it secret, different from the chat "identity code") |

## 5. Deploy
Render will build and give you a URL like `https://dhrubo-xxxx.onrender.com`.

## 6. Connect the desktop app
In your desktop `config.py`, add:
```python
WEBSITE_URL = "https://dhrubo-xxxx.onrender.com"
ADMIN_API_KEY = "the same random string you set in step 4"
```
Now the "⚙ Website Settings" link on the launcher screen will be able to reach your site.

## Notes
- Render's free tier sleeps after inactivity and wakes up on the next visit (takes ~30-60s to
  wake up) - normal for a free hobby project, not a bug.
- The website has its own empty `facts.json`/`rules.json` (created fresh on the server) - your
  personal facts from your PC are NOT synced there for privacy. A Swopnil-verified session gets
  Dhrubo's full personality/instructions, just not your private facts database.
- Chat history resets if Render restarts the free instance (normal for free tier) - but the
  `data/chat_log.json` file (used by "Pull new messages") persists across restarts as long as the
  service isn't redeployed.
