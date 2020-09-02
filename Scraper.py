from bs4 import BeautifulSoup
from requests_html import HTMLSession # to remove
from datetime import timedelta
import pandas as pd
import numpy as np
import re

"""
UTILITY
"""
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
STAGE RACING OVERVIEW
"""

# scrape the list of top competitors & their urls from the overview page of a stagerace
# https://www.procyclingstats.com/race/tour-de-france/2019/overview
def scrape_stage_race_overview_top_competitors(url:str) -> pd.DataFrame:
    # fetch data
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate list
    right_div=soup.find_all("div",{"class":"w48"})[1]
    top_competitor_list=right_div.find_all("ul")[0]
    top_competitor_list_items=top_competitor_list.find_all("li")

    # prepare data frame
    df=pd.DataFrame(columns=["rider_name","rider_url","rider_nationality_code"])

    # fill data frame
    for list_item in top_competitor_list_items:
        series={}

        series["rider_name"]=list_item.text
        series["rider_url"]="www.procyclingstats.com/"+list_item.find("a")["href"]
        series["rider_nationality_code"]=list_item.find("span",{"class":"flag"})["class"][-1]

        df=df.append(pd.Series(series),ignore_index=True)

    return df

# scrape the list of teams & their urls from the overview page of a stagerace
# https://www.procyclingstats.com/race/tour-de-france/2019/overview
def scrape_stage_race_overview_competing_teams(url:str) -> pd.DataFrame:
    # fetch data
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate list
    right_div=soup.find_all("div",{"class":"w48"})[1]
    top_competitor_list=right_div.find_all("ul")[1]
    top_competitor_list_items=top_competitor_list.find_all("li")

    # prepare data frame
    df=pd.DataFrame(columns=["team_name","team_url"])

    # fill data frame
    for list_item in top_competitor_list_items:
        series={}

        series["team_name"]=list_item.text
        series["team_url"]="www.procyclingstats.com/"+list_item.find("a")["href"]
        series["team_nationality_code"]=list_item.find("span",{"class":"flag"})["class"][-1]

        df=df.append(pd.Series(series),ignore_index=True)

    return df

# scrape details of each stage from stage race overview page
#https://www.procyclingstats.com/race/tour-de-france/2019/overview
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
    df=pd.DataFrame(columns=["date","stage_name","start_location","end_location","profile","distance","stage_url"])

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
    series["stage_url"]="www.procyclingstats.com/"+stage_details["href"]

    # locations & name
    stage_detail_divs=stage_details.find_all("div")
    series["stage_name"]=stage_detail_divs[0].text
    locations=stage_detail_divs[2].text.split("›")
    series["start_location"]=locations[0].strip()
    series["end_location"]=locations[1].strip()

    # profile
    series["profile"]=stage_details.find("div",{"class":"profile"})["class"][-2]

    # length of stage
    series["distance"]=float(stage_details.find("span").text.replace("(","").replace("km)",""))

    return pd.Series(series)

"""
STAGE RACING STAGES
"""

# scrape finish results from stage of a stage race
# https://www.procyclingstats.com/race/tour-de-france/2020/stage-5
def scrape_stage_race_stage_results(url:str) -> pd.DataFrame:
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
    df=pd.DataFrame(columns=["stage_pos","gc_pos","gc_time_diff_after","bib_number","rider_age","team_name","rider_name","rider_nationality_code","uci_points","points","finish_time"])

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
    series["rider_nationality_code"]=row_data[4].find("span",{"class":"flag"})["class"][-1]

    # point results
    uci_points=row_data[7].text
    points=row_data[8].text
    series["uci_points"]=int(uci_points) if (uci_points!="") else 0
    series["points"]=int(points) if (points!="") else 0

    # results
    finish_time=row_data[9].find("span",{"class":"timeff"}).text
    series["finish_time"]=parse_finish_times(finish_time) if (finish_time!="-") else np.NaN

    return pd.Series(series)

"""
ONE DAY RACING
"""

"""
RIDER PROFILES
"""

# returns list containing years in which results are held for a rider
# e.g. https://www.procyclingstats.com/rider/caleb-ewan/
def get_rider_years(url:str) -> [int]:
    # start session
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate desired table
    table=soup.find("ul",{"class":"rdrSeasonNav"})
    table_items=table.find_all("li")

    # extract year values
    years=[]
    for item in table_items[:-1]:
        if ("more" in item.text): break
        years.append(int(item.text))

    return years

# scrape results from riders overview page (for a specific year)
# e.g. https://www.procyclingstats.com/rider/caleb-ewan/2020
def scrape_rider_year_results(url:str) -> pd.DataFrame:
    # start session
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate desired table
    table=soup.find("table",{"class":"rdrResults"})
    results_table=table.find("tbody")
    rows=results_table.find_all("tr")

    # prepare data frame
    df=pd.DataFrame(columns=["date","type","result","gc_pos","race_country_code","race_name","race_class","stage_name","distance","pcs_points","uci_points","url"])

    # fill data frame
    current={"race":"","race_class":"","flag":""}
    for row in rows:
        add,series=parse_rider_year_results_row(row,current)
        current={"race":series["race_name"],"race_class":series["race_class"],"flag":series["race_country_code"]}
        if add: df=df.append(series,ignore_index=True)

    return df

# parse row of rider details to a series
# return boolean stating whether to add details to dataframe (ie not just details of a stage race)
def parse_rider_year_results_row(row,current={"race":"","race_class":"","flag":""}) -> (bool,pd.Series):
    series={}
    row_details=row.find_all("td")

    # extract data
    date=row_details[0].text
    result=row_details[1].text
    gc_pos=row_details[2].text
    name=row_details[4].text
    url="www.procyclingstats.com/"+row_details[4].find("a")["href"]
    distance=row_details[5].text
    pcs_points=row_details[6].text
    uci_points=row_details[7].text

    # prepare series depending on race type
    if (row["data-main"]=="0"): # stage or final classification of a stage race
        if (date==""): # FINAL CLASSIFICATION missing date
            series={"date":date,"type":name,"result":result,"gc_pos":np.NaN,"race_country_code":current["flag"],"race_name":current["race"],"race_class":current["race_class"],"stage_name":np.NaN,"distance":np.NaN,"pcs_points":pcs_points,"uci_points":uci_points,"url":url}
        else: # STAGE
            series={"date":date,"type":"Stage","result":result,"gc_pos":gc_pos,"race_country_code":current["flag"],"race_name":current["race"],"race_class":current["race_class"],"stage_name":name,"distance":distance,"pcs_points":pcs_points,"uci_points":uci_points,"url":url}

    elif (row["data-main"]=="1"): # stage race or one day
        # update details for stage results
        race_class=re.search("\((.*)\)",name,re.IGNORECASE).group(1) # uci rating of race
        race=name.split(" (")[0]
        flag=row_details[4].find("span",{"class":"flag"})["class"][-1]

        if (row_details[1].text==""): # STAGE RACE missing position
            series={"race_country_code":flag,"race_name":race,"race_class":race_class}
            return False, pd.Series(series)

        else: # ONE DAY RACE
            series={"date":date,"type":"One Day","result":result,"gc_pos":np.NaN,"race_country_code":flag,"race_name":race,"race_class":race_class,"stage_name":np.NaN,"distance":distance,"pcs_points":pcs_points,"uci_points":uci_points,"url":url}

    return True, pd.Series(series)

# get all results for a specific rider in a single data frame
# e.g. https://www.procyclingstats.com/rider/caleb-ewan/
def scrape_rider_all_results(url:str) -> pd.DataFrame:
    # ensure formating of url
    if (url[-1]!="/"): url+="/"

    # get years for which results exist
    years=get_rider_years(url)

    # fetch data for all years
    all_results=pd.DataFrame()
    for year in years:
        new_url=url+str(year)
        year_results=scrape_rider_year_results(new_url)
        year_results["year"]=year # add column stating year of race
        all_results=pd.concat([all_results,year_results],ignore_index=True) # add to table of all results

    return all_results

"""
TODO
"""
# auto scraping (ie how the urls are constructed)
# race overviews

pd.set_option('display.max_columns', None) # print all rows

# df=scrape_stage_race_stage_results("https://www.procyclingstats.com/race/tour-de-france/2020/stage-4")
# print(df)

# df=scrape_stage_race_overview_stages("https://www.procyclingstats.com/race/tour-de-france/2019/overview")
# print(df)

# df=scrape_stage_race_overview_top_competitors("https://www.procyclingstats.com/race/tour-de-france/2019/overview")
# print(df)

# df=scrape_stage_race_overview_competing_teams("https://www.procyclingstats.com/race/tour-de-france/2019/overview")
# print(df)

# years=get_rider_years("https://www.procyclingstats.com/rider/wout-van-aert")
# print(years)

# df=scrape_rider_year_results("https://www.procyclingstats.com/rider/caleb-ewan/2020")
# print(df)

# df=scrape_rider_all_results("https://www.procyclingstats.com/rider/caleb-ewan/")
# df.to_csv("caleb_ewan_results.csv")
# print(df)
