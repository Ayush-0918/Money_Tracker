
# Azure App Service Deployment Guide

This guide walks you through deploying the Money Tracker FastAPI backend to Microsoft Azure App Service using **Code Deployment** (No Docker).

## 1. Prerequisites
- **VS Code** with the **Azure Tools** extension installed (specifically **Azure App Service**).
- You should be signed into Azure inside VS Code (`Ctrl+Shift+P` -> `Azure: Sign In`).
- Your project should be in a Git repository (even locally).

## 2. Setting Up the App Service
1. Open the Azure extension in VS Code.
2. Under **App Services**, click the `+` (Create New Web App...) icon.
3. Choose **Create New Web App (Advanced)** (important for controlling settings):
   - **Name**: Choose a unique name (e.g., `moneytracker-api`).
   - **Resource Group**: Create new (e.g., `MoneyTracker-RG`).
   - **Runtime stack**: `Python 3.11`.
   - **OS**: `Linux`.
   - **Location**: `Central India` (or your preferred region).
   - **App Service Plan**: Create new.
   - **Pricing Tier**: 
     - ⚠️ **Highly Recommended: Basic B1** — F1 (Free) tier goes to sleep after 20 minutes of inactivity. Since your Android app triggers notifications unpredictably in the background, a sleeping F1 app will cause "Cold Start" delays (taking 30+ seconds to wake up), causing the Android background sync to fail/timeout. B1 stays active and prevents this.
     - **Free F1** — Can be used for zero-cost testing, but expect background sync timeouts.

## 3. Configuring Application Settings (Environment Variables)
Azure handles environment variables securely via "Application Settings" in the Portal. Do **NOT** upload your `.env` file. Azure will automatically inject these into the OS environment.

1. Go to the [Azure Portal](https://portal.azure.com), find your Web App.
2. Go to **Settings > Environment variables** (or Configuration > Application settings).
3. Add the following variables (matching your local `.env`):
   - `DATABASE_URL`: `postgresql+asyncpg://...` (Your Supabase connection string).
   - `JWT_SECRET_KEY`: Your generated secure hex key.
   - `ADMIN_API_KEY`: Your admin password/key.
   - `ENVIRONMENT`: `production` (Crucial for secure logging and hiding `/docs`).
   - `CORS_ORIGINS`: e.g., `https://your-frontend.com` (We will update this for Android later).
4. **Save** and let the app restart.

## 4. Configuring the Startup Command
Azure needs to know how to start your FastAPI app.
1. In the Azure Portal, go to **Settings > Configuration > General settings**.
2. Find the **Startup Command** box.
3. Enter exactly:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```
   *(Why? Gunicorn is a production-grade WSGI HTTP Server for UNIX. Using 4 workers allows it to handle concurrent requests efficiently, and the UvicornWorker class bridges it to your ASGI FastAPI application.)*
4. **Save**.

## 5. Deployment via VS Code
1. Open the VS Code Command Palette (`Ctrl+Shift+P`).
2. Type **Azure App Service: Deploy to Web App...**
3. Select the folder containing your backend code (`/Users/aayu/Desktop/Money_Tracker`).
4. Select the Web App you created.
5. Click **Deploy**. Azure will upload the code, run `pip install -r requirements.txt`, and start the app using your Startup Command.

---

## 6. Post-Deployment Checklist
- [ ] **Verify /health**: Visit `https://<your-app-name>.azurewebsites.net/health`. It should return `{"status":"ok", "database":"ok", "version":"1.0.0"}`.
- [ ] **Update CORS**: Once you know your exact frontend domain or Android requirements (sometimes Android requires `*` or a specific custom scheme for WebView, though standard Retrofit calls don't strictly enforce CORS like a browser does), update the `CORS_ORIGINS` variable in Azure.
- [ ] **Update Android App**: Change the `BASE_URL` in your Android Retrofit client from `http://10.0.2.2:8000` to `https://<your-app-name>.azurewebsites.net/`.

---

## 7. Cost Management (Budget Alert)
Since you are using $10k free credits, it's wise to set up a budget alert so you don't accidentally burn credits if something spins out of control.
1. In the Azure Portal search bar, search for **Cost Management + Billing**.
2. Go to **Cost Management > Budgets**.
3. Click **+ Add**.
4. Set a monthly budget (e.g., $10).
5. Under Alerts, set an email alert when costs reach 50% ($5) and 100% ($10).
6. Azure will now email you if you ever approach these tiny thresholds, ensuring your $10k lasts the full year.
