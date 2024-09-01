import streamlit as st
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="Data CPNS 2024", layout="wide")

conn = st.connection("postgresql", type='sql')
# Set up the sidebar
st.sidebar.title("Data CPNS 2024")

def read_options(file_path):
    with open(file_path, 'r') as file:
        options = [line.strip() for line in file if line.strip()]
    return options

# Path to the text file
file_path = 'prodi.txt'

# Get options from the file
options = read_options(file_path)
options.insert(0, "All")
# Sidebar widgets
option = st.sidebar.selectbox("Choose an option", ["Home", "Insight", "Contact"])

# Initialize session state
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1
if 'selected_prodi' not in st.session_state:
    st.session_state.selected_prodi = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'download_button' not in st.session_state:
    st.session_state.download_button = None

if 'data_all' not in st.session_state:
    st.session_state.data_all = pd.read_csv('data_cpns_v2.csv', sep=';')
else:
    data_all = st.session_state.data_all  # If already initialized, use the session state value

def verify_key():
    key = st.session_state.secret_key
    query = f"""
    SELECT *
    FROM key_cpns
    WHERE secret_key = '{key}'
    """
    df_key = conn.query(query)
    print('df_key', df_key)
    if len(df_key) > 0:
        st.session_state.key_valid = True
        st.session_state.access_to = df_key['access_to'].iloc[0]  # Store the access_to value
    else:
        st.session_state.key_valid = False
        st.session_state.access_to = None

# Main content based on the selected option
if option == "Home":
    st.title("Data CPNS 2024")
    st.write("Made with ❤️ by [Raka Luthfi](https://www.linkedin.com/in/rakaluth/)")
    # Add custom CSS to hide the download button and index
    hide_table_row_index = """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
        """
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

    dropdown1 = st.selectbox("Program Studi", options, key="prodi_dropdown")
    submit_button = st.button("Submit")

    if submit_button or st.session_state.selected_prodi:
        if submit_button:
            st.session_state.selected_prodi = dropdown1
            st.session_state.page_number = 1  # Reset page number on new selection

        # Find the Excel file based on the selected dropdown
        if st.session_state.selected_prodi == "All":
            df = st.session_state.data_all
        else:
            excel_file = f'./data/{st.session_state.selected_prodi}_data.xlsx'
            df = pd.read_excel(header=0, io=excel_file, sheet_name=0)
        
        df_prodi = data_all[data_all['program_studi'] == st.session_state.selected_prodi]
        # Read the Excel file if it hasn't been read before or if it's a new selection
        if st.session_state.df is None or submit_button:
            
            # Drop unnecessary column
            df.drop(columns=['formasi_id'], inplace=True)
            
            # Rename columns
            df.rename(columns={
                'ins_nm': 'Nama Instansi',
                'jp_nama': 'Jenis Pengadaan',
                'formasi_nm': 'Formasi',
                'jabatan_nm': 'Jabatan',
                'jumlah_formasi': 'Jumlah Formasi',
                'gaji_min': 'Gaji Minimum',
                'gaji_max': 'Gaji Maximum',
            }, inplace=True)
            
            st.session_state.df = df

        # Pagination parameters
        rows_per_page = 15
        total_rows = len(st.session_state.df)
        total_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page > 0 else 0)

        # Ensure total_pages is at least 1
        total_pages = max(total_pages, 1)

        # Display the DataFrame for the current page
        start_idx = (st.session_state.page_number - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        df_page = st.session_state.df[start_idx:end_idx]
        
        # Reset the index and drop it before displaying
        df_page = df_page.reset_index(drop=True)
        
        # Display the dataframe without index and download button
        st.dataframe(df_page)

        # Pagination control
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col1:
            if st.button("Previous", disabled=st.session_state.page_number == 1):
                st.session_state.page_number = max(1, st.session_state.page_number - 1)
                st.rerun()
        with col2:
            st.write(f"Page {st.session_state.page_number} of {total_pages}")
        with col3:
            if st.button("Next", disabled=st.session_state.page_number == total_pages):
                st.session_state.page_number = min(total_pages, st.session_state.page_number + 1)
                st.rerun()
        with col4:
            with st.popover("Download Data"):
                st.markdown(f"Download Data untuk Program Studi {st.session_state.selected_prodi}")
                
                st.text_input("Secret Key", key="secret_key", on_change=verify_key)
                
                if 'key_valid' in st.session_state:
                    if st.session_state.key_valid:
                        if 'access_to' in st.session_state:
                            if st.session_state.access_to == 'all':
                                # Allow download for all program studi
                                if st.session_state.selected_prodi == 'All':
                                    csv = st.session_state.data_all.to_csv(index=False)
                                    st.success("Access Granted, Please Wait")
                                    st.download_button(
                                        label="Download All Data",
                                        data=csv,
                                        file_name="all_cpns_data.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    csv = df_prodi.to_csv(index=False)
                                    st.success("Access Granted, Please Wait")
                                    st.download_button(
                                        label=f"Download {st.session_state.selected_prodi} Data",
                                        data=csv,
                                        file_name=f"{st.session_state.selected_prodi}_cpns_data.csv",
                                        mime="text/csv"
                                    )
                            elif st.session_state.access_to == st.session_state.selected_prodi:
                                # Allow download only for the specific program studi
                                csv = df_prodi.to_csv(index=False)
                                st.success("Access Granted, Please Wait")
                                st.download_button(
                                    label=f"Download {st.session_state.selected_prodi} Data",
                                    data=csv,
                                    file_name=f"{st.session_state.selected_prodi}_cpns_data.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.error("Access Denied for this Program Studi")
                        else:
                            st.error("Access information not available")
                    else:
                        st.error("Key Invalid")
                        
                    

elif option == "Insight":
    st.title("Insight CPNS 2024")
    
    # Query to get the total number of formasi for each prodi
    query = """
        with base as (
            SELECT distinct formasi_id, jumlah_formasi, "disable", gaji_min, gaji_max
            FROM public.data_cpns_v2
            )
            select sum(jumlah_formasi) as total_formasi
            from base
            ;
    """

    # Execute the query
    total_formasi = conn.query(query)
    total_formasi = total_formasi['total_formasi'][0]

    # st.write(f"Total Formasi: {total_formasi}")

    # Query to get the total number of formasi for each prodi
    query = """
        SELECT 
            count(distinct program_studi)
        FROM data_cpns_v2
    """

    total_prodi = conn.query(query)
    total_prodi = total_prodi['count'][0]

    query = """
        SELECT 
            count(distinct ins_nm)
        FROM data_cpns_v2
    """

    total_instansi = conn.query(query)
    total_instansi = total_instansi['count'][0]

    # Execute the query
    # total_formasi_prodi = conn.query(query)
    col1, col2, col3 = st.columns(3)
    with col1:
        # st.write("Program Studi")
        st.metric("Total Kuota", f"{total_formasi:,}")
    with col2:
        st.metric("Total Prodi", f"{total_prodi:,}")
    with col3:
        st.metric("Total Instansi", f"{total_instansi:,}")
    

    kolom1, kolom2= st.columns(2)

    with kolom1:
        # Query and plot for Distribution of Maximum Salaries Across Program Studi
        query = """
                with base as (
                SELECT distinct
                                program_studi,
                                gaji_max,
                                row_number() over(partition by program_studi order by gaji_max desc) as rn
                            FROM data_cpns_v2
                            order by program_studi, gaji_max desc
                )
                select 
                    program_studi,
                    gaji_max
                from base
                where rn = 1
                order by gaji_max desc
                limit 10
        """
        df = conn.query(query)
        fig1 = px.bar(df, 
                    x='gaji_max', 
                    y='program_studi', 
                    title=' ', 
                    color='program_studi',
                    text_auto=True,
                    orientation='h'
                    )
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=20, color='black', family='Arial'),
            font=dict(size=12, color='black'),
            xaxis_title="Maximum Salary (IDR)",
            yaxis_title="",
            margin=dict(l=40, r=40, t=40, b=40),
            showlegend=False
        )
        st.subheader("Top 10 Program Studi with the Highest Maximum Salaries", divider=True)
        st.plotly_chart(fig1)

        # Query and plot for Distribution of Program Studi
        query = """
            SELECT distinct program_studi, sum(jumlah_formasi) as jumlah_formasi
            FROM data_cpns_v2
            group by program_studi
            order by sum(jumlah_formasi) desc
            limit 5
        """
        df = conn.query(query)
        fig2 = px.pie(df, 
                    values='jumlah_formasi', 
                    names='program_studi', 
                    title=' ',
                    color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=20, color='black', family='Arial'),
            font=dict(size=12, color='black'),
            legend_title_text='Program Studi',
        )
        st.subheader("Top 5 Program Studi with the Most Formasi", divider=True)
        st.plotly_chart(fig2)

        # Execute the SQL query
        query = """
        with base as (
           SELECT distinct 
           		program_studi
           		, ins_nm
           		, sum(jumlah_formasi) as jumlah_formasi
           		, row_number() over(partition by program_studi order by program_studi, sum(jumlah_formasi) desc) as rn
            FROM data_cpns_v2
            group by program_studi, ins_nm
            )
            , most_jumlah_formasi as (
            	select distinct 
           		program_studi
           		, sum(jumlah_formasi) as jumlah_formasi
           		from data_cpns_v2
           		group by program_studi
           		order by sum(jumlah_formasi) desc
           		limit 5
            )
            select 
            	program_studi
           		, ins_nm
           		, jumlah_formasi
            from base 
            where rn <= 5 and program_studi in (select program_studi from most_jumlah_formasi)
            order by program_studi, jumlah_formasi desc
        """
        df = conn.query(query)
        df = df.sort_values(by=['program_studi', 'jumlah_formasi'], ascending=[True, False])

        # Create a stacked bar chart
        fig = px.bar(df, 
                    x='program_studi', 
                    y='jumlah_formasi', 
                    color='ins_nm', 
                    title='Top 5 Institutions by Program Studi', 
                    text_auto=True, 
                    labels={'jumlah_formasi':'Jumlah Formasi', 'program_studi':'Program Studi', 'ins_nm':'Institution'},
                    color_discrete_sequence=px.colors.qualitative.Pastel)  # Use a pastel color scale for aesthetics

        # Customize the layout for aesthetics
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            title_font=dict(size=20, color='black', family='Arial'),  # Title font style
            font=dict(size=12, color='black'),  # Axis and label font style
            xaxis_title="Program Studi",  # Customize x-axis title
            yaxis_title="Jumlah Formasi",  # Customize y-axis title
            barmode='stack'  # Stacked bar mode
        )

        # Display the chart
        st.plotly_chart(fig)

    with kolom2:
        # Query and plot for Distribution of Maximum Salaries Across Institutions
        query = """
            with base as (
            SELECT distinct
                            ins_nm,
                            gaji_max,
                            row_number() over(partition by ins_nm order by gaji_max desc) as rn
                        FROM data_cpns_v2
                        order by ins_nm, gaji_max desc
            )
            select 
                ins_nm,
                gaji_max
            from base
            where rn = 1
            order by gaji_max desc
            limit 10
            ;
        """
        df = conn.query(query)
        # df
        fig3 = px.bar(df, 
                    x='gaji_max', 
                    y='ins_nm', 
                    title=' ',
                    color='ins_nm',
                    text_auto=True,
                    orientation='h',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                    )
        fig3.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=20, color='black', family='Arial'),
            font=dict(size=12, color='black'),
            xaxis_title="Maximum Salary (IDR)",
            yaxis_title="",
            margin=dict(l=40, r=40, t=40, b=40),
            showlegend=False
        )
        st.subheader("Top 10 Institutions with the Highest Maximum Salaries", divider=True)
        st.plotly_chart(fig3)

        # Query and plot for Distribution of Institutions
        query = """
            SELECT ins_nm, sum(jumlah_formasi) as jumlah_formasi
            FROM data_cpns_v2
            group by ins_nm
            order by jumlah_formasi desc
            limit 5
        """
        df = conn.query(query)
        df['short_ins_nm'] = df['ins_nm'].apply(lambda x: x if len(x) <= 20 else x[:20] + '...')

        fig4 = px.pie(df, 
                    values='jumlah_formasi', 
                    names='short_ins_nm', 
                    title=' ',
                    color_discrete_sequence=px.colors.qualitative.Pastel)
        fig4.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font=dict(size=20, color='black', family='Arial'),
            font=dict(size=12, color='black'),
            legend_title_text='Institutions',
            legend=dict(
                x=1, 
                y=0.5,
                orientation='v',
                font=dict(size=10),
            )
        )
        st.subheader("Top 5 Institutions with the Most Formasi", divider=True)
        st.plotly_chart(fig4)

        query = """
            with base as (
            select distinct formasi_id, formasi_nm, jumlah_formasi 
            from public.data_cpns_v2
            )
            select 
                formasi_nm
                , sum(jumlah_formasi) total_formasi
            from base
            group by formasi_nm
            order by sum(jumlah_formasi) desc
        """

        # Execute the query
        df = conn.query(query)

        # Create a bar chart
        fig = px.bar(df, 
                    x='formasi_nm', 
                    y='total_formasi', 
                    title='Total Formasi by Formasi', 
                    text_auto=True,
                    labels={'total_formasi': 'Total Formasi', 'formasi_nm': 'Formasi'},
                    color='formasi_nm',  # Use 'formasi_nm' to assign different colors
                    color_discrete_sequence=px.colors.qualitative.Pastel)  # Customize the color sequence

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            title_font=dict(size=20, color='black', family='Arial'),  # Title font style
            font=dict(size=12, color='black'),  # Axis and label font style
            xaxis_title="Formasi",  # Customize x-axis title
            yaxis_title="Total Formasi",  # Customize y-axis title
        )

        # Display the chart
        st.subheader("Total Formasi by Formasi", divider=True)
        st.plotly_chart(fig)






elif option == "Contact":
    st.title("Contact Page")
    st.write("This is the Contact Page.")
