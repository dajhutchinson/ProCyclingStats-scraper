from requests_html import HTMLSession
from datetime import timedelta
import pandas as pd
import numpy as np

"""
STAGE RACING
"""
def scrape_stage_race_stage_results(url) -> pd.DataFrame:

    session = HTMLSession()
    r=session.get(url)
    r.html.render() # run js (so table is actually filled)

    # extract results table rows
    results_table=r.html.find("table",first=True)
    results_body=results_table.find("tbody",first=True)
    rows=results_body.find("tr")

    # prepare data frame
    df=pd.DataFrame(columns=["stage_pos","gc_pos","gc_time_diff_after","bib_number","rider_age","team_name","rider_name","uci_points","points","finish_time"])

    # fill data frame
    for row in rows:
        series=parse_stage_race_stage_results_row(row)
        df=df.append(series,ignore_index=True)

    return df

# parse a row from the table of results
def parse_stage_race_stage_results_row(row) -> pd.Series:
    series={}
    row_data=row.find("td")

    # race details
    stage_pos=row_data[0].text
    gc_pos=row_data[1].text
    gc_time_diff_after=row_data[2].text.replace("+","")
    series["stage_pos"]=int(stage_pos) if (stage_pos!="DNF") else np.NaN
    series["gc_pos"]=int(gc_pos) if (gc_pos!="") else np.NaN
    series["gc_time_diff_after"]=parse_finish_times(gc_time_diff_after) if ("-" not in gc_time_diff_after) else np.NaN
    series["bib_number"]=int(row_data[3].text)

    # rider and team details
    series["rider_age"]=int(row_data[5].text)
    series["team_name"]=row_data[6].text
    series["rider_name"]=row_data[4].text.replace(series["team_name"],"")

    # point results
    uci_points=row_data[7].text
    points=row_data[8].text
    series["uci_points"]=int(uci_points) if (uci_points!="") else 0
    series["points"]=int(points) if (points!="") else 0

    # results
    finish_time=row_data[9].find(".timeff",first=True).text
    series["finish_time"]=parse_finish_times(finish_time) if (finish_time!="-") else np.NaN

    return pd.Series(series)

# parse finish time string
def parse_finish_times(time_str:str) -> timedelta:
    spl=time_str.split(":")
    spl=[int(val) for val in spl]

    if (time_str.count(":")==2): # hours:mins:secs
        return timedelta(hours=spl[0],minutes=spl[1],seconds=spl[2])

    elif (time_str.count(":")==1): # mins:secs
        return timedelta(minutes=spl[0],seconds=spl[1])

    else: return np.NaN

"""
ONE DAY RACING
"""

"""
RIDER PROFILES
"""

"""
TODO
"""
# auto scraping (ie how the urls are constructed)
# race overviews
# stage race summaries

pd.set_option('display.max_columns', None) # print all rows
df=scrape_stage_race_stage_results("https://www.procyclingstats.com/race/tour-de-france/2020/stage-4")
print(df)
