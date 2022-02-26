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


## Amber Electric Invoice Estimate

This is a command line tool that produces a text-based estimate of an Amber 
Electric customer's invoice for a particular month or months in the past, using
usage and pricing data from Amber's API.

Once configured, the tool can output an invoice breakdown like this one for any 
past whole month during which you were an Amber customer:

```
Month: 2022-01

   Usage Fees:
      General Usage Wholesale                319.9     8.10   $  25.91
      Controlled Load Wholesale               39.9     8.07   $   3.22
      Network - Peak Energy                   35.2    25.37   $   8.93
...
```

The tool has been written to match the format of Amber's most recent invoice
format as closely as possible.


### ⚠️ Important Note About Accuracy

The tool deliberately has "Estimate" in the name because it is NOT, and cannot
be, a 100% accurate re-creation of Amber's billing engine that creates your
actual invoices.

The purpose for creating this tool was to enable a rough comparison of 
different DNSP tariffs against historical usage data, and in my own use it 
appears to be accurate *enough* to serve this purpose.

While no warranty is given about any aspect of these tools, I want to 
specifically call out that I'm offering ZERO guarantees that the output of this 
tool is accurate.
Amber themselves have 
[published information about some of the reasons that make reproducing bills from API data problematic](https://github.com/amberelectric/public-api/discussions/50). 

If you find inaccuracies in the output, and know why they are happening, I'd be
happy to hear from you in order to improve the tool (and even happier to have 
you develop and submit a patch after chatting with me about it).
See 'Contributions' below.


### ⚠️ Important Note About Limitations

The following limitations are known to exist with the tool:
* There is no handling for block tariffs.
* There is no handling for capacity pricing.
* The outputs of demand pricing have not been tested against real bills.
* There is no provision for mid-month changes, e.g. if a tariff changes or
  GreenPower is switched on or off in the middle of a month.
* There is no special handling for doing part of the current month (per-day 
  charges will be calculated for the full month).
* Only Ausgrid residential tariffs have been encoded (and only non-closed ones).
* Only NSW charges have been encoded.
* Only public holidays in NSW from 2021-2023 have been comprehensively encoded.

There are likely other limitations that are unknown.

Re-producing a bill requires a lot more data than what is available from the API.
At a high level, the tariffs you want to use for each channel, the prices that
make up those tariffs, and other charges specific to your state, your network,
and even your site's location, all need to be available and accurate to make a
good estimate.

So far, I've only entered this data for scenarios that I've wanted to test.
This means if you are in NSW, on the Ausgrid network, have an IntelliHub smart
meter, and are connected to the Sydney South TNI, the tool *might* produce good
estimates for you.
If you're not part of that small niche, you will probably need to do some data
acquisition and entry in order to get the tool estimating your own bills.

If you add new data for your own purposes, and you'd like to contribute it
for others to use, I'd be happy to hear from you.
See 'Contributions' below.


### How To Use It


### Configuration

Before using this tool, you'll need to configure it to have the correct tariffs 
and other data for the location and scenario you want to test.

At the very least, you'll need to either edit or create your own copy
(recommended) of ``data/accountConfigs/my_account_config_example.json5``, and 
review/update all the values in the file to ensure they're accurate for your 
site.

If you're using tariffs that aren't already encoded in a tariff file, you'll
need to create a new tariff file.
The document `data/tariffs/TariffsReadme.md` explains the format for creating
a tariff file.
It will probably be easiest to copy an existing one for a similar style of 
tariff and modify it rather than start from scratch.
But it shouldn't be too hard.

Lastly, if there isn't an "Other Charges" file for your location under 
`data/otherCharges`, or it's out of date, you'll need to create one of those.
This file has a similar format to tariff files with a few small differences as
explained at the top of the NSW file.
There are links in the NSW file that should help in finding the right values.

Note that, except for the Amber monthly fee, all other tariffs and charges 
should be entered as *exclusive* of GST.


### Running

⚠️ IMPORTANT: If you skipped "Configuration" above, go back and read it, and
do it!
If you don't, your results will be meaningless unless you just happen to live 
in the same part of Sydney as me and are on the same tariff.

Using a terminal, in the directory of this project:

1. Start using the virtual environment with this command:
```
source  ./venv/bin/activate
```

2. Run the tool with this command, replacing `YOUR_API_TOKEN` with your own API
token, and the account config filename with the path of your own account config:
```
python  amber_invoice_estimate.py  --api-token  YOUR_API_TOKEN  data/accountConfigs/my_account_config_example.json5
```


#### Options


##### Months

By default, the report generates an estimate of your bill for the last complete
month.
You can select what months to include in the output by listing one or more 
months as arguments to the script in `yyyy-MM` format: 
```
python  amber_invoice_estimate.py  ACCOUNT_CONFIG_FILE  2021-10  2021-11  2021-12
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
