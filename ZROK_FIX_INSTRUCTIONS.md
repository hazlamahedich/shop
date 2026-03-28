# 🔧 Fix Zrok Tunnel - Quick Steps

## Issue
Zrok environment was disabled and needs to be re-enabled.

## Solution

### Step 1: Enable Zrok (Do this in your terminal)

Open a new terminal window and run:

```bash
zrok enable
```

This will open a browser window. If you don't have your token:
1. Go to https://api-v1.zrok.io
2. Log in with your account
3. Copy your enable token from the dashboard
4. Paste it in the terminal when prompted

### Step 2: Start the Tunnel

Once enabled, run the tunnel script:

```bash
cd /Users/sherwingorechomante/shop
bash scripts/start_permanent_tunnel.sh
```

Your permanent URL will be: `https://shopdevsherwingor.share.zrok.io`

### Step 3: Verify it Works

In a new terminal:

```bash
curl https://shopdevsherwingor.share.zrok.io/api/v1/widget/faq-buttons/1
```

You should see JSON with FAQ buttons.

### Step 4: Test Widget on Portfolio Site

1. Open your portfolio site: https://portfolio-website-phi-brown.vercel.app
2. Open browser console (F12)
3. Check for the widget in bottom-right corner
4. Widget should now be visible!

## Alternative: Quick Start (If You Have Your Token)

If you have your zrok enable token, you can run:

```bash
zrok enable YOUR_TOKEN_HERE
bash scripts/start_permanent_tunnel.sh
```

## Need Help?

If you don't remember your token or have trouble logging in:
1. Run: `zrok invite`
2. Check your email for invitation link
3. Set up your account
4. Get your enable token from the dashboard
