import requests, json

url = "https://graphql.anilist.co"
query = """
{ __type(name: "Media") {
    fields {
      name
      type {
        name
        kind
        ofType { name kind }
      }
    }
  }
}
"""
resp = requests.post(url, json={"query": query}, timeout=10)
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))