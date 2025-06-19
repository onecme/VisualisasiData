import streamlit as st
import pandas as pd
import plotly.express as px
from shapely import wkt
import matplotlib.pyplot as plt
import geopandas as gpd
import plotly.graph_objects as go

# Load data
df = pd.read_csv("perguruanTinggiIndonesia.csv")

# Hapus index jika ada
if "Unnamed: 0" in df.columns:
    df = df.drop(columns=["Unnamed: 0"])

# Rename kolom
df.rename(columns={
    "Rasio": "Rasio 2017",
    "Rasio.1": "Rasio 2018",
    "Dosen": "Dosen 2017",
    "Dosen.1": "Dosen 2018",
    "Mhs": "Mahasiswa 2017",
    "Mhs.1": "Mahasiswa 2018",
    "Nama Prodi": "Nama Perguruan Tinggi",
    "ID_x": "Id Perguruan Tinggi",
    "ID_y": "Id Geometry",
    "kode": "Kode",
    "SUMBER": "Sumber"
}, inplace=True)

# Ubah kolom 'geometry' menjadi geometri
df['geometry'] = df['geometry'].apply(wkt.loads)

# Set halaman
st.set_page_config(layout="wide")
st.title("📊 Dashboard Perguruan Tinggi Indonesia")

# Sidebar filter
st.sidebar.header("🔎 Filter Data Utama")
provinsi = st.sidebar.multiselect("Pilih Provinsi", df['Provinsi'].unique(), key="filter_provinsi")
penyelenggara = st.sidebar.multiselect("Pilih Penyelenggara", df['Penyelenggara'].unique(), key="filter_penyelenggara")
status = st.sidebar.multiselect("Pilih Status", df['Status'].unique(), key="filter_status")

# Filter Data
filtered_df = df.copy()
if provinsi:
    filtered_df = filtered_df[filtered_df['Provinsi'].isin(provinsi)]
if penyelenggara:
    filtered_df = filtered_df[filtered_df['Penyelenggara'].isin(penyelenggara)]
if status:
    filtered_df = filtered_df[filtered_df['Status'].isin(status)]

# Statistik Ringkas
st.subheader("📌 Statistik Ringkas")
col1, col2, col3 = st.columns(3)
col1.metric("Jumlah Penguruan Tinggi", len(filtered_df))
col2.metric("Provinsi Tercakup", filtered_df['Provinsi'].nunique())
col3.markdown("Penyelenggara:  \n" + "<br>".join(filtered_df['Penyelenggara'].unique()), unsafe_allow_html=True)

# Hitung frekuensi prodi dari data yang difilter
frekuensi_prodi = filtered_df.groupby('Provinsi').size().reset_index(name='Jumlah Perguruan Tinggi')
frekuensi_prodi['Persentase'] = (frekuensi_prodi['Jumlah Perguruan Tinggi'] / frekuensi_prodi['Jumlah Perguruan Tinggi'].sum()) * 100

# Ambil seluruh data provinsi dan geometry (unik)
df_all_geo = df.drop_duplicates(subset='Provinsi')[['Provinsi', 'geometry']]

# Gabungkan dengan frekuensi hasil filter
df_freq = df_all_geo.merge(frekuensi_prodi, on='Provinsi', how='left')
df_freq['Persentase'] = df_freq['Persentase'].fillna(0)

# GeoDataFrame
gdf_freq = gpd.GeoDataFrame(df_freq, geometry='geometry')

# Hitung min dan max dari data global (agar warna tetap konsisten)
frekuensi_global = df.groupby('Provinsi').size().reset_index(name='Jumlah Perguruan Tinggi')
frekuensi_global['Persentase'] = (frekuensi_global['Jumlah Perguruan Tinggi'] / frekuensi_global['Jumlah Perguruan Tinggi'].sum()) * 100
min_persen = frekuensi_global['Persentase'].min()
max_persen = frekuensi_global['Persentase'].max()

# Plot Peta
fig, ax = plt.subplots(figsize=(20, 12))
gdf_freq.plot(
    column='Persentase',
    cmap='Greens',
    linewidth=0.8,
    edgecolor='0.8',
    legend=True,
    ax=ax,
    vmin=min_persen,
    vmax=max_persen,
    legend_kwds={
        'label': "Persentase Jumlah Perguruan Tinggi (%)",
        'orientation': "vertical",
        'shrink': 0.6,
        'aspect': 20
    }
)

# Tambahkan label
for idx, row in gdf_freq.iterrows():
    if row['geometry'].centroid.is_empty:
        continue
    plt.annotate(
        text=row['Provinsi'],
        xy=(row['geometry'].centroid.x, row['geometry'].centroid.y),
        ha='center',
        fontsize=8,
        color='black'
    )

ax.set_title("Sebaran Persentase Perguruan Tinggi per Provinsi", fontsize=20)
ax.axis('off')
plt.tight_layout()
st.pyplot(fig)

# Bar Chart: Jumlah Perguruan Tinggi
st.subheader("📍 Jumlah Perguruan Tinggi per Provinsi")
pt_per_prov = filtered_df['Provinsi'].value_counts().reset_index()
pt_per_prov.columns = ['Provinsi', 'Jumlah Perguruan Tinggi']
fig_bar = px.bar(pt_per_prov, x='Provinsi', y='Jumlah Perguruan Tinggi', color='Jumlah Perguruan Tinggi', title="Jumlah Perguruan Tinggi per Provinsi")
st.plotly_chart(fig_bar, use_container_width=True)

# Stacked Bar Chart: Dosen & Mahasiswa
st.subheader("📊 Perbandingan Dosen dan Mahasiswa (Stacked Bar Interaktif)")
df_plot = df[['Provinsi', 'Dosen 2017', 'Mahasiswa 2017', 'Dosen 2018', 'Mahasiswa 2018']].copy()
df_grouped = df_plot.groupby('Provinsi').sum().reset_index()
df_grouped['Total'] = df_grouped[['Dosen 2017', 'Mahasiswa 2017', 'Dosen 2018', 'Mahasiswa 2018']].sum(axis=1)
df_grouped = df_grouped.sort_values('Total', ascending=False)

fig_stack = go.Figure()
fig_stack.add_trace(go.Bar(x=df_grouped['Provinsi'], y=df_grouped['Dosen 2017'], name='Dosen 2017', marker_color='#1f77b4'))
fig_stack.add_trace(go.Bar(x=df_grouped['Provinsi'], y=df_grouped['Mahasiswa 2017'], name='Mahasiswa 2017', marker_color='#aec7e8'))
fig_stack.add_trace(go.Bar(x=df_grouped['Provinsi'], y=df_grouped['Dosen 2018'], name='Dosen 2018', marker_color='#ff7f0e'))
fig_stack.add_trace(go.Bar(x=df_grouped['Provinsi'], y=df_grouped['Mahasiswa 2018'], name='Mahasiswa 2018', marker_color='#ffbb78'))

fig_stack.update_layout(
    barmode='stack',
    title='📚 Perbandingan Jumlah Dosen dan Mahasiswa per Provinsi (2017 & 2018)',
    xaxis_title='Provinsi',
    yaxis_title='Jumlah',
    legend_title='Kategori',
    height=600
)
st.plotly_chart(fig_stack, use_container_width=True)

# Data Table
st.subheader("📄 Data Lengkap")
search_term = st.text_input("Cari Nama Perguruan Tinggi")
final_filtered_df = filtered_df.copy()
if search_term:
    final_filtered_df = final_filtered_df[final_filtered_df['Nama Perguruan Tinggi'].str.contains(search_term, case=False, na=False)]
st.dataframe(final_filtered_df.drop(columns=['geometry']))

# Download tombol
st.download_button(
    "📥 Download Data yang Difilter",
    filtered_df.drop(columns=['geometry']).to_csv(index=False),
    "filtered_data.csv",
    "text/csv"
)
