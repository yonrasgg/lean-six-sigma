import os
from dotenv import load_dotenv
from common import (
    pd, np, sm, ols, pairwise_tukeyhsd, shapiro, levene, sns, plt, 
    create_output_dir, setup_logging, AnalyticsDataProcessor
)
from typing import Dict
from datetime import datetime
from scipy import stats

# Load environment variables and setup
load_dotenv()

OUTPUT_DIR = create_output_dir("anova_report")
logger = setup_logging(OUTPUT_DIR, 'anova.log')

class GA4AnovaAnalyzer:
    def __init__(self, data: pd.DataFrame, output_dir: str):
        self.output_dir = output_dir
        self.dependent_vars = [
            'userEngagementDuration',
            'averageSessionDuration',
            'bounceRate',
            'eventCount'
        ]
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Clean and prepare the data upon initialization
        self.data = self.clean_data(data)

    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data to appropriate types"""
        # Create a copy to avoid modifying the original data
        df = data.copy()
        
        # Convert eventName to category
        df['eventName'] = df['eventName'].astype('category')
        
        # Convert numeric columns
        for var in self.dependent_vars:
            df[var] = pd.to_numeric(df[var], errors='coerce')
        
        # Drop any rows with NaN values
        df = df.dropna(subset=self.dependent_vars)
        
        logger.info(f"Cleaned data: {df.head()}")
        logger.info(f"Data types after cleaning: {df[self.dependent_vars].dtypes}")
        
        return df

    def perform_anova(self):
        """Perform ANOVA analysis and generate visualizations"""
        results = {}
        
        for var in self.dependent_vars:
            try:
                logger.info(f"Performing ANOVA for {var}")
                
                # Create figure for visualization
                plt.figure(figsize=(12, 6))
                
                # Create boxplot
                plt.title(f'Distribution of {var} by Event')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Save the plot
                plot_path = os.path.join(self.output_dir, f'{var}_boxplot.png')
                plt.savefig(plot_path)
                plt.close()
                
                # Perform one-way ANOVA
                groups = [group[var].values for name, group in self.data.groupby('eventName')]
                f_stat, p_val = stats.f_oneway(*groups)
                
                # Perform Tukey's HSD test
                tukey = pairwise_tukeyhsd(endog=self.data[var],
                                        groups=self.data['eventName'],
                                        alpha=0.05)
                
                # Store results
                results[var] = {
                    'assumptions': {
                        'Shapiro-Wilk Test': shapiro(self.data[var]),
                        'Levene Test': levene(*groups)
                    },
                    'one_way_anova': {
                        'f_statistic': f_stat,
                        'p_value': p_val
                    },
                    'post_hoc': tukey
                }
                
                # Save detailed results
                with open(os.path.join(self.output_dir, f'{var}_analysis.txt'), 'w') as f:
                    f.write(f"ANOVA Results for {var}\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"F-statistic: {f_stat}\n")
                    f.write(f"p-value: {p_val}\n")
                    f.write("\nTukey's HSD Test Results:\n")
                    f.write(str(tukey))
                
            except Exception as e:
                logger.error(f"Error analyzing {var}: {str(e)}")
                continue
        
        return results

def main():
    try:
        property_id = os.getenv('GA4_PROPERTY_ID')
        if not property_id:
            raise ValueError("GA4_PROPERTY_ID environment variable not set")

        # Initialize data processor and get data
        processor = AnalyticsDataProcessor()
        df = processor.get_analytics_data(property_id)
        
        if df is None or df.empty:
            raise ValueError("Failed to fetch analytics data")

        logger.info(f"Retrieved data with columns: {df.columns.tolist()}")
        logger.info(f"Data shape: {df.shape}")

        # Save raw data
        df.to_csv(os.path.join(OUTPUT_DIR, 'raw_data.csv'), index=False)

        # Initialize analyzer and perform analysis
        analyzer = GA4AnovaAnalyzer(df, OUTPUT_DIR)
        results = analyzer.perform_anova()

        # Save summary results
        with open(os.path.join(OUTPUT_DIR, 'summary_results.txt'), 'w') as f:
            for var, result in results.items():
                f.write(f"\nResults for {var}:\n")
                f.write("=" * 50 + "\n")
                f.write(f"ANOVA p-value: {result['one_way_anova']['p_value']}\n")
                f.write("=" * 50 + "\n\n")

        logger.info("Analysis completed successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()

