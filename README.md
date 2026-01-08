# CSV/Excel File Comparison Tool

A Python command-line tool that compares two CSV or Excel files based on specified key columns and generates a comprehensive HTML report showing differences, common records, and unique records in each file.

## Features

- **Multiple File Format Support**: Works with CSV (.csv) and Excel (.xlsx, .xls) files
- **Case-Insensitive Matching**: Column names are matched case-insensitively
- **Space-Tolerant**: Handles column names with spaces and extra whitespace
- **Flexible Comparison**: Compare specific columns or all common columns
- **Comprehensive HTML Report**: 
  - Summary statistics
  - Side-by-side comparison of differences
  - Records unique to each file
  - Color-coded highlighting for easy visualization
- **Duplicate Handling**: Automatically uses first occurrence when duplicate keys exist

## Installation

1. Ensure you have Python 3.7 or higher installed

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install pandas openpyxl
```

## Usage

### Basic Usage

Compare two files using a key column:

```bash
python compare_files.py file1.csv file2.csv --key-columns ID
```

### Specify Columns to Compare

Compare only specific columns:

```bash
python compare_files.py file1.csv file2.xlsx --key-columns "User ID" --compare-columns "Name,Amount,Status"
```

### Custom Output File

Specify a custom output HTML file name:

```bash
python compare_files.py data1.xlsx data2.xlsx --key-columns ID --output my_report.html
```

## Command-Line Arguments

- `file1`: Path to the first file (required)
- `file2`: Path to the second file (required)
- `--key-columns, -k`: Key column name for matching records (required, case-insensitive)
- `--compare-columns, -c`: Comma-separated list of columns to compare (optional, compares all common columns if not specified)
- `--output, -o`: Output HTML file name (default: comparison_report.html)

## Examples

### Example 1: Compare CSV files with key column "ID"

```bash
python compare_files.py sales_2023.csv sales_2024.csv --key-columns ID
```

### Example 2: Compare Excel files with specific columns

```bash
python compare_files.py inventory_old.xlsx inventory_new.xlsx --key-columns "Product Code" --compare-columns "Quantity,Price,Supplier"
```

### Example 3: Mixed file formats with space in column name

```bash
python compare_files.py customers.csv customers_updated.xlsx --key-columns "Customer ID" --output customer_comparison.html
```

## HTML Report

The generated HTML report includes:

1. **Summary Section**
   - File names
   - Key column used
   - Total records in each file
   - Count of common keys
   - Count of unique records in each file
   - Count of records with differences

2. **Common Records with Differences**
   - Side-by-side comparison showing:
     - Key value
     - Column name
     - Value from File 1 (highlighted in red)
     - Value from File 2 (highlighted in green)

3. **Records Only in File 1**
   - Complete rows that exist only in the first file

4. **Records Only in File 2**
   - Complete rows that exist only in the second file

## Features in Detail

### Case-Insensitive Column Matching

Column names are automatically normalized for matching:
- "UserID", "userid", "USER ID" are all treated as the same column
- Whitespace is trimmed from column names

### String Comparison

When comparing text values:
- Comparison is case-insensitive
- Leading/trailing whitespace is ignored

### Duplicate Key Handling

If a key appears multiple times in a file:
- Only the first occurrence is used
- Other occurrences are ignored
- This prevents comparison errors

### Missing Columns

If a specified comparison column doesn't exist:
- An error message is displayed
- Available columns are listed
- The script exits gracefully

## Error Handling

The tool handles various error scenarios:
- File not found
- Unsupported file format
- Empty files
- Missing key columns
- Invalid column names

Error messages are clear and informative, helping you resolve issues quickly.

## Requirements

- Python 3.7+
- pandas >= 2.0.0
- openpyxl >= 3.0.0

## Output Example

After running the comparison, you'll see output like:

```
Loading file1.csv...
  Loaded 150 records with 5 columns
Loading file2.csv...
  Loaded 155 records with 5 columns
Comparing files...
Generating HTML report...
HTML report generated: comparison_report.html

=== Comparison Summary ===
Common keys: 145
Only in File 1: 5
Only in File 2: 10
Records with differences: 12
```

## License

This tool is provided as-is for data comparison purposes.

## Support

For issues or questions, please review the error messages carefully. The tool provides detailed feedback about:
- File loading issues
- Column name problems
- Data format issues

