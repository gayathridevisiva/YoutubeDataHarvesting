import pandas as pd
import plotly.express as px
import streamlit as st
import googleapiclient
from googleapiclient.discovery import build
import pymongo
import mysql.connector
from datetime import datetime
from streamlit_option_menu import option_menu
from PIL import Image
import re
# SETTING PAGE CONFIGURATIONS
icon = Image.open("C:\\Users\\HP\\OneDrive\\Desktop\\New folder\\youtubelogo.png")
st.set_page_config(page_title= "Youtube Data Harvesting and Warehousing | By Gayathri Devi",
                   page_icon=icon,
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# This app is created by *Gayathri Devi S!*"""})

# CREATING OPTION MENU
with st.sidebar:
    selected = option_menu(menu_title=None,options= ["Home","Extract Data","Transform Data","Analysis"], 
                           icons=["house-door-fill","tools","card-text"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "20px", "text-align": "centre", "margin": "0px", 
                                                "--hover-color": "#33A5FF"},
                                   "icon": {"font-size": "20px"},
                                   "container" : {"max-width": "6000px"},
                                   "nav-link-selected": {"background-color": "#33A5FF"}})
# Bridging a connection with MongoDB Atlas and Creating a new database(Youtube)
client = pymongo.MongoClient("localhost:27017")
db = client.youtube_Data
coll=db.myproject
# CONNECTING WITH MYSQL DATABASE

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Pragadhan09@",
    auth_plugin="mysql_native_password",
    database="utube",
    charset='utf8mb4',
    collation='utf8mb4_unicode_ci') 
mycursor = mydb.cursor(buffered=True)


api_key = "AIzaSyBn_QUE8xfOU2unzSEoukw_NWA0qu2NW5k" 
youtube = build('youtube','v3',developerKey=api_key)
    #function to channel_details
def channel_details(channel_id):
        request = youtube.channels().list(part = 'snippet,contentDetails,statistics', id= channel_id)
        response=request.execute()
        channel_details=[{
            "Channel_name": response['items'][0]['snippet']['title'],
            "Channel_id ":response['items'][0]['id'],
            "channel_type":response['items'][0]['snippet']['title'],
            "playlist_id":response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
            "Subscribers" :response['items'][0]['statistics']['subscriberCount'],
            "Views" : response['items'][0]['statistics']['viewCount'],
            "Total_videos" : response['items'][0]['statistics']['videoCount'],
            "Description" : response['items'][0]['snippet']['description']}]
        return channel_details
    #function to playlist_details
def playlist_details(channel_id):
        token=None
        playlist=[]
        while True:
            request = youtube.playlists().list(part="snippet,contentDetails",channelId=channel_id,maxResults=50,pageToken=token)
            response = request.execute()
            for i in range(len(response['items'])):
                playlist_details=dict(
                    Channel_id=response['items'][i]['snippet']['channelId'],
                    Playlist_id= response['items'][i]['id'],
                    playlist_title=response['items'][i]['snippet']['title'])
                playlist.append(playlist_details)
            if response.get("nextPageToken") is None:
                break
            token =response.get("nextPageToken")
        return playlist
    #function to video_ids
def get_videoid(pl):
        next_page_token = None
        videoid = []
        while True: #loop to get video id
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=pl,
                maxResults=50,
                pageToken=next_page_token)
            response = request.execute()
            for i in range(len(response['items'])):
                videoid.append(response['items'][i]['contentDetails']['videoId']) #append video id
            next_page_token = response.get("nextPageToken") #get next page
            if response.get("nextPageToken") is None:
                break
        return videoid
    #function to changeduration
    
def convert_duration(duration):
        regex=r'PT(\d+H)?(\d+M)?(\d+S)?'
        match=re.match(regex,duration)
        if not match:
            return'00:00:00'
        hours,minutes,seconds=match.groups()
        hours=int(hours[:-1])if hours else 0
        minutes=int(minutes[:-1])if minutes else 0
        seconds=int(seconds[:-1])if seconds else 0
        total_seconds=hours*3600+minutes*60+seconds
        return"{:02d}:{:02d}:{:02d}".format(int(total_seconds//3600),int((total_seconds%3600)//60),int(total_seconds%3600)%60)
    #function to video_details
def video_details(v):
        videoinfo=[]
        for i in v:
            request = youtube.videos().list(
                        part="snippet,contentDetails,statistics",
                        id=i)
            response = request.execute()
            for video in response['items']:
                    video_details = {
                                    "channel_name":video['snippet']['channelTitle'],
                                    "Channel_id" : video['snippet']['channelId'],
                                    "Video_id" : i,
                                    "Title" : video['snippet']['title'],
                                    "Thumbnail" : video['snippet']['thumbnails']['default']['url'],
                                    "Description" : video['snippet']['description'],
                                    "Published_date" : datetime.fromisoformat(video['snippet']['publishedAt']),
                                    "Duration" : convert_duration(video['contentDetails']['duration']),
                                    "Views" : int(video['statistics']['viewCount']),
                                    "Likes": video['statistics'].get('likeCount'),
                                    "Dislikes" : video['statistics'].get('dislikeCount',0),
                                    "Comments" : video['statistics'].get('commentCount'),
                                    "Favorite_count" : int(video['statistics']['favoriteCount']),
                                "Caption_status" : video['contentDetails']['caption']}
                    videoinfo.append(video_details)
        return videoinfo
    #function to comment_details
def comment(v):
        comment_data = []
        for i in v:
            try:
                #next_page_token = None
                #while True:
                    request = youtube.commentThreads().list(part="snippet,replies",
                                                            videoId=i)
                    response=request.execute()
                    for cmt in response['items']:
                        data = {"Comment_id ": cmt['snippet']['topLevelComment']['id'],
                                    "Video_id" : i,
                                    "Comment_text": cmt['snippet']['topLevelComment']['snippet']['textDisplay'],
                                    "Comment_author" : cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                                    "Comment_posted_date" : datetime.fromisoformat(cmt['snippet']['topLevelComment']['snippet']['publishedAt'])}
                        comment_data.append(data)
                    #next_page_token = response.get('nextPageToken')
                    #if next_page_token is None:
                        #break
            except:
                pass
        return comment_data
    #function to get all the details
def main_function(channel_id):
        c=channel_details(channel_id)
        pl=playlist_details(channel_id)
        v=get_videoid(c[0]['playlist_id'])
        vid=video_details(v)
        cmt=comment(v)
        data= [{"channel_details":c,
            "playlist_details":pl,
            "video_details":vid,
            "comment_details":cmt}]
        return data
    # FUNCTION TO GET CHANNEL NAMES FROM MONGODB
def channel_names():
        ch_name=[]
        for i in coll.find():
            ch_name.append(i['channel_details'][0]['Channel_name'])
        return ch_name
if selected == "Home":
    
    
    col1,col2 = st.columns(2,gap= 'medium')
    col1.markdown("## :blue[Domain] : Social Media")
    col1.markdown("## :blue[Technologies used] : Python,MongoDB, Youtube Data API, MySql, Streamlit")
    col1.markdown("## :blue[Overview] : Retrieving the Youtube channels data from the Google API, storing it in a MongoDB as data lake, migrating and transforming data into a SQL database,then querying the data and displaying it in the Streamlit app.")
    col2.markdown("#   ")
    col2.markdown("#   ")
if selected == "Extract Data":
    st.write("###Enter youtube channel_id below:")
    channel_id=st.text_input("Hint : Goto channel's home page > Right click > View page source > Find channel_id")
    if channel_id and st.button("Extract Data"):
            c=channel_details(channel_id)
            st.write(f'#### Extracted data from :green["{c[0]["Channel_name"]}"] channel')
            st.table(c)
    if st.button("Upload to MongoDB"):
            with st.spinner('Please Wait for it...'):
                final=main_function(channel_id)
                coll=db["myproject"]
                coll.insert_many(final)
                st.success("Upload to MongoDB successful !!")
## TRANSFORM TAB
if selected == "Transform Data":
        st.markdown("#   ")
        st.markdown("### Select a channel to begin Transformation to SQL")
        c_names = channel_names()  
        options = st.selectbox("Select channel",c_names)
        st.write('selected channel', options)
        coll=db["myproject"]
        x=coll.find()
        def collection():
            datas=[]
            for i in coll.find():
                if i['channel_details'][0]['Channel_name']==options:
                     datas.append(i)
            return datas
        data=collection()
        

        def insert_into_channels():
                    
                    sql = """INSERT INTO channels(channel_name,channel_id,channel_type,playlist_id,subscribers,views,total_videos,description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
                    val=tuple(data[0]['channel_details'][0].values())
                    mycursor.execute(sql,val)
                    mydb.commit()

        def insert_into_playlists():
            sql1 = """INSERT INTO playlists(channel_id,playlist_id,playlist_title) VALUES (%s,%s,%s)"""
            for i in data[0]['playlist_details']:
                val1=tuple(i.values())
                mycursor.execute(sql1,val1)
                mydb.commit()
        def insert_into_videos():
            sql2= """INSERT INTO videos(channel_name,
                            channel_id, 
                             video_id,  
                             Title, 
                             thumbnail,
                             Description, 
                             publishedDate,
                             Duration,
                             viewCount, 
                             likeCount, 
                             Dislikecount, 
                             commentCount,
                             favouritecount,
                             captionstatus) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            for i in data[0]['video_details']:
                val2=tuple(i.values())
                mycursor.execute(sql2,val2)
                mydb.commit()
        def insert_into_comments():
            sql3= """INSERT INTO comments(commentid, 
                               videoid, 
                               commenttext, 
                               commentauthor, 
                               commentposteddate) VALUES (%s,%s,%s,%s,%s)"""
            for i in data[0]['comment_details']:
                val3=tuple(i.values())
                mycursor.execute(sql3,val3)
                mydb.commit()
        if st.button("Submit"):
            try:
                insert_into_channels()
                insert_into_playlists()
                insert_into_videos()
                insert_into_comments()
                st.success("Transformation to MySQL Successful !!")
            except:
                st.error("Channel details already transformed !!")

            
if selected == "Analysis":
    
    st.write("## :orange[Select any question to get Insights]")
    questions = st.selectbox('Questions',
    ['Click the question that you would like to query',
    '1. What are the names of all the videos and their corresponding channels?',
    '2. Which channels have the most number of videos, and how many videos do they have?',
    '3. What are the top 10 most viewed videos and their respective channels?',
    '4. How many comments were made on each video, and what are their corresponding video names?',
    '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
    '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
    '7. What is the total number of views for each channel, and what are their corresponding channel names?',
    '8. What are the names of all the channels that have published videos in the year 2022?',
    '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
    '10. Which videos have the highest number of comments, and what are their corresponding channel names?'])
    
    if questions == '1. What are the names of all the videos and their corresponding channels?':
        mycursor.execute("""select title,channel_name
                            from videos 
                            order by title DESC
                            limit 10;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
    elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
        mycursor.execute("""select channel_name,total_videos
                            from channels
                            order by total_videos DESC;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Number of videos in each channel :]")
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
    elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
        mycursor.execute("""select channel_name,title
                            from videos v
                            order by viewcount desc
                            limit 10;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
    elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
        mycursor.execute("""select commentcount,title
                            from videos
                            order by commentcount DESC
                            limit 10;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
    elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        mycursor.execute("""select likecount,channel_name
                            from videos 
                            order by likecount desc
                            limit 10;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
    elif questions == '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?':
        mycursor.execute("""select likecount,title
                            from videos
                            order by likecount DESC;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
    elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        mycursor.execute("""select views,channel_name
                            from channels 
                            order by views desc;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Channels vs Views :]")
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
    elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
        mycursor.execute("""SELECT publishedDate,channel_name 
                            from videos where publishedDate like '2022%'
                            ORDER BY channel_name desc;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
    elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        mycursor.execute("""SELECT channel_name,
                            AVG(Duration) as Average_duration FROM videos
                            group by channel_name
                            ORDER BY channel_name DESC;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)
        st.write("### :green[Avg video duration for channels :]")
        fig = px.bar(df,
                     x=mycursor.column_names[0],
                     y=mycursor.column_names[1],
                     orientation='v',
                     color=mycursor.column_names[0]
                    )
        st.plotly_chart(fig,use_container_width=True)
    elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        mycursor.execute("""select t.title,c.channel_name
                            from videos t
                            join channels c
                            on t.channel_id=c.channel_id
                            order by t.commentcount desc
                            limit 10;""")
        df = pd.DataFrame(mycursor.fetchall(),columns=mycursor.column_names)
        st.write(df)

