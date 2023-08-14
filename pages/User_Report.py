import streamlit as st
import pandas as pd
from core.db_utils import db_connection

st.set_page_config(layout='wide')
st.title("User Report")


# DB_NAME = get_dbname()
DB_NAME = 'srmlt_attendance'
conn = db_connection(DB_NAME)

mysql_cursor = conn.cursor(buffered=True)

id = st.text_input("Enter the User_id:")

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
        
