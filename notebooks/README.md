# Jupyter Notebooks for API Testing

This directory contains Jupyter notebooks for interactive testing and analysis of the customer matching API.

## Available Notebooks

### 1. `quick_test.ipynb` - Quick API Validation
**Purpose**: Rapid validation of basic API functionality
**Use when**: 
- You want to quickly check if the API is running
- Basic functionality testing during development
- Quick smoke tests before running comprehensive tests

**Features**:
- Health check endpoint testing
- Basic customer creation and matching
- Simple search functionality test
- Minimal setup required

### 2. `api_testing.ipynb` - Comprehensive API Testing
**Purpose**: Thorough testing of all API features with detailed analysis
**Use when**:
- Comprehensive testing of the matching system
- Performance analysis and optimization
- Threshold tuning and algorithm validation
- Regression testing

**Features**:
- Systematic variation testing
- Performance benchmarking
- Threshold analysis
- Data visualization
- Results export functionality

### 3. `data_analysis.ipynb` - Data Analysis and Insights
**Purpose**: Deep analysis of existing customer data and matching results
**Use when**:
- Analyzing system performance over time
- Data quality assessment
- Matching algorithm optimization
- Business intelligence and reporting

**Features**:
- Customer data profiling
- Matching results analysis
- Performance metrics calculation
- Data quality assessment
- Recommendations generation

## Setup Instructions

### Prerequisites

1. **Install Jupyter**: Already included in `requirements-dev.txt`
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Start Jupyter**: From the project root
   ```bash
   jupyter notebook
   ```

3. **API Running**: Ensure your API is running
   ```bash
   uvicorn app.main:app --reload
   ```

### Configuration

Before running notebooks, update the configuration in each notebook:

1. **API Base URL**: Update `BASE_URL` if your API runs on a different port
   ```python
   BASE_URL = "http://localhost:8000"  # Adjust as needed
   ```

2. **Database Connection**: In `data_analysis.ipynb`, update the database URL
   ```python
   DB_URL = "postgresql://username:password@localhost:5432/vectordb"
   ```

## Usage Workflow

### For Development Testing

1. **Start with Quick Test**:
   ```bash
   jupyter notebook notebooks/quick_test.ipynb
   ```
   - Run all cells to verify basic functionality
   - Check for any immediate issues

2. **Run Comprehensive Tests**:
   ```bash
   jupyter notebook notebooks/api_testing.ipynb
   ```
   - Execute cells systematically
   - Review visualizations and metrics
   - Export results for comparison

3. **Analyze Data** (if you have existing data):
   ```bash
   jupyter notebook notebooks/data_analysis.ipynb
   ```
   - Review system performance
   - Identify optimization opportunities

### For Production Monitoring

1. **Regular Health Checks**: Run `quick_test.ipynb` daily
2. **Weekly Analysis**: Run `data_analysis.ipynb` weekly
3. **Performance Testing**: Run `api_testing.ipynb` after deployments

## Notebook Features

### Interactive Testing
- **Real-time Results**: See API responses immediately
- **Parameter Tuning**: Adjust thresholds and parameters interactively
- **Data Visualization**: Charts and graphs for result analysis
- **Export Capabilities**: Save results to CSV files

### Comprehensive Coverage
- **Health Checks**: API availability and status
- **Functional Testing**: All API endpoints
- **Performance Testing**: Response times and throughput
- **Data Quality**: Completeness and consistency analysis
- **Matching Analysis**: Similarity scores and confidence levels

### Debugging Support
- **Error Handling**: Graceful handling of API errors
- **Detailed Logging**: Full request/response information
- **Step-by-step Execution**: Run cells individually for debugging
- **Data Validation**: Verify data quality and consistency

## Best Practices

### Testing Strategy

1. **Start Small**: Begin with `quick_test.ipynb` for basic validation
2. **Systematic Approach**: Use `api_testing.ipynb` for comprehensive testing
3. **Regular Monitoring**: Use `data_analysis.ipynb` for ongoing analysis
4. **Document Results**: Export and save test results for comparison

### Performance Testing

1. **Baseline Establishment**: Run performance tests before changes
2. **Regression Testing**: Compare results after modifications
3. **Load Testing**: Test with larger datasets for scalability
4. **Threshold Optimization**: Use threshold analysis to find optimal settings

### Data Analysis

1. **Regular Reviews**: Analyze data quality and completeness
2. **Trend Analysis**: Monitor performance over time
3. **Anomaly Detection**: Identify unusual patterns or issues
4. **Optimization**: Use insights to improve matching algorithms

## Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Verify API is running: `uvicorn app.main:app --reload`
   - Check port configuration in notebook
   - Ensure firewall settings allow connections

2. **Database Connection Issues**:
   - Verify database is running and accessible
   - Check connection string in `data_analysis.ipynb`
   - Ensure proper credentials and permissions

3. **Import Errors**:
   - Install required packages: `pip install -r requirements-dev.txt`
   - Restart Jupyter kernel after installing packages
   - Check Python environment compatibility

4. **Memory Issues**:
   - Reduce dataset size in analysis notebooks
   - Process data in smaller chunks
   - Restart kernel if memory usage is high

### Debugging Tips

1. **Cell-by-Cell Execution**: Run cells individually to isolate issues
2. **Error Messages**: Read full error messages for debugging clues
3. **API Logs**: Check API server logs for additional information
4. **Data Validation**: Verify data format and content before processing

## Integration with CI/CD

### Automated Testing

You can integrate notebook testing into your CI/CD pipeline:

```bash
# Run notebooks programmatically
jupyter nbconvert --to notebook --execute notebooks/quick_test.ipynb
jupyter nbconvert --to notebook --execute notebooks/api_testing.ipynb
```

### Result Export

Notebooks automatically export results to CSV files with timestamps:
- `test_results_variations_YYYYMMDD_HHMMSS.csv`
- `test_results_search_YYYYMMDD_HHMMSS.csv`
- `test_results_thresholds_YYYYMMDD_HHMMSS.csv`
- `test_results_performance_YYYYMMDD_HHMMSS.csv`

## Contributing

### Adding New Tests

1. **Create New Notebook**: Add new `.ipynb` files for specific testing scenarios
2. **Update README**: Document new notebooks and their purposes
3. **Follow Patterns**: Use consistent structure and naming conventions
4. **Include Documentation**: Add markdown cells explaining test purposes

### Notebook Standards

- **Clear Structure**: Use markdown cells for organization
- **Error Handling**: Include proper exception handling
- **Documentation**: Explain what each cell does
- **Export Results**: Include data export functionality
- **Visualization**: Add charts and graphs where appropriate

## Support

For issues with the notebooks:
1. Check the troubleshooting section above
2. Review API documentation
3. Check database connectivity
4. Verify all dependencies are installed

The notebooks are designed to be self-documenting and include detailed explanations for each testing scenario. 