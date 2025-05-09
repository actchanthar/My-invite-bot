# Anime ACT Bot

A Telegram bot with referral and withdrawal features, deployed on Heroku.

## Deployment Instructions

1. **Fork this repository** on GitHub.
2. **Create a Heroku app**:
   - Go to [Heroku Dashboard](https://dashboard.heroku.com/apps).
   - Click "New" > "Create new app".
   - Choose a name (e.g., `anime-act-bot`).
3. **Link GitHub repository**:
   - In Heroku, go to the "Deploy" tab.
   - Connect your GitHub account and select the forked repository.
4. **Set environment variables**:
   - Go to the "Settings" tab in Heroku.
   - Click "Reveal Config Vars".
   - Add the following (use values from your `.env.example`):
     ```
     BOT_TOKEN=6977715954:AAFEWxWP8ALPNRtdduhWnzG6oFYMaSmCluk
     MONGODB_URI=mongodb+srv://2234act:2234act@cluster0.rwjacbj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
     APP_ID=25255650
     API_HASH=8eeadfa8f9b832d18657a63585b75bc0
     ADMIN_ID=5062124930
     LOG_CHANNEL=-1002555129360
     FORCE_SUB_CHANNELS=-1002097823468
     ```
5. **Deploy the bot**:
   - Go back to the "Deploy" tab.
   - Select the `main` branch and click "Deploy Branch".
6. **Enable the worker**:
   - Go to the "Resources" tab in Heroku.
   - Turn on the `worker` dyno (`python bot.py`).

## Commands

- `/start` - Start the bot and view your profile.
- `/withdraw` - Withdraw MMK (minimum 1000, maximum 20000 per day).
- `/stats` - View total users (admin only).
- `/broadcast` - Broadcast a message (admin only).
- `/ban_user` - Ban a user (admin only).
- `/unban_user` - Unban a user (admin only).
- `/banned_users` - List banned users (admin only).
- `/users` - View bot statistics (admin only).
- `/add_bonus` - Add MMK to a user's balance (admin only).
- `/set_referral_reward` - Set custom referral rewards for a user (admin only).