import json
import urllib.request


BASE = "http://127.0.0.1:8000"


def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def main():
    print(post("/api/demo/seed", {}))


if __name__ == "__main__":
    main()
