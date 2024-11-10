import pandas as pd
import datetime
from dateutil.parser import parse
import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_cp(data, usl, lsl):
    """
    Calculate the process capability index (Cp).
    
    Args:
    data (array-like): The process data
    usl (float): Upper specification limit
    lsl (float): Lower specification limit
    
    Returns:
    float: The calculated Cp value, or None if calculation is not possible
    """
    try:
        if usl <= lsl:
            logging.warning("USL must be greater than LSL for Cp calculation.")
            return None
        
        sigma = np.std(data, ddof=1)  # Using sample standard deviation
        if sigma == 0:
            logging.warning("Standard deviation is zero, Cp calculation not possible.")
            return None
        
        cp = (usl - lsl) / (6 * sigma)
        return cp
    except Exception as e:
        logging.error(f"Error in Cp calculation: {str(e)}")
        return None

# Load the Excel file directly using pandas with correct column names
column_names = [
    "Nombre del evento",
    "Fuente/medio de la sesión",
    "Sesiones con interacción",
    "Sesiones",
    "Eventos por sesión",
    "Sesiones con interacción por usuario activo",
    "Vistas por sesión",
    "Porcentaje de rebote",
    "Porcentaje de interacciones",
    "Tiempo de interacción medio por sesión",
    "Total"
]

try:
    # Load the Excel file
    df = pd.read_excel("Sheet 3.xlsx", skiprows=7)

    # Set the column names
    df.columns = column_names

    # Print column names for debugging
    logging.info("Available columns in DataFrame:")
    logging.info(df.columns.tolist())
    logging.info("\nFirst few rows of the DataFrame:")
    logging.info(df.head())

    # Clean column names by stripping whitespace
    df.columns = df.columns.str.strip()

    # Calculate specification limits
    metrics = {
        'bounce_rate': {
            'column': 'Porcentaje de rebote',
            'unit': '%'
        },
        'avg_time': {
            'column': 'Tiempo de interacción medio por sesión',
            'unit': 'minutes'
        },
        'sessions': {
            'column': 'Sesiones',
            'unit': ''
        }
    }

    # Calculate Cp for all numeric columns
    for column in df.select_dtypes(include=[np.number]).columns:
        # Note: Using column max and min as USL and LSL respectively.
        # In a real-world scenario, these limits should be set based on process requirements.
        usl = df[column].max()
        lsl = df[column].min()
        
        metrics[f'cp_{column}'] = {
            'column': column,
            'unit': '',
            'usl': usl,
            'lsl': lsl
        }
        
        # Calculate and log Cp value
        cp_value = calculate_cp(df[column], usl, lsl)
        if cp_value is not None:
            logging.info(f"Process Capability Index (Cp) for {column}: {cp_value}")
        else:
            logging.warning(f"Unable to calculate Cp for {column}")
        
    logging.info("Cp calculation completed for all numeric columns.")
except Exception as e:
    logging.error(f"Error during initial setup: {str(e)}")
    raise

# Print data types and unique values of columns used in metrics
print("\nDetailed information about columns used in metrics:")
for metric, info in metrics.items():
    column_data = df[info['column']]
    print(f"\n{info['column']}:")
    print(f"Data type: {column_data.dtype}")
    print("Unique values and their types:")
    for value in column_data.unique():
        print(f"  {value}: {type(value)}")

def contains_datetime(series):
    def is_date(value):
        if isinstance(value, (pd.Timestamp, datetime.datetime)):
            return True
        if isinstance(value, str):
            try:
                parse(value)
                return True
            except (ValueError, TypeError):
                return False
        return False

    return any(is_date(x) for x in series if pd.notna(x))

def get_column_types(series):
    types = set()
    for value in series:
        if pd.isna(value):
            continue
        if isinstance(value, (pd.Timestamp, datetime.datetime)):
            types.add('datetime')
        elif isinstance(value, (int, float)):
            types.add('numeric')
        elif isinstance(value, str):
            try:
                parse(value)
                types.add('datetime')
            except (ValueError, TypeError):
                types.add('string')
        else:
            types.add('unknown')
    return types

def safe_min_max(series):
    non_null = series.dropna()
    if len(non_null) == 0:
        return 'N/A', 'N/A'
    
    types = set(map(type, non_null))
    
    if len(types) == 1:
        # All elements are of the same type
        if types.pop() in (int, float, pd.Timestamp, datetime.datetime):
            return min(non_null), max(non_null)
    
    # If we reach here, we have mixed types or non-comparable types
    try:
        # Try to convert everything to strings
        str_series = non_null.astype(str)
        return min(str_series), max(str_series)
    except TypeError as e:
        print(f"Error in safe_min_max: {e}")
        print(f"Problematic values: {non_null.tolist()}")
        return 'Error', 'Error'

def safe_mean_sum(series):
    non_null = series.dropna()
    if len(non_null) == 0:
        return 'N/A', 'N/A'
    
    try:
        numeric_data = pd.to_numeric(non_null, errors='coerce')
        return numeric_data.mean(), numeric_data.sum()
    except Exception as e:
        print(f"Error in safe_mean_sum: {e}")
        print(f"Problematic values: {non_null.tolist()}")
        return 'Error', 'Error'

def calculate_cp(data, usl, lsl):
    """
    Calculate the process capability index (Cp).
    
    Args:
    data (array-like): The process data
    usl (float): Upper specification limit
    lsl (float): Lower specification limit
    
    Returns:
    float: The calculated Cp value, or None if calculation is not possible
    """
    try:
        if usl <= lsl:
            logging.warning("USL must be greater than LSL for Cp calculation.")
            return None
        
        sigma = np.std(data, ddof=1)  # Using sample standard deviation
        if sigma == 0:
            logging.warning("Standard deviation is zero, Cp calculation not possible.")
            return None
        
        cp = (usl - lsl) / (6 * sigma)
        return cp
    except Exception as e:
        logging.error(f"Error in Cp calculation: {str(e)}")
        return None

# Calculate statistics for each metric
stats = {}
processed_metrics = []
error_metrics = []

try:
    for metric, info in metrics.items():
        try:
            column_data = df[info['column']]
            logging.info(f"\nProcessing {metric}:")
            logging.info(f"Column data: {column_data.head()}")
            logging.info(f"Data type: {column_data.dtype}")
            logging.info(f"Unique values: {column_data.unique()}")
            
            column_types = get_column_types(column_data)
            logging.info(f"Detected column types: {column_types}")
            
            try:
                lsl, usl = safe_min_max(column_data)
                mean, total = safe_mean_sum(column_data)
                
                stats[metric] = {
                    'lsl': lsl,
                    'usl': usl,
                    'mean': mean,
                    'total': total,
                    'unit': info['unit']
                }
                processed_metrics.append(metric)
            except Exception as e:
                logging.error(f"Error processing {metric}: {str(e)}")
                logging.error(f"Problematic column data: {column_data.tolist()}")
                stats[metric] = {
                    'lsl': 'Error',
                    'usl': 'Error',
                    'mean': 'Error',
                    'total': 'Error',
                    'unit': info['unit']
                }
                error_metrics.append(metric)
            
            # Log the calculated stats
            logging.info(f"Calculated stats for {metric}: {stats[metric]}")
        except KeyError as e:
            logging.warning(f"Column '{info['column']}' not found in DataFrame")
            error_metrics.append(metric)

except Exception as e:
    logging.critical(f"Unexpected error occurred: {str(e)}")

# Log the final statistics
logging.info("\nFinal Statistics:")
for metric, stat in stats.items():
    logging.info(f"{metric}:")
    for key, value in stat.items():
        logging.info(f"  {key}: {value}")

# Log summary
logging.info("\nProcessing Summary:")
logging.info(f"Total metrics: {len(metrics)}")
logging.info(f"Successfully processed metrics: {len(processed_metrics)}")
logging.info(f"Metrics with errors: {len(error_metrics)}")
if error_metrics:
    logging.info(f"Metrics that encountered errors: {', '.join(error_metrics)}")

# Create the results table
headers = [
    "Nombre del evento",
    "Fuente/medio de la sesión",
    "Sesiones con interacción",
    "Sesiones",
    "Eventos por sesión",
    "Sesiones con interacción por usuario activo",
    "Vistas por sesión",
    "Porcentaje de rebote",
    "Porcentaje de interacciones",
    "Tiempo de interacción medio por sesión"
]

# Create specification limits rows
lsl = ["LSL"] + [""] * (len(headers) - 1)
usl = ["USL"] + [""] * (len(headers) - 1)

# Add specification limits where available
for metric, info in stats.items():
    if 'bounce_rate' in metric:
        lsl[7] = f"{info['lsl']}{info['unit']}"
        usl[7] = f"{info['usl']}{info['unit']}"
    elif 'avg_time' in metric:
        lsl[9] = f"{info['lsl']}{info['unit']}"
        usl[9] = f"{info['usl']}{info['unit']}"

# Convert DataFrame to list for tabulate
data = df.values.tolist()
data.insert(0, usl)
data.insert(0, lsl)

# Print results using tabulate
from tabulate import tabulate
headers_align = ["center"] * len(headers)
print("\n")

# Print summary statistics
for metric, info in stats.items():
    print(f"{'=' * 50}")
    print(f"Statistics for {metric}:")
    print(f"Total: {info['total']}{info['unit']}")
    print(f"Mean: {info['mean']:.2f}{info['unit']}")
    print(f"Range: {info['lsl']}{info['unit']} - {info['usl']}{info['unit']}")
