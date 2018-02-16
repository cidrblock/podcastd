import os
import opml
import yaml

def build_yaml():
    """ docstring
    """
    added = False
    if os.path.exists('podcasts.yml'):
        with open('podcasts.yml', 'r') as stream:
            yaml_entries = yaml.load(stream)
    else:
        yaml_entries = {}
    opml_entries = opml.parse('podcasts.ompl')
    for podcast in opml_entries[0]:
        if podcast.text not in yaml_entries:
            yaml_entries[podcast.text] = {}
            yaml_entries[podcast.text]['image'] = None
            yaml_entries[podcast.text]['max_age'] = "7d"
            yaml_entries[podcast.text]['max_episodes'] = 3
            yaml_entries[podcast.text]['url'] = podcast.xmlUrl
            added = True
    if added:
        with open('podcasts.yml', 'w') as outfile:
            yaml.dump(yaml_entries, outfile, default_flow_style=False)

def main():
    """ docstring
    """
    build_yaml()

if __name__ == "__main__":
    main()
