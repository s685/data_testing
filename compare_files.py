#!/usr/bin/env python3
"""
CSV/Excel File Comparison Tool
Compares two CSV or Excel files based on key columns and generates an HTML report.
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Set, Any
import pandas as pd
from html import escape


def normalize_column_name(col_name: str) -> str:
    """Normalize column name: lowercase and strip whitespace."""
    return str(col_name).lower().strip()


def load_file(file_path: str) -> pd.DataFrame:
    """Load CSV or Excel file based on extension."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Use .csv, .xlsx, or .xls")
        
        if df.empty:
            raise ValueError(f"File is empty: {file_path}")
        
        return df
    except Exception as e:
        raise Exception(f"Error loading {file_path}: {str(e)}")


def create_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """Create mapping from normalized column names to original column names."""
    return {normalize_column_name(col): col for col in df.columns}


def find_column(normalized_name: str, column_mapping: Dict[str, str], file_name: str) -> str:
    """Find original column name from normalized name."""
    if normalized_name not in column_mapping:
        raise ValueError(f"Column '{normalized_name}' not found in {file_name}. "
                        f"Available columns: {', '.join(column_mapping.values())}")
    return column_mapping[normalized_name]


def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, 
                       key_column: str, compare_columns: List[str] = None) -> Dict[str, Any]:
    """
    Compare two dataframes based on key column.
    Returns dictionary with comparison results.
    """
    # Create column mappings
    col_map1 = create_column_mapping(df1)
    col_map2 = create_column_mapping(df2)
    
    # Normalize key column name
    norm_key = normalize_column_name(key_column)
    
    # Find actual column names in both files
    key_col1 = find_column(norm_key, col_map1, "file1")
    key_col2 = find_column(norm_key, col_map2, "file2")
    
    # Handle duplicate keys - use first occurrence
    df1_dedup = df1.drop_duplicates(subset=[key_col1], keep='first')
    df2_dedup = df2.drop_duplicates(subset=[key_col2], keep='first')
    
    # Get sets of keys
    keys1 = set(df1_dedup[key_col1].astype(str))
    keys2 = set(df2_dedup[key_col2].astype(str))
    
    common_keys = keys1 & keys2
    only_in_file1 = keys1 - keys2
    only_in_file2 = keys2 - keys1
    
    # Determine columns to compare
    if compare_columns:
        norm_compare_cols = [normalize_column_name(col) for col in compare_columns]
        compare_cols1 = [find_column(nc, col_map1, "file1") for nc in norm_compare_cols]
        compare_cols2 = [find_column(nc, col_map2, "file2") for nc in norm_compare_cols]
    else:
        # Compare all columns that exist in both files
        common_norm_cols = set(col_map1.keys()) & set(col_map2.keys())
        common_norm_cols.discard(norm_key)  # Don't compare key column
        compare_cols1 = [col_map1[nc] for nc in common_norm_cols]
        compare_cols2 = [col_map2[nc] for nc in common_norm_cols]
    
    # Find differences in common keys
    differences = []
    for key in common_keys:
        row1 = df1_dedup[df1_dedup[key_col1].astype(str) == key].iloc[0]
        row2 = df2_dedup[df2_dedup[key_col2].astype(str) == key].iloc[0]
        
        diff_cols = []
        for col1, col2 in zip(compare_cols1, compare_cols2):
            val1 = row1[col1]
            val2 = row2[col2]
            
            # Handle case-insensitive string comparison
            if isinstance(val1, str) and isinstance(val2, str):
                if val1.lower().strip() != val2.lower().strip():
                    diff_cols.append({
                        'column': col1,
                        'file1_value': val1,
                        'file2_value': val2
                    })
            elif pd.isna(val1) and pd.isna(val2):
                # Both are NaN, no difference
                continue
            elif val1 != val2:
                diff_cols.append({
                    'column': col1,
                    'file1_value': val1,
                    'file2_value': val2
                })
        
        if diff_cols:
            differences.append({
                'key': key,
                'key_column': key_col1,
                'row1': row1,
                'row2': row2,
                'differences': diff_cols
            })
    
    return {
        'df1': df1_dedup,
        'df2': df2_dedup,
        'key_col1': key_col1,
        'key_col2': key_col2,
        'common_keys': common_keys,
        'only_in_file1': only_in_file1,
        'only_in_file2': only_in_file2,
        'differences': differences,
        'compare_cols1': compare_cols1,
        'compare_cols2': compare_cols2
    }


def generate_html_report(comparison_results: Dict[str, Any], 
                         file1_name: str, file2_name: str, 
                         output_file: str = "comparison_report.html"):
    """Generate HTML report from comparison results."""
    
    df1 = comparison_results['df1']
    df2 = comparison_results['df2']
    key_col1 = comparison_results['key_col1']
    key_col2 = comparison_results['key_col2']
    common_keys = comparison_results['common_keys']
    only_in_file1 = comparison_results['only_in_file1']
    only_in_file2 = comparison_results['only_in_file2']
    differences = comparison_results['differences']
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Comparison Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 8px;
        }}
        .summary {{
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            margin: 10px 0;
            font-size: 16px;
        }}
        .summary-item strong {{
            display: inline-block;
            min-width: 200px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            background-color: white;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        .difference {{
            background-color: #fff9c4 !important;
        }}
        .file1-value {{
            background-color: #ffebee;
            padding: 4px 8px;
            border-radius: 3px;
            display: inline-block;
            margin: 2px;
        }}
        .file2-value {{
            background-color: #e8f5e9;
            padding: 4px 8px;
            border-radius: 3px;
            display: inline-block;
            margin: 2px;
        }}
        .section {{
            margin: 40px 0;
        }}
        .count-badge {{
            background-color: #2196F3;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 14px;
            margin-left: 10px;
        }}
        .timestamp {{
            color: #999;
            font-size: 14px;
            margin-top: 10px;
        }}
        .no-data {{
            color: #999;
            font-style: italic;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>File Comparison Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-item"><strong>File 1:</strong> {escape(file1_name)}</div>
            <div class="summary-item"><strong>File 2:</strong> {escape(file2_name)}</div>
            <div class="summary-item"><strong>Key Column:</strong> {escape(key_col1)}</div>
            <div class="summary-item"><strong>Total Records in File 1:</strong> {len(df1)}</div>
            <div class="summary-item"><strong>Total Records in File 2:</strong> {len(df2)}</div>
            <div class="summary-item"><strong>Common Keys:</strong> {len(common_keys)}</div>
            <div class="summary-item"><strong>Only in File 1:</strong> {len(only_in_file1)}</div>
            <div class="summary-item"><strong>Only in File 2:</strong> {len(only_in_file2)}</div>
            <div class="summary-item"><strong>Records with Differences:</strong> {len(differences)}</div>
        </div>
"""
    
    # Section: Differences in common records
    if differences:
        html_content += f"""
        <div class="section">
            <h2>Common Records with Differences <span class="count-badge">{len(differences)}</span></h2>
            <table>
                <tr>
                    <th>{escape(key_col1)}</th>
                    <th>Column</th>
                    <th>File 1 Value</th>
                    <th>File 2 Value</th>
                </tr>
"""
        for diff in differences:
            for d in diff['differences']:
                html_content += f"""
                <tr class="difference">
                    <td>{escape(str(diff['key']))}</td>
                    <td>{escape(str(d['column']))}</td>
                    <td><span class="file1-value">{escape(str(d['file1_value']))}</span></td>
                    <td><span class="file2-value">{escape(str(d['file2_value']))}</span></td>
                </tr>
"""
        html_content += """
            </table>
        </div>
"""
    else:
        html_content += """
        <div class="section">
            <h2>Common Records with Differences</h2>
            <div class="no-data">No differences found in common records.</div>
        </div>
"""
    
    # Section: Records only in File 1
    if only_in_file1:
        html_content += f"""
        <div class="section">
            <h2>Records Only in File 1 <span class="count-badge">{len(only_in_file1)}</span></h2>
            <table>
                <tr>
"""
        # Add column headers
        for col in df1.columns:
            html_content += f"<th>{escape(str(col))}</th>"
        html_content += "</tr>"
        
        # Add rows
        for key in sorted(only_in_file1):
            row = df1[df1[key_col1].astype(str) == key].iloc[0]
            html_content += "<tr>"
            for col in df1.columns:
                html_content += f"<td>{escape(str(row[col]))}</td>"
            html_content += "</tr>"
        
        html_content += """
            </table>
        </div>
"""
    else:
        html_content += """
        <div class="section">
            <h2>Records Only in File 1</h2>
            <div class="no-data">No unique records in File 1.</div>
        </div>
"""
    
    # Section: Records only in File 2
    if only_in_file2:
        html_content += f"""
        <div class="section">
            <h2>Records Only in File 2 <span class="count-badge">{len(only_in_file2)}</span></h2>
            <table>
                <tr>
"""
        # Add column headers
        for col in df2.columns:
            html_content += f"<th>{escape(str(col))}</th>"
        html_content += "</tr>"
        
        # Add rows
        for key in sorted(only_in_file2):
            row = df2[df2[key_col2].astype(str) == key].iloc[0]
            html_content += "<tr>"
            for col in df2.columns:
                html_content += f"<td>{escape(str(row[col]))}</td>"
            html_content += "</tr>"
        
        html_content += """
            </table>
        </div>
"""
    else:
        html_content += """
        <div class="section">
            <h2>Records Only in File 2</h2>
            <div class="no-data">No unique records in File 2.</div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    # Write HTML to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML report generated: {output_file}")


def main():
    """Main function to parse arguments and run comparison."""
    parser = argparse.ArgumentParser(
        description='Compare two CSV or Excel files based on key columns.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compare_files.py file1.csv file2.csv --key-columns ID
  python compare_files.py data1.xlsx data2.xlsx --key-columns "User ID" --compare-columns "Name,Amount,Status"
  python compare_files.py file1.csv file2.xlsx --key-columns ID --output report.html
        """
    )
    
    parser.add_argument('file1', help='Path to first file (CSV or Excel)')
    parser.add_argument('file2', help='Path to second file (CSV or Excel)')
    parser.add_argument('--key-columns', '-k', required=True,
                       help='Key column name for matching records (case-insensitive)')
    parser.add_argument('--compare-columns', '-c', 
                       help='Comma-separated list of columns to compare (optional, compares all if not specified)')
    parser.add_argument('--output', '-o', default='comparison_report.html',
                       help='Output HTML file name (default: comparison_report.html)')
    
    args = parser.parse_args()
    
    try:
        # Load files
        print(f"Loading {args.file1}...")
        df1 = load_file(args.file1)
        print(f"  Loaded {len(df1)} records with {len(df1.columns)} columns")
        
        print(f"Loading {args.file2}...")
        df2 = load_file(args.file2)
        print(f"  Loaded {len(df2)} records with {len(df2.columns)} columns")
        
        # Parse compare columns
        compare_cols = None
        if args.compare_columns:
            compare_cols = [col.strip() for col in args.compare_columns.split(',')]
        
        # Perform comparison
        print("Comparing files...")
        results = compare_dataframes(df1, df2, args.key_columns, compare_cols)
        
        # Generate HTML report
        print("Generating HTML report...")
        generate_html_report(results, args.file1, args.file2, args.output)
        
        # Print summary
        print("\n=== Comparison Summary ===")
        print(f"Common keys: {len(results['common_keys'])}")
        print(f"Only in File 1: {len(results['only_in_file1'])}")
        print(f"Only in File 2: {len(results['only_in_file2'])}")
        print(f"Records with differences: {len(results['differences'])}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

