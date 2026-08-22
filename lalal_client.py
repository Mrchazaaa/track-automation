"""LALAL.AI HTTP integration."""

import json
import os
import time

import requests


class LalalAI:
    """Client for uploading, separating, polling, and downloading audio stems."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.lalal.ai/api"
        self.headers = {"Authorization": f"license {api_key}"}

    @staticmethod
    def _success_response(response, operation):
        if response.status_code != 200:
            raise Exception(f"{operation} failed (Status: {response.status_code}): {response.text}")
        try:
            result = response.json()
        except ValueError as error:
            raise Exception(f"Failed to parse {operation.lower()} response as JSON: {response.text}") from error
        if result.get("status") != "success":
            raise Exception(f"{operation} failed: {result.get('error', 'Unknown error')}")
        return result

    def check_limits(self):
        response = requests.get(
            "https://www.lalal.ai/billing/get-limits/", params={"key": self.api_key}
        )
        print(f"Limits check status code: {response.status_code}")
        print(f"Limits check response: {response.text}")
        return self._success_response(response, "Limits check")

    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        filename = os.path.basename(file_path)
        print(f"Uploading file: {filename}")
        with open(file_path, "rb") as file:
            file_data = file.read()
        headers = {**self.headers, "Content-Disposition": f'attachment; filename="{filename}"'}
        response = requests.post(f"{self.base_url}/upload/", headers=headers, data=file_data)
        print(f"Upload response status code: {response.status_code}")
        print(f"Upload response: {response.text}")
        return self._success_response(response, "Upload")

    def split_audio(self, file_id, stem):
        params = json.dumps([{
            "id": file_id,
            "stem": stem,
            "enhanced_processing_enabled": True,
        }])
        print(f"Starting split with params: {params}")
        response = requests.post(
            f"{self.base_url}/split/", headers=self.headers, data={"params": params}
        )
        print(f"Split response status code: {response.status_code}")
        print(f"Split response: {response.text}")
        return self._success_response(response, "Split")

    def check_status(self, file_id):
        response = requests.post(
            f"{self.base_url}/check/", headers=self.headers, data={"id": file_id}
        )
        return self._success_response(response, "Status check")

    def download_file(self, url, output_path):
        print(f"Downloading from: {url}")
        print(f"Saving to: {output_path}")
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise Exception(f"Download failed (Status: {response.status_code}): {response.text}")
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"✓ Downloaded: {output_path}")
        return True

    def wait_for_completion(self, file_id, timeout=600):
        start_time = time.time()
        print(f"⏳ Waiting for processing to complete (timeout: {timeout}s)...")
        while time.time() - start_time < timeout:
            try:
                file_status = self.check_status(file_id).get("result", {}).get(file_id, {})
                print(f"Current status: {json.dumps(file_status, indent=2)}")
                if file_status.get("status") == "error":
                    raise Exception(f"File processing error: {file_status.get('error', 'Unknown error')}")
                task = file_status.get("task", {})
                if task.get("state") == "success" and file_status.get("split"):
                    print("✅ Processing completed successfully!")
                    return file_status["split"]
                if task.get("state") in {"error", "cancelled"}:
                    raise Exception(f"Processing {task.get('state')}: {task.get('error', '')}")
                if task.get("state") == "progress":
                    print(f"⏳ Processing... {task.get('progress', 0)}%")
            except Exception as error:
                print(f"Error checking status: {error}")
            time.sleep(10)
        raise Exception(f"Timeout reached after {timeout} seconds")
