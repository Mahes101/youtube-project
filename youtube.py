import streamlit as st
import plotly.express as px
from streamlit_option_menu import option_menu
import pymongo
import pymysql as sql
import pandas as pd
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.discovery import build
import json
from PIL import Image

icon = Image.open("youtube-logo.png")

with st.sidebar:
    choice_op = option_menu(None, ["Home","Extract and Transform","View"], 
                           icons=["house-fill","tools","card-text"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "30px", "text-align": "centre", "margin": "0px", 
                                                "--hover-color": "#C80101"},
                                   "icon": {"font-size": "30px"},
                                   "container" : {"max-width": "6000px"},
                                   "nav-link-selected": {"background-color": "#C80101"},})


#api_key = "AIzaSyDbVVK_JXJNBR1aO9XtITlx8C735CnyJhQ"
#api_key = "AIzaSyDatJbgMnt3wWmp1FHwYLQlPjlrEmyfHOU"    
api_key = "AIzaSyD7RFRdEvG-5pQFwBnSblRmUXtdLXbshNY"    

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=api_key)

# Connecting mongoDB.    
client = pymongo.MongoClient('mongodb://localhost:27017')    
db = client['youtube_db']

#Connecting MYSQL Database.
mydb = sql.connect(host="localhost",
                   user="root",
                   password="admin@123",
                   database= "youtube_db"
                  )
mycur = mydb.cursor()
playlist_list = []
playlist_id = ""
ch_name = ""
def getting_channel_names_from_mongodb():
    data = []
    info1 = db.channel_db
    for i in info1.find({},{'channel_name':1,'_id':0}):
        data.append(i)
    data1 = [d['channel_name'] for d in data]    
    return data1    

def getting_channel_details(ch_id):
    #getting channel details and extract channel details
    #youtube = googleapiclient.discovery.build(api_service_name, api_version,developerKey=api_key)

    request = youtube.channels().list(
    part="snippet,contentDetails,statistics",
    id=ch_id)
    response = request.execute()
    ch_info_from_yt = response
    #filtering channel details.
    ch_name = ch_info_from_yt['items'][0]['snippet']['title']
    playlist_id = ch_info_from_yt['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    subcription_count = ch_info_from_yt['items'][0]['statistics']['subscriberCount']
    ch_view_count = ch_info_from_yt['items'][0]['statistics']['viewCount']
    ch_description = ch_info_from_yt['items'][0]['snippet']['description']
    total_videos = ch_info_from_yt['items'][0]['statistics']['videoCount']
    ch_info_for_db = {"channel_name":ch_name,"channel_id":ch_id,"playlist_id":playlist_id,
                    "subscription_count":subcription_count,"channel_viewcount":ch_view_count,
                    "channel_description":ch_description,"total_videos_count":total_videos}
    return ch_info_for_db

def getting_video_ids(chl_id):
    #getting playlist details and extracting info.
    
    res = youtube.channels().list(id=chl_id, 
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    video_id = ""
    while True:
        request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=25,
        playlistId=playlist_id,pageToken=next_page_token)
        playlist_response = request.execute()
        for i in range(0,len(playlist_response)):
        # Get the video ID.
            video_id = playlist_response['items'][0]['snippet']['resourceId']['videoId']
            playlist_list.append(video_id)
        next_page_token = playlist_response.get('nextPageToken')     
        if next_page_token is None:
            break  
    return playlist_list

def getting_video_details(playlist_list):
    video_details = []
    video_info = []
   
    for i in range(0,len(playlist_list),25):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(playlist_list[i:i+25]))
        video_response = request.execute()
        video_details.append(video_response)
    #pprint.pprint(video_response)


    for i in range(0,len(video_details)):
        video_id = video_details[i]["items"][0]["id"]
        video_name = video_details[i]["items"][0]["snippet"]["title"]
        # Extract the video information
        video_description = video_details[i]["items"][0]["snippet"]["description"]
        published_at = video_details[i]["items"][0]["snippet"]["publishedAt"]
        thumbnail = video_details[i]["items"][0]["snippet"]["thumbnails"]["default"]["url"]
        view_count = video_details[i]["items"][0]["statistics"]["viewCount"]
        caption_status = video_details[i]["items"][0]["contentDetails"]["caption"]
        duration = video_details[i]["items"][0]["contentDetails"]["duration"]
        if 'likeCount' in video_details[i]["items"][0]["statistics"]:
            like_count = video_details[i]["items"][0]["statistics"]["likeCount"]
        favorite_count = video_details[i]["items"][0]["statistics"]["favoriteCount"]
        if 'commentCount' in video_details[i]["items"][0]["statistics"]:
            comment_count = video_details[i]["items"][0]["statistics"]["commentCount"]
        channel_name = video_details[i]["items"][0]["snippet"]["channelTitle"]
        video_info_dic = {"video_id":video_id,"video_name":video_name,
                          "channel_name":channel_name,"video_description":video_description,
                        "published_at":published_at,"thumbnail":thumbnail,
                        "caption_status":caption_status,"duration":duration,
                        "view_count":view_count,"like_count":like_count,
                        "favourite_count":favorite_count,"comment_count":comment_count,
                        }
        video_info.append(video_info_dic)
    return video_info

def comment_details(video_Id):
    #getting comment details.
    comment_threads = []
    
    try:
        next_page_token = None
        while True:
            request = youtube.commentThreads().list(
            part="snippet,replies",
            maxResults=25,
            pageToken=next_page_token,
            videoId=video_Id)
            response = request.execute()
            for cmt in response['items']:
                        data = dict(Comment_id = cmt['id'],
                                    Video_id = cmt['snippet']['videoId'],
                                    channel_name = ch_name,
                                    Comment_text = cmt['snippet']['topLevelComment']['snippet']['textDisplay'],
                                    Comment_author = cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                                    Comment_published_date = cmt['snippet']['topLevelComment']['snippet']['publishedAt'],
                                    Like_count = cmt['snippet']['topLevelComment']['snippet']['likeCount'],
                                    Reply_count = cmt['snippet']['totalReplyCount'])
                        comment_threads.append(data)
            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break
            
    except:     
        pass 
    return comment_threads
def comments():
    com_d = []
    for i in playlist_list:
        com_d+= comment_details(i)
    return com_d

#streamlit coding.
if choice_op == "Home":
    # Title Image
    
    col1,col2 = st.columns(2,gap= 'medium')
    col1.markdown("## :blue[Domain] : Social Media")
    col1.markdown("## :blue[Technologies used] : Python,MongoDB, Youtube Data API, MySql, Streamlit")
    col1.markdown("## :blue[Overview] : Retrieving the Youtube channels data from the Google API, storing it in a MongoDB as data lake, migrating and transforming data into a SQL database,then querying the data and displaying it in the Streamlit app.")
    col2.markdown("#   ")
    col2.markdown("#   ")
    col2.markdown("#   ")
    #col2.image("youtubeMain.png")

# EXTRACT and TRANSFORM PAGE
elif choice_op == "Extract and Transform":
    tab1,tab2 = st.tabs(["$\huge EXTRACT $", "$\huge TRANSFORM $"])
    
    # EXTRACT TAB
    with tab1:
        st.markdown("#    ")
        st.write("### Enter YouTube Channel_ID below :")
        ch_id = st.text_input("Hint : Goto channel's home page > Right click > View page source > Find channel_id").split(',')
        try:
            if ch_id and st.button("Extract Data"):
                ch_details = getting_channel_details(ch_id)
                
                st.write(f'#### Extracted data from :green["{ch_details["channel_name"]}"] channel')
                st.table(ch_details)
        except TypeError as e:
                    st.write(e)
                    st.write("handled successfully")
              
        if st.button("Upload to MongoDB"):
                with st.spinner('Please Wait for it...'):
                    ch_det = getting_channel_details(ch_id)
                    video_ids = getting_video_ids(ch_id)
                    video_det = getting_video_details(video_ids)
                    comm_det = comments()
                    # Connecting mongoDB.    
                    client = pymongo.MongoClient('mongodb://localhost:27017')    
                    db = client['youtube_db']
                    if st.button("Upload To MongoDB"):
                        
                        information1 = db.channel_db
                        information1.insert_one(ch_det)
                        
                        information2 = db.video_db
                        information2.insert_many(video_det)
                        
                        information3 = db.comment_db
                        information3.insert_many(comm_det)
                    st.success("Upload to MongoDB successful !!")

     # TRANSFORM TAB
    with tab2:     
        st.markdown("#   ")
        st.markdown("### Select a channel to begin Transformation to SQL")
        
        ch_names_dic = getting_channel_names_from_mongodb()
        #ch_names = [d['channel_name'] for d in ch_names_dic]
        user_inp = st.selectbox("Select channel",options= ch_names_dic)
        #Connecting MYSQL Database.
        mydb = sql.connect(host="localhost",
                        user="root",port=3306,
                        password="admin@123",
                        database= "youtube_db"
                        )
        mycur = mydb.cursor()
        
        def insert_into_channels():
            info1 = db.channel_db
            query = "INSERT INTO channel(channel_name,channel_id,playlist_id,subs_count,view_count,channel_description,total_videos) VALUES(%s,%s,%s,%s,%s,%s,%s)"
                
            for i in info1.find({},{'_id':0}):
                mycur.execute(query,tuple(i.values()))
                mydb.commit()

                
        def insert_into_videos():
            info2 = db.video_db
            query = "INSERT INTO video(video_id,video_name,channel_name,video_description,published_date,thumbnail,caption_status,duration,view_count,like_count,favourite_count,comment_count) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                
            for i in info2.find({},{'_id':0}):
                mycur.execute(query,tuple(i.values()))
                mydb.commit()
        def insert_into_comments():
            info3 = db.comment_db
            query = "INSERT INTO comment1(comment_id,video_id,channel_name,comment_text,comment_author,comment_published_date,like_count,reply_count) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
                
            for i in info3.find({},{'_id':0}):
                mycur.execute(query,tuple(i.values()))
                mydb.commit()
        if st.button("Submit"):
            try:
                
                insert_into_channels()
                insert_into_videos()
                insert_into_comments()
                st.success("Transformation to MySQL Successful!!!")
            except:
                st.error("Channel details already transformed!!")

# VIEW PAGE
elif choice_op == "View":
    
    st.write("## :orange[Select any question to get Insights]")
    questions = ['1. What are the names of all the videos and their corresponding channels?',
    '2. Which channels have the most number of videos, and how many videos do they have?',
    '3. What are the top 10 most viewed videos and their respective channels?',
    '4. How many comments were made on each video, and what are their corresponding video names?',
    '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
    '6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
    '7. What is the total number of views for each channel, and what are their corresponding channel names?',
    '8. What are the names of all the channels that have published videos in the year 2022?',
    '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
    '10. Which videos have the highest number of comments, and what are their corresponding channel names?']
    choice_ques = st.selectbox('Questions : Click the question that you would like to query',questions)
    
    if choice_ques == questions[0]:
        df = pd.read_sql_query("select video_name,channel_name from video order by channel_name",mydb)
        st.write(df)
        
    elif choice_ques == questions[1]:
        df = pd.read_sql_query("select total_videos,channel_name from channel order by total_videos desc",mydb)
        st.write(df)
        st.write("### :green[Number of videos in each channel :]")
        fig = px.bar(df,x='channel_name',y='total_videos',orientation='v',color='channel_name')
        st.plotly_chart(fig,use_container_width = True)
        
    elif choice_ques == questions[2]:
        df = pd.read_sql_query("select view_count , channel_name from video order by view_count desc limit 10",mydb)
        st.write(df)
        st.write("### :green[Top 10 most viewed videos :]")
        fig = px.bar(df,x='channel_name',y='view_count',orientation='h',color='channel_name')
        st.plotly_chart(fig,use_container_width = True)
        
    elif choice_ques == questions[3]:
        df = pd.read_sql_query("select comment_count,video_name,channel_name from video",mydb)
        st.write(df)
          
    elif choice_ques == questions[4]:
        df = pd.read_sql_query("select like_count,video_name,channel_name from video order by like_count desc",mydb)
        st.write(df)
        st.write("### :green[Top 10 most liked videos :]")
        fig=px.bar(df,x='video_name',y='like_count',color='channel_name')
        st.plotly_chart(fig)
        
    elif choice_ques == questions[5]:
        df = pd.read_sql_query("select view_count,channel_name from channel order by view_count desc",mydb)
        st.write(df)
        fig = px.bar(df,x='channel_name',y='view_count',color='channel_name')
        st.plotly_chart(fig)
         
    elif choice_ques == questions[6]:
        df = pd.read_sql_query("select like_count,video_name, channel_name from video",mydb)
        st.write(df)
        st.write("### :green[Channels vs Views :]")
        fig = px.bar(df,x='channel_name',y='like_count',color='channel_name')
        st.plotly_chart(fig)
        
    elif choice_ques == questions[7]:
        df = pd.read_sql_query("""SELECT channel_name FROM video 
                       WHERE published_date LIKE '2023%' 
                       GROUP BY channel_name
                       ORDER BY channel_name""",mydb)
        st.write(df)

    elif choice_ques == questions[8]:
        df = pd.read_sql_query("""SELECT channel_name, 
                        SUM(duration_sec) / COUNT(*) AS average_duration
                        FROM (
                            SELECT channel_name, 
                            CASE
                                WHEN duration REGEXP '^PT[0-9]+H[0-9]+M[0-9]+S$' THEN 
                                TIME_TO_SEC(CONCAT(
                                SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'H', 1), 'T', -1), ':',
                            SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'M', 1), 'H', -1), ':',
                            SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'S', 1), 'M', -1)
                            ))
                                WHEN duration REGEXP '^PT[0-9]+M[0-9]+S$' THEN 
                                TIME_TO_SEC(CONCAT(
                                '0:', SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'M', 1), 'T', -1), ':',
                                SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'S', 1), 'M', -1)
                            ))
                                WHEN duration REGEXP '^PT[0-9]+S$' THEN 
                                TIME_TO_SEC(CONCAT('0:0:', SUBSTRING_INDEX(SUBSTRING_INDEX(duration, 'S', 1), 'T', -1)))
                                END AS duration_sec
                        FROM video
                        ) AS subquery
                        GROUP BY channel_name""",mydb)
        st.write(df)
        st.write("### :green[Average video duration for channels :]")
        fig = px.bar(df,x='channel_name',y='average_duration',color ='channel_name')
        st.plotly_chart(fig)

    elif choice_ques == questions[9]:
        df = pd.read_sql_query("""SELECT channel_name,video_id,comment_count
                            FROM video
                            ORDER BY comment_count DESC
                            LIMIT 10""",mydb)
        st.write("### :green[Videos with most comments :]")
        fig = px.bar(df,x='video_id',y='comment_count',color ='channel_name')
        st.plotly_chart(fig,use_container_width=True)