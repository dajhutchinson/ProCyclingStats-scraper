# ProCyclingStats-scraper
Web scraper for procyclingstats.com

## Available methods
| Method Name | Description | Parameters | Returns |
|-------------|-------------|------------|---------|
| ```get_race_editions``` | all editions of a race | race overview url | list |
| ```scrape_races_for_year``` | all races held in a given year| year | dataframe |
| ```get_available_tours_for_year``` | race tours held in a given year | year | dictionary |
| ```scrape_tour_races_for_year``` | races in a given race tour and year | year, tour_code | dataframe |
| ```scrape_teams_for_year``` | professional teams in a given year | year | series |
| ```scrape_riders_from_team``` | riders in a given team and year | team overview url (year specific) | dataframe |
| ```scrape_race_startlist``` | riders to start a given race | race startlist url | dataframe |
| ```scrape_race_information``` | information about a race | race overview url | series |
| ```scrape_stage_race_overview_top_competitors``` | top competitors in a stage race | race overview url | dataframe |
| ```scrape_stage_race_overview_competing_teams``` | teams in a given race | race overview url | dataframe |
| ```scrape_stage_race_overview_stages``` | stages in a stage race | stage race overview url | dataframe |
| ```scrape_stage_race_all_stage_results``` | results from every stage of a stage race | stage race overview page url | list of  dataframes |
| ```scrape_stage_race_stage_results``` | result from single stage of a stage race | stage url | dataframe |
| ```scrape_one_day_results``` | results from one day race | one day race overview url | dataframe |
| ```get_rider_details``` | details about rider | rider url | series |
| ```get_rider_teams``` | teams rider rode to each season | rider url | dataframe |
| ```get_rider_years``` | years in which rider competed | rider url | list |
| ```scrape_rider_year_results``` | rider's results from a specific year | rider year results url | dataframe |
| ```scrape_rider_all_results``` | all a rider's results | rider url | dataframe |


## Example URLs
| URL Description | Example |
|-----------------|---------|
| race overview url | *https://www.procyclingstats.com/race/gp-samyn/overview* |
| stage race overview url | *https://www.procyclingstats.com/race/tour-de-france/2019/overview* |
| one day race overview url | *https://www.procyclingstats.com/race/gp-samyn/overview* |
| stage url | *https://www.procyclingstats.com/race/tour-de-france/2020/stage-5* |
| team overview url (year specific) | *https://www.procyclingstats.com/team/ag2r-la-mondiale-2020* |
| race startlist url | *https://www.procyclingstats.com/race/tour-de-france/2020/startlist* |
| rider url | *https://www.procyclingstats.com/rider/caleb-ewan/* |
| rider year results url | *https://www.procyclingstats.com/rider/caleb-ewan/2020* |
