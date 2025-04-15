# Telegram Invite Link Bot

A Telegram bot with referral, withdrawal, and admin features, deployed on Heroku with MongoDB.

## Setup Instructions

1. Clone the repository.
2. Create a `.env` file based on `.env.example` and fill in your credentials.
3. Install dependencies: `pip install -r requirements.txt`
4. Deploy to Heroku:
   - Link your GitHub repository.
   - Set up Heroku config vars matching `.env`.
   - Deploy the `worker` dyno.
5. Ensure MongoDB is accessible (e.g., MongoDB Atlas).

## Features
- Force-subscribe to up to 4 channels.
- Referral system: Earn 50,000 MMK per 15 referrals (configurable).
- User profiles showing referrals and earnings.
- Admin commands: stats, broadcast, ban/unban users, view users.
- Withdrawal system with KBZ Pay and Wave Pay (admin approval).
- Inline buttons for user interaction.

## Commands
- /start - Start the bot and check subscription status.
- /profile - View your referrals and earnings.
- /withdraw - Request a withdrawal.
- /stats - View total users (admin).
- /broadcast - Broadcast a message (admin).
- /ban_user - Ban a user (admin).
- /unban_user - Unban a user (admin).
- /banned_users - List banned users (admin).
- /users - View bot statistics (admin).