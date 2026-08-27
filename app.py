import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Dashboard Konsinyasi PT Semen Padang", layout="wide")

# ==========================================
# 2. DATA LIVE DARI GOOGLE SHEETS
# ==========================================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcN6N90LcQD0MDEGGlJoYqL6OGRJxH4y6ZUu-yk9pnf6LAyab6U5N1VD6uiHwxK6vuMKdvQa_-2Erk/pub?output=csv"

try:
    if SHEET_CSV_URL == "TARUH_LINK_CSV_GOOGLE_SHEETS_KAMU_DI_SINI":
        st.warning("⚠️ Menampilkan data sementara. Jangan lupa masukkan link CSV Google Sheets kamu ke dalam kode!")
        df = pd.DataFrame({'No':[1], 'Kategori':['Bearing'], 'Vendor':['Dummy'], 'Material':['SI000000'], 'Description':['Dummy Data'], 'Stock_Sistem':[0], 'Stock_Fisik':[0], 'Selisih':[0]})
    else:
        df = pd.read_csv(SHEET_CSV_URL)
except Exception as e:
    st.error(f"Gagal mengambil data. Detail error: {e}")
    st.stop()

# --- FUNGSI GENERATOR LOKASI DUMMY ---
def generate_dummy_location(row):
    vendor = str(row.get('Vendor', '')).upper()
    material = str(row.get('Material', 'Unknown'))
    
    # Mengunci angka acak berdasarkan nama Material agar posisinya tidak berubah-ubah saat di-refresh
    random.seed(material) 
    
    if 'MULTICIPTA' in vendor:
        ruang = 'Ruang 1'
        # Pilihan rak beserta max levelnya untuk Ruang 1
        rak_choices = [('Rak A', 3), ('Rak B', 5), ('Rak C', 5), ('Rak D', 4)]
    elif 'TEKNINDO' in vendor or 'CENTRAL' in vendor or 'CBI' in vendor:
        ruang = 'Ruang 2'
        # Pilihan rak beserta max levelnya untuk Ruang 2
        rak_choices = [('R-01', 6), ('R-02', 6)]
    else:
        ruang = 'Ruang 1'
        rak_choices = [('Rak A', 3)]
        
    chosen_rak, max_lvl = random.choice(rak_choices)
    chosen_lvl = f"L{random.randint(1, max_lvl):02d}"
    
    return pd.Series([ruang, chosen_rak, chosen_lvl])

# Menerapkan lokasi jika kolom tidak ada atau kosong
if 'Ruang' not in df.columns or df['Ruang'].isna().all():
    df[['Ruang', 'Rak', 'Level']] = df.apply(generate_dummy_location, axis=1)

# Fungsi Penentuan Status Otomatis
def tentukan_status(selisih):
    if pd.isna(selisih): return 'Cukup'
    if selisih > 0: return 'Lebih'
    elif selisih < 0: return 'Kurang'
    else: return 'Cukup'

if 'Selisih' in df.columns:
    df['Status'] = df['Selisih'].apply(tentukan_status)
else:
    df['Status'] = 'Cukup'

# ==========================================
# 3. FUNGSI MENGGAMBAR RAK 2D
# ==========================================
def draw_rack(rack_name, max_levels, target_rack=None, target_level=None):
    html = f"<div style='text-align: center; margin-bottom: 20px; font-family: sans-serif;'>"
    html += f"<div style='font-weight: bold; margin-bottom: 8px; color: #2C3E50; font-size: 16px;'>{rack_name}</div>"
    html += f"<div style='border: 2px solid #555; border-radius: 8px; display: inline-block; padding: 12px; background-color: #F8F9FA; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);'>"
    
    for i in range(max_levels, 0, -1):
        lvl_str = f"L{i:02d}"
        is_target = (rack_name == target_rack) and (lvl_str == target_level)
        
        bg_color = "#DC3545" if is_target else "#FFFFFF"
        text_color = "#FFFFFF" if is_target else "#555555"
        border_color = "#DC3545" if is_target else "#CCCCCC"
        icon = "📌" if is_target else ""
        font_weight = "bold" if is_target else "normal"
        
        html += f"<div style='border: 1px solid {border_color}; border-radius: 4px; padding: 6px; margin: 4px; background-color: {bg_color}; color: {text_color}; font-size: 14px; font-weight: {font_weight}; width: 85px; height: 38px; display: flex; align-items: center; justify-content: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.05);'>"
        html += f"{lvl_str} {icon}"
        html += f"</div>"
        
    html += f"</div></div>"
    return html

# ==========================================
# 4. HEADER DASHBOARD
# ==========================================
col_head1, col_head2 = st.columns([5, 1])

with col_head1:
    st.title("Dashboard Monitoring & Locator Konsinyasi")
    st.caption(f"Last Update: {datetime.now().strftime('%d %b %Y, %H:%M WIB')} | Unit Pengelolaan Gudang PT Semen Padang")

with col_head2:
    # Solusi Logo: Menggunakan URL alternatif yang lebih stabil
    st.image("logo_sp.png", width=150)

st.markdown("---")

# ==========================================
# 5. PEMBAGIAN TAB UX 
# ==========================================
tab_summary, tab_locator, tab_data = st.tabs([
    "📊 Ringkasan & Grafik", 
    "🗺️ Lokator 2D Bearing", 
    "📋 Data Tabel"
])

# ----------------- TAB 1: SUMMARY & CHART -----------------
with tab_summary:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Material Aktual", f"{len(df)} Jenis")
    col2.metric("🟢 Stock Cukup", len(df[df['Status'] == 'Cukup']))
    col3.metric("🟠 Stock Lebih", len(df[df['Status'] == 'Lebih']))
    col4.metric("🔴 Stock Kurang", len(df[df['Status'] == 'Kurang']))
    
    st.markdown("<br>", unsafe_allow_html=True) 

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        if 'Status' in df.columns and len(df) > 1:
            fig_status = px.pie(df, names='Status', title="Persentase Berdasarkan Status",
                                color='Status', color_discrete_map={'Cukup':'#28a745', 'Lebih':'#fd7e14', 'Kurang':'#dc3545'}, hole=0.3)
            st.plotly_chart(fig_status, use_container_width=True)

    with col_chart2:
        if 'Status' in df.columns:
            df_kurang = df[df['Status'] == 'Kurang']
            if not df_kurang.empty:
                fig_vendor = px.pie(df_kurang, names='Vendor', title="Stock Kurang Berdasarkan Vendor", hole=0.4)
                st.plotly_chart(fig_vendor, use_container_width=True)
            else:
                st.info("Saat ini tidak ada perbedaan stock yang kurang.")

# ----------------- TAB 2: LOCATOR 2D -----------------
with tab_locator:
    st.markdown("Cari / Masukkan Nomor Material (SI) untuk melihat denah lokasi:")
    
    if 'Material' in df.columns:
        selected_material = st.selectbox("", df['Material'].dropna().unique(), label_visibility="collapsed")
        
        if selected_material:
            loc_data = df[df['Material'] == selected_material].iloc[0]
            target_ruang = str(loc_data.get('Ruang', ''))
            target_rak = str(loc_data.get('Rak', ''))
            target_level = str(loc_data.get('Level', ''))
            
            st.success(f"**Identitas:** {loc_data.get('Material Description', loc_data.get('Description', '-'))} | **Vendor:** {loc_data.get('Vendor', '-')} | **Stok Fisik:** {loc_data.get('Stock Fisik', loc_data.get('Stock_Fisik', 0))} Unit")
            st.markdown(f"### Denah Lokasi: {target_ruang} 🔗")
            
            if target_ruang == 'Ruang 1':
                st.info(f"📌 **Vendor:** {loc_data.get('Vendor', '-')}")
                r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)
                with r1_col1: st.markdown(draw_rack("Rak A", 3, target_rak, target_level), unsafe_allow_html=True)
                with r1_col2: st.markdown(draw_rack("Rak B", 5, target_rak, target_level), unsafe_allow_html=True)
                with r1_col3: st.markdown(draw_rack("Rak C", 5, target_rak, target_level), unsafe_allow_html=True)
                with r1_col4: st.markdown(draw_rack("Rak D", 4, target_rak, target_level), unsafe_allow_html=True)
                    
            elif target_ruang == 'Ruang 2':
                st.info(f"📌 **Vendor:** {loc_data.get('Vendor', '-')}")
                r2_col1, r2_col2 = st.columns(2)
                with r2_col1: st.markdown(draw_rack("R-01", 6, target_rak, target_level), unsafe_allow_html=True)
                with r2_col2: st.markdown(draw_rack("R-02", 6, target_rak, target_level), unsafe_allow_html=True)
            else:
                st.warning("Data lokasi Ruang tidak sesuai format.")

# ----------------- TAB 3: DATA TABEL -----------------
with tab_data:
    st.markdown("### 📋 Data Lengkap Barang Konsinyasi")
    st.dataframe(df, use_container_width=True, height=500, hide_index=True)