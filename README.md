# House Search

![Static Badge](https://img.shields.io/badge/code_style-black-black)
![Static Badge](https://img.shields.io/badge/license-MIT-8A2BE2)

## Summary
Working project on retrieving information on available rentals in Leiden from the following sites:
* Room
* Funda
* Kamernet
* Pararius


Data retrieved using bare Python `requests` as well as Selenium and the classes that run/execute these queries can be run from CRON. Listing information stored in SQLite database for later retrieval/analysis. Some initial visualizations can be seen below.

![hist](static/rent_distribution.png)

![lin_fit_by_nh_boxed](static/lin_fit_rent_area_by_nh_boxed.png)

## Note on proxies for Selenium
Funda/Pararius require a proxy list, otherwise requests will fail. **Published code does not support generation/acquisition of proxies.** Proxies can be passsed directly as a list of IP addesses/ports or as a file path to be read in via `puller_configs.py` by changing the value of `PROXY_PATH`. Files must be `.txt.` files with only `\n` seperators between IP adresses. In either case, addresses must be in the format `123.456.789:8080`. Running through `pullers_run.py` only supports file based proxy read-in, until input ingestion is switched from `sys.argv` to `argparse`.

## Setting up for `house_search`
This current codebase is intended for running on either MacOS or Linux (Raspbian). 

#### MacOS
Please ensure that you have `Firefox` as well as a working `geckodriver` binary installed and accessible via either the `bin` directory or in your `PATH` variable. `house_search` should then work out of the box.

#### Raspbian
**Note: This has only been tested on a Raspberry Pi 2B running Raspbian 11, which is on armv71**

The following steps are required to run on Raspbian:
1. Install Firefox: `sudo apt-get install firefox-esr`
2. Check what version of Firefox you have: `firefox -v`
3. Based on your version of Firefox, check what version of Python and Geckodriver are required [here](https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html)
4. Update Python to a version >= the version required
    - Get tarball from [python.org](python.org): `wget https://www.python.org/ftp/python/INSERTVERSIONHERE/Python-INSERTVERSIONHERE.tgz`
    - Unzip tarball: `tar -zxvf Python-INSERTVERSIONHERE.tgz`
    - Within the extracted directory, run configs: `./configure --enable-optimizations`
    - Build Python with `make`: `make -j NUMBEROFCORES`
    - Install Python as alternative version of system Python: `sudo make altinstall`
    - This can now be verified by running `pythonINSERTVERSIONHERE --version`
5. As Mozilla no longer releases ARMv7 builds as of 2018, unless you are running a old version of Fireefox, which is not recommended, you will have to create your own Geckodriver build from the relevant compatible source code version from step 3
    - Clone the following central repo: https://github.com/mozilla/gecko-dev
    - The steps to compile the source code to a build can be found [here](https://firefox-source-docs.mozilla.org/testing/geckodriver/ARM.html)
6. Move `geckodriver` to `/usr/local/bin`

#### Environment Variables
The following two environment variables are required for email functionality. Please ensure these are available to Python via `os.environ.get`. This can be accomplished in any way, but it is recommended to have these added to the runtime environment upon initialization of the `venv` or container.
```
GMAIL_USER_EMAIL="GMAIL_ACCOUNT@gmail.com"
GMAIL_APP_PASSWORD="GMAIL_APP_PASSWORD"
```

The below two environment variables are used for `recipient_sync.py`, but in the event that your recipient list is generated in a different way, feel free to ignore.
```
SHEETS_PAGE_ID="GSHEETS_DOC_ID"
SHEETS_RANGE="GSHEETS_CELL_RANGE"
```

## Running Instructions
1. Set up and activate a `venv` for `house_search`
2. Run `pip install -r requirements.txt`
3. Populate a file named `proxy_list.txt`, or if using a different file name, change the value of `PROXY_PATH` in `puller_configs.py`
    * It is recommended that this list is generated as close as possible to run time if you do not control your proxies, to avoid dead proxies. `utils.py` handles dead proxies by validating prior to using for a request, but this adds to the overall run time.
4. Run `puller_run.py` from the command line with a `headless` parameter if needed, i.e. `python3 puller_run.py T` for headless run, or `python3 puller_run.py F` for non-headless run

From here you can access `listings.db` using `sqlite` as needed. Short examples provided in `db_retrieval.ipynb`.

## License

MIT License 

Copyright (c) 2024 Colin Yip

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
