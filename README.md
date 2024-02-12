# youtube-project
youtube harvesting and warehousing using MYSQL, Streamlit, MongoDB and python
1.	Set up a Streamlit app: Streamlit is a great choice for building data visualization and analysis tools quickly and easily. I used Streamlit to create a simple UI where users can enter a YouTube channel ID, view the channel details, and select channels to migrate to the data warehouse.
2.	Connect to the YouTube API: I used the YouTube API to retrieve channel and video data. I used the Google API client library for Python to make requests to the API.
3.	Store data in a MongoDB data lake: Once I retrieved the data from the YouTube API, I stored it in a MongoDB data lake. MongoDB is a great choice for a data lake because it can handle unstructured and semi-structured data easily.
4.	Migrate data to a SQL data warehouse: After i've collected data for multiple channels,  migrate it to a SQL data warehouse. I could use a SQL database such as MySQL for this.
5.	Query the SQL data warehouse: I used SQL queries to join the tables in the SQL data warehouse and retrieve data for specific channels based on user input. I used a Python SQL library such as Pymysql to interact with the SQL database.
6.	Display data in the Streamlit app: Finally, I displayed the retrieved data in the Streamlit app. I used Streamlit's data visualization features to create charts and graphs to help users analyze the data.
