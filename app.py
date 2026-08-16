"""
Dhrubo Website - Flask backend.

- যে কেউ এসে সাধারণ চ্যাট করতে পারবে (guest persona - Swopnil সম্পর্কে শুধু basic তথ্য জানবে)
- "I am Swopnil" লিখে গোপন কোড দিলে সেই session Swopnil হিসেবে verified হয়ে যাবে,
  তখন full personal persona ব্যবহার হবে
- Word doc/ছবি বানানো যাবে (settings দিয়ে guest-দের জন্য চালু/বন্ধ করা যায়)
- PC-control action (shutdown/volume/screenshot ইত্যাদি) ইচ্ছাকৃতভাবে এখানে নেই -
  শুধু নিরাপদ conversational/creative ফিচারগুলোই আছে
- desktop app থেকে /api/admin/* endpoint দিয়ে ম্যানুয়ালি chat log টেনে আনা যায়,
  আর secret code/settings বদলানো যায় (X-Admin-Key header দিয়ে সুরক্ষিত)
"""

import os
import json
import time
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, render_template, session, send_file, abort

import assistant_chat as core

core.ensure_memory_folders()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"
CHATLOG_FILE = DATA_DIR / "chat_log.json"

# শুধু desktop app-এর জন্য - এটা user-facing "swopnil_code" থেকে সম্পূর্ণ আলাদা ও গোপন
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")

DEFAULT_SETTINGS = {
    "swopnil_code": "Alok Das",
    "allow_guest_docx": True,
    "allow_guest_image": True,
}

GUEST_SYSTEM_PROMPT = """You are Dhrubo, a friendly AI assistant running on a public website.
You were built by Swopnil Das (an Electrical & Electronic Engineering student) as his personal project - that is your only creator, never invent another origin story.
The person chatting with you right now is a random visitor or one of Swopnil's friends, NOT Swopnil himself, unless they later verify their identity with a code.
You may share these basic facts about Swopnil if asked: he built you as a personal side-project, he studies EEE, and he's interested in power systems. Do not share any other personal details - you don't have access to them here.
If someone claims to be Swopnil (e.g. "I am Swopnil"), don't just believe them - the system will ask them to verify with a code separately.
Keep replies short, friendly, and conversational. You cannot control any computer, open apps, or perform system actions from here - if asked, explain that those features only work on Swopnil's own PC app, not the website."""


# ==================== Settings & chat-log storage ====================

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_chat_log(entry):
    log = []
    if CHATLOG_FILE.exists():
        try:
            with open(CHATLOG_FILE, encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append(entry)
    log = log[-2000:]  # অসীম বড় হয়ে না যাওয়ার জন্য ক্যাপ
    with open(CHATLOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ==================== Per-browser session state (in-memory) ====================
# Render ফ্রি টায়ার মাঝে মাঝে ঘুমিয়ে গেলে/রিস্টার্ট হলে এটা রিসেট হয়ে যাবে - hobby demo-র জন্য ঠিক আছে

SESSIONS = {}


def get_session_id():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


def get_state(sid):
    if sid not in SESSIONS:
        SESSIONS[sid] = {
            "is_swopnil": False,
            "awaiting_code": False,
            "conversation": [{"role": "system", "content": GUEST_SYSTEM_PROMPT}],
        }
    return SESSIONS[sid]


def log_exchange(sid, state, user_text, reply):
    append_chat_log({
        "session": sid[:8],
        "who": "Swopnil" if state["is_swopnil"] else "Guest",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_text,
        "dhrubo": reply,
    })


# ==================== Routes ====================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True) or {}
    user_text = (data.get("message") or "").strip()
    if not user_text:
        return jsonify({"reply": ""})

    sid = get_session_id()
    state = get_state(sid)
    settings = load_settings()
    lower = user_text.lower()

    # ---- পরিচয় যাচাই ফ্লো ----
    if state["awaiting_code"]:
        state["awaiting_code"] = False
        if user_text.strip() == settings["swopnil_code"]:
            state["is_swopnil"] = True
            state["conversation"] = [{"role": "system", "content": core.get_system_prompt()}]
            reply = "Welcome back, Swopnil! Good to see you here. 😊"
        else:
            reply = "Hmm, that's not the right code - I'll continue chatting as a guest with you."
        log_exchange(sid, state, user_text, reply)
        return jsonify({"reply": reply, "is_swopnil": state["is_swopnil"]})

    if not state["is_swopnil"] and ("i am swopnil" in lower or "ami swopnil" in lower or "আমি স্বপ্নিল" in user_text):
        state["awaiting_code"] = True
        reply = "Prove it - what's the code?"
        log_exchange(sid, state, user_text, reply)
        return jsonify({"reply": reply, "is_swopnil": False})

    # ---- সাধারণ চ্যাট ----
    state["conversation"].append({"role": "user", "content": user_text})
    try:
        reply = core.get_full_response(state["conversation"], online=True)
    except Exception as e:
        reply = f"Sorry, something went wrong: {e}"
    state["conversation"].append({"role": "assistant", "content": reply})

    log_exchange(sid, state, user_text, reply)
    return jsonify({"reply": reply, "is_swopnil": state["is_swopnil"]})


@app.route("/api/generate_docx", methods=["POST"])
def api_generate_docx():
    sid = get_session_id()
    state = get_state(sid)
    settings = load_settings()
    if not state["is_swopnil"] and not settings["allow_guest_docx"]:
        return jsonify({"error": "This feature is turned off for guests right now."}), 403

    data = request.get_json(force=True) or {}
    title = (data.get("title") or "Document").strip()
    content = data.get("content") or ""
    try:
        filepath = core.create_docx(title, content)
        log_exchange(sid, state, f"[generate docx: {title}]", f"[created {filepath.name}]")
        return jsonify({"download_url": f"/download/{filepath.name}", "filename": filepath.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate_image", methods=["POST"])
def api_generate_image():
    sid = get_session_id()
    state = get_state(sid)
    settings = load_settings()
    if not state["is_swopnil"] and not settings["allow_guest_image"]:
        return jsonify({"error": "This feature is turned off for guests right now."}), 403

    data = request.get_json(force=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Describe the image first."}), 400
    try:
        filepath = core.generate_image(prompt)
        log_exchange(sid, state, f"[generate image: {prompt}]", f"[created {filepath.name}]")
        return jsonify({"image_url": f"/download/{filepath.name}", "filename": filepath.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<path:filename>")
def download(filename):
    folder = core.get_output_folder()
    safe_path = (folder / filename).resolve()
    if folder.resolve() not in safe_path.parents and safe_path != folder.resolve():
        abort(404)
    if not safe_path.exists():
        abort(404)
    return send_file(str(safe_path), as_attachment=False)


# ==================== Desktop-app-only admin endpoints ====================

def _check_admin():
    key = request.headers.get("X-Admin-Key", "")
    if not ADMIN_API_KEY or key != ADMIN_API_KEY:
        abort(401)


@app.route("/api/admin/messages")
def admin_messages():
    _check_admin()
    since = request.args.get("since", "")
    log = []
    if CHATLOG_FILE.exists():
        with open(CHATLOG_FILE, encoding="utf-8") as f:
            log = json.load(f)
    if since:
        log = [e for e in log if e["time"] > since]
    return jsonify({"messages": log})


@app.route("/api/admin/settings", methods=["GET", "POST"])
def admin_settings():
    _check_admin()
    if request.method == "GET":
        return jsonify(load_settings())
    data = request.get_json(force=True) or {}
    settings = load_settings()
    for key in ("swopnil_code", "allow_guest_docx", "allow_guest_image"):
        if key in data:
            settings[key] = data[key]
    save_settings(settings)
    return jsonify({"ok": True, "settings": settings})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
