import requests

url = "https://kluan-facial-recognition-for-attendance-tracking.hf.space/register"

with open("WIN_20250918_07_49_22_Pro.jpg", "rb") as f:
    r = requests.post(
        url,
        data={
            "employee_id": "Luan",
            "slot_id": 1
        },
        files={
            "file": f
        }
    )
print(r.status_code)
print(r.json())