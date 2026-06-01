import requests

url = "https://kluan-facial-recognition-for-attendance-tracking.hf.space/recognize"

with open("WIN_20250930_17_02_14_Pro.jpg", "rb") as f:
    response = requests.post(
        url,
        files={"file": f}
    )

print(response.status_code)
print(response.json())