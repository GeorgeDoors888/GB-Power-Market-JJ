# 📊 ChatGPT Analysis Prompts - UK Electricity Data

**Your Setup**: ChatGPT Actions connected to Railway → BigQuery  
**Data Available**: 155,405 rows of UK electricity market data

---

## ✅ Correct Column Names for bmrs_mid table:

- `settlementDate` (camelCase, NOT settlement_date)
- `settlementPeriod` 
- `price`
- `volume`
- `startTime`
- `dataProvider`

---

## 🎯 Ready-to-Use ChatGPT Prompts:

### 1. Get Recent Prices
```
Query my BigQuery database:
SELECT settlementDate, settlementPeriod, price, volume 
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` 
ORDER BY settlementDate DESC, settlementPeriod DESC 
LIMIT 20
```

### 2. Price Statistics Analysis
```
Query my BigQuery database for the last 100 prices from bmrs_mid table:
SELECT price FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` 
ORDER BY settlementDate DESC LIMIT 100

Then execute Python code to calculate:
- Mean price
- Median price
- Standard deviation
- Min and max
- Volatility (stdev/mean * 100)
```

### 3. Daily Average Prices
```
Query my BigQuery database:
SELECT 
    settlementDate,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    COUNT(*) as periods
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
GROUP BY settlementDate
ORDER BY settlementDate DESC
LIMIT 30
```

### 4. Price Distribution by Settlement Period
```
Query my BigQuery database to analyze price patterns by time of day:
SELECT 
    settlementPeriod,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
GROUP BY settlementPeriod
ORDER BY settlementPeriod
```

### 5. Volume Analysis
```
Query my BigQuery database:
SELECT 
    settlementDate,
    SUM(volume) as total_volume,
    AVG(price) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
GROUP BY settlementDate
ORDER BY settlementDate DESC
LIMIT 30

Then analyze the correlation between volume and price using Python
```

---

## 🔬 Advanced Analysis Prompts:

### SSP/SBP Correlation (if you have both tables)
```
Query my BigQuery database for System Sell Price and System Buy Price data.
Calculate the correlation between SSP and SBP.
Show the spread distribution.
```

### ARIMA Forecast
```
Query my BigQuery database to get 500 recent prices:
SELECT settlementDate, settlementPeriod, price 
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 500

Then execute Python code to:
1. Create a time series
2. Run ARIMA(1,1,1) model
3. Forecast next 10 periods
4. Show forecast values
```

### Price Volatility by Hour
```
Query my BigQuery database:
SELECT 
    settlementPeriod,
    STDDEV(price) as price_volatility,
    AVG(price) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
GROUP BY settlementPeriod
ORDER BY settlementPeriod

Then create a volatility chart description
```

### Peak vs Off-Peak Analysis
```
Query my BigQuery database:
SELECT 
    CASE 
        WHEN settlementPeriod BETWEEN 16 AND 40 THEN 'Peak'
        ELSE 'Off-Peak'
    END as period_type,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    COUNT(*) as count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
GROUP BY period_type
```

---

## 🐍 Python Analysis Examples:

### Correlation Analysis
```
Execute this Python code on my server:

import statistics
import math

# Sample price data (replace with actual BigQuery results)
prices_a = [45.3, 52.1, 38.9, 67.2, 41.4]
prices_b = [46.1, 53.2, 39.5, 68.1, 42.0]

# Calculate correlation
mean_a = statistics.mean(prices_a)
mean_b = statistics.mean(prices_b)

covariance = sum((a - mean_a) * (b - mean_b) for a, b in zip(prices_a, prices_b)) / len(prices_a)
std_a = statistics.stdev(prices_a)
std_b = statistics.stdev(prices_b)

correlation = covariance / (std_a * std_b)

print(f"Correlation coefficient: {correlation:.4f}")
```

### Moving Average
```
Execute this Python code to calculate 7-day moving average:

prices = [45.3, 52.1, 38.9, 67.2, 41.4, 55.8, 49.2, 58.4, 43.7, 51.9]
window = 3

moving_avg = []
for i in range(len(prices) - window + 1):
    avg = sum(prices[i:i+window]) / window
    moving_avg.append(avg)
    print(f"Period {i+1}: {avg:.2f}")
```

### Spread Analysis
```
Execute Python code to analyze price spreads:

import statistics

spreads = [2.5, 3.1, 1.8, 4.2, 2.9, 3.5, 2.2]

print("Spread Statistics:")
print(f"Mean: £{statistics.mean(spreads):.2f}")
print(f"Median: £{statistics.median(spreads):.2f}")
print(f"Std Dev: £{statistics.stdev(spreads):.2f}")
print(f"Min: £{min(spreads):.2f}")
print(f"Max: £{max(spreads):.2f}")
```

---

## 📋 Available Tables:

Query to list all your tables:
```
Query my BigQuery database:
SELECT table_name 
FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.TABLES`
```

Main tables you have:
- `bmrs_mid` - System prices (155,405 rows) ✅
- `bmrs_bod` - Bid-Offer Data
- `bmrs_boalf` - Bid-Offer Acceptance Level Flags
- `bmrs_indgen_iris` - Individual generator data
- `bmrs_fuelinst_iris` - Fuel mix instant data
- `bmrs_b1610` - Actual generation by fuel type

---

## 💡 Tips for ChatGPT:

1. **Be explicit**: Say "Query my BigQuery database" to trigger the action
2. **Use correct column names**: `settlementDate` not `settlement_date`
3. **Specify the full table name**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
4. **Chain operations**: First query data, then analyze with Python
5. **Test simple first**: Start with COUNT(*) queries before complex analysis

---

## 🚀 Example Full Workflow:

```
Step 1: Query my BigQuery database for the last 50 prices:
SELECT settlementDate, settlementPeriod, price 
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 50

Step 2: Execute Python code to analyze the data:
- Calculate mean, median, std deviation
- Find highest and lowest prices
- Calculate the coefficient of variation
- Identify any outliers (values > 2 std dev from mean)

Step 3: Present insights in a clear format
```

---

**Last Updated**: 2025-11-08  
**Status**: ✅ All endpoints working  
**BigQuery Project**: inner-cinema-476211-u9  
**Dataset**: uk_energy_prod
