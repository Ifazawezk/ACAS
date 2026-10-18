# 🍎 ACAS iPad App Installation Guide

## What You Get

Your ACAS system is now a **Progressive Web App (PWA)** that works on your iPad just like a native app!

### Features:
✅ **Installs on Home Screen** - Tap to launch like any app  
✅ **Offline Support** - Works without internet (with data caching)  
✅ **Full Screen App** - No browser chrome when installed  
✅ **Fast Launch** - Cached assets load instantly  
✅ **Background Sync** - Queues actions when offline  
✅ **Responsive Design** - Perfect on iPad Pro, Air, or Mini  

---

## 📱 Installation on iPad (3 Steps)

### Step 1: Open Safari and Navigate
1. Open **Safari** on your iPad
2. Enter URL: `http://127.0.0.1:8000/frontend/login.html`
   - OR bookmark if server is on laptop: `http://[YOUR-LAPTOP-IP]:8000/frontend/login.html`
3. Wait for the page to load completely

### Step 2: Install as App
1. Tap the **Share button** (⬆️ in bottom toolbar)
2. Scroll down and select **"Add to Home Screen"**
3. In the dialog that appears:
   - **Title**: "ACAS" (or whatever you prefer)
   - **URL**: Automatically filled
   - Tap **"Add"** button

### Step 3: Launch & Login
1. iPad home screen now has **"ACAS"** app icon
2. Tap icon to open in full-screen app mode
3. Login with: **admin / admin@123**
4. You're done! 🎉

---

## 🔧 Configuration for Local Network Access

If your ACAS server is running on a desktop/laptop (not iPad):

### Option A: Same WiFi Network (Recommended)
1. On your laptop/desktop, find your IP address:
   - **Windows**: Open Command Prompt → `ipconfig` → look for "IPv4 Address"
   - **Mac**: System Preferences → Network → see IP address
   - Example: `192.168.1.100`

2. On iPad, use full URL:
   ```
   http://192.168.1.100:8000/frontend/login.html
   ```

3. Tap "Add to Home Screen" as normal

### Option B: Local Server Hostname
If your laptop has hostname `mohan-laptop`:
```
http://mohan-laptop.local:8000/frontend/login.html
```

### Option C: External Access (for testing on different networks)
1. Use ngrok tunnel (if configured):
   ```
   ngrok http 8000
   ```
2. Use the ngrok public URLs starting with `https://`

---

## 🌐 Server Configuration

### For Local Network (Private IP - `192.168.x.x`)

**Edit** `app/main.py`:
```python
# Allow requests from local network
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://192.168.*",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then restart server:
```bash
python start_server.py
```

### For HTTPS (Production)
1. Get SSL certificate (Let's Encrypt)
2. Update FastAPI to use SSL:
   ```bash
   uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
   ```

---

## 📱 Usage Guide - iPad App Mode

### Launch
- Tap ACAS icon on home screen
- App opens in full screen (no Safari address bar)

### Navigation
- Use sidebar menu on left (or hamburger ☰ on small screens)
- All features work exactly like web version
- Share button for exporting data

### Gestures
- **Swipe left/right**: Navigate sections  
- **Pinch to zoom**: On charts (if needed)
- **Long press**: On items for quick actions
- **Shake device**: Bounce action (if enabled)

### Keyboard Shortcuts (iPad with keyboard)
```
Cmd + H  → Go to home
Cmd + R  → Refresh
Cmd + W  → Close app
```

### Offline Usage
- ✅ Dashboard loads from cache
- ✅ Comments display from cached data
- ✅ New actions queue automatically
- ❌ Cannot reach server APIs when offline
- ⚠️ Syncs when connection restored

---

## 🎨 Customization

### Change App Name
Edit `frontend/manifest.json`:
```json
{
  "name": "YOUR APP NAME",
  "short_name": "SHORT NAME",
  "description": "Your description"
}
```

### Change App Icon
1. Create image: 192x192 pixels, PNG format
2. Save as: `frontend/icons/icon-192x192.png`
3. Create 512x512 version too
4. Resize icons to needed sizes:
   - 192x192 (home screen)
   - 512x512 (splash screen)
   - 1024x1024 (additional)

### Change Theme Color
Edit `frontend/manifest.json`:
```json
{
  "theme_color": "#1F77C2",      // Your brand color
  "background_color": "#ffffff"
}
```

---

## 🔍 Troubleshooting

### "App Won't Install"
**Problem**: "Add to Home Screen" not appearing
- **Solution**: 
  - Make sure page fully loaded (wait 3-5 seconds)
  - Try refreshing (Cmd + R)
  - Clear Safari cache: Settings → Safari → Clear History and Website Data
  - Make sure using Safari (not Chrome)

### "Can't Connect to Server"
**Problem**: "Connection failed" error
- **Check 1**: Server still running?
  ```bash
  python start_server.py
  ```
- **Check 2**: Using correct IP?
  ```bash
  # On Windows: ipconfig
  # On Mac: ifconfig
  ```
- **Check 3**: Same WiFi network?
  - Both iPad and laptop on same WiFi

### "App Running Very Slow"
**Problem**: App feels sluggish on iPad
- **Solution 1**: Refresh app (pull down to refresh)
- **Solution 2**: Close other apps
- **Solution 3**: Restart iPad
- **Solution 4**: Clear app cache:
  - Settings → Safari → Advanced → Website Data → ACAS → Edit → Delete

### "Data Not Syncing"
**Problem**: Changes not saving
- **Solution**: Check server connection
  - Look at browser console (Develop menu)
  - Make sure logged in
  - Verify token not expired

### "Offline Features Not Working"
**Problem**: Can't use app without internet
- **Solution**: Service Worker takes time to cache
  - First time: use online to cache data
  - Then offline features available
  - Give 30 seconds for cache to populate

---

## 📊 Performance Tips

### Make App Faster
1. **Reduce data**: Use filters in live dashboard before offline
2. **Close not-used files**: Saves memory
3. **Restart periodically**: Fresh start helps
4. **Clear old cache**: Settings → Safari → Clear Data

### Battery Usage
- App uses minimal battery (just web tech)
- If slow, discharge iPad a bit then recharge (recalibrate)
- Brightness affect battery more than app

### Storage Usage
- Expects ~50-100MB for full cache
- Can delete and reinstall anytime
- Settings → General → iPad Storage → ACAS → Offload if needed

---

## 🔐 Security on iPad

### Data Protection
- Login token stored securely
- HTTPS recommended for production
- Browse privately if needed: Settings → Safari → Private Browsing

### Multi-User Setup
Each iPad user account gets own cache:
- User A: Has User A's login token
- User B: Has User B's login token
- Logout completely to switch users

### Logout Properly
1. Tap user menu (top right)
2. Click "Logout"
3. Token removed, cache cleared (optionally)
4. Now safe to pass iPad to others

---

## 🌍 Sharing App With Team

### Public Link (everyone on your network)
Server running on shared laptop:
```
http://shared-laptop-ip:8000/frontend/login.html
```

### External Network
Use ngrok:
```bash
ngrok http 8000
# Get: https://xxxx-xxxx-xxxx.ngrok.io
```

Then share the ngrok link.

### Multiple iPads
1. Each iPad installs same app independently
2. All connect to same server
3. See shared data in real-time
4. Each person logs with their account

---

## 📲 Advanced Features

### Share Data via AirDrop
1. In app, export to CSV or JSON
2. File saves to Files or Downloads
3. Use AirDrop to share file
4. Other iPad opens file in app

### iPad Keyboard Shortcuts
With Bluetooth keyboard attached:
```
Cmd+Z     Undo
Cmd+Shift+Z   Redo  
Cmd+X     Cut
Cmd+C     Copy
Cmd+V     Paste
Cmd+A     Select All
Cmd+F     Find
```

### Multitasking on iPad
- **Split Screen**: Drag app to left/right to split
- **Slide Over**: Swipe from right edge to overlay
- **Picture in Picture**: Support for videos (when added)

### App Switcher
- Swipe up from bottom: See all open apps
- Drag app card to another space
- Close app by swiping up and off screen

---

## 📚 Server Management

### Check Server Status
```bash
# See if running
curl http://127.0.0.1:8000/health

# View logs
python test_system_complete.py
```

### Restart Server
```bash
python start_server.py
```

### Stop Server
Press `Ctrl+C` in terminal

### Change Port
Edit `start_server.py`:
```python
port = 8000  # Change this
```

---

## 💾 Backup & Restore

### Backup Data
1. **Export all comments**: Dashboard → Export → CSV/JSON
2. **Save to iCloud**: Move to Files app → iCloud Drive
3. **Send to Mac/PC**: Use AirDrop or email

### Restore Data
1. **Get exported CSV/JSON file**
2. **Use API to import**: POST /api/comments/import
3. **Or manual**: Use Test tab → paste comments one by one

### Database Backup
On laptop/desktop:
```bash
# Backup database
cp dev.db dev.db.backup

# Restore database  
cp dev.db.backup dev.db
```

---

## 🚀 Production Deployment

### For Real-World Use
1. **Getting SSL Certificate**:
   ```bash
   # Use Let's Encrypt
   certbot certonly --standalone -d yourdomain.com
   ```

2. **Use HTTPS**:
   ```bash
   uvicorn app.main:app \
     --ssl-keyfile=/path/to/key.pem \
     --ssl-certfile=/path/to/cert.pem
   ```

3. **Update manifest.json**:
   ```json
   {
     "start_url": "https://yourdomain.com/frontend/login.html"
   }
   ```

4. **Install app with HTTPS URL** on iPad

---

## 🎯 Best Practices

✅ **DO**:
- Logout before passing iPad to others
- Use HTTPS for production
- Keep server running while using app
- Backup data weekly
- Test on iPad before sharing

❌ **DON'T**:
- Share login credentials
- Use on untrusted WiFi without VPN
- Leave sensitive data visible on shared iPad
- Clear cookies without backing up first
- Run too many other apps while using ACAS

---

## 📞 Support & Help

### Common Questions

**Q: Can I use offline?**
A: Yes, after initial load. App caches pages and syncs when online.

**Q: Can I install on iPhone?**
A: Yes! Same process works on any iOS device.

**Q: Will my data sync across devices?**
A: Yes, all devices connected to same server see same data.

**Q: How do I update the app?**
A: Automatic! Service worker checks for updates hourly.

**Q: Can I customize the app?**
A: Yes! Edit manifest.json and HTML files to customize.

---

## 🎉 You're All Set!

Your ACAS system is now ready to use on your iPad as a full-featured app!

**Next Steps**:
1. ✅ Install app on iPad
2. ✅ Login with admin/admin@123
3. ✅ Explore all features
4. ✅ Try offline mode
5. ✅ Share with team

**Enjoy analyzing comments on your iPad! 📱✨**
