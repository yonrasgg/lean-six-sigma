import os
from common import (
    pd, np, plt, Path, logging, BetaAnalyticsDataClient, DateRange, Dimension, Metric, RunReportRequest, load_dotenv, create_output_dir, setup_logging, AnalyticsDataProcessor
)
from typing import Optional, Dict, NamedTuple

# Load environment variables and setup
load_dotenv()

OUTPUT_DIR = create_output_dir("process_capacity_report")
logger = setup_logging(OUTPUT_DIR, 'process_capacity.log')

class MetricSpecification(NamedTuple):
    """Specification limits and target for a metric"""
    usl: float  # Upper Specification Limit
    lsl: float  # Lower Specification Limit
    target: float  # Target Value

class ProcessCapabilityMetrics(NamedTuple):
    """Process capability metrics with additional context"""
    cp: float
    cpk: float
    cpm: float
    mean: float
    std: float
    target: float
    usl: float
    lsl: float

class ProcessCapacityAnalyzer:
    # Define specification limits for each metric
    METRIC_SPECIFICATIONS = {
        'totalUsers': MetricSpecification(
            usl=1000,  # max expected users
            lsl=100,   # min acceptable users
            target=500 # target users
        ),
        'sessions': MetricSpecification(
            usl=1500,
            lsl=200,
            target=800
        ),
        'engagedSessions': MetricSpecification(
            usl=1000,
            lsl=150,
            target=600
        ),
        'eventCount': MetricSpecification(
            usl=5000,
            lsl=500,
            target=2000
        ),
        'screenPageViews': MetricSpecification(
            usl=3000,
            lsl=300,
            target=1500
        ),
        'bounceRate': MetricSpecification(
            usl=60,    # 60% maximum acceptable bounce rate
            lsl=20,    # 20% minimum acceptable bounce rate
            target=35  # 35% target bounce rate
        ),
        'userEngagementDuration': MetricSpecification(
            usl=900,   # 15 minutes maximum
            lsl=60,    # 1 minute minimum
            target=300 # 5 minutes target
        ),
        'averageSessionDuration': MetricSpecification(
            usl=600,   # 10 minutes maximum
            lsl=30,    # 30 seconds minimum
            target=180 # 3 minutes target
        )
    }

    def __init__(self):
        self.client = BetaAnalyticsDataClient()

    def get_analytics_data(self, property_id: str) -> Optional[pd.DataFrame]:
        """
        Get data from Google Analytics 4 API
        
        Args:
            property_id (str): GA4 property ID
        
        Returns:
            Optional[pd.DataFrame]: Analytics data or None if error occurs
        """
        try:
            request = RunReportRequest(
                property=f"properties/{property_id}",
                dimensions=[
                    Dimension(name="eventName")
                ],
                metrics=[
                    Metric(name="totalUsers"),
                    Metric(name="sessions"),
                    Metric(name="engagedSessions"),
                    Metric(name="eventCount"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate"),
                    Metric(name="userEngagementDuration"),
                    Metric(name="averageSessionDuration")
                ],
                date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            )
            
            response = self.client.run_report(request)
            return self._process_response(response, request)
            
        except Exception as e:
            logger.error(f"Error fetching analytics data: {str(e)}")
            return None

    def _process_response(self, response, request) -> pd.DataFrame:
        """Process the API response into a DataFrame"""
        rows = []
        for row in response.rows:
            row_dict = {}
            for i, dimension in enumerate(row.dimension_values):
                row_dict[request.dimensions[i].name] = dimension.value
            for i, metric in enumerate(row.metric_values):
                row_dict[request.metrics[i].name] = float(metric.value)
            rows.append(row_dict)
        
        df = pd.DataFrame(rows)
        return df

    def calculate_process_capability(
        self, 
        data: pd.Series,
        metric_name: str
    ) -> Optional[ProcessCapabilityMetrics]:
        """
        Calculate process capability metrics using specified limits and targets
        
        Args:
            data: Series containing metric values
            metric_name: Name of the metric being analyzed
            
        Returns:
            ProcessCapabilityMetrics if calculation successful, None otherwise
        """
        try:
            if len(data) < 2:
                logger.warning(f"Insufficient data points for {metric_name}")
                return None

            # Remove zeros and nulls
            data = data[data.notna() & (data != 0)]
            
            if len(data) < 2:
                logger.warning(f"Insufficient valid data points for {metric_name}")
                return None

            # Get specification limits and target
            spec = self.METRIC_SPECIFICATIONS.get(metric_name)
            if not spec:
                logger.warning(f"No specifications defined for {metric_name}")
                return None

            mean = data.mean()
            std = data.std()
            
            if std == 0:
                logger.warning(f"Zero standard deviation found for {metric_name}")
                return None

            # Calculate Cp using specified limits
            cp = (spec.usl - spec.lsl) / (6 * std)
            
            # Calculate Cpu and Cpl
            cpu = (spec.usl - mean) / (3 * std)
            cpl = (mean - spec.lsl) / (3 * std)
            
            # Calculate Cpk as minimum of Cpu and Cpl
            cpk = min(cpu, cpl)
            
            # Calculate Cpm using specified target
            cpm = cp / np.sqrt(1 + ((mean - spec.target) / std) ** 2)

            return ProcessCapabilityMetrics(
                cp=cp,
                cpk=cpk,
                cpm=cpm,
                mean=mean,
                std=std,
                target=spec.target,
                usl=spec.usl,
                lsl=spec.lsl
            )

        except Exception as e:
            logger.error(f"Error calculating capability for {metric_name}: {str(e)}")
            return None

    def calculate_cp_values(self, data: pd.DataFrame) -> Dict[str, ProcessCapabilityMetrics]:
        """Calculate process capability metrics for all specified metrics"""
        capability_values = {}
        
        for metric_name in self.METRIC_SPECIFICATIONS.keys():
            if metric_name in data.columns:
                metrics = self.calculate_process_capability(data[metric_name], metric_name)
                if metrics:
                    capability_values[metric_name] = metrics
                    logger.info(
                        f"Calculated capability metrics for {metric_name}:\n"
                        f"  Cp={metrics.cp:.2f}, Cpk={metrics.cpk:.2f}, Cpm={metrics.cpm:.2f}\n"
                        f"  Mean={metrics.mean:.2f}, Target={metrics.target:.2f}\n"
                        f"  USL={metrics.usl:.2f}, LSL={metrics.lsl:.2f}"
                    )

        return capability_values

def plot_cp_values(capability_values: Dict[str, ProcessCapabilityMetrics], output_path: Path) -> None:
    if not capability_values:
        logger.error("No capability values to plot")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    # Prepare data for plotting
    metrics_data = {
        k: {'Cp': v.cp, 'Cpk': v.cpk, 'Cpm': v.cpm} 
        for k, v in capability_values.items()
    }
    metrics_df = pd.DataFrame.from_dict(metrics_data, orient='index')
    
    # Plot 1: Capability Indices
    metrics_df.plot(kind='bar', ax=ax1, width=0.8)
    ax1.set_title('Process Capability Indices by Metric', fontsize=12, pad=20)
    ax1.set_xlabel('Metrics', fontsize=10)
    ax1.set_ylabel('Capability Index Value', fontsize=10)
    ax1.axhline(y=1.33, color='g', linestyle='--', label='Target Capability (1.33)')
    ax1.legend(loc='upper right')
    ax1.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 2: Pareto Chart
    if 'Cp' in metrics_df.columns:
        sorted_cp = metrics_df['Cp'].sort_values(ascending=False)
        cumulative_percentage = (sorted_cp.cumsum() / sorted_cp.sum() * 100)
        
        bars = ax2.bar(range(len(sorted_cp)), sorted_cp, color='steelblue')
        ax2.set_title('Pareto Chart of Process Capability', fontsize=12, pad=20)
        ax2.set_xlabel('Metrics', fontsize=10)
        ax2.set_ylabel('Cp Value', fontsize=10)
        
        ax2_twin = ax2.twinx()
        ax2_twin.plot(range(len(sorted_cp)), cumulative_percentage, 
                     color='red', marker='o', linewidth=2, label='Cumulative %')
        ax2_twin.set_ylabel('Cumulative Percentage (%)', fontsize=10)
        
        # Add value labels
        for idx, bar in enumerate(bars):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom')
        
        for idx, value in enumerate(cumulative_percentage):
            ax2_twin.text(idx, value, f'{value:.1f}%', ha='center', va='bottom')
        
        ax2.set_xticks(range(len(sorted_cp)))
        ax2.set_xticklabels(sorted_cp.index, rotation=45, ha='right')
        ax2.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path / 'process_capability_analysis.png', 
                bbox_inches='tight', dpi=300)
    plt.close()

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

        analyzer = ProcessCapacityAnalyzer()
        capability_values = analyzer.calculate_cp_values(df)
        if not capability_values:
            raise ValueError("No valid capability values calculated")

        plot_cp_values(capability_values, OUTPUT_DIR)
        df.to_csv(OUTPUT_DIR / 'analytics_data.csv', index=False)
        logger.info("Process capacity report generated successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
