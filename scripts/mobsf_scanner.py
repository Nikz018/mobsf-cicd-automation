#!/usr/bin/env python3
import requests
import argparse
import json
import os
from pathlib import Path

class MobSFScanner:
    def __init__(self, server_url="http://localhost:8000", api_key=None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key or os.getenv('MOBSF_API_KEY', '')
        self.headers = {'Authorization': self.api_key} if self.api_key else {}

    def upload_file(self, file_path):
        url = f"{self.server_url}/api/v1/upload"
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
            response = requests.post(url, files=files, headers=self.headers)
        if response.status_code != 200:
            print(f"Upload failed with status {response.status_code}: {response.text}")
        return response.json()

    def start_scan(self, file_name, hash_value):
        url = f"{self.server_url}/api/v1/scan"
        data = {'file_name': file_name, 'hash': hash_value}
        response = requests.post(url, data=data, headers=self.headers)
        return response.json()

    def get_report(self, hash_value, report_type='json'):
        url = f"{self.server_url}/api/v1/report_{report_type}"
        data = {'hash': hash_value}
        response = requests.post(url, data=data, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Report generation failed: {response.status_code} - {response.text}")
            return None
            
        if report_type == 'json':
            return response.json()
        else:
            # Check if PDF response is valid
            if response.content.startswith(b'%PDF') and len(response.content) > 1000:
                return response.content
            else:
                print(f"Invalid PDF response (length: {len(response.content)}): {response.text[:200]}")
                return None

    def scan_app(self, app_path, output_dir='reports'):
        print(f"Uploading {app_path}...")
        upload_result = self.upload_file(app_path)
        
        if 'hash' not in upload_result:
            raise Exception(f"Upload failed: {upload_result}")
        
        hash_value = upload_result['hash']
        file_name = upload_result['file_name']
        
        print(f"Starting scan for {file_name}...")
        scan_result = self.start_scan(file_name, hash_value)
        
        print("Generating reports...")
        json_report = self.get_report(hash_value, 'json')
        
        os.makedirs(output_dir, exist_ok=True)
        
        if json_report:
            json_path = f"{output_dir}/{Path(app_path).stem}_report.json"
            with open(json_path, 'w') as f:
                json.dump(json_report, f, indent=2)
            print(f"JSON report saved: {json_path}")
            
            # Create a summary report
            summary_path = f"{output_dir}/{Path(app_path).stem}_summary.txt"
            self.create_summary_report(json_report, summary_path)
            print(f"Summary report saved: {summary_path}")
        
        # Generate PDF report (mandatory)
        print("Generating PDF report...")
        pdf_report = self.get_report(hash_value, 'pdf')
        if not pdf_report:
            raise Exception("PDF report generation failed - this is mandatory")
        
        pdf_path = f"{output_dir}/{Path(app_path).stem}_report.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_report)
        print(f"PDF report saved: {pdf_path}")
        
        return json_report
    
    def create_summary_report(self, json_report, output_path):
        """Create a human-readable summary report"""
        with open(output_path, 'w') as f:
            f.write("=== MobSF Security Scan Summary ===\n\n")
            
            if 'file_name' in json_report:
                f.write(f"App: {json_report['file_name']}\n")
            if 'app_name' in json_report:
                f.write(f"App Name: {json_report['app_name']}\n")
            if 'package_name' in json_report:
                f.write(f"Package: {json_report['package_name']}\n")
            
            f.write("\n=== Security Summary ===\n")
            f.write(f"Total Issues Found: {len(str(json_report))} characters of data\n")
            f.write("\nFull details available in JSON report.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MobSF Security Scanner')
    parser.add_argument('--app', required=True, help='Path to mobile app file')
    parser.add_argument('--server', default='http://localhost:8000', help='MobSF server URL')
    parser.add_argument('--output', default='reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    api_key = os.getenv('MOBSF_API_KEY')
    if not api_key:
        print("Warning: No API key found, trying without authentication")
    scanner = MobSFScanner(args.server, api_key)
    scanner.scan_app(args.app, args.output)