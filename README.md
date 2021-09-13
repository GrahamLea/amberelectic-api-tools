# Amber Electric Usage Summary

This is a command line tool that produces a summary CSV report of an Amber 
Electric customer's energy consumption and cost data.

You simply need to provide your Amber API token, and the tool will output a CSV
like this for the last 12 months:

```
CHANNEL                         , 2020-09-01, 2020-09-02, 2020-09-03, ...
B4 (FEED_IN) Usage (kWh)        ,      1.351,      0.463,      0.447, ...
E3 (CONTROLLED_LOAD) Usage (kWh),      2.009,      2.669,      2.757, ...
E4 (GENERAL) Usage (kWh)        ,     20.400,     20.965,     16.011, ...
```


## About Amber Electric

[Amber Electric](https://amber.com.au/) is an innovative energy retailer in 
Australia which gives customers access to the wholesale energy price as 
determined by the National Energy Market.
This gives customers the opportunity to reduce their bills and their reliance 
on fossil fuels by shifting their biggest energy usage to times of the day when 
energy is cheaper and greener.


### Amber's API

Amber gives customers access to a LOT of their own data through their public 
Application Programming Interface or API.

This tool relies on you having access to Amber's API, which means you need
to be an Amber customer, and you need to get an API token.
But that's pretty easy.
[Start here](https://help.amber.com.au/hc/en-us/articles/360038985552-Do-you-have-an-API-).


## How To Get The Tool

If you're a programmer comfortable with Git, I'm sure you already know how to
get this code onto your machine from GitHub.

If you're not familiar with Git, you can download this code as a Zip file
by clicking on [this link](https://github.com/GrahamLea/amber-usage-summary/archive/refs/heads/main.zip).
Once it's downloaded, unzip the file, which will create a directory containing
all the files of this project.


## How To Use It


### Pre-Requisites

You'll need [Python 3.9+](https://www.python.org/downloads/) installed.

And an Amber API token. (See above)


### Setup

Using a terminal, in the directory of this project:

1. Create a Python virtual environment with this command:
```
python3.9  -m  venv  venv
```

2. Start using the virtual environment with this command:
```
source  ./venv/bin/activate
```

3. Install the required dependencies with this command:
```
python  -m  pip  install  -r  requirements.txt
```


### Running the tool

Using a terminal, in the directory of this project:

1. Start using the virtual environment with this command:
```
source  ./venv/bin/activate
```

2. Run the tool with this command, replacing `YOUR_API_TOKEN` with your own API
token:
```
python  amber_usage_summary.py  --api-token  YOUR_API_TOKEN  >  my_amber_usage_data.csv
```

Using the above, your summary consumption data for the last year will be saved 
to the file called `my_amber_usage_data.csv` in the same directory.


### Options


#### Help

Run the script with the `-h` option to see its help page:
```
python  amber_usage_summary.py  -h
```


#### API Token File

If you'd prefer not to paste your API token into a terminal command, you can 
save it in a file called `apitoken` in the project's directory.


#### Costs Summary

By default, the tool just outputs energy consumption data.
If you also want a summary of your cost data, add the `--include-cost` option:
```
python  amber_usage_summary.py  --include-cost
```


#### Site Selection

If you have multiple sites in your Amber Electric account, you'll need to select
one using the `--site-id` option:
```
python  amber_usage_summary.py  --site-id  SITE_ID_YOU_WANT_DATA_FOR
```


#### Date Range

By default, the report includes the last 12 full calendar months of data, plus
all of the current month's data up until yesterday.
You can select what date range to include in the output by adding and start date
and, optionally, an end date to the command.
```
python  amber_usage_summary.py  2020-07-01  2021-06-30
```


## License

All files in this project are licensed under the 
[3-clause BSD License](https://opensource.org/licenses/BSD-3-Clause).
See [LICENSE.md](LICENSE.md) for details.
