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
        
        # Drop any rows with NaN values in the dependent variables
        df = df.dropna(subset=self.dependent_vars)
        
        # Ensure there are enough samples for each group
        for var in self.dependent_vars:
            group_counts = df['eventName'].value_counts()
            if any(group_counts < 2):
                logger.warning(f"Not enough samples for {var}. Groups with less than 2 samples will be excluded.")
                df = df[df['eventName'].isin(group_counts[group_counts >= 2].index)]
        
        logger.info(f"Cleaned data: {df.head()}")
        logger.info(f"Data types after cleaning: {df[self.dependent_vars].dtypes}")
        return df

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
                f.write(str(analysis.get('assumptions', 'No assumptions test results')) + "\n")
                f.write("\nOne-way ANOVA:\n")
                f.write(str(analysis.get('one_way_anova', 'No one-way ANOVA results')) + "\n")
                f.write("\nTwo-way ANOVA:\n")
                f.write(str(analysis.get('two_way_anova', 'No two-way ANOVA results')) + "\n")
                f.write("\nPost-hoc Analysis:\n")
                f.write(str(analysis.get('post_hoc', 'No post-hoc analysis results')) + "\n")
                f.write("\n" + "=" * 50 + "\n")

    def perform_statistical_tests(self, df: pd.DataFrame, var: str) -> Dict:
        """Perform statistical tests on the data."""
        results = {
            'descriptive': df.groupby('eventName')[var].describe(),
            'group_sizes': df.groupby('eventName')[var].size(),
            'total_samples': len(df),
            'anova_possible': False
        }
        
        try:
            # Create groups for ANOVA
            groups = [group[var].values for name, group in df.groupby('eventName')]
            groups = [group for group in groups if len(group) >= 2]  # Only keep groups with sufficient samples
            
            if len(groups) >= 2:
                # Perform normality test
                _, norm_p_value = shapiro(df[var])
                results['assumptions'] = {
                    'normality_test': {
                        'test': 'Shapiro-Wilk',
                        'p_value': norm_p_value
                    }
                }
                
                # Perform homogeneity of variance test
                _, hov_p_value = levene(*groups)
                results['assumptions']['variance_test'] = {
                    'test': 'Levene',
                    'p_value': hov_p_value
                }
                
                # Perform one-way ANOVA
                f_stat, p_val = stats.f_oneway(*groups)
                results['one_way_anova'] = {
                    'f_statistic': f_stat,
                    'p_value': p_val
                }
                results['anova_possible'] = True
                
                # Perform Tukey's HSD if ANOVA is significant
                if p_val < 0.05:
                    tukey = pairwise_tukeyhsd(df[var], df['eventName'])
                    results['post_hoc'] = tukey
                
        except Exception as e:
            logger.error(f"Error performing statistical tests for {var}: {str(e)}")
        
        return results

    def perform_analysis(self):
        """Perform complete analysis for all variables."""
        results = {}
        
        for var in self.dependent_vars:
            try:
                logger.info(f"\nAnalyzing {var}")
                
                # Clean data for this specific variable
                clean_df = self.clean_data(self.data)
                
                if clean_df.empty:
                    logger.warning(f"No valid data for analysis of {var}")
                    continue
                
                # Perform statistical tests
                analysis_results = self.perform_statistical_tests(clean_df, var)
                results[var] = analysis_results
                
                # Create visualization
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.boxplot(x='eventName', y=var, data=clean_df, ax=ax)
                ax.set_title(f'Boxplot of {var} by Event Name')
                ax.grid(True)  # Add grid to the plot
                self.save_plot(fig, f'{var}_boxplot.png')
                
                # Save analysis results
                self.save_results(results, f'{var}_analysis.txt')
                
            except Exception as e:
                logger.error(f"Error performing analysis for {var}: {str(e)}")
        
        return results

def main():
    try:
        # Get configuration from environment variables
        property_id = os.getenv('GA4_PROPERTY_ID')
        if not property_id:
            raise ValueError("GA4_PROPERTY_ID environment variable not set")

        # Get dates from environment variables or use defaults
        end_date = os.getenv('GA4_END_DATE', datetime.now().strftime('%Y-%m-%d'))
        start_date = os.getenv('GA4_START_DATE', 
                              (datetime.strptime(end_date, '%Y-%m-%d') - pd.Timedelta(days=30)).strftime('%Y-%m-%d'))

        logger.info(f"Fetching analytics data for property ID: {property_id}")
        logger.info(f"Date range: {start_date} to {end_date}")

        # Initialize data processor and get data
        processor = AnalyticsDataProcessor()
        df = processor.get_analytics_data(
            property_id=property_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            raise ValueError("No data retrieved from Google Analytics")

        logger.info(f"Retrieved data with columns: {df.columns.tolist()}")
        logger.info(f"Data shape: {df.shape}")

        # Save the raw data to a CSV file
        raw_data_path = os.path.join(OUTPUT_DIR, 'raw_data.csv')
        df.to_csv(raw_data_path, index=False)
        logger.info(f"Saved raw data to: {raw_data_path}")

        # Perform ANOVA analysis
        analyzer = GA4AnovaAnalyzer(df, OUTPUT_DIR)
        results = analyzer.perform_analysis()
        logger.info("ANOVA report generated successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
