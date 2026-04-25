import requests

BASE_URL = "http://127.0.0.1:5900"


def upload_file(file_path):
    with open(file_path, "rb") as f:
        files = {"file": f}
        res = requests.post(f"{BASE_URL}/upload", files=files)
        print(res.json())


def download_file(filename):
    res = requests.get(f"{BASE_URL}/download/{filename}")
    print(res.json())


if __name__ == "__main__":
    while True:
        print("\n1. Upload File")
        print("2. Download File")
        print("3. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            path = input("Enter file path: ")
            upload_file(path)

        elif choice == "2":
            filename = input("Enter filename: ")
            download_file(filename)

        else:
            break