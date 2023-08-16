import streamlit as st
import pandas as pd
from core.db_utils import db_connection
from core.db_connect import get_dbname

st.set_page_config(layout='wide')
st.title("User Attendance Report")


DB_NAME = get_dbname()
# DB_NAME = 'srmlt_attendance'
conn = db_connection(DB_NAME)

mysql_cursor = conn.cursor(buffered=True)

user_ids = mysql_cursor.execute('SELECT attendee_name FROM manual_registration')
user_ids = mysql_cursor.fetchall()
str_id = [str(item[0]) for item in user_ids]

user_id = st.selectbox('Select Userid', str_id)

get_id = mysql_cursor.execute("SELECT userid FROM manual_registration WHERE attendee_name =%s", (user_id,))
get_id= mysql_cursor.fetchone()
id = get_id[0]

search_container = st.empty()
try:
    search_btn = search_container.button('search')
except Exception as e:
    print('error', e)

if search_btn:
    mysql_cursor.execute("""SELECT * FROM checkinout WHERE userid = %s ORDER BY checktime DESC""", (id,))
    attendance_result = mysql_cursor.fetchall()
    if attendance_result:
        attendance_df = pd.DataFrame(attendance_result,
                            columns=['id', 'userid', 'checktime', 'checktype', 'verifycode', 'SN', 'sensorid', 'WorkCode', 'Reserved'])
        st.write(attendance_df)
    else:
        st.warning("User not Found!")
        
