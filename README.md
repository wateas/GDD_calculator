# GDD_calculator
Calculate Growing Degree Days (GDD) from weather history data available from NOAA.

This script allows the user to calculate GDD using data from one station or average the results from several stations.  Unless the user believes that a single, nearby weather station is a good representation of their immediate area, the user may want to average data from 2 or 3 nearby stations.

For the most accurate calculation of GDD, soil temperatures should ideally be used in place of air temperatures until leaf emergence.  Soil temperature data can easily be substituted in the output files (csv).  Otherwise, air temperatures can probably provide a reasonable estimate of GDD if the chosen starting date (see below) is approximately when the average soil temperature reaches 50 degrees F.  Syngenta has online soil temperature map data available: https://www.greencastonline.com/tools/soil-temperature

Weather station data can be downloaded from NOAA:

- URL:
	https://www.ncdc.noaa.gov/cdo-web/datatools/lcd
- Use search menu to find weather station of interest and "add to cart".
- In cart:
	- Select "LCD CSV".
	- Select desired date range.
	- Provide an email address for the data to be sent to..

The user will need to edit the script to specify the directory containing the source data (and where the output data will be placed), the source data file name(s), and the start date from which GDD will be calculated.  All of these parameters can be found in the function "main".

If the start date is set too soon in the season, an inflated calculation of GDD will result.  As mentioned above, the user should have some knowledge about their local climate, specifically when average soil temperatures reach 50 degrees F.     

Contact: [Fred Teasley](mailto:wateas@gmail.com?subject=[GitHub]%20GDD%20Calculator)
