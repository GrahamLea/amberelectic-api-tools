# Tariff File Format

Tariff files are [JSON5](https://json5.org/) files (essentially JSON with 
comments) that typically contain two things:
* the `distributionLossFactor` at the top level
* a list of `components` which make up the tariff

(Other Charges files use the same format as tariff `components`, but have no
`distributionLossFactor`, and add a `publicHolidayDatePatterns` section.)


## Components

Each tariff component has the following properties:


### `amberLabel`

A string specifying they label for the output charges in the invoice estimates


### `dnspLabel`

An optional string property that is purely documentation allowing for easy 
reference back to official tariff documents.


### Filters

Any combination (including none) of the following filters:


#### Filter: `periodFilter`

A list of 1 or more Period Types for which this tariff component applies, from 
the values `"peak"`, `"shoulder"`, `"offPeak"`, and `"solarSponge"`. 

Example: `periodFilter: ["peak", "shoulder"]`
      

#### Filter: `channelTypeFilter`

A list of 1 or more Channel Types for which this tariff component applies, from 
the values `"general"`, `"controlledLoad"`, and `"feedIn"`.

Note that, because network tariffs are typically assigned to a specific channel 
type, it's usually not necessary to use this filter within a tariff.
(The obvious exception would be a tariff that encompasses two channel types.)

This filter is used in Other Charges files to isolate charges to usage from
specific channels.

Example: `channelTypeFilter: ["general", "feedIn"]`
      

#### Filter: `monthFilter`

A list of 1 or months for which this tariff component applies, as whole numbers.

Example: `monthFilter: [11, 12, 1, 2, 3]` (that's November to March, inclusive)
      

#### Filter: `hourFilter`

A list of 1 or more hours of the day for which this tariff component applies, as 
whole numbers.

Example: `hourFilter: [14, 15, 16, 17, 18, 19]` (that's 2:00pm to 7:59pm)


#### Filter: `workingWeekdayFilter`

Just has a value of `true` if this tariff component should only apply on 
working weekdays, i.e. not weekends and not public holidays.
Public holidays are determined from the active Other Charges file.

Example: `workingWeekdayFilter: true`


#### Filter: `greenPowerFilter`

Just has a value of `true` if this tariff component should only apply if the 
account has GreenPower enabled. (You should!)

Probably only useful in an Other Charges file.

Example: `greenPowerFilter: true`


### Charges

Each tariff component must have one and ONLY one of these charge properties.

All charges should be described exclusive of GST.


#### `centsPerKwh`

What the name says.


#### `centsPerDay`

What the name says.


#### `centsPerPeakDemandKwPerDay`

Again, what the name says, but it's complicated!

There's a good explanation here: https://www.globirdenergy.com.au/demand-charge/

But, hopefully, you shouldn't need to understand it.
If you're on a demand tariff and you can copy in something from the tariff
like "Demand Price: cents per kW per day", the code should do the rest.
**However**, you will need to accurately describe the demand window in order for
the peak demand to be calculated correctly. 
It's a good idea to have a look at an existing demand tariff to see how this 
can be done. 
