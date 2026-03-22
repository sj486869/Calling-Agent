# 📞 Real-Time Voice AI Agent (VideoSDK + Gemini)

A real-time AI voice assistant that can handle phone calls, built using **VideoSDK Agents** and **Google Gemini Realtime API**.

This project creates a smart assistant that listens, responds, and interacts naturally with users over voice.

---

## 🚀 Features

* 🎙️ Real-time voice interaction
* 🤖 Powered by Google Gemini (low-latency audio model)
* 📞 Phone-call style AI assistant
* ⚡ Fast response with streaming pipeline
* 🔁 Auto-reconnect & retry logic
* 🛠️ Bug fixes for audio stream stability

---

## 🧠 How It Works

* Uses **VideoSDK Agents** to manage sessions
* Uses **Gemini Realtime API** for voice processing
* Handles live audio input/output
* Maintains a conversational flow like a real human

---

## 📁 Project Structure

```
.
├── main.py          # Main entry point
├── ma.py            # Additional logic
├── try.py           # Testing file
├── t.py             # Utility/testing
├── requirements.txt # Dependencies
├── .env             # Environment variables (DO NOT UPLOAD)
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

---

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / Mac
.venv\Scripts\activate      # Windows
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in root folder:

```env
GOOGLE_API_KEY=your_google_api_key
VIDEOSDK_AUTH_TOKEN=your_videosdk_token
```

⚠️ Never upload `.env` to GitHub

---

## ▶️ Run the Project

```bash
python main.py
```

You should see:

```
Starting VideoSDK agent worker...
```

---

## 📞 AI Assistant Behavior

* Greets the caller
* Listens carefully
* Responds concisely and clearly
* Handles unknown queries politely

Example:

```
Hello! I'm your real-time assistant. How can I help you today?
```

---

## 🛠️ Fixes Included

This project includes patches for:

* Audio stream `NoneType` crash
* WebSocket keepalive issues
* Event handling stability

---

## 📌 Requirements

* Python 3.10+
* VideoSDK account
* Google AI (Gemini API key)

---

## 🔥 Future Improvements

* Add call recording
* Add multi-language support
* Deploy on cloud (AWS / GCP)
* Integrate with Twilio

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first.

---

## 📄 License

This project is for educational purposes.

---

## 👨‍💻 Author

Suman Jana
