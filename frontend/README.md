# Insurance Assistant - Web Chat Interface

Simple HTML/CSS/JavaScript chat interface for the Insurance Assistant.

## Features

- 🗨️ **Simple Chat Interface** - No React, just plain HTML/CSS/JavaScript
- 📄 **Document Upload** - Upload travel documents via button
- 💬 **Real-time Chat** - Send messages and get AI responses
- 🎨 **Beautiful Design** - Modern gradient design with smooth animations
- 📱 **Responsive** - Works on desktop and mobile

## Setup

### 1. Start Backend Server

```bash
cd backend
python app/main.py
```

Backend runs on `http://localhost:8000`

### 2. Open the Web Page

Simply open `index.html` in your web browser:

**Option A: Double-click the file**
- Navigate to `frontend/index.html`
- Double-click to open in default browser

**Option B: Use a local server (recommended)**
```bash
# Using Python
cd frontend
python -m http.server 3000

# Then open: http://localhost:3000
```

**Option C: Live Server extension**
- If you use VS Code, install "Live Server" extension
- Right-click `index.html` → "Open with Live Server"

## How It Works

### The HTML File Contains Everything:

1. **HTML Structure** - Chat container, header, messages area, input area
2. **CSS Styles** - All styling is in `<style>` tag (no separate CSS file)
3. **JavaScript Code** - All logic is in `<script>` tag (no separate JS file)

### Key Functions:

- `startConversation()` - Gets initial greeting from backend
- `sendMessage()` - Sends user message and receives bot response
- `addMessage()` - Displays message in chat
- `handleFileUpload()` - Uploads documents for extraction
- `changePersona()` - Switches conversation style

### API Communication:

The page communicates with the backend API at `http://localhost:8000/api`:
- `POST /api/conversation/start` - Start conversation
- `POST /api/conversation/message` - Send message
- `POST /api/document/extract` - Upload document

## File Structure

```
frontend/
└── index.html    # Everything is in this single file!
```

That's it! One file contains everything.

## Customization

### Change Colors

Edit the CSS in the `<style>` tag:
```css
/* Change gradient colors */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to your colors */
background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
```

### Change API URL

Edit the JavaScript variable:
```javascript
const API_BASE = 'http://localhost:8000/api';
// Change to your backend URL
```

### Add Features

All code is in the same file, so you can easily:
- Add new buttons
- Modify message styling
- Add new functions
- Integrate more API endpoints

## Troubleshooting

**Can't connect to backend?**
- Make sure backend is running on port 8000
- Check browser console for errors
- Verify API_BASE URL is correct

**CORS errors?**
- Backend already has CORS enabled for all origins
- If issues persist, check backend CORS settings

**Messages not appearing?**
- Check browser console (F12) for JavaScript errors
- Verify backend is running and responding

## Browser Compatibility

Works on:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers

## No Build Step Required!

Unlike React apps, this is just plain HTML/CSS/JavaScript:
- ✅ No npm install
- ✅ No build process
- ✅ No dependencies
- ✅ Just open the file!

