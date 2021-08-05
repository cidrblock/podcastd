import requests
import yaml

def load():
    with open('podcasts.yml', 'r') as stream:
        podcasts = yaml.load(stream)
    for name, details in podcasts.items():
        details.update({"name": name})
        print(name)
        response = requests.post("http://localhost:5000/podcast", json=details)
        print(response.text)

def main():
    load()

if __name__ == '__main__':
    main()
