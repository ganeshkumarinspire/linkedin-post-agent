# LinkedIn Developer App Setup

Follow these steps once to get your `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_URN`.

---

## Step 1 — Create a LinkedIn Developer App

1. Go to https://developer.linkedin.com
2. Click **Create App**
3. Fill in:
   - **App name**: `LinkedIn Post Agent` (or anything)
   - **LinkedIn Page**: link it to your personal LinkedIn page (required)
   - **App logo**: upload any square image
4. Click **Create App**

---

## Step 2 — Configure OAuth 2.0

1. In your new app, open the **Auth** tab
2. Under **OAuth 2.0 Settings → Authorized redirect URLs**, add:
   ```
   http://localhost:8000/callback
   ```
3. Copy your **Client ID** and **Client Secret** — add them to `.env`

---

## Step 3 — Request the Required Product

LinkedIn gates posting behind the **Share on LinkedIn** product.

1. In the app, open the **Products** tab
2. Click **Request Access** next to **Share on LinkedIn**
3. Fill in the short form — approval is usually instant for personal use

This unlocks the `w_member_social` OAuth scope you need to post.

---

## Step 4 — Generate Your Access Token (one-time manual step)

LinkedIn's OAuth requires a browser redirect. Run this once:

### 4a. Build the authorization URL

Replace `YOUR_CLIENT_ID` and open this URL in your browser:

```
https://www.linkedin.com/oauth/v2/authorization
  ?response_type=code
  &client_id=YOUR_CLIENT_ID
  &redirect_uri=http://localhost:8000/callback
  &scope=openid%20profile%20w_member_social
```

(Put it all on one line in your browser.)

### 4b. Authorize and capture the code

Log in, approve the permissions, and LinkedIn redirects you to:
```
http://localhost:8000/callback?code=AQXXXXXXXX...
```

Copy the `code` value from the URL.

### 4c. Exchange code for access token

Run this in your terminal (replace the placeholders):

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=PASTE_YOUR_CODE_HERE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=http://localhost:8000/callback"
```

The response contains `access_token` — copy it into `.env`.

> **Token lifetime**: 60 days. Re-run step 4 every two months.

---

## Step 5 — Get Your Person URN

Run this once with your token:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.linkedin.com/v2/userinfo
```

The `sub` field is your person ID. Your URN is `urn:li:person:<sub_value>`.
Add it to `.env` as `LINKEDIN_PERSON_URN=urn:li:person:XXXXXXXX`.

---

## Step 6 — Final .env file

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_60_day_token
LINKEDIN_PERSON_URN=urn:li:person:XXXXXXXX
```

---

## Step 7 — Install & Run

```bash
cd linkedin-post-agent
pip install -r requirements.txt

# One-shot post (test):
python agent.py

# Automated scheduler (Tue/Wed/Thu at 08:00 Paris time):
python scheduler.py
```

Keep `scheduler.py` running in the background (e.g., in a `tmux` session, a systemd service, or a cloud VM).
