# Lean Six Sigma Analysis

This repository contains scripts for performing Lean Six Sigma analysis using data from Google Analytics 4 (GA4). The scripts calculate various process capability indices, perform Gage R&R analysis, and generate Pareto charts to help identify and improve process performance.

## Directory Structure

```
src/
├── app.py          # Main application file
└── gagernr.py      # GA4 data generation and reporting module
```

## Requirements

- google-analytics-data
- pandas
- numpy
- python-dotenv

## Setup

1. Clone the repository:

```sh
git clone https://github.com/yourusername/lean-six-sigma.git
cd lean-six-sigma
```

2. Create a `.env` file in the project root with:

```env
GA4_PROPERTY_ID=your_property_id_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
```

3. Install dependencies:

```sh
pip install -r requirements.txt
```

## Usage

### Setting Up Environment Variables

Ensure you have set up your environment variables in the `.env` file as mentioned in the setup section.

### Running the Main Application

To run the main application, execute:

```sh
python src/app.py
```

## Functionality

### Process Capability Indices

The application calculates various process capability indices to help in Lean Six Sigma analysis.

### Error Handling and Logging

Implements robust error handling and logging mechanisms to ensure smooth operation and easier debugging.

### Metrics Processed

The application processes the following metrics:

- Total Users
- Sessions
- Engaged Sessions
- Event Count
- Screen Page Views
- Bounce Rate
- User Engagement Duration
- Average Session Duration

### GA4 Data Generation and Reporting Module (`src/gagernr.py`)

This module:

- Provides custom report generation
- Handles GA4 API interactions
- Implements data transformation utilities

## Authentication

### Enable the Google Analytics Data API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the Google Analytics Data API for your project.

### Create a Service Account and Download Credentials

1. In the Google Cloud Console, go to the "IAM & Admin" section.
2. Create a new service account.
3. Download the JSON credentials file and save it to a secure location.

### Set the `GOOGLE_APPLICATION_CREDENTIALS` Environment Variable

Set the path to your credentials file in the `.env` file:

```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
```

### GA4 Property ID

To find your GA4 Property ID:

1. Go to GA4 Admin.
2. Click on Property Settings.
3. Look for "Property ID".

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a Pull Request.

## License

This project is licensed under the [GNU General Public License v3.0](https://github.com/yonrasgg/lean-six-sigma/blob/main/LICENSE).

## Summary

This README provides:
1. Project overview
2. File structure
3. Setup instructions
4. File descriptions
5. Usage guidelines
6. Authentication setup
7. Contributing guidelines
