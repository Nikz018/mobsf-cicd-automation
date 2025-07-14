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
            if response.content.startswith(b'%PDF'):
                return response.content
            else:
                print(f"Invalid PDF response: {response.text[:200]}")
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
        pdf_report = self.get_report(hash_value, 'pdf')
        
        os.makedirs(output_dir, exist_ok=True)
        
        json_path = f"{output_dir}/{Path(app_path).stem}_report.json"
        
        if json_report:
            with open(json_path, 'w') as f:
                json.dump(json_report, f, indent=2)
            print(f"JSON report saved: {json_path}")
        
        if pdf_report:
            pdf_path = f"{output_dir}/{Path(app_path).stem}_report.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_report)
            print(f"PDF report saved: {pdf_path}")
        else:
            print("PDF report generation failed - skipping PDF")
        
        return json_report

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