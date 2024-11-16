import os
from dotenv import load_dotenv
from common import (
    pd, np, sm, ols, pairwise_tukeyhsd, shapiro, levene, sns, plt, 
    create_output_dir, setup_logging, AnalyticsDataProcessor
)
from typing import Dict
from datetime import datetime

# Load environment variables and setup
load_dotenv()

OUTPUT_DIR = create_output_dir("anova_report")
logger = setup_logging(OUTPUT_DIR, 'anova.log')

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
