import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

data = [
    ["2025-11-26", 50.0059, 49.818, 50.186, 31338, {"CCGT":19128.86,"WIND":9396.05,"NUCLEAR":4122.54}],
    ["2025-11-25", 50.0102, 49.779, 50.210, 10520, {"CCGT":17160.93,"WIND":8447.80,"NUCLEAR":4109.57}],
    ["2025-11-24", 49.9964, 49.835, 50.235, 18789, {"CCGT":13660.51,"WIND":11819.27,"NUCLEAR":4076.60}],
    ["2025-11-23", 50.0058, 49.811, 50.191, 16966, {"WIND":12828.96,"NUCLEAR":4058.26,"CCGT":3457.70}],
    ["2025-11-22", 49.9800, 49.854, 50.156, 7438, {"WIND":10401.36,"CCGT":10088.90,"NUCLEAR":3967.20}],
    ["2025-11-21", 50.0089, 49.759, 50.225, 18911, {"CCGT":19491.38,"WIND":7133.52,"NUCLEAR":3791.00}],
    ["2025-11-20", 50.0145, 49.815, 50.190, 18545, {"CCGT":17229.46,"WIND":12434.85,"NUCLEAR":3743.75}],
    ["2025-11-19", 49.9814, 49.800, 50.223, 15840, {"WIND":14393.99,"CCGT":12535.94,"NUCLEAR":3728.57}]
]

records=[]
for d,avg_f,min_f,max_f,boa,fuels in data:
    row={"Date":pd.to_datetime(d),"Avg_Freq":avg_f,"Min_Freq":min_f,"Max_Freq":max_f,"BOAs":boa}
    row.update(fuels)
    records.append(row)
df=pd.DataFrame(records).sort_values("Date")

sns.set_theme(style="whitegrid")
fig,axes=plt.subplots(3,1,figsize=(10,14))

# Frequency trend
sns.lineplot(ax=axes[0],x="Date",y="Avg_Freq",data=df,marker="o",color="royalblue",label="Average Frequency (Hz)")
axes[0].fill_between(df["Date"],df["Min_Freq"],df["Max_Freq"],color="skyblue",alpha=0.3,label="Min–Max Range")
axes[0].set_title("System Frequency Trend (Nov 19–26 2025)")
axes[0].set_ylabel("Frequency (Hz)")
axes[0].legend()

# Dispatch activity
sns.barplot(ax=axes[1],x="Date",y="BOAs",data=df,color="lightcoral")
axes[1].set_title("Dispatch Activity (BOAs per Day)")
axes[1].set_ylabel("Count of Accepted BOAs")
axes[1].tick_params(axis='x',rotation=45)

# Fuel-mix evolution
sns.lineplot(ax=axes[2],x="Date",y="CCGT",data=df,marker="o",label="CCGT (MW)")
sns.lineplot(ax=axes[2],x="Date",y="WIND",data=df,marker="o",label="Wind (MW)")
sns.lineplot(ax=axes[2],x="Date",y="NUCLEAR",data=df,marker="o",label="Nuclear (MW)")
axes[2].set_title("Top Fuel Generation Trends (7-Day)")
axes[2].set_ylabel("Average Generation (MW)")
axes[2].legend()

plt.tight_layout()
plt.show()
