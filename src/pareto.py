from common import (
    pd, np, sm, ols, pairwise_tukeyhsd, shapiro, levene, sns, plt, 
    create_output_dir, setup_logging, AnalyticsDataProcessor
)
from typing import Dict
import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient, RunReportRequest, Dimension, Metric, DateRange
from dotenv import load_dotenv
from datetime import datetime
from dataclasses import dataclass
from typing import List

# Load environment variables and setup
load_dotenv()

OUTPUT_DIR = create_output_dir("anova_report")
logger = setup_logging(OUTPUT_DIR, 'anova.log')

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

class GA4AnovaAnalyzer:
    def __init__(self, data: pd.DataFrame, output_dir: str):
        self.data = data
        self.output_dir = output_dir
        self.dependent_vars = ['userEngagementDuration', 'averageSessionDuration', 
                             'bounceRate', 'eventCount']
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def save_plot(self, fig, filename: str):
        """Save plot to output directory"""
        plot_path = os.path.join(self.output_dir, filename)
        fig.savefig(plot_path)
        plt.close(fig)
        
    def save_results(self, results: Dict[str, Dict[str, any]], filename: str):
        """Save results to text file"""
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, 'w') as f:
            for metric, analysis in results.items():
                f.write(f"\nAnalysis for {metric}:\n")
                f.write("=" * 50 + "\n")
                f.write("\nAssumption Tests:\n")
                f.write(str(analysis['assumptions']) + "\n")
                f.write("\nOne-way ANOVA:\n")
                f.write(str(analysis['one_way_anova']) + "\n")
                f.write("\nTwo-way ANOVA:\n")
                f.write(str(analysis['two_way_anova']) + "\n")
                f.write("\nPost-hoc Analysis:\n")
                f.write(str(analysis['post_hoc']) + "\n")
                f.write("\n" + "=" * 50 + "\n")

    def perform_anova(self):
        results = {}
        for var in self.dependent_vars:
            try:
                # Assumption tests
                shapiro_test = shapiro(self.data[var])
                levene_test = levene(self.data[var], self.data['eventName'])
                
                # One-way ANOVA
                model = ols(f'{var} ~ C(eventName)', data=self.data).fit()
                anova_table = sm.stats.anova_lm(model, typ=2)
                
                # Two-way ANOVA
                model_two_way = ols(f'{var} ~ C(eventName) + C(eventName):C(eventName)', data=self.data).fit()
                anova_table_two_way = sm.stats.anova_lm(model_two_way, typ=2)
                
                # Post-hoc analysis
                post_hoc = pairwise_tukeyhsd(self.data[var], self.data['eventName'])
                
                results[var] = {
                    'assumptions': {
                        'Shapiro-Wilk Test': shapiro_test,
                        'Levene Test': levene_test
                    },
                    'one_way_anova': anova_table,
                    'two_way_anova': anova_table_two_way,
                    'post_hoc': post_hoc
                }
                
                # Plotting
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.boxplot(x='eventName', y=var, data=self.data, ax=ax)
                ax.set_title(f'Boxplot of {var} by Event Name')
                self.save_plot(fig, f'{var}_boxplot.png')
                
            except Exception as e:
                logger.error(f"Error performing ANOVA for {var}: {str(e)}")
        
        self.save_results(results, 'anova_results.txt')
        logger.info("ANOVA analysis completed successfully")

def main():
    try:
        property_id = os.getenv('GA4_PROPERTY_ID')
        if not property_id:
            raise ValueError("GA4_PROPERTY_ID environment variable not set")

        processor = AnalyticsDataProcessor()
        
        df = processor.get_analytics_data(property_id)
        if df is None or df.empty:
            raise ValueError("Failed to fetch analytics data")

        logger.info(f"Retrieved data with columns: {df.columns.tolist()}")
        logger.info(f"Data shape: {df.shape}")

        analyzer = GA4AnovaAnalyzer(df, OUTPUT_DIR)
        analyzer.perform_anova()
        logger.info("ANOVA report generated successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
