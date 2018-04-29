from requests import exceptions
import argparse
import cv2
import requests
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ap = argparse.ArgumentParser()
ap.add_argument("-q", "--query", required=True,
    help="search query to search Bing Image API for")
ap.add_argument("-o", "--output", required=True,
    help="path to output directory of images")
args = vars(ap.parse_args())

# Global Variables
API_KEY = ""
MAX_RESULTS = 250
GROUP_SIZE = 50

# set the endpoint API URL
URL = "https://api.cognitive.microsoft.com/bing/v7.0/images/search"

# Possible exceptions from requests
EXCEPTIONS = set([IOError, FileNotFoundError,
                    exceptions.RequestException, exceptions.HTTPError,
                    exceptions.ConnectionError, exceptions.Timeout])

# Search query
term = args["query"]
headers = {"0cp-Apim-Subscription-Key" : API_KEY}
params = {"q": term, "offset": 0, "count": GROUP_SIZE}
logging.info("searching Bing API for '{}'".format(term))
search = requests.get(URL, headers=headers, params=params)
search.raise_for_status()
results = search.json()
estNumResults = min(results["totalEstimatedMatches"], MAX_RESULTS)
logging.info("{} total results for '{}'".format(estNumResults, term))

# Download images
total = 0
# Loop over total results in GROUP_SIZE batches
for offset in range(0, estNumResults, GROUP_SIZE):
    logging.info("making request for group {}-{} of {}...".format(
        offset, 
        offset+GROUP_SIZE, 
        estNumResults
    ))
    params["offset"] = offset
    search = requests.get(URL, headers=headers, params=params)
    search.raise_for_status()
    results = search.json()
    logging.info("saving images for group {}-{} of {}...".format(
        offset,
        offset+GROUP_SIZE,
        estNumResults
    ))
    # Loop over group batch
    for v in results["value"]:
        try:
            logging.info("fetching: {}".format(v["contentUrl"]))
            r = requests.get(v["contentUrl"], timeout=30)
            ext = v["contentUrl"][v["contentUrl"].rfind("."):]
            # path in format 'outputPath/number.ext'
            p = os.path.sep.join(
                [args["output"], 
                 "{}{}".format(str(total).zfill(8), ext)]
            )
            # Write to disk
            f = open(p, "wb")
            f.write(r.content)
            f.close()
        except Exception as e:
            if type(e) in EXCEPTIONS:
                logging.warning("skipping: {}".format(v["contentUrl"]))
                continue
            else:
                raise e
        # verify it's a good image
        image = cv2.imread(p)
        if image is None:
            logging.warning("deleting corrupted image: {}".format(p))
            os.remove(p)
            continue
        total += 1

