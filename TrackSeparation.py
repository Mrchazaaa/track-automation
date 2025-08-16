#!/usr/bin/env python3
"""
LALAL.AI Stem Separation Script

This script uses the LALAL.AI API to separate drums and vocals from an MP3 file.
Requires an API key from LALAL.AI (https://www.lalal.ai/api/)

Usage:
    python lalal_separator.py input_file.mp3

Requirements:
    pip install requests
"""

import argparse
import os
import sys
import time
import json
import requests
from pathlib import Path


class LalalAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.lalal.ai/api"
        self.headers = {
            "Authorization": f"license {api_key}"
        }

    def check_limits(self):
        """Check account limits and usage"""
        response = requests.get(
            f"https://www.lalal.ai/billing/get-limits/",
            params={"key": self.api_key}
        )
        print(f"Limits check status code: {response.status_code}")
        print(f"Limits check response: {response.text}")

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("status") == "success":
                    return data
                else:
                    raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
            except ValueError:
                print("Warning: Could not parse limits response as JSON")
                return {"status": "error", "error": "Invalid JSON response"}
        else:
            raise Exception(f"Failed to check limits (Status: {response.status_code}): {response.text}")

    def upload_file(self, file_path):
        """Upload file to LALAL.AI"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)

        print(f"Uploading file: {filename}")

        with open(file_path, 'rb') as f:
            file_data = f.read()

        headers = self.headers.copy()
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        response = requests.post(
            f"{self.base_url}/upload/",
            headers=headers,
            data=file_data
        )

        print(f"Upload response status code: {response.status_code}")
        print(f"Upload response: {response.text}")

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    return result
                else:
                    raise Exception(f"Upload failed: {result.get('error', 'Unknown error')}")
            except ValueError as e:
                raise Exception(f"Failed to parse upload response as JSON: {response.text}")
        else:
            raise Exception(f"Upload failed (Status: {response.status_code}): {response.text}")

    def split_audio(self, file_id, stem):
        """
        Split audio into stems
        stems: list of stems to extract ("vocals", "drum", "bass", "piano", etc.)
        """
        # Create parameters for each stem
        split_params = [{
            "id": file_id,
            "stem": stem,
            "enhanced_processing_enabled": True}]

        params_json = json.dumps(split_params)

        print(f"Starting split with params: {params_json}")

        response = requests.post(
            f"{self.base_url}/split/",
            headers=self.headers,
            data={"params": params_json}
        )

        print(f"Split response status code: {response.status_code}")
        print(f"Split response: {response.text}")

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    return result
                else:
                    raise Exception(f"Split failed: {result.get('error', 'Unknown error')}")
            except ValueError as e:
                raise Exception(f"Failed to parse split response as JSON: {response.text}")
        else:
            raise Exception(f"Split failed (Status: {response.status_code}): {response.text}")

    def check_status(self, file_id):
        """Check processing status"""
        response = requests.post(
            f"{self.base_url}/check/",
            headers=self.headers,
            data={"id": file_id}
        )

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    return result
                else:
                    raise Exception(f"Status check failed: {result.get('error', 'Unknown error')}")
            except ValueError as e:
                raise Exception(f"Failed to parse status response as JSON: {response.text}")
        else:
            raise Exception(f"Status check failed (Status: {response.status_code}): {response.text}")

    def download_file(self, url, output_path):
        """Download a file from URL"""
        print(f"Downloading from: {url}")
        print(f"Saving to: {output_path}")

        response = requests.get(url, stream=True)

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"✓ Downloaded: {output_path}")
            return True
        else:
            raise Exception(f"Download failed (Status: {response.status_code}): {response.text}")

    def wait_for_completion(self, file_id, timeout=600):
        """Wait for processing to complete"""
        start_time = time.time()

        print(f"⏳ Waiting for processing to complete (timeout: {timeout}s)...")

        while (time.time() - start_time) < timeout:
            try:
                status_result = self.check_status(file_id)
                file_status = status_result.get("result", {}).get(file_id, {})

                print(f"Current status: {json.dumps(file_status, indent=2)}")

                if file_status.get("status") == "success":
                    task_info = file_status.get("task", {})
                    split_info = file_status.get("split")

                    if task_info.get("state") == "success" and split_info:
                        print("✅ Processing completed successfully!")
                        return split_info
                    elif task_info.get("state") == "error":
                        raise Exception(f"Processing failed: {task_info.get('error', 'Unknown error')}")
                    elif task_info.get("state") == "progress":
                        progress = task_info.get("progress", 0)
                        print(f"⏳ Processing... {progress}%")
                    elif task_info.get("state") == "cancelled":
                        raise Exception("Processing was cancelled")
                elif file_status.get("status") == "error":
                    raise Exception(f"File processing error: {file_status.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"Error checking status: {e}")

            time.sleep(10)  # Wait 10 seconds before checking again

        raise Exception(f"Timeout reached after {timeout} seconds")


def split_instr(input_file_path, api_key, output_dir, stem, back_filename_descr):
    # Validate input file
    input_file = Path(input_file_path)
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    if input_file.suffix.lower() not in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']:
        print("⚠️  Warning: Input file should be an audio file (mp3, wav, flac, ogg, m4a)")


    # Get API key
    api_key = api_key or os.getenv('LALAL_API_KEY')
    if not api_key:
        print("❌ Error: API key required. Set LALAL_API_KEY environment variable or use --api-key")
        print("Get your API key from: https://www.lalal.ai/api/")
        sys.exit(1)

    # Set output directory
    output_dir = Path(output_dir) if output_dir else input_file.parent
    output_dir.mkdir(exist_ok=True)

    # Initialize LALAL.AI client
    client = LalalAI(api_key)

    # Check account limits
    print("🔍 Checking account limits...")
    limits_info = client.check_limits()
    if limits_info.get("status") == "success":
        print(f"💰 Account: {limits_info.get('option', 'Unknown')}")
        print(f"📧 Email: {limits_info.get('email', 'Unknown')}")
        print(f"⏱️  Duration left: {limits_info.get('process_duration_left', 0):.1f} minutes")

    # Upload file
    print(f"\n📤 Uploading: {input_file.name}")
    upload_result = client.upload_file(str(input_file))
    file_id = upload_result["id"]
    print(f"✓ File uploaded successfully. ID: {file_id}")
    print(f"  Duration: {upload_result.get('duration', 0):.1f} seconds")
    print(f"  Size: {upload_result.get('size', 0)} bytes")

    # Start splitting
    print(f"\n🎵 Starting stem separation for: {stem}")
    split_result = client.split_audio(file_id, stem)
    print("✓ Split job started successfully")

    # Wait for completion
    split_info = client.wait_for_completion(file_id)

    # Download results
    print(f"\n⬇️  Downloading results to: {output_dir}")

    # Download stem track
    if split_info.get("stem_track"):
        stem_name = split_info.get("stem", "stem")
        stem_filename = f"{input_file.stem}_{stem_name}{input_file.suffix}"
        stem_path = output_dir / stem_filename
        client.download_file(split_info["stem_track"], str(stem_path))

    # Download back track (everything else)
    if split_info.get("back_track"):
        back_filename = f"{back_filename_descr}{input_file.suffix}"
        back_path = output_dir / back_filename
        client.download_file(split_info["back_track"], str(back_path))

    print(f"\n✅ Stem separation complete! Check output directory: {output_dir}")

    return {
        "stem_track": stem_path,
        "back_track": back_path
    }


def main():
    parser = argparse.ArgumentParser(description="Separate drums and vocals from MP3 using LALAL.AI")
    parser.add_argument("--input-file", help="Path to input MP3 file")
    parser.add_argument("--api-key", help="LALAL.AI API key (or set LALAL_API_KEY environment variable)")
    parser.add_argument("--output-dir", help="Output directory (default: same as input file)")
    # parser.add_argument("--stems", nargs="+", default=["vocals", "drum"], help="Stems to extract (default: vocals drum)")

    args = parser.parse_args()

    try:
        input_file = Path(args.input_file)
        if not input_file.exists():
            print(f"❌ Error: Input file not found: {input_file}")
            sys.exit(1)


        result1 = split_instr(input_file, args.api_key, args.output_dir, "drum", f"{input_file.stem}_no_drums")
        split_instr(result1["back_track"], args.api_key, args.output_dir, "vocals", f"{input_file.stem}_no_drums_no_vocals")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
