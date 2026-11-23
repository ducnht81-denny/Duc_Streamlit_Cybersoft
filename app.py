import streamlit as st
import pandas as pd
import openai

#1. Cấu hình cơ bản cho streamlit page:

st.set_page_config(
    page_title= "Ask your CSV",
    page_icon= "📊",
    layout= "wide" 
)
#Khởi tạo OpenAI Client:
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])



#Khởi tạo các thông số cần cho 1 section của Streamlit
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

#3. Main Chat Interface:
if st.session_state.df is not None: #Nếu đã có df thì mới thực hiện
    #Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    #Chat input: Nhập câu hỏi vào cho AI
    user_input = st.chat_input("Ask a question about your data: ")
    
    if user_input: #Người dùng đã nhập câu hỏi vào
        #Add user message to history
        st.session_state.messages.append({"role":"user", "content": user_input}) #Lưu lại lịch sử người dùng đã nhập vào
        
        #Display user message:
        with st.chat_message("user"):
            st.markdown(user_input)
            
        #Prepare data context with token optimization:
        df = st.session_state.df
        if len(df) > 100:
            data_context = f"""
            Data shape: {st.session_state.data_summary['shape']},
            Columns: {', '.join(st.session_state.data_summary['columns'])},
            Data types: {st.session_state.data_summary['dtypes']},
            Sample row: {st.session_state.data_summary['sample']},
            Basic statistics: {st.session_state.data_summary['stats']}
            """
        else: #len(df) <100 -> đưa cho AI full data
            data_context = f"""
            Full dataset:
            {df.to_string()}
            """
        #System Prompt:
        system_prompt = f"""
        You are a helpful data analyst assistant.
        The user has uploaded a CSV file with the following information:
        {data_context}
        
        Guidelines:
        1. Answer the user's question clearly and concisely
        2. Focus on providing insights about the data
        3. Be specific and helpful
        """
        #Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your data.."):
                try: #Định nghĩa model và cấu hình AI Model
                    response = client.chat.completions.create(
                        model="gpt-6-luna",
                        messages=[
                            {"role": "system", "content": system_prompt}, #Chọn nghề và chuyên môn hóa cho AI
                            {"role": "user", "content": user_input} #Là người dùng đặt câu hỏi cho AI
                        ],
                        # temperature=0.1 #0.1 -> 1: càng thấp thì ít lan man
                        max_completion_tokens=1500 #Độ dài tối đa ~ 1500 chữ
                    )
                    reply = response.choices[0].message.content #Lưu kết quả phản hồi cho AI
                    st.markdown(reply) #In ra kết quả từ AI
                    
                    #Save assistant reponse to history
                    st.session_state.messages.append({"role": "assistant","content": reply})
                    
                except Exception as e:
                    st.error(f"Error generation reponse: {str(e)}")
                    st.info("Please try again or rephrase your question.")
        
else:
    #No data uploaded state
    
    col1, col2, col3 = st.columns([1,2,1]) #Chia làm 4 phần: col1, col3 -> 25%, col2 -> 50%
    with col2:
        st.info("Please upload a CSV file to start")
        
        #Example questions:
        st.markdown("### Example question you can ask:")
        st.markdown("""
            - What are the main trends in my data?
            - Show me a correlation matrix
            - Create a bar chart of the top 10 categories
            - What's the average value by month?
            - Are there any outliers in the price column?
                    """)