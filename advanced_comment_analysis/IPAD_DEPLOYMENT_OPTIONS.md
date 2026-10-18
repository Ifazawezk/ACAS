# 🌍 ACAS iPad App Deployment Options

Deploy your ACAS app to iPad using one of these methods:

---

## 🏠 Option 1: Local Network (Recommended for Home/Office)

**Best for**: Same WiFi network, laptop next to iPad

### Setup
1. **Server on Laptop**: `python start_server.py`
2. **Find IP**: `ipconfig` → look for IPv4
3. **URL**: `http://192.168.1.100:8000/frontend/login.html`
4. **Install**: Share → Add to Home Screen

### Pros
- ✅ Fastest performance
- ✅ No external service needed
- ✅ Most secure
- ✅ Works offline after caching

### Cons
- ❌ iPad must be on same WiFi
- ❌ Server must stay running
- ❌ Can't access from outside home

### Code Changes
None! Works out of the box.

---

## 🌐 Option 2: ngrok Tunneling (Easy External Access)

**Best for**: Temporary external access, testing on different networks

### Setup

**Step 1**: Install ngrok
```bash
# Download from https://ngrok.com/download
# Or use Windows package manager:
choco install ngrok
```

**Step 2**: Get authtoken (free account)
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

**Step 3**: Create tunnel
```bash
# Terminal 1: Start ACAS server
python start_server.py

# Terminal 2: Create ngrok tunnel
ngrok http 8000
```

**Step 4**: Use ngrok URL on iPad
```
https://xxxx-xxxx-xxxx.ngrok.io/frontend/login.html
```

### Code Changes

Update `app/main.py` CORS:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://192.168.*",
        "https://*.ngrok.io",  # Add this
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Pros
- ✅ Works from anywhere
- ✅ Free tier available
- ✅ Easy setup
- ✅ Good for demos

### Cons
- ❌ Random URL changes (free tier)
- ❌ Slightly slower than local
- ❌ Relies on ngrok service
- ❌ URL sharing = access to system

### Pricing
- **Free**: 1 online ngrok instance, random URLs
- **Pro**: $5/month - Custom domain, more instances

---

## ☁️ Option 3: Cloud Deployment (AWS, Azure, Google Cloud)

**Best for**: Production use, team access, 24/7 availability

### Setup (AWS Example)

**Step 1**: Create EC2 instance
```bash
# AWS Console → EC2 → Launch Instance
# Select Ubuntu 22.04 LTS
# t3.medium (sufficient for ACAS)
# Allow inbound: 80, 443, 22
```

**Step 2**: SSH into instance
```bash
ssh -i key.pem ubuntu@YOUR_EC2_IP
```

**Step 3**: Install dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip
pip3 install -r requirements.txt
```

**Step 4**: Get SSL certificate (Let's Encrypt)
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.com
```

**Step 5**: Start with SSL
```bash
export PYTHONPATH=/path/to/ACAS
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile=/etc/letsencrypt/live/yourdomain.com/privkey.pem \
  --ssl-certfile=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
```

**Step 6**: Use on iPad
```
https://yourdomain.com/frontend/login.html
```

### Code Changes
None (HTTPS just works)

### Pros
- ✅ Production-ready
- ✅ Always available
- ✅ Team access
- ✅ Professional domain
- ✅ Automatic SSL renewal

### Cons
- ❌ Costs money ($5-20/month)
- ❌ More complex setup
- ❌ Need domain name
- ❌ Network latency

### Pricing
- **AWS**: $5-15/month
- **Azure**: $10-20/month
- **DigitalOcean**: $4-7/month
- **Heroku**: $7-50/month
- **Domain**: $10-15/year

---

## 🐳 Option 4: Docker Deployment

**Best for**: Consistent deployment across environments

### Setup

**Step 1**: Create Dockerfile (already exists)
```dockerfile
# Use: Dockerfile in project root
```

**Step 2**: Build image
```bash
docker build -t acas-app:latest .
```

**Step 3**: Run container
```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DATABASE_URL=sqlite:///data/dev.db \
  acas-app:latest
```

**Step 4**: Access on iPad
```
http://YOUR_IP:8000/frontend/login.html
```

### Code Changes
None (Docker handles it)

### Pros
- ✅ Consistent across systems
- ✅ Easy to scale
- ✅ Works anywhere (Linux, Mac, Windows)
- ✅ Good for Docker Swarm/Kubernetes

### Cons
- ❌ Need Docker installed
- ❌ Slightly more overhead
- ❌ Learning curve

### Deployment Platforms
- Docker Hub (registry)
- AWS ECS (container service)
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform

---

## 📱 Option 5: Heroku Deployment

**Best for**: Zero-infrastructure deployment

### Setup

**Step 1**: Create Heroku account
```bash
# Sign up at https://heroku.com
# Install Heroku CLI
```

**Step 2**: Create Procfile
```bash
# File: Procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Step 3**: Create runtime.txt
```bash
# File: runtime.txt
python-3.10.6
```

**Step 4**: Deploy
```bash
heroku login
heroku create acas-app
git push heroku main
```

**Step 5**: Use on iPad
```
https://acas-app.herokuapp.com/frontend/login.html
```

### Code Changes
None required!

### Pros
- ✅ Free tier available
- ✅ Very easy deployment
- ✅ Automatic SSL
- ✅ Git-based workflow

### Cons
- ❌ Free tier limited (sleeps after idle)
- ❌ Slower cold start
- ❌ Data resets monthly
- ❌ Limited resources

### Pricing
- **Free**: Limited, sleeps after inactivity
- **Paid**: $7-50/month

---

## 📊 Deployment Comparison

| Feature | Local | ngrok | AWS | Docker | Heroku |
|---------|-------|-------|-----|--------|--------|
| Speed | ⚡⚡⚡ | ⚡⚡ | ⚡⚡ | ⚡⚡⚡ | ⚡ |
| Cost | Free | Free* | $5+ | Free | Free* |
| Setup | Easy | Easy | Hard | Medium | Easy |
| Reliability | Good | Good | Excellent | Excellent | Good |
| Scalability | Poor | Poor | Excellent | Excellent | Medium |
| External Access | No | Yes | Yes | Yes | Yes |
| Always Available | No | No | Yes | Yes | Partial |
| Custom Domain | No | Paid | No | No | Paid |
| SSL/HTTPS | No | Yes | Yes | Yes | Yes |
| Offline Support | Yes | No | No | No | No |

---

## 🚀 Recommendation by Use Case

### I want to use on my iPad right now
→ **Option 1 (Local Network)** - 5 minutes setup

### I want to share with a friend for testing
→ **Option 2 (ngrok)** - Share URL, 10 minutes

### I want a professional setup for a team
→ **Option 3 (AWS)** or **Option 5 (Heroku)**

### I want zero maintenance deployment
→ **Option 5 (Heroku Free)**

### I want fastest performance
→ **Option 1 (Local)** or **Option 4 (Docker local)**

### I want to learn cloud deployment
→ **Option 3 (AWS)** - best learning experience

---

## 🔐 Security by Deployment

### Most Secure to Least Secure

1. **Local Network** ✅ Best
   - Data never leaves your network
   - No external service involved
   - Only people on WiFi access

2. **Docker (Private Network)** ✅ Secure
   - Isolated container
   - Can firewall ports
   - SSL optional but recommended

3. **AWS/Azure/GCP** ✅ Good
   - Industry-standard security
   - Requires login
   - Can use SSL, VPN, IAM
   - Audit trails available

4. **Heroku** ⚠️ Okay
   - SSL automatic
   - Requires login
   - Less granular control
   - Data on shared infrastructure

5. **ngrok Public** ⚠️ Be Careful
   - URL is guessable
   - Temporary access
   - Good for demos only
   - Don't expose production data

---

## 📝 Setup Instructions by Environment

### Windows Developer Machine (You)
```bash
cd C:\Users\mohan\OneDrive\Desktop\ACAS\advanced_comment_analysis
python start_server.py
# On iPad: http://192.168.1.100:8000/frontend/login.html
```

### Mac Developer Machine
```bash
cd ~/Projects/ACAS/advanced_comment_analysis
python3 start_server.py
# On iPad: http://192.168.x.x:8000/frontend/login.html
```

### Linux Server (Production)
```bash
cd /opt/acas
python3 start_server.py --host 0.0.0.0 --port 8000
# On iPad: https://yourdomain.com/frontend/login.html
```

### Docker (Any OS)
```bash
docker run -p 8000:8000 acas-app:latest
# On iPad: http://CONTAINER_IP:8000/frontend/login.html
```

### Heroku
```bash
git push heroku main
# On iPad: https://acas-app.herokuapp.com/frontend/login.html
```

---

## 🛠️ Troubleshooting by Deployment Type

### Local Network Issues
- Check firewall: Allow Python port 8000
- Verify WiFi connection on both devices
- Make sure server in same network

### ngrok Issues
- Check authtoken (if free tier)
- URL changes every restart (free tier)
- Connection limits (free tier: 40 connections/minute)

### AWS Issues
- Security groups: Allow ports 80, 443
- Elastic IP: Prevents IP changes
- CloudFront: Can cache static assets

### Docker Issues
- Port mapping: `-p 8000:8000`
- Volume mounting: `-v $(pwd)/data:/app/data`
- Environment variables: `-e DATABASE_URL=...`

### Heroku Issues
- App sleeps after 30 mins/day inactivity (free)
- Dyno restart: `heroku restart`
- Check logs: `heroku logs --tail`

---

## 🎯 Next Steps

1. **Choose deployment** (Option 1 easiest)
2. **Follow setup instructions**
3. **Test on iPad**: Open Safari → enter URL
4. **Install app**: Share → Add to Home Screen
5. **Share credentials**: Give others login info
6. **Monitor usage**: Check server logs
7. **Scale up**: Move to Option 3 if needed

---

**Questions? Check the specific deployment documentation above! 🚀**
