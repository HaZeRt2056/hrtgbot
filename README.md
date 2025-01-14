# Telegram Bot for Job Applications

## 📚 About the Project
This Telegram bot was developed for a company to streamline job applications by integrating with Trello. Users can easily browse vacancies, submit their resumes, and track the process, while administrators can manage regions and job openings with ease.

### Key Features
1. **User Mode**:
   - Select one of three countries.
   - Choose a region within the selected country.
   - View available vacancies in the region.
   - Submit an application by filling out a form:
     - Full Name
     - Age
     - Work experience
     - Current location
     - Previous workplaces
     - Photo upload
   - Once submitted, the application is automatically sent to a Trello board.

2. **Admin Mode**:
   - Secure login with a password.
   - Manage available regions (add/delete).
   - Manage job vacancies with descriptions (add/delete).

---

## 🌐 How It Works

### User Workflow:
- The user initiates a conversation with the bot.
- The bot guides the user through country and region selection.
- The user views vacancies and submits an application.
- The application data is sent to the designated Trello board.

### Admin Workflow:
- The admin logs in with a secure password.
- Admins can update the list of regions and vacancies in real time.

---

## 📂 Project Structure
| File/Folder         | Description                                       |
|----------------------|---------------------------------------------------|
| `TGbotforhr/`       | Root directory of the project                     |
| `bot_data.db`| SQLite database for storing bot data              |
| `admin_handlers.py` | Handlers for admin-specific actions            |
| `configs.py`     | Configuration file (e.g., API keys, bot token)    |
| `database.py`    | Database interaction logic                        |
| `keyboards.py`   | Inline and reply keyboards for user interactions  |
| `main.py`        | Entry point for the bot                           |
| `messages.py`    | Predefined bot messages and templates(coming soon)             |
| `setup_database.py` | Script to initialize the database              |
| `urls.py`        | Trello API endpoints or other external URLs       |

## 🔄 Integrations
- **Trello API**: Automates adding user applications to the Trello board.
- **Telegram Bot API**: Enables interaction with users and admins.

---

## 🔧 Installation

Clone the repository:
   ```bash
   git clone https://github.com/your-username/telegram-job-bot.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the bot:
Update configs.py with your Telegram Bot Token and Trello API keys.

Run the bot:
```bash
python main.py
```

## 🔧 Contributions
Contributions are welcome! Feel free to open issues or submit pull requests to improve the bot.

---

## 🚀 Future Improvements
- Add support for multiple languages.
- Integrate notifications for users about application status.
- Add analytics for admins to track application metrics.

---

## 💪 Support
If you find this bot useful, give it a star! 🌟

