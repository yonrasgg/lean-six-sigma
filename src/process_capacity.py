import pandas as pd
import numpy as np
from typing import Optional, Dict, NamedTuple
import matplotlib.pyplot as plt
from pathlib import Path
import logging
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
import os
from dotenv import load_dotenv

# Load environment variables and setup
load_dotenv()

OUTPUT_DIR = Path("process_capacity_report")
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=OUTPUT_DIR / 'process_capacity.log'
)
logger = logging.getLogger(__name__)

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

class AnalyticsDataProcessor:
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

    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Prepare data for plotting
    metrics_data = {
        k: {'Cp': v.cp, 'Cpk': v.cpk, 'Cpm': v.cpm} 
        for k, v in capability_values.items()
    }
    metrics_df = pd.DataFrame.from_dict(metrics_data, orient='index')
    
    # Plot Capability Indices
    metrics_df.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title('Process Capability Indices by Metric', fontsize=14, pad=20)
    ax.set_xlabel('Metrics', fontsize=12)
    ax.set_ylabel('Capability Index Value', fontsize=12)
    ax.axhline(y=1.33, color='g', linestyle='--', label='Target Capability (1.33)')
    ax.legend(loc='upper right')
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add value labels
    for p in ax.patches:
        ax.annotate(f'{p.get_height():.2f}', 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', xytext=(0, 10), 
                    textcoords='offset points', fontsize=10, color='black')

    plt.tight_layout()
    plt.savefig(output_path / 'process_capability_analysis.png', 
                bbox_inches='tight', dpi=300)
    plt.close()

    # Plot normal distribution for each metric
    for metric, values in capability_values.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        mean = values.mean
        std = values.std
        usl = values.usl
        lsl = values.lsl
        target = values.target

        # Generate data for normal distribution
        x = np.linspace(mean - 4*std, mean + 4*std, 100)
        y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)

        ax.plot(x, y, label='Normal Distribution', color='blue')
        ax.axvline(mean, color='black', linestyle='--', label='Mean')
        ax.axvline(usl, color='red', linestyle='--', label='USL')
        ax.axvline(lsl, color='red', linestyle='--', label='LSL')
        ax.axvline(target, color='green', linestyle='--', label='Target')

        ax.fill_between(x, y, where=(x >= lsl) & (x <= usl), color='blue', alpha=0.1)
        ax.set_title(f'Normal Distribution for {metric}', fontsize=14, pad=20)
        ax.set_xlabel('Value', fontsize=12)
        ax.set_ylabel('Probability Density', fontsize=12)
        ax.legend(loc='upper right')
        ax.grid(True, linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.savefig(output_path / f'{metric}_normal_distribution.png', 
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

        capability_values = processor.calculate_cp_values(df)
        if not capability_values:
            raise ValueError("No valid capability values calculated")

        plot_cp_values(capability_values, OUTPUT_DIR)
        df.to_csv(OUTPUT_DIR / 'analytics_data.csv', index=False)
        logger.info("Process capacity report generated successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
