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
AVAILABLE RACES
"""
# get list of editions for a race
# e.g. https://www.procyclingstats.com/race/gp-samyn/overview
def get_race_editions(url:str) -> pd.DataFrame:
    # start session
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate select options
    div=soup.find("div",{"class":"editions"})
    edition_select=div.find("select")
    edition_options=edition_select.find_all("option")

    # prepare data frame
    df=pd.DataFrame(columns=["year","edition_url"])

    # fill data frame
    for option in edition_options:
        series={}

        series["year"]=option.text
        series["edition_url"]="https://www.procyclingstats.com/"+option["value"]

        series=pd.Series(series)
        df=df.append(series,ignore_index=True)

    return df

# scrape all races which happen in a year
# e.g. https://www.procyclingstats.com/races.php?year=2020
def scrape_races_for_year(year=2020) -> pd.DataFrame:
    years=get_available_tours_for_year(year)

    # prepare data frame
    df=pd.DataFrame()

    for key,value in years.items():
        print("{}             ".format(key),end="\r")
        year_race_series=scrape_tour_races_for_year(year=year,tour_code=value)
        year_race_series["tour"]=key
        year_race_series["tour_code"]=value
        df=pd.concat([df,year_race_series],ignore_index=True)

    return df

# get dictionary of all race series run in a given year (as well as ids)
# e.g. https://www.procyclingstats.com/races.php?year=2020
def get_available_tours_for_year(year=2020) -> {str:int}:
    # format url
    url="https://www.procyclingstats.com/races.php?year={}".format(year)

    # fetch data
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate input field
    select_field=soup.find("select",{"name":"circuit"})
    select_field_options=select_field.find_all("option")

    # prepare dict
    tours={}

    # fill dict
    for option in select_field_options:
        tours[option.text]=int(option["value"])

    return tours

# scrape all races in a given year for a given series
# https://www.procyclingstats.com/races.php?year=2020&circuit=1
def scrape_tour_races_for_year(year=2020,tour_code=1) -> pd.DataFrame:
    # format url
    url="https://www.procyclingstats.com/races.php?year={}&circuit={}".format(year,tour_code)

    # fetch data
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    table_div=soup.find("div",{"class":"tableCont"})
    table_body=table_div.find("tbody")
    table_rows=table_body.find_all("tr")

    df=pd.DataFrame(columns=["race_dates","race_name","stage_race","race_class","race_country_code","cancelled","race_url"])

    for row in table_rows:
        series=parse_tour_races_for_year_row(row)
        df=df.append(series,ignore_index=True)

    return df

def parse_tour_races_for_year_row(row) -> pd.Series:
    series={}

    row_details=row.find_all("td")

    # extract details
    series["cancelled"]=("striked" in row["class"])
    series["race_dates"]=row_details[0].text
    series["stage_race"]=("-" in row_details[0].text)
    series["race_country_code"]=row_details[1].find("span",{"class":"flag"})["class"][-1]
    series["race_url"]="https://www.procyclingstats.com/"+row_details[1].find("a")["href"]
    series["race_name"]=row_details[1].find("a").text
    series["race_class"]=row_details[3].text

    return pd.Series(series)

"""
AVAILABLE TEAMS
"""
# scrape all world tour & contintental teams for a given year
# e.g. https://www.procyclingstats.com/teams.php?s=worldtour&year=2005
def scrape_teams_for_year(year=2020):
    url="https://www.procyclingstats.com/teams.php?s=worldtour&year={}".format(year)

    # fetch data
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    df=pd.DataFrame()

    # isolate areas
    div=soup.find("div",{"class":"statDivLeft"})

    # get team classifications
    headings=div.find_all("h3")
    headings=[heading.text for heading in headings]

    # isolate team divs
    team_divs=div.find_all("div",{"class":"teamsOverview"})

    # top class
    class_name=headings[0]
    class_divs=team_divs[:2]

    # fill data frame
    for div in class_divs:
        div_df=parse_team_div(div)
        div_df["team_class"]=class_name
        df=pd.concat([df,div_df],ignore_index=True)

    # second class
    class_name=headings[1]
    class_divs=team_divs[2:]

    # fill data frame
    for div in class_divs:
        div_df=parse_team_div(div)
        div_df["team_class"]=class_name
        df=pd.concat([df,div_df],ignore_index=True)

    return df

def parse_team_div(div) -> pd.DataFrame:
    anchors=div.find_all("a")
    spans=div.find_all("span")

    df=pd.DataFrame(columns=["team_name","team_nationality_code","team_url"])

    for i in range(len(anchors)):
        series={}

        series["team_name"]=anchors[i].text
        series["team_url"]="https://www.procyclingstats.com/"+anchors[i]["href"]
        series["team_nationality_code"]=spans[i]["class"][-1]

        df=df.append(pd.Series(series),ignore_index=True)

    return df

"""
AVAILABLE RIDERS
"""

# e.g. https://www.procyclingstats.com/team/ag2r-la-mondiale-2020
def scrape_riders_from_team(url:str) -> pd.DataFrame:
    # fetch data
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate rider list
    rider_list=soup.find("ul",{"class","riderlist"})
    rider_list_items=rider_list.find_all("li")

    # prepare data frame
    df=pd.DataFrame(columns=["rider_name","rider_nationality_code","rider_career_points","rider_age","rider_url"])

    # fill data frame
    for item in rider_list_items:
        series=parse_rider_list_item(item)
        df=df.append(series,ignore_index=True)

    return df

def parse_rider_list_item(item) -> pd.Series:
    series={}

    anchor=item.find("a")
    series["rider_name"]=anchor.text
    series["rider_url"]="https://www.procyclingstats.com/"+anchor["href"]

    series["rider_nationality_code"]=item["data-nation"]
    series["rider_career_points"]=item["data-pnts"]
    series["rider_age"]=item["data-age"]

    return pd.Series(series)

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
        series["rider_url"]="https://www.procyclingstats.com/"+list_item.find("a")["href"]
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
        series["team_url"]="https://www.procyclingstats.com/"+list_item.find("a")["href"]
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
def parse_stage_list_item(list_item) -> pd.Series:
    series={}

    # date of stage
    series["date"]=list_item.find("div").text

    # url
    stage_details=list_item.find("a")
    series["stage_url"]="https://www.procyclingstats.com/"+stage_details["href"]

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
# return a list containing a data frame for each stage of a race
# https://www.procyclingstats.com/race/tour-de-france/2020/gc/overview
def scrape_stage_race_all_stage_results(url:str) -> [pd.DataFrame]:
    stages=scrape_stage_race_overview_stages(url)

    results=[]
    for stage_url in stages[stages["stage_name"]!="REST DAY"]["stage_url"]:
        if stage_url[:4]!="http": stage_url="https://"+stage_url
        print(stage_url)
        stage_results_df=scrape_stage_race_stage_results(stage_url)
        results.append(stage_results_df)

    return results

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
    if (table is None): return None # results don't exist

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
    series["stage_pos"]=int(stage_pos) if (stage_pos not in ["DNF","OTL","DNS"]) else np.NaN
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

# scrape finish results from one day race
# e.g. https://www.procyclingstats.com/race/gp-samyn/2020/result
def scrape_one_day_results(url:str) -> pd.DataFrame:
    # start session
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate desired table
    table=soup.find("table")
    if (table is None): return None # results don't exist

    results_table=table.find("tbody")
    rows=results_table.find_all("tr")

    # prepare data frame
    df=pd.DataFrame(columns=["finish_pos","bib_number","rider_age","team_name","rider_name","rider_nationality_code","uci_points","points","finish_time"])

    # fill data frame
    for row in rows:
        series=parse_one_day_results_row(row)
        df=df.append(series,ignore_index=True)

    return df

# parse a row from the table of results
def parse_one_day_results_row(row) -> pd.Series:
    series={}
    row_data=row.find_all("td")

    # race details
    finish_pos=row_data[0].text
    series["finish_pos"]=int(finish_pos) if (finish_pos not in ["DNF","OTL","DNS"]) else np.NaN
    series["bib_number"]=int(row_data[1].text)

    # rider and team details
    series["team_name"]=row_data[4].text
    series["rider_name"]=row_data[2].text.replace(series["team_name"],"")
    series["rider_nationality_code"]=row_data[2].find("span",{"class":"flag"})["class"][-1]
    series["rider_age"]=int(row_data[3].text)

    # point results
    uci_points=row_data[5].text
    points=row_data[6].text
    series["uci_points"]=int(uci_points) if (uci_points!="") else 0
    series["points"]=int(points) if (points!="") else 0

    # results
    finish_time=row_data[7].find("span",{"class":"timeff"}).text
    series["finish_time"]=parse_finish_times(finish_time) if (finish_time!="-") else np.NaN

    return pd.Series(series)


"""
RIDER PROFILES
"""

# returns series specificing personal details by a rider
# e.g. https://www.procyclingstats.com/rider/caleb-ewan/
def get_rider_details(url:str) -> pd.Series:
    series=pd.Series() # series to fill in

    # start session
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # find riders name
    name_header=soup.find("h1")
    name_header_text=name_header.text

    # remove parts which are not in name
    spans=name_header.find_all("span")
    for span in spans: name_header_text=name_header_text.replace(span.text,"")

    series["name"]=name_header_text.strip().rstrip()

    # isolate desired table
    info_div=soup.find("div",{"class":"rdr-info-cont"})

    # extract details from body
    text=info_div.text
    series["dob"]=re.search("Date of birth: (.*) \(",text,re.IGNORECASE).group(1)
    series["nationality"]=re.search("Nationality: (.*)Weight",text,re.IGNORECASE).group(1)
    series["birth_place"]=re.search("Place of birth: (.*)Points per",text,re.IGNORECASE).group(1)
    series["weight"]=re.search("([0-9]+ kg)",text,re.IGNORECASE).group(1)
    series["height"]=re.search("([0-2].[0-9]{2} m)",text,re.IGNORECASE).group(1)

    # rating points
    pps_list_items=info_div.find("ul",{"class":"pps"}).find_all("li")
    for item in pps_list_items:
        point_type=item["class"][0]
        series["points_"+point_type]=item.find_all("span")[1].text

    return series

# get dataframe containing teams a rider has ridden for
# https://www.procyclingstats.com/rider/philippe-gilbert
def get_rider_teams(url:str) -> pd.DataFrame:
    # start session
    session=HTMLSession()
    response=session.get(url)
    response.html.render()
    soup=BeautifulSoup(response.html.html,"lxml")

    # isolate team table
    team_list=soup.find("ul",{"class":"rdr-teams"})
    team_list_items=team_list.find_all("li")

    df=pd.DataFrame(columns=["year","team_name","team_class","team_url"])

    for item in team_list_items:
        series={}

        item_details=item.find_all("span")

        if (len(item_details[0].text)==4): # on occassion a retirement is noted here
            series["year"]=int(item_details[0].text)

            anchor=item_details[1].find("a")
            series["team_url"]="https://www.procyclingstats.com/"+anchor["href"]
            series["team_name"]=anchor.text

            series["team_class"]=re.search("\((\w+)\)",item_details[1].text,re.IGNORECASE).group(1)

            df=df.append(pd.Series(series),ignore_index=True)

    df=df.set_index("year")
    return df

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
    url="https://www.procyclingstats.com/"+row_details[4].find("a")["href"]
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

# tours=get_available_tours_for_year(2020)
# print(tours)

# df=scrape_tour_races_for_year(2020,15)
# print(df)

# df=scrape_races_for_year(2020)
# print(df)

# df=scrape_teams_for_year(2020)
# print(df)

# df=scrape_riders_from_team("https://www.procyclingstats.com/team/ag2r-la-mondiale-2020")
# print(df)

# df=scrape_stage_race_stage_results("https://www.procyclingstats.com/race/tour-de-france/2020/stage-5")
# print(df)

# df=scrape_stage_race_overview_stages("https://www.procyclingstats.com/race/tour-de-france/2019/overview")
# print(df)

# dfs=scrape_stage_race_all_stage_results("https://www.procyclingstats.com/race/tour-de-france/2020/overview")
# print(len(dfs),dfs[0],dfs[-1],sep="\n")

# df=scrape_stage_race_overview_top_competitors("https://www.procyclingstats.com/race/tour-de-france/2019/overview")
# print(df)

# df=scrape_stage_race_overview_competing_teams("https://www.procyclingstats.com/race/tour-de-france/2019/overview")
# print(df)

# years=get_rider_years("https://www.procyclingstats.com/rider/wout-van-aert")
# print(years)

# df=scrape_rider_year_results("https://www.procyclingstats.com/rider/caleb-ewan/2020")
# print(df)

# series=get_rider_details("https://www.procyclingstats.com/rider/caleb-ewan/")
# print(series)

# df=get_rider_teams("https://www.procyclingstats.com/rider/philippe-gilbert")
# print(df)

# df=scrape_rider_all_results("https://www.procyclingstats.com/rider/caleb-ewan/")
# df.to_csv("caleb_ewan_results.csv")
# print(df)

# df=scrape_one_day_results("https://www.procyclingstats.com/race/gp-samyn/2020/result")
# print(df)

df=get_race_editions("https://www.procyclingstats.com/race/tour-de-france")
print(df)
