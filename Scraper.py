from bs4 import BeautifulSoup
from requests_html import HTMLSession # to remove
from datetime import timedelta
import pandas as pd
import numpy as np

"""
STAGE RACING
"""

# scrape details of each stage from stage race overview page
def scrape_stage_race_overview_stages(url:str) -> pd.DataFrame:
    # fetch data
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate desired list
    left_div=soup.find("div",{"class":"w36"})
    stage_list=left_div.find_all("ul")[1]

    # get list items
    stage_list_items=stage_list.find_all("li")

    # prepare data frame
    df=pd.DataFrame(columns=["date","stage_name","start_location","end_location","distance","url"])

    # fill data frame
    for list_item in stage_list_items:
        if (list_item.text!="Rest day"): series=parse_stage_list_item(list_item) # not a rest day
        else: series=pd.Series({"stage_name":"REST DAY"}) # is a rest day
        df=df.append(series,ignore_index=True)

    return df

# parse details from list of stages on stage race overview page
def parse_stage_list_item(list_item) -> pd.Series():
    series={}

    # date of stage
    series["date"]=list_item.find("div").text

    # url
    stage_details=list_item.find("a")
    series["url"]="www.procyclingstats.com/"+stage_details["href"]

    # locations & name
    stage_detail_divs=stage_details.find_all("div")
    series["stage_name"]=stage_detail_divs[0].text
    locations=stage_detail_divs[2].text.split("›")
    series["start_location"]=locations[0].strip()
    series["end_location"]=locations[1].strip()

    # length of stage
    series["distance"]=float(stage_details.find("span").text.replace("(","").replace("km)",""))

    return pd.Series(series)

# scrape finish results from stage of a stage race
def scrape_stage_race_stage_results(url) -> pd.DataFrame:
    # start session
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate desired table
    table=soup.find("table")
    results_table=table.find("tbody")
    rows=results_table.find_all("tr")

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
    row_data=row.find_all("td")

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
    finish_time=row_data[9].find("span",{"class":"timeff"}).text
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

# df=scrape_stage_race_stage_results("https://www.procyclingstats.com/race/tour-de-france/2020/stage-4")
# print(df)

# df=scrape_stage_race_overview("https://www.procyclingstats.com/race/tour-de-france/2019/overview")
# print(df)
