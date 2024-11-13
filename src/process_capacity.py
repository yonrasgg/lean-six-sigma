import pandas as pd
import datetime
from dateutil.parser import parse
import logging
import numpy as np
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
import os
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Load environment variables from .env file
load_dotenv()

# Set up logging with a more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnalyticsDataProcessor:
    """Class to handle Google Analytics data processing"""
    
    COLUMN_MAPPING = {
        'eventName': 'Nombre del evento',
        'source': 'Fuente',
        'medium': 'Medio',
        'totalUsers': 'Usuarios totales',
        'sessions': 'Sesiones',
        'engagedSessions': 'Sesiones con interacción',
        'eventCount': 'Número de eventos',
        'screenPageViews': 'Vistas de página',
        'bounceRate': 'Porcentaje de rebote',
        'userEngagementDuration': 'Duración del compromiso',
        'averageSessionDuration': 'Duración media de la sesión'
    }

    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "blogtndx-59d7dc876bd1.json"
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
        return df.rename(columns=self.COLUMN_MAPPING)

def calculate_cp(data: np.ndarray, usl: float, lsl: float) -> Optional[float]:
    """
    Calculate the process capability index (Cp).
    
    Args:
        data (np.ndarray): The process data
        usl (float): Upper specification limit
        lsl (float): Lower specification limit
    
    Returns:
        Optional[float]: The calculated Cp value, or None if calculation is not possible
    """
    try:
        if usl <= lsl:
            logger.warning("USL must be greater than LSL for Cp calculation.")
            return None
        
        sigma = np.std(data, ddof=1)
        if np.isclose(sigma, 0):
            logger.warning("Standard deviation is zero, Cp calculation not possible.")
            return None
        
        return (usl - lsl) / (6 * sigma)
    except Exception as e:
        logger.error(f"Error in Cp calculation: {str(e)}")
        return None

def main():
    try:
        # Get property ID from environment variable
        property_id = os.getenv('GA4_PROPERTY_ID')
        if not property_id:
            raise ValueError("GA4_PROPERTY_ID environment variable not set")

        # Initialize analytics processor
        processor = AnalyticsDataProcessor()
        
        # Get analytics data
        df = processor.get_analytics_data(property_id)
        if df is None:
            raise ValueError("Failed to fetch analytics data")

        # Calculate Cp for numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        cp_values = {}
        for column in numeric_columns:
            usl = df[column].max()
            lsl = df[column].min()
            
            cp_value = calculate_cp(df[column].values, usl, lsl)
            if cp_value is not None:
                cp_values[column] = cp_value
                logger.info(f"Process Capability Index (Cp) for {column}: {cp_value:.2f}")

        # Plot Cp values
        if cp_values:
            plt.figure(figsize=(12, 8))
            bars = plt.bar(cp_values.keys(), cp_values.values(), color='skyblue')
            plt.xlabel('Metrics')
            plt.ylabel('Cp Value')
            plt.title('Process Capability Index (Cp) for Numeric Columns')
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Annotate bars with Cp values
            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), 
                         ha='center', va='bottom', fontsize=10, color='black')

            plt.savefig('cp_values_chart.png')  # Save the plot as a file
            plt.show()  # Display the plot

        logger.info("Analysis completed successfully")
        return df

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
