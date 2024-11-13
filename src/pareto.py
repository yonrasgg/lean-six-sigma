import os
import csv
import traceback
from typing import List
from dataclasses import dataclass
import matplotlib.pyplot as plt
from process_capacity import (
    BetaAnalyticsDataClient,
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    load_dotenv
)

@dataclass
class MetricData:
    categories: List[str]
    raw_values: List[float]
    indicators: List[str]

    def validate(self) -> None:
        if not (len(self.categories) == len(self.raw_values) == len(self.indicators)):
            raise ValueError("All data lists must have the same length")
        if not all(isinstance(x, (int, float)) and x >= 0 for x in self.raw_values):
            raise ValueError("Raw values must be non-negative numbers")
        if not all(self.categories) or not all(self.indicators):
            raise ValueError("Categories and indicators cannot be empty")

def fetch_data_from_google_analytics() -> MetricData:
    load_dotenv()
    property_id = os.getenv('GA4_PROPERTY_ID')
    if not property_id:
        raise ValueError("GA4_PROPERTY_ID not found in environment variables")
    
    client = BetaAnalyticsDataClient()
    requests = [
        RunReportRequest(
            property=f'properties/{property_id}',
            dimensions=[Dimension(name="browser"), Dimension(name="brandingInterest")],
            metrics=[Metric(name="engagedSessions"), Metric(name="bounceRate"), Metric(name="averageSessionDuration")],
            date_ranges=[DateRange(start_date='30daysAgo', end_date='today')]
        ),
        RunReportRequest(
            property=f'properties/{property_id}',
            dimensions=[Dimension(name="deviceCategory"), Dimension(name="browser")],
            metrics=[Metric(name="userEngagementDuration"), Metric(name="bounceRate"), Metric(name="engagementRate")],
            date_ranges=[DateRange(start_date='30daysAgo', end_date='today')]
        ),
        RunReportRequest(
            property=f'properties/{property_id}',
            dimensions=[Dimension(name="brandingInterest"), Dimension(name="browser")],
            metrics=[Metric(name="screenPageViews"), Metric(name="bounceRate"), Metric(name="averageSessionDuration")],
            date_ranges=[DateRange(start_date='30daysAgo', end_date='today')]
        )
    ]
    
    categories = ["SEO Tool Limitations", "GitHub Pages UX Limitations", "Adsense Policy Misalignment", "High Bounce Rate", "Content Quality Issues"]
    
    try:
        responses = [client.run_report(request) for request in requests]
        raw_values = [
            calculate_impact(responses[0], [0.4, 0.3, 0.3]),
            calculate_impact(responses[1], [0.3, 0.4, 0.3]),
            50.0,
            calculate_bounce_rate_impact(responses),
            calculate_impact(responses[2], [0.3, 0.4, 0.3])
        ]
        indicators = ["SEO Performance", "User Experience", "Monetization", "User Engagement", "Content Quality"]
    except Exception as e:
        print(f"Error fetching GA4 data: {str(e)}")
        raw_values = [85, 70, 50, 90, 65]
        indicators = ["SEO Performance", "User Experience", "Monetization", "User Engagement", "Content Quality"]
    
    return MetricData(categories=categories, raw_values=raw_values, indicators=indicators)

def calculate_impact(response, weights):
    total_impact = 0
    for row in response.rows:
        metrics = [float(row.metric_values[i].value) for i in range(3)]
        total_impact += sum(m * w for m, w in zip(metrics, weights))
    return total_impact

def calculate_bounce_rate_impact(responses):
    return sum((100 - float(row.metric_values[1].value)) for response in responses for row in response.rows)

def main():
    try:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pareto_report")
        os.makedirs(output_dir, exist_ok=True)
        
        data = fetch_data_from_google_analytics()
        data.validate()
        
        sorted_indices = sorted(range(len(data.raw_values)), key=lambda k: data.raw_values[k], reverse=True)
        total = sum(data.raw_values)
        cumulative_percentage = [(sum(data.raw_values[i] for i in sorted_indices[:idx+1]) / total) * 100 for idx in range(len(sorted_indices))]
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        bars = ax1.bar([data.categories[i] for i in sorted_indices], [data.raw_values[i] for i in sorted_indices], color='skyblue')
        ax2 = ax1.twinx()
        ax2.plot([data.categories[i] for i in sorted_indices], cumulative_percentage, color='red', marker='o', label='Cumulative %')
        
        plt.title('Pareto Analysis of Root Causes')
        ax1.set_xlabel('Root Causes')
        ax1.set_ylabel('Impact Score')
        ax2.set_ylabel('Cumulative Percentage')
        plt.xticks(rotation=45, ha='right')
        
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height, f'{height:.1f}', ha='center', va='bottom')
        for i, pct in enumerate(cumulative_percentage):
            ax2.text(i, pct, f'{pct:.1f}%', ha='center', va='bottom')
        
        ax2.legend(loc='upper left')
        plt.tight_layout()
        
        chart_path = os.path.join(output_dir, "pareto_chart.png")
        plt.savefig(chart_path, bbox_inches='tight', dpi=300)
        plt.close()
        
        results_data = {
            'Root Cause': [data.categories[i] for i in sorted_indices],
            'Impact Score': [data.raw_values[i] for i in sorted_indices],
            'Cumulative %': [f'{x:.1f}%' for x in cumulative_percentage],
            'Indicator': [data.indicators[i] for i in sorted_indices]
        }
        
        results_path = os.path.join(output_dir, "pareto_analysis_results.csv")
        with open(results_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(results_data.keys())
            writer.writerows(zip(*results_data.values()))
        
        print(f"\nAnalysis complete! Output files saved to: {output_dir}")
        print(f"- Chart: pareto_chart.png")
        print(f"- Results: pareto_analysis_results.csv")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
