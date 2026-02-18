#!/usr/bin/env python3
"""
Extract simulation results from results.txt and create a CSV file.
Parses sim_seconds, ipc, and miss rates organized by width and threads.
"""

import re
import csv
from pathlib import Path

def extract_results(input_file, output_file):
    """
    Extract results from the results_fixed.txt file and save to CSV.
    The file has header lines starting with === followed by data lines also starting with ===.
    """
    
    results = []
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for header line (e.g., === results/stats_o3_w2_t16_m32.txt)
        match = re.match(r'===\s*results/stats_o3_w(\d+)_t(\d+)_m\d+\.txt', line)
        if match:
            width = int(match.group(1))
            threads = int(match.group(2))
            
            # The next line contains the data
            if i + 1 < len(lines):
                data_line = lines[i + 1].strip()
                
                # Extract sim_seconds
                sim_match = re.search(r'sim_seconds\s+([\d.e+-]+)', data_line)
                sim_seconds = float(sim_match.group(1)) if sim_match else 0.0
                
                # Extract IPC (ipc_total)
                ipc_match = re.search(r'ipc_total\s+([\d.]+)', data_line)
                ipc = float(ipc_match.group(1)) if ipc_match else 0.0
                
                # Extract L1d cache miss rate
                l1d_match = re.search(r'dcache\.overall_miss_rate::total\s+([\d.]+)', data_line)
                l1d_miss = float(l1d_match.group(1)) if l1d_match else 0.0
                
                # Extract L1i cache miss rate
                l1i_match = re.search(r'icache\.overall_miss_rate::total\s+([\d.]+)', data_line)
                l1i_miss = float(l1i_match.group(1)) if l1i_match else 0.0
                
                results.append({
                    'width': width,
                    'threads': threads,
                    'sim_seconds': sim_seconds,
                    'ipc': ipc,
                    'l1d_miss_rate': l1d_miss,
                    'l1i_miss_rate': l1i_miss,
                })
                
                i += 2  # Skip both header and data line
            else:
                i += 1
        else:
            i += 1
    
    # Sort results by width, then by threads
    results.sort(key=lambda x: (x['width'], x['threads']))
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['width', 'threads', 'sim_seconds', 'ipc', 'l1d_miss_rate', 'l1i_miss_rate'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ Extracted {len(results)} results to {output_file}")
    print(f"\nSample of extracted data:")
    print(f"{'width':<8} {'threads':<10} {'sim_seconds':<15} {'ipc':<10} {'l1d_miss':<12} {'l1i_miss':<12}")
    print("-" * 75)
    for result in results[:6]:
        print(f"{result['width']:<8} {result['threads']:<10} {result['sim_seconds']:<15.6f} {result['ipc']:<10.4f} {result['l1d_miss_rate']:<12.4f} {result['l1i_miss_rate']:<12.4f}")
    if len(results) > 6:
        print(f"... ({len(results) - 6} more results)")

if __name__ == '__main__':
    input_file = Path(__file__).parent / 'results_fixed.txt'
    output_file = Path(__file__).parent / 'results.csv'
    
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        exit(1)
    
    extract_results(str(input_file), str(output_file))
