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
| `WHATSAPP_API_KEY` | a third random long string, different from the other two - only MacroDroid on your phone will know this |

## 7. Turn the site into an installable phone app (PWA)
Two new files (`static/manifest.json`, `static/service-worker.js`) plus small edits to
`templates/index.html` make Chrome on Android offer "Install app" / "Add to Home screen" -
after that it opens full-screen with its own icon, just like a normal app.

You still need to add two icon image files to `static/`:
- `static/icon-192.png` (192x192)
- `static/icon-512.png` (512x512)

Export these from your existing `dhrubo_ai.ico` or the character art (any square PNG works -
an online ico-to-png/resizer site can do this for free, no install needed).

Once deployed, open `https://dhrubo-website.onrender.com` in Chrome on your phone → menu (⋮) →
**"Install app"**. That's the whole "app install" step - no APK, no Android Studio, no Play Store.

If you want an actual `.apk` file instead (e.g. to install without opening Chrome first), feed
this same URL into [pwabuilder.com](https://www.pwabuilder.com) (free, no account needed) - it
packages the PWA into a signed APK you can download and install directly.

## 8. WhatsApp auto-reply (MacroDroid on your phone)
A new endpoint `/api/whatsapp/reply` is ready for this - it always replies with your full
Dhrubo persona (facts/rules included), introduces itself as Dhrubo, and never claims to be you.

In MacroDroid, build one macro:
- **Trigger:** Notification received → WhatsApp
- **Action 1:** Wait 2 minutes
- **Condition:** you haven't replied in that chat yourself (see MacroDroid's "cancel on new trigger"
  pattern - re-triggering the same macro when you send a message yourself, which then stops the
  waiting instance)
- **Action 2:** HTTP Request → POST to `https://dhrubo-website.onrender.com/api/whatsapp/reply`
  - Header: `X-Whatsapp-Key: <the WHATSAPP_API_KEY you set above>`
  - Body (JSON): `{"contact_id": "<sender name>", "text": "<the message text>"}`
- **Action 3:** Take the `reply` field from the response and use WhatsApp's "reply to notification"
  action to send it
- **Action 4:** Send yourself a local notification: "Dhrubo replied for you"

You (or the PC admin panel via `/api/admin/settings`) can turn this off anytime by setting
`whatsapp_autoreply_enabled` to `false` - no redeploy needed.

## 9. Render free tier waking up
The free tier sleeps after ~15 minutes of no traffic and takes 30-60s to wake on the first
request after that - so the very first WhatsApp auto-reply or app open after a quiet period will
be slow once. This is normal for the free tier; a workaround (optional, still free) is a service
like [cron-job.org](https://cron-job.org) pinging `/api/welcome` every 10 minutes to keep it awake.

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
