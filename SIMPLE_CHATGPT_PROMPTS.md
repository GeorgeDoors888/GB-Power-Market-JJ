# 🚀 SIMPLE ChatGPT Prompts - Copy & Paste These EXACTLY

## ⚡ Just Want to Run Python Code?

**Copy this EXACTLY to ChatGPT:**

```
Execute this Python code on my server:

import statistics

prices = [103.3, 105.0, 102.99, 98.5, 110.2]

print("Price Analysis:")
print(f"Mean: £{statistics.mean(prices):.2f}")
print(f"Min: £{min(prices):.2f}")
print(f"Max: £{max(prices):.2f}")
```

---

## 🔥 Want Real BigQuery Data + Analysis?

**Copy this EXACTLY to ChatGPT:**

```
Step 1: Query my BigQuery database:
SELECT price FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` LIMIT 50

Step 2: Then execute Python code to calculate the average of those prices
```

---

## 💰 Want ARIMA Forecast?

**Copy this EXACTLY to ChatGPT:**

```
Query my BigQuery database:
SELECT settlementDate, price FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` 
ORDER BY settlementDate DESC LIMIT 100

Then execute Python code to:
1. Print the first 5 prices
2. Calculate the mean
3. Show a simple trend (compare first 10 vs last 10 average)
```

---

## ⚠️ WHY IT'S "HARD"

It's not hard - ChatGPT just needs you to be **EXPLICIT**:

❌ **DON'T SAY:** "analyze my data"  
✅ **DO SAY:** "Execute this Python code on my server: print('hello')"

❌ **DON'T SAY:** "run some analysis"  
✅ **DO SAY:** "Query my BigQuery database: SELECT * FROM bmrs_mid LIMIT 5"

---

## 🎯 ULTIMATE TEST - Copy This Right Now:

```
Execute this Python code on my server:

print("🚀 Testing Python Execution")
print("=" * 40)

# Simple calculation
result = sum([1, 2, 3, 4, 5])
print(f"Sum of 1-5: {result}")

# Data analysis
import statistics
data = [45.3, 52.1, 38.9, 67.2, 41.4]
print(f"\nPrice Statistics:")
print(f"  Mean: £{statistics.mean(data):.2f}")
print(f"  Median: £{statistics.median(data):.2f}")

print("\n✅ Python execution working perfectly!")
```

**If this works → Your setup is 100% correct!**

---

## 🔑 The Secret:

ChatGPT needs these EXACT phrases:
- **"Execute this Python code on my server:"** → Triggers `/execute` endpoint
- **"Query my BigQuery database:"** → Triggers `/query_bigquery` endpoint

Without those phrases, ChatGPT doesn't know you want to use your Railway server!

---

**Test the "ULTIMATE TEST" prompt above RIGHT NOW** ⬆️

If it works (it will), then you know the setup is perfect and it's just about using the right wording! 🎉
