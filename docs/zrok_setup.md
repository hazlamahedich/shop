# Permanent Tunnel Setup (zrok)

This project uses **zrok** to provide a persistent local tunnel. Unlike ngrok (free tier) or Cloudflare (quick tunnels), zrok allows you to have the **same URL** every time you restart your tunnel.

## 🛠 One-Time Setup

To get your permanent URL, you must complete this brief activation:

1. **Invite Yourself** (Free)
   Run this in your terminal:
   ```bash
   zrok invite
   ```
   Enter your email. You will receive an invitation link.

2. **Set Password**
   Click the link in your email and set a password for your zrok account.

3. **Enable Account**
   Copy the `zrok enable <token>` command from your zrok dashboard (it appears after you set your password) and run it in your terminal.

## 🚀 Starting the Tunnel

Once activated, simply run the management script. It will automatically handle the reservation and update your `backend/.env` file for you.

```bash
chmod +x scripts/start_permanent_tunnel.sh
./scripts/start_permanent_tunnel.sh
```

## 🔒 Benefits
- **Fixed URL**: Use `https://shop-dev-persis-username.share.zrok.io` forever.
- **No Domain Needed**: You don't need to buy a domain name.
- **Auto-Update**: The script automatically keeps your `.env` in sync.
