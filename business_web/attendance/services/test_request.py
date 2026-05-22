import requests


    {
      "v": "17",
      "name": "AddPerson",
      "method": "POST",
      "endpoint": "http://192.168.0.87/action/AddPerson",
      "params": [],
      "headers": [],
      "preRequestScript": "",
      "testScript": "",
      "auth": {
        "authType": "basic",
        "username": "admin",
        "password": "1",
        "authActive": true
      },
      "body": {
        "contentType": "application/json",
        "body": "{\n  \"operator\": \"AddPerson\",\n  \"info\": {\n    \"DeviceID\":1992079,\n    \"PersonType\": 0,\n    \"Name\":\"test\",\n    \"Gender\":0,\n    \"Nation\":1,\n    \"CardType\":0,\n    \"IdCard\":\"430923199011044411\",\n    \"Birthday\":\"1990-11-04\",\n    \"Telnum\":\"18888888888\",\n    \"Notes\": \"\",\n    \"MjCardFrom\": 2,\n    \"WiegandType\": 7,\n    \"CardMode\":1,\n    \"WGFacilityCode\": \"9A\",\n    \"MjCardNo\": \"018B2D\",\n    \"Tempvalid\": 1,\n    \"CustomizeID\": 123456,\n    \"PersonUUID\": \"4476c20c-23ce-4178-8672-b292d33a3cd8\",\n    \"isCheckSimilarity\": 0,\n    \"ValidBegin\":\"2018-03-12T09:09:20\",\n    \"ValidEnd\":\"2025-12-14T23:59:59\"\n  },\n  \"picURI\":\"https://aiclub.uit.edu.vn/smartdoor/backend/person/avatar?person_id=18521479&direction=left&time=1685443231731\"\n}"
      },
      "requestVariables": [],
      "responses": {},
      "description": null
    }
response_get = requests.get(url)
data_get = response_get.json()
print("Dữ liệu nhận được:")
print(data_get)