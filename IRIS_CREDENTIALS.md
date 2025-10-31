# 🔐 IRIS Credentials

## ✅ Registered: 30 October 2025

### Client Details:
- **Client ID:** `5ac22e4f-fcfa-4be8-b513-a6dc767d6312`
- **Client Secret:** `gCC8Q~fU.FWRjGiFWZ~Bsixd7xFAAEcv6NsaTdoV`
- **Secret Expiry:** **30 October 2027** ⚠️ (2 years)

### Queue Configuration:
- **Queue Name:** `iris.047b7f5d-7cc1-4f3d-a454-fe188a9f42f3`
- **Queue URL:** `https://elexon-insights-iris.servicebus.windows.net/iris.047b7f5d-7cc1-4f3d-a454-fe188a9f42f3`
- **Service Bus Namespace:** `elexon-insights-iris`
- **Tenant ID:** `4203b7a0-7773-4de5-b830-8b263a20426e`

---

## 🔔 Important Reminders

### ⚠️ Client Secret Expiry
**MARK YOUR CALENDAR:** Secret expires on **30 October 2027**

You'll need to:
1. Visit https://bmrs.elexon.co.uk/iris before expiry
2. Generate new client secret
3. Update `iris_settings.json` with new secret
4. Restart IRIS client

### 🔒 Security Notes
- ✅ Credentials saved in `iris_settings.json`
- ⚠️ **NEVER commit this file to git!**
- ✅ Already in `.gitignore` (should be)
- 🔐 Keep these credentials private

---

## 📋 Quick Reference

### Configuration File:
`iris_settings.json` contains:
```json
{
  "ClientId": "5ac22e4f-fcfa-4be8-b513-a6dc767d6312",
  "QueueName": "iris.047b7f5d-7cc1-4f3d-a454-fe188a9f42f3",
  "ServiceBusNamespace": "elexon-insights-iris",
  "Secret": "gCC8Q~fU.FWRjGiFWZ~Bsixd7xFAAEcv6NsaTdoV",
  "RelativeFileDownloadDirectory": "./iris_data"
}
```

### IRIS Portal:
https://bmrs.elexon.co.uk/iris

---

## 🚀 Next Steps

1. ✅ Credentials saved
2. ⏳ Clone IRIS client repo
3. ⏳ Install dependencies
4. ⏳ Test connection
5. ⏳ Build BigQuery integration

See `TODO_FUTURE_ANALYTICS.md` for full implementation plan!

---

**Created:** 30 October 2025
**Expiry Date:** 30 October 2027
**Status:** ✅ Active
