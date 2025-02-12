# Introduction

This is a fast web crawler built using the `multiprocessing` library in python. This crawler can visit and save the content of up to 2600 wikipedia articles per minute (benchmarked using a 16 core CPU).

This application utilizes multiprocessing to gather many requests and process their results in parallel. A Bloom filter is used to prevent pages from being re-visited.

# Notice

While this web crawler is written to conform to policies in a website's `robots.txt`, this web crawler should not be used or modified to conduct any unethical activities. This crawler is licensed under the MIT license, with no warranty.

# Getting started

1. Install the required libraries using: `pip install -r requirements.txt`.
1. Define your desired configuration in `config.yaml`
1. run `python main.py`.
1. view the results in the `crawl_data/` directory.