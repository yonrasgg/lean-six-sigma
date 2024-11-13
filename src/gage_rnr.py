from process_capacity import np, os, plt
from GageRnR import GageRnR

def perform_gage_rnr_analysis(data: np.ndarray, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    g = GageRnR(data)
    g.calculate()
    summary = g.summary()
    print(summary)

    sources = ["Operator", "Part", "Operator by Part", "Measurement"]
    variances = g.get_variances()  # Assuming this method exists in GageRnR
    std_devs = g.get_std_devs()  # Assuming this method exists in GageRnR

    def plot_chart(values, ylabel, title, filename, color):
        plt.figure(figsize=(12, 8))
        bars = plt.bar(sources, values, color=color)
        plt.xlabel('Sources of Variance')
        plt.ylabel(ylabel)
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 3), ha='center', va='bottom', fontsize=10, color='black')
        path = os.path.join(output_dir, filename)
        plt.savefig(path)
        plt.show()
        return path

    variance_chart_path = plot_chart(variances, 'Variance (σ²)', 'Gage R&R Variance Analysis', 'gage_rnr_variance_chart.png', 'skyblue')
    std_dev_chart_path = plot_chart(std_devs, 'Standard Deviation (σ)', 'Gage R&R Standard Deviation Analysis', 'gage_rnr_std_dev_chart.png', 'lightgreen')

    report_path = os.path.join(output_dir, 'gage_rnr_report.html')
    with open(report_path, 'w') as f:
        f.write(f'<html><head><title>Gage R&R Report</title></head><body><h1>Gage R&R Report</h1><pre>{summary}</pre>')
        f.write(f'<h2>Variance Chart</h2><img src="{variance_chart_path}" alt="Variance Chart">')
        f.write(f'<h2>Standard Deviation Chart</h2><img src="{std_dev_chart_path}" alt="Standard Deviation Chart"></body></html>')
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    data = np.array([
        [[3.29, 3.41, 3.64], [2.44, 2.32, 2.42], [4.34, 4.17, 4.27], [3.47, 3.5, 3.64], [2.2, 2.08, 2.16]],
        [[3.08, 3.25, 3.07], [2.53, 1.78, 2.32], [4.19, 3.94, 4.34], [3.01, 4.03, 3.2], [2.44, 1.8, 1.72]],
        [[3.04, 2.89, 2.85], [1.62, 1.87, 2.04], [3.88, 4.09, 3.67], [3.14, 3.2, 3.11], [1.54, 1.93, 1.55]]
    ])
    output_dir = 'gage_rnr_report'
    perform_gage_rnr_analysis(data, output_dir)
    print("Gage R&R analysis completed successfully.")
