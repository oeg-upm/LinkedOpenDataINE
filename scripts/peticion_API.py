import requests

url = "https://servicios.ine.es/wstempus/jsCache/ES/DATOS_TABLA/66615"

# Make the GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Print the JSON response
    data = response.json()
    print(data)
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
