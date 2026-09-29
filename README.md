# 🤖 XARTECH Client Visit Management Telegram Bot

Field Interns & Agents ke client visits ko bina kisi confusion ke track, record aur manage karne ke liye complete automated Telegram Bot solution.

---

## ✨ Key Features

### 👤 1. Field Agent / Intern Flow
- **Secure ID & Password Login**: Admin dwara banayi gayi ID se login.
- **Session Auto-Save**: Baar-baar login karne ki jaroorat nahi.
- **Sequential Visit Recording**:
  1. **Shop Name** (Dukaan / Business ka naam)
  2. **Owner / Contact Person Name** *(Skip option available)*
  3. **Mobile Number** (Auto-cleaned digits)
  4. **Shop Front Photo** 📸 (Telegram se high-res photo download ho kar database me link hoti hai)
  5. **Visiting Card Photo** 🪪 *(Skip option available)*
  6. **Location / Address** 📍 (Telegram GPS share button ya type kiya hua address)
  7. **Remarks / Client Requirements** 📝 (Deal notes, follow-up date, etc.)
  8. **Final Review & 'OK' / 'Confirm' Button** -> Server & Database par save ho jata hai!
- **Fast Next Shop Visit**: Bas `🏪 New Shop Visit` button ya `/new_visit` dabayein aur agli dukan ka data feed karein.

---

### ⚡ 2. Admin Control Panel (`/admin`)
- **Master Admin Login**: Default username: `admin` | Password: `xartech@123`
- **➕ Add New Agent**: Interns/Employees ke liye unique Username & Password generate karein.
- **👥 List & Manage Agents**: Kisi bhi agent ko 1-tap me Activate ya Deactivate karein.
- **📊 4 Formats me Reports Download**:
  1. 🌐 **Interactive HTML Report**: Single self-contained file jisme saari photos Base64 embedded hain (Bina internet ke bhi open hoti hai, live search bar, zoom modal, aur print button ke sath).
  2. 📑 **Formatted PDF Report**: Clean printable cards jisme shop photo, card photo, agent info aur metadata rehta hai.
  3. 📊 **Excel Sheet (.xlsx)**: Har cell me thumbnail photo embed rehti hai sath me saare data columns.
  4. 🗂️ **Complete ZIP Package**: Excel + HTML + Har shop ke naam se bane organized photo folders.
- **Time & Agent Filters**: All Time, Today's Visits, Past 7 Days, ya kisi specific Agent ka data download karein.

---

## 🚀 Setup & Running Instructions

### Step 1: Add your Telegram Bot Token
1. Telegram open karein aur **[@BotFather](https://t.me/BotFather)** par jayein.
2. `/newbot` command dekar apna bot banayein aur **HTTP API Token** copy karein.
3. [`.env`](file:///c:/Users/DHRUV/Desktop/Xartech%20bot/.env) file ko open karein aur apna token paste karein:
```env
BOT_TOKEN=your_telegram_bot_token_here
```

### Step 2: Run the Bot
- **Windows Double-Click**: [`start_bot.bat`](file:///c:/Users/DHRUV/Desktop/Xartech%20bot/start_bot.bat) file par double-click karein.
- **Ya Terminal Se**:
```powershell
python bot.py
```

---

## 🔑 Default Login Credentials
- **Admin**:
  - Username: `admin`
  - Password: `xartech@123`
- **Created Agents**: Admin panel (`/admin` -> `➕ Add New Agent`) se admin nayi IDs banakar interns ko de sakta hai.
