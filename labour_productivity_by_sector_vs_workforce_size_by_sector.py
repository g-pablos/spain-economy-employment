import pandas as pd
import matplotlib.pyplot as plt
import unicodedata

# === File paths ===
path_gdp = '[file path]'
path_employment = '[file path]'

# === Load GDP data ===
df_gdp = pd.read_csv(path_gdp, sep='\t', encoding='latin1')
df_gdp = df_gdp[(df_gdp['Agregados macroeconómicos'] == 'Valor añadido bruto') & df_gdp['CNAE Agrupación A10'].notna()]
df_gdp = df_gdp.rename(columns={
    'CNAE Agrupación A10': 'Sector',
    'Periodo': 'Year',
    'Total': 'GDP'
})
# === THIS IS THE FIX ===
df_gdp['Sector'] = df_gdp['Sector'].str.extract(r'^([A-Z]+)', expand=False)
df_gdp['Year'] = pd.to_numeric(df_gdp['Year'], errors='coerce')
df_gdp['GDP'] = df_gdp['GDP'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
df_gdp = df_gdp[df_gdp['Year'] == 2023]
year_used = df_gdp['Year'].unique()[0]

# === Load Employment data ===
df_emp = pd.read_csv(path_employment, sep='\t', encoding='latin1')
df_emp = df_emp[(df_emp['Sexo'] == 'Ambos sexos') & (df_emp['Unidad'] == 'Valor absoluto')]
df_emp['Total'] = df_emp['Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

# === Normalize both mapping keys and column values ===
raw_sector_mapping = {
    'A Agricultura, ganadería, silvicultura y pesca': 'A',
    'B Industrias extractivas': 'BDE',
    'C Industria manufacturera': 'C',
    'D Suministro de energía eléctrica, gas, vapor y aire acondicionado': 'BDE',
    'E Suministro de agua, actividades de saneamiento, gestión de residuos y descontaminación': 'BDE',
    'F Construcción': 'F',
    'G Comercio al por mayor y al por menor; reparación de vehículos de motor y motocicletas': 'GHI',
    'H Transporte y almacenamiento': 'GHI',
    'I Hostelería': 'GHI',
    'J Información y comunicaciones': 'J',
    'K Actividades financieras y de seguros': 'K',
    'L Actividades inmobiliarias': 'L',
    'M Actividades profesionales, científicas y técnicas': 'MN',
    'N Actividades administrativas y servicios auxiliares': 'MN',
    'O Administración Pública y defensa; Seguridad Social obligatoria': 'O',
    'P Educación': 'P',
    'Q Actividades sanitarias y de servicios sociales': 'Q',
    'R Actividades artísticas, recreativas y de entretenimiento': 'RSTU',
    'S Otros servicios': 'RSTU',
    'T Actividades de los hogares como empleadores de personal doméstico; actividades de los hogares como productores de bienes y servicios para uso propio': 'RSTU',
    'U Actividades de organizaciones y organismos extraterritoriales': 'RSTU',
    'Total': 'Total Economy'
}

sector_mapping = {
    unicodedata.normalize('NFKD', k).encode('ascii', 'ignore').decode(): v
    for k, v in raw_sector_mapping.items()
}

# Normalize data column values
column = 'Rama de actividad CNAE 2009'
df_emp[column] = df_emp[column].apply(lambda x: unicodedata.normalize('NFKD', str(x)).encode('ascii', 'ignore').decode().strip())
df_emp['Sector'] = df_emp[column].map(sector_mapping)

# === Aggregate employment by sector ===
df_emp_agg = df_emp.groupby('Sector')['Total'].mean().reset_index()
df_emp_agg = df_emp_agg.rename(columns={'Total': 'Employment'})

# === Aggregate GDP by sector ===
df_gdp_agg = df_gdp.groupby('Sector')['GDP'].sum().reset_index()

# === Merge ===
df_merged = pd.merge(df_gdp_agg, df_emp_agg, on='Sector', how='inner')
df_merged['GDP_per_worker_thousands'] = ((df_merged['GDP'] * 1e6) / (df_merged['Employment'] * 1e3)) / 1e3

# === Translate sectors ===
sector_name_dict = {
    'A': 'Agriculture & Fishing',
    'BDE': 'Extractive, Energy, Water & Waste',
    'C': 'Manufacturing',
    'F': 'Construction',
    'GHI': 'Trade, Transport & Hospitality',
    'J': 'Information & Comms',
    'K': 'Finance & Insurance',
    'L': 'Real Estate',
    'MN': 'Professional & Admin Services',
    'O': 'Public Admin',
    'P': 'Education',
    'Q': 'Health & Social Work',
    'RSTU': 'Arts & Other',
    'Total Economy': 'Total Economy'
}
df_merged['Sector Label'] = df_merged['Sector'].map(sector_name_dict)

# === Color palette ===
sector_color_dict = {
    'Agriculture & Fishing': '#8FBC8F',
    'Extractive, Energy, Water & Waste': '#DAA520',
    'Manufacturing': '#4682B4',
    'Construction': '#D2691E',
    'Trade, Transport & Hospitality': '#FFD700',
    'Information & Comms': '#00CED1',
    'Finance & Insurance': '#000080',
    'Real Estate': '#BC8F8F',
    'Professional & Admin Services': '#9932CC',
    'Public Admin': '#2E8B57',
    'Education': '#6A5ACD',
    'Health & Social Work': '#FF6347',
    'Arts & Other': '#DB7093',
    'Total Economy': '#B0B0B0'
}
colors = df_merged['Sector Label'].map(sector_color_dict)

# === Diagnostics ===
print("=== GDP Aggregate ===")
print(df_gdp_agg.head(10))
print("\n=== Employment Aggregate ===")
print(df_emp_agg.head(10))
print("\n=== Merged Data ===")
print(df_merged[['Sector', 'Employment', 'GDP', 'GDP_per_worker_thousands']])
print("\nMerged row count:", len(df_merged))

# === Plot ===
fig, ax = plt.subplots(figsize=(12, 8))
ax.scatter(df_merged['Employment'], df_merged['GDP_per_worker_thousands'], s=150, color=colors)

for _, row in df_merged.iterrows():
    ax.text(row['Employment'], row['GDP_per_worker_thousands'], row['Sector Label'], fontsize=10, ha='center', va='bottom')

if 'Total Economy' in df_merged['Sector'].values:
    avg_gdp_pw = df_merged[df_merged['Sector'] == 'Total Economy']['GDP_per_worker_thousands'].values[0]
    ax.axhline(avg_gdp_pw, color='gray', linestyle='--', linewidth=1)
    ax.text(df_merged['Employment'].max(), avg_gdp_pw, 'Total Economy Avg', va='bottom', ha='right', fontsize=10, color='gray')

ax.set_xlabel('Employment (Thousands)', fontsize=12)
ax.set_ylabel('GVA per Worker (€ Thousands)', fontsize=12)
ax.set_title(f'Labour Productivity vs. Workforce Size by Sector ({year_used})', fontsize=14)
ax.grid(True, linestyle=':', linewidth=0.5)
from matplotlib.patches import Patch

# Build legend handles
legend_handles = [
    Patch(color=color, label=label)
    for label, color in sector_color_dict.items()
    if label in df_merged['Sector Label'].values
]

# Add the legend to the plot
ax.legend(handles=legend_handles, title='Sectors', loc='upper right', bbox_to_anchor=(1.15, 1))

plt.tight_layout()
plt.show()

