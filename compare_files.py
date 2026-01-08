#!/usr/bin/env python3
"""
CSV/Excel File Comparison Tool - Polars Edition (Lightning Fast!)
Uses Polars (Rust-based) for 10-50x faster performance than pandas.
"""

import argparse
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Set, Any
from html import escape
import polars as pl


def normalize_column_name(name: str) -> str:
    """Normalize column name: lowercase and strip whitespace."""
    return str(name).lower().strip()


def load_file(file_path: str) -> pl.DataFrame:
    """Load CSV or Excel file based on extension - POLARS OPTIMIZED."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.csv':
            # Polars is MUCH faster at reading CSVs
            df = pl.read_csv(file_path, infer_schema_length=10000)
        elif ext in ['.xlsx', '.xls']:
            # For Excel, use calamine engine (Rust-based, faster)
            df = pl.read_excel(file_path, engine='calamine')
        else:
            raise ValueError(f"Unsupported file format: {ext}. Use .csv, .xlsx, or .xls")
        
        if df.is_empty():
            raise ValueError(f"File is empty: {file_path}")
        
        return df
    except Exception as e:
        raise Exception(f"Error loading {file_path}: {str(e)}")


def create_column_mapping(df: pl.DataFrame) -> Dict[str, str]:
    """Create mapping from normalized column names to original column names."""
    return {normalize_column_name(col): col for col in df.columns}


def find_column(normalized_name: str, column_mapping: Dict[str, str], file_name: str) -> str:
    """Find original column name from normalized name."""
    if normalized_name not in column_mapping:
        raise ValueError(f"Column '{normalized_name}' not found in {file_name}. "
                        f"Available columns: {', '.join(column_mapping.values())}")
    return column_mapping[normalized_name]


def compare_dataframes(df1: pl.DataFrame, df2: pl.DataFrame, 
                       key_column: str, compare_columns: List[str] = None) -> Dict[str, Any]:
    """
    Compare two Polars dataframes based on key column - BLAZING FAST.
    Returns dictionary with comparison results.
    """
    start_time = time.time()
    
    # Create column mappings
    col_map1 = create_column_mapping(df1)
    col_map2 = create_column_mapping(df2)
    
    # Normalize key column name
    norm_key = normalize_column_name(key_column)
    
    # Find actual column names in both files
    key_col1 = find_column(norm_key, col_map1, "file1")
    key_col2 = find_column(norm_key, col_map2, "file2")
    
    print("  Removing duplicates...", end='', flush=True)
    # Handle duplicate keys - use first occurrence (Polars is FAST at this)
    df1_dedup = df1.unique(subset=[key_col1], keep='first')
    df2_dedup = df2.unique(subset=[key_col2], keep='first')
    
    # Create string key column for comparison with WHITESPACE TRIMMING (vectorized, super fast)
    df1_dedup = df1_dedup.with_columns(
        pl.col(key_col1).cast(pl.Utf8).str.strip_chars().alias('__key_str__')
    )
    df2_dedup = df2_dedup.with_columns(
        pl.col(key_col2).cast(pl.Utf8).str.strip_chars().alias('__key_str__')
    )
    print(" Done", flush=True)
    
    print("  Finding common and unique keys...", end='', flush=True)
    # Get sets of keys (blazing fast with Polars)
    keys1 = set(df1_dedup['__key_str__'].to_list())
    keys2 = set(df2_dedup['__key_str__'].to_list())
    
    common_keys = keys1 & keys2
    only_in_file1 = keys1 - keys2
    only_in_file2 = keys2 - keys1
    print(" Done", flush=True)
    
    # Determine columns to compare
    print("  Determining columns to compare...", end='', flush=True)
    if compare_columns:
        norm_compare_cols = [normalize_column_name(col) for col in compare_columns]
        compare_cols1 = [find_column(nc, col_map1, "file1") for nc in norm_compare_cols]
        compare_cols2 = [find_column(nc, col_map2, "file2") for nc in norm_compare_cols]
    else:
        # Compare all columns that exist in both files
        common_norm_cols = set(col_map1.keys()) & set(col_map2.keys())
        common_norm_cols.discard(norm_key)
        compare_cols1 = [col_map1[nc] for nc in common_norm_cols]
        compare_cols2 = [col_map2[nc] for nc in common_norm_cols]
    print(" Done", flush=True)
    
    # Create dictionaries for fast lookup (Polars to dict is very fast)
    print(f"  Comparing {len(common_keys)} common records...", end='', flush=True)
    
    # Convert to row-oriented dicts for comparison (only for common keys)
    df1_common = df1_dedup.filter(pl.col('__key_str__').is_in(list(common_keys)))
    df2_common = df2_dedup.filter(pl.col('__key_str__').is_in(list(common_keys)))
    
    # Create lookup dictionaries
    df1_dict = {row['__key_str__']: row for row in df1_common.to_dicts()}
    df2_dict = {row['__key_str__']: row for row in df2_common.to_dicts()}
    
    differences = []
    
    for key in common_keys:
        row1 = df1_dict.get(key)
        row2 = df2_dict.get(key)
        
        if not row1 or not row2:
            continue
        
        diff_cols = []
        for col1, col2 in zip(compare_cols1, compare_cols2):
            val1 = row1.get(col1)
            val2 = row2.get(col2)
            
            # Handle None/null values
            if val1 is None and val2 is None:
                continue
            elif val1 is None or val2 is None:
                diff_cols.append({
                    'column': col1,
                    'file1_value': str(val1).strip() if val1 is not None else '',
                    'file2_value': str(val2).strip() if val2 is not None else ''
                })
            # String comparison (case-insensitive, strip whitespace)
            elif isinstance(val1, str) and isinstance(val2, str):
                # Strip leading/trailing spaces from both values before comparing
                val1_clean = val1.strip()
                val2_clean = val2.strip()
                if val1_clean.lower() != val2_clean.lower():
                    diff_cols.append({
                        'column': col1,
                        'file1_value': val1,  # Show original with spaces
                        'file2_value': val2   # Show original with spaces
                    })
            # Numeric or other comparison
            else:
                # Convert to string, strip spaces, compare
                str_val1 = str(val1).strip()
                str_val2 = str(val2).strip()
                if str_val1 != str_val2:
                    diff_cols.append({
                        'column': col1,
                        'file1_value': str(val1),
                        'file2_value': str(val2)
                    })
        
        if diff_cols:
            differences.append({
                'key': key,
                'key_column': key_col1,
                'row1': row1,
                'row2': row2,
                'differences': diff_cols
            })
    
    print(f" Found {len(differences)} with differences", flush=True)
    
    elapsed = time.time() - start_time
    print(f"  Comparison completed in {elapsed:.2f}s ⚡", flush=True)
    
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
    """Generate HTML report from comparison results - OPTIMIZED."""
    
    print("  Building HTML report...", end='', flush=True)
    start_time = time.time()
    
    df1 = comparison_results['df1']
    df2 = comparison_results['df2']
    key_col1 = comparison_results['key_col1']
    key_col2 = comparison_results['key_col2']
    common_keys = comparison_results['common_keys']
    only_in_file1 = comparison_results['only_in_file1']
    only_in_file2 = comparison_results['only_in_file2']
    differences = comparison_results['differences']
    common_keys_matching = len(common_keys) - len(differences)
    total_non_common = len(only_in_file1) + len(only_in_file2)
    
    # Use list for efficient string building
    html_parts = []
    
    html_parts.append(f"""<!DOCTYPE html>
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
        .powered-by {{
            background-color: #fff3e0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 14px;
            color: #e65100;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>File Comparison Report ⚡</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <div class="powered-by">⚡ Powered by Polars (Rust) - Lightning Fast Performance!</div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-item"><strong>File 1:</strong> {escape(file1_name)}</div>
            <div class="summary-item"><strong>File 2:</strong> {escape(file2_name)}</div>
            <div class="summary-item"><strong>Key Column:</strong> {escape(key_col1)}</div>
            <div class="summary-item"><strong>Total Records in File 1:</strong> {len(df1)}</div>
            <div class="summary-item"><strong>Total Records in File 2:</strong> {len(df2)}</div>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <div class="summary-item" style="background-color: #e8f5e9; padding: 8px; margin: 8px -10px; border-radius: 4px;">
                <strong>Common Keys (Total):</strong> {len(common_keys)}
            </div>
            <div class="summary-item" style="margin-left: 20px;">
                <strong>Matching Records:</strong> {common_keys_matching}
            </div>
            <div class="summary-item" style="margin-left: 20px;">
                <strong>Records with Differences:</strong> {len(differences)}
            </div>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <div class="summary-item" style="background-color: #ffebee; padding: 8px; margin: 8px -10px; border-radius: 4px;">
                <strong>Non-Common Keys (Total):</strong> {total_non_common}
            </div>
            <div class="summary-item" style="margin-left: 20px;">
                <strong>Only in File 1:</strong> {len(only_in_file1)}
            </div>
            <div class="summary-item" style="margin-left: 20px;">
                <strong>Only in File 2:</strong> {len(only_in_file2)}
            </div>
        </div>
""")
    
    # Differences section
    if differences:
        html_parts.append(f"""
        <div class="section">
            <h2>🔍 Column Differences in Common Keys <span class="count-badge">{len(differences)}</span></h2>
            <p style="color: #666; margin-top: -10px; margin-bottom: 20px;">
                Showing ONLY the {len(differences)} record(s) with differences out of {len(common_keys)} common keys.
                ({common_keys_matching} records match perfectly)
            </p>
            <table>
                <tr>
                    <th>{escape(key_col1)}</th>
                    <th>Column</th>
                    <th>File 1 Value</th>
                    <th>File 2 Value</th>
                </tr>
""")
        
        for diff in differences:
            for d in diff['differences']:
                html_parts.append(f"""
                <tr class="difference">
                    <td>{escape(str(diff['key']))}</td>
                    <td>{escape(str(d['column']))}</td>
                    <td><span class="file1-value">{escape(str(d['file1_value']))}</span></td>
                    <td><span class="file2-value">{escape(str(d['file2_value']))}</span></td>
                </tr>
""")
        
        html_parts.append("""
            </table>
        </div>
""")
    else:
        html_parts.append(f"""
        <div class="section">
            <h2>🔍 Column Differences in Common Keys</h2>
            <div class="no-data">✓ Perfect match! All {len(common_keys)} common records have identical values in all compared columns.</div>
        </div>
""")
    
    # Records only in File 1
    if only_in_file1:
        html_parts.append(f"""
        <div class="section">
            <h2>📄 Non-Common Keys: Only in File 1 <span class="count-badge">{len(only_in_file1)}</span></h2>
            <p style="color: #666; margin-top: -10px; margin-bottom: 20px;">
                These {len(only_in_file1)} record(s) exist in File 1 but NOT in File 2.
            </p>
            <table>
                <tr>
""")
        
        for col in df1.columns:
            if col != '__key_str__':
                html_parts.append(f"<th>{escape(str(col))}</th>")
        html_parts.append("</tr>\n")
        
        # Filter for only_in_file1 keys
        df1_unique = df1.filter(pl.col('__key_str__').is_in(list(only_in_file1)))
        
        for row in df1_unique.to_dicts():
            html_parts.append("<tr>")
            for col in df1.columns:
                if col != '__key_str__':
                    val = row.get(col, '')
                    html_parts.append(f"<td>{escape(str(val))}</td>")
            html_parts.append("</tr>\n")
        
        html_parts.append("""
            </table>
        </div>
""")
    else:
        html_parts.append("""
        <div class="section">
            <h2>📄 Non-Common Keys: Only in File 1</h2>
            <div class="no-data">✓ No unique records in File 1. All keys exist in File 2.</div>
        </div>
""")
    
    # Records only in File 2
    if only_in_file2:
        html_parts.append(f"""
        <div class="section">
            <h2>📄 Non-Common Keys: Only in File 2 <span class="count-badge">{len(only_in_file2)}</span></h2>
            <p style="color: #666; margin-top: -10px; margin-bottom: 20px;">
                These {len(only_in_file2)} record(s) exist in File 2 but NOT in File 1.
            </p>
            <table>
                <tr>
""")
        
        for col in df2.columns:
            if col != '__key_str__':
                html_parts.append(f"<th>{escape(str(col))}</th>")
        html_parts.append("</tr>\n")
        
        # Filter for only_in_file2 keys
        df2_unique = df2.filter(pl.col('__key_str__').is_in(list(only_in_file2)))
        
        for row in df2_unique.to_dicts():
            html_parts.append("<tr>")
            for col in df2.columns:
                if col != '__key_str__':
                    val = row.get(col, '')
                    html_parts.append(f"<td>{escape(str(val))}</td>")
            html_parts.append("</tr>\n")
        
        html_parts.append("""
            </table>
        </div>
""")
    else:
        html_parts.append("""
        <div class="section">
            <h2>📄 Non-Common Keys: Only in File 2</h2>
            <div class="no-data">✓ No unique records in File 2. All keys exist in File 1.</div>
        </div>
""")
    
    html_parts.append("""
    </div>
</body>
</html>
""")
    
    # Write HTML to file
    html_content = ''.join(html_parts)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    elapsed = time.time() - start_time
    print(f" Done ({elapsed:.2f}s)", flush=True)
    print(f"HTML report generated: {output_file}")


def main():
    """Main function to parse arguments and run comparison."""
    parser = argparse.ArgumentParser(
        description='Compare two CSV or Excel files - Polars Edition (Lightning Fast!).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compare_files.py file1.csv file2.csv --key-columns ID
  python compare_files.py data1.xlsx data2.xlsx --key-columns "User ID" --compare-columns "Name,Amount,Status"
  python compare_files.py file1.csv file2.xlsx --key-columns ID --output report.html

Performance:
  Powered by Polars (Rust-based) for 10-50x faster performance than pandas!
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
    
    print("\n" + "="*60)
    print("⚡ POLARS-POWERED FILE COMPARISON (Lightning Fast!)")
    print("="*60 + "\n")
    
    overall_start = time.time()
    
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
        common_keys_matching = len(results['common_keys']) - len(results['differences'])
        total_non_common = len(results['only_in_file1']) + len(results['only_in_file2'])
        
        print("\n" + "="*60)
        print("COMPARISON SUMMARY")
        print("="*60)
        print(f"\nCOMMON KEYS: {len(results['common_keys'])} total")
        print(f"  - Matching records: {common_keys_matching}")
        print(f"  - Records with differences: {len(results['differences'])}")
        print(f"\nNON-COMMON KEYS: {total_non_common} total")
        print(f"  - Only in File 1: {len(results['only_in_file1'])}")
        print(f"  - Only in File 2: {len(results['only_in_file2'])}")
        print("="*60)
        
        total_time = time.time() - overall_start
        print(f"\n⚡ Total execution time: {total_time:.2f}s (Lightning Fast!)")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
