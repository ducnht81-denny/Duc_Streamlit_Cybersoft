import streamlit as st
import pandas as pd 

st.set_page_config(
    page_title= "Ask your CSV",
    page_icon= "📊",
    layout= "wide" 
)

#Session state initialization:
if "messages" not in st.session_state: #Nếu chưa có message ban đầu thì khởi tạo
    st.session_state.messages = []
    
#Khởi tạo "df" -> None, "data_summary" -> None
if "df" not in st.session_state:
    st.session_state.df = None
if "data_summary" not in st.session_state:
    st.session_state.data_summary = None

st.title("📊 Ask your CSV")
st.markdown("Upload your data and ask questions in plain English!")

#2. Tạo sidebar để upload data từ bên ngoài vào
with st.sidebar:
    st.header("📤 Data Upload")
    uploaded_file = st.file_uploader("Upload a CSV file", type = ["csv"]) #chỉ nhận file csv
    
    if uploaded_file: #Nếu file này không rỗng
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state.df = df #Lưu DataFrame vào Session State
            
            #Create data summary for token optimization
            #Shape, column names, dtypes, sample (head(10)), basic statistics
            st.session_state.data_summary = {
                "shape": df.shape,
                "columns": df.columns.to_list(),
                "dtypes": df.dtypes.to_list(),
                "sample": df.head(3).to_dict(),
                "stats": df.describe().to_dict() if not df.empty else{} #Nếu df rỗng -> không kết quả
            }
            
            st.success(f"✅ Loaded {df.shape[0]} rows x {df.shape[1]} columns") #in ra kết quả
            
            #Data preview:
            with st.expander("Preview Data"):
                st.dataframe(df.head(10)) #Hiện thị 10 dòng đầu tiên của Dataframe
                
            #Data summary:
            with st.expander("Data Prompt for AI"):
                st.session_state.data_summary
                
            #Basic statistics:
            with st.expander("Data Summary"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Rows", df.shape[0])
                    st.metric("Total Columns", df.shape[1])
                with col2:
                    st.metric("Memory Usage", f"{df.memory_usage().sum() / 1024:.1f} KB")
                    st.metric("Missing Value", df.isnull().sum().sum())
                        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.info("Please make sure your file is a valid CSV format.")
    else:
        st.info("Upload a CSV file to start analyzing!")

