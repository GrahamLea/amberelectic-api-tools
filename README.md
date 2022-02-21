# Amber Electric API Tools

A collection of command-line tools (and Python functions) that can be used to
work with data from the Amber Electric API.


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


## How To Get The Tools

If you're a programmer comfortable with Git, I'm sure you already know how to
get this code onto your machine from GitHub.

If you're not familiar with Git, you can download this code as a Zip file
by clicking on [this link](https://github.com/GrahamLea/amber-usage-summary/archive/refs/heads/main.zip).
Once it's downloaded, unzip the file, which will create a directory containing
all the files of this project.


## Pre-Requisites For These Tools

You'll need [Python 3.9+](https://www.python.org/downloads/) installed.

And an Amber API token. (See above)


## Setup

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


## Common Options

The following options are common among all the tools.


### Help

Run the script with the `-h` option to see its help page:
```
python  SCRIPT_NAME  -h
```


### API Token File

If you'd prefer not to paste your API token into a terminal command, you can
save it in a file called `apitoken` in the project's directory.


### Site Selection

If you have multiple sites in your Amber Electric account, you'll need to select
one using the `--site-id` option:
```
python  SCRIPT_NAME  --site-id  SITE_ID_YOU_WANT_DATA_FOR
```


## Amber Electric Usage Summary

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


### How To Use It

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


#### Options


##### Costs Summary

By default, the tool just outputs energy consumption data.
If you also want a summary of your cost data, add the `--include-cost` option:
```
python  amber_usage_summary.py  --include-cost
```


##### Date Range

By default, the report includes the last 12 full calendar months of data, plus
all of the current month's data up until yesterday.
You can select what date range to include in the output by adding and start date
and, optionally, an end date to the command.
```
python  amber_usage_summary.py  2020-07-01  2021-06-30
```


## Amber Electric Spot Price History

This is a command line tool that produces a detailed CSV report of an Amber 
Electric customer's historical spot prices.

You simply need to provide your Amber API token, and the tool will output a CSV
like this for the last month:

```
DATE +10:00, CHANNEL                , 00:00:00, 00:30:00, 01:00:00, ...
2022-01-21 , GENERAL (c/kWh)        ,   17.456,   17.743,   17.736, ...
2022-01-21 , CONTROLLED_LOAD (c/kWh),   14.366,   14.653,   14.646, ...
2022-01-21 , FEED_IN (c/kWh)        ,   -5.913,   -6.174,   -6.168, ...
2022-01-22 , GENERAL (c/kWh)        ,  118.627,   17.623,   18.280, ...
...
```


### How To Use It

Using a terminal, in the directory of this project:

1. Start using the virtual environment with this command:
```
source  ./venv/bin/activate
```

2. Run the tool with this command, replacing `YOUR_API_TOKEN` with your own API
token:
```
python  amber_spot_price_export.py  --api-token  YOUR_API_TOKEN  >  my_amber_spot_price_data.csv
```

Using the above, your spot price data for the last month will be saved 
to the file called `my_amber_spot_price_data.csv` in the same directory.


#### Options


##### Date Range

By default, the report includes the last month of data.
You can select what date range to include in the output by adding a start date
and, optionally, an end date to the command.
```
python  amber_spot_price_export.py  2020-07-01  2021-06-30
```


## Contributions

I'm open to accepting contributions that improve the tool.

If you're planning on altering the code with the intention of contributing the
changes back, it'd be great to have a chat about it first to check we're on
the same page about how the improvement might be added.
It's probably easiest to create an issue describing your planned improvement (and
being clear that you plan to implement it yourself).


## License

All files in this project are licensed under the 
[3-clause BSD License](https://opensource.org/licenses/BSD-3-Clause).
See [LICENSE.md](LICENSE.md) for details.
