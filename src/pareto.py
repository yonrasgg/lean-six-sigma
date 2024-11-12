from app import pd
from app import plt
import seaborn as sns

sns.set()

# GA4 metrics-based data with measured impact percentages
data = {
    "Metric Category": [
        "Traffic Source Performance",
        "User Experience Issues",
        "Content Engagement",
        "Technical Performance",
        "Monetization Alignment",
        "Navigation Structure",
        "SEO Optimization"
    ],
    "Impact (%)": [28, 22, 15, 12, 10, 8, 5],
    "Key Indicators": [
        "Organic/Direct/Social distribution",
        "Bounce Rate & Session Duration",
        "Pages/Session & Event Engagement",
        "Page Load Time & Performance",
        "Ad Click-through & Conversion",
        "Site Structure & User Flow",
        "Keywords & Content Performance"
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Calculate cumulative percentage
df['Cumulative (%)'] = df['Impact (%)'].cumsum()

# Sort by impact in descending order
df = df.sort_values(by="Impact (%)", ascending=False).reset_index(drop=True)

# Create figure and axis objects
fig, ax1 = plt.subplots(figsize=(12, 7))

# Bar plot
bars = ax1.bar(df["Metric Category"], df["Impact (%)"], 
               color='#2E86C1', alpha=0.7)

# Customize primary axis
ax1.set_xlabel("GA4 Metric Categories", fontsize=10, fontweight='bold')
ax1.set_ylabel("Impact (%)", color="#2E86C1", fontsize=10, fontweight='bold')
ax1.tick_params(axis="y", labelcolor="#2E86C1")

# Add title
plt.title("GA4 Metrics Pareto Analysis", pad=20, fontsize=14, fontweight='bold')

# Create secondary axis for cumulative line
ax2 = ax1.twinx()
line = ax2.plot(df["Metric Category"], df["Cumulative (%)"], 
                color='#E67E22', marker='D', ms=8, linewidth=2)
ax2.set_ylabel("Cumulative (%)", color="#E67E22", fontsize=10, fontweight='bold')
ax2.tick_params(axis="y", labelcolor="#E67E22")

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{height}%',
             ha='center', va='bottom')

# Add cumulative percentage labels
for i, cumulative in enumerate(df["Cumulative (%)"]):
    ax2.annotate(f'{cumulative:.1f}%', 
                 (i, cumulative),
                 textcoords="offset points",
                 xytext=(0,10),
                 ha='center',
                 color='#E67E22',
                 fontweight='bold')

# Rotate x-axis labels
plt.xticks(rotation=45, ha='right')

# Add grid
ax1.yaxis.grid(True, linestyle='--', alpha=0.7)

# Adjust layout
plt.tight_layout()

# Save the plot (optional)
plt.savefig('pareto_analysis.png', bbox_inches='tight', dpi=300)

# Display the plot
plt.show()

# Print analysis
print("\nDetailed Metric Analysis:")
for index, row in df.iterrows():
    print(f"\n{row['Metric Category']} ({row['Impact (%)']}%):")
    print(f"Key Indicators: {row['Key Indicators']}")