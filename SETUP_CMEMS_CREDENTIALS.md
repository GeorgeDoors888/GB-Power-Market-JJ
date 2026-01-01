# CMEMS Credentials Setup

## Quick Setup

You need to register for a free Copernicus Marine account and configure credentials.

### Option 1: Environment Variables (Recommended for Scripts)

```bash
# Add to ~/.bashrc or ~/.bash_profile
export CMEMS_USERNAME="your_email@domain.com"
export CMEMS_PASSWORD="your_password"

# Then reload:
source ~/.bashrc
```

### Option 2: Interactive Login (One-time)

```bash
copernicusmarine login
# Enter username and password when prompted
```

### Option 3: Temporary Session (This Terminal Only)

```bash
export CMEMS_USERNAME="your_email@domain.com"
export CMEMS_PASSWORD="your_password"
python3 download_cmems_waves_uk.py
```

## Registration

1. Go to: https://data.marine.copernicus.eu
2. Click "Register" (free account)
3. Verify email
4. Use those credentials above

## Testing

```bash
# Test credentials
copernicusmarine describe --product-id GLOBAL_MULTIYEAR_WAV_001_032
```

If successful, you'll see product metadata. Then you can run the wave downloader.
