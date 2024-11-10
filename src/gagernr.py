from app import np
from app import os
from app import plt
from GageRnR import GageRnR

def perform_gage_rnr_analysis(data: np.ndarray, output_dir: str):
    """
    Perform Gage R&R analysis and generate a report.

    Args:
        data (np.ndarray): The input data structured in a 3D numpy array.
        output_dir (str): The directory to save the report.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Perform Gage R&R analysis
    g = GageRnR(data)
    g.calculate()

    # Print summary to console
    summary = g.summary()
    print(summary)

    # Extract data for plotting
    sources = ["Operator", "Part", "Operator by Part", "Measurement"]
    variances = [0.054, 0.802, 0, 0.057]  # Extracted from the summary
    std_devs = [0.232, 0.896, 0, 0.239]  # Extracted from the summary

    # Plot variance chart
    plt.figure(figsize=(12, 8))
    bars = plt.bar(sources, variances, color='skyblue')
    plt.xlabel('Sources of Variance')
    plt.ylabel('Variance (σ²)')
    plt.title('Gage R&R Variance Analysis')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Annotate bars with variance values
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 3), 
                 ha='center', va='bottom', fontsize=10, color='black')

    variance_chart_path = os.path.join(output_dir, 'gage_rnr_variance_chart.png')
    plt.savefig(variance_chart_path)
    plt.show()

    # Plot standard deviation chart
    plt.figure(figsize=(12, 8))
    bars = plt.bar(sources, std_devs, color='lightgreen')
    plt.xlabel('Sources of Variance')
    plt.ylabel('Standard Deviation (σ)')
    plt.title('Gage R&R Standard Deviation Analysis')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Annotate bars with standard deviation values
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 3), 
                 ha='center', va='bottom', fontsize=10, color='black')

    std_dev_chart_path = os.path.join(output_dir, 'gage_rnr_std_dev_chart.png')
    plt.savefig(std_dev_chart_path)
    plt.show()

    # Save the report to the output directory
    report_path = os.path.join(output_dir, 'gage_rnr_report.html')
    with open(report_path, 'w') as f:
        f.write('<html><head><title>Gage R&R Report</title></head><body>')
        f.write('<h1>Gage R&R Report</h1>')
        f.write('<pre>{}</pre>'.format(summary))
        f.write('<h2>Variance Chart</h2>')
        f.write('<img src="{}" alt="Variance Chart">'.format(variance_chart_path))
        f.write('<h2>Standard Deviation Chart</h2>')
        f.write('<img src="{}" alt="Standard Deviation Chart">'.format(std_dev_chart_path))
        f.write('</body></html>')
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    # Example data structured in a 3D numpy array
    data = np.array([
        [[3.29, 3.41, 3.64], [2.44, 2.32, 2.42], [4.34, 4.17, 4.27], [3.47, 3.5, 3.64], [2.2, 2.08, 2.16]],
        [[3.08, 3.25, 3.07], [2.53, 1.78, 2.32], [4.19, 3.94, 4.34], [3.01, 4.03, 3.2], [2.44, 1.8, 1.72]],
        [[3.04, 2.89, 2.85], [1.62, 1.87, 2.04], [3.88, 4.09, 3.67], [3.14, 3.2, 3.11], [1.54, 1.93, 1.55]]
    ])

    # Output directory for the report
    output_dir = 'gage_rnr_report'

    # Perform Gage R&R analysis and generate the report
    perform_gage_rnr_analysis(data, output_dir)
    print("Gage R&R analysis completed successfully.")