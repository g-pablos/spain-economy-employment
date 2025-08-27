import pandas as pd
import matplotlib.pyplot as plt

# === Load Data ===
file_path = '/mnt/c/Users/Guille/Desktop/stuff_pc/py_projects/20250606_data_analysis/NEW DATA/empleo_por_sector.csv'
df = pd.read_csv(file_path, sep='\t', encoding='latin1')

# === Filter Sex and Period ===
selected_sex = 'Ambos sexos'  # or 'Hombres', or 'Mujeres', or 'Ambos sexos'
selected_year = '2024'

# Map from CSV values to English words for the title
sex_title_map = {
    'Mujeres': 'Women',
    'Hombres': 'Men',
    'Ambos sexos': 'Both sexes'
}
sex_title = sex_title_map.get(selected_sex, selected_sex)  # fallback to original if missing

df = df[df['Sexo'] == selected_sex]
df = df[df['Periodo'].str.startswith(selected_year)]


# === Clean 'Total' (safe version with .loc)
df.loc[:, 'Total'] = df['Total'].str.replace(',', '.').astype(float)

# === Group and Calculate Raw Sector Averages ===
sector_data = df.groupby('Rama de actividad CNAE 2009')['Total'].mean()
total_economy = sector_data.sum()

# === Calculate each sector’s % of the total ===
sector_percent = 100 * sector_data / total_economy

# === Filter by Threshold ===
threshold = 2.5
included = sector_percent[sector_percent >= threshold].sort_values(ascending=False)
excluded = sector_percent[sector_percent < threshold].sort_values(ascending=False)

# === Translations (Short Labels) ===
sector_translation = {
    'A Agricultura, ganadería, silvicultura y pesca': 'Agriculture & Fishing',
    'B Industrias extractivas': 'Extractive Industries',
    'C Industria manufacturera': 'Manufacturing',
    'D Suministro de energía eléctrica, gas, vapor y aire acondicionado': 'Energy Supply',
    'E Suministro de agua, actividades de saneamiento, gestión de residuos y descontaminación': 'Water & Waste',
    'F Construcción': 'Construction',
    'G Comercio al por mayor y al por menor; reparación de vehículos de motor y motocicletas': 'Trade & Repair',
    'H Transporte y almacenamiento': 'Transport & Storage',
    'I Hostelería': 'Hospitality',
    'J Información y comunicaciones': 'Information & Comms',
    'K Actividades financieras y de seguros': 'Finance & Insurance',
    'L Actividades inmobiliarias': 'Real Estate',
    'M Actividades profesionales, científicas y técnicas': 'Professional & Technical',
    'N Actividades administrativas y servicios auxiliares': 'Administrative Services',
    'O Administración Pública y defensa; Seguridad Social obligatoria': 'Public Administration',
    'P Educación': 'Education',
    'Q Actividades sanitarias y de servicios sociales': 'Health & Social Services',
    'R Actividades artísticas, recreativas y de entretenimiento': 'Arts & Entertainment',
    'S Otros servicios': 'Other Services',
    'T Actividades de los hogares como empleadores de personal doméstico; actividades de los hogares como productores de bienes y servicios para uso propio': 'Household Activities',
    'U Actividades de organizaciones y organismos extraterritoriales': 'Extraterritorial Organizations'
}

# === Updated Color Mapping with Two New Hues ===
sector_color_dict = {
    'Agriculture & Fishing': '#8FBC8F',
    'Extractive Industries': '#DAA520',
    'Manufacturing': '#4682B4',
    'Energy Supply': '#B22222',
    'Water & Waste': '#20B2AA',
    'Construction': '#D2691E',
    'Trade & Repair': '#FFD700',
    'Transport & Storage': '#708090',
    'Hospitality': '#FF8C00',
    'Information & Comms': '#00CED1',
    'Finance & Insurance': '#000080',
    'Real Estate': '#BC8F8F',
    'Professional & Technical': '#9932CC',
    'Administrative Services': '#A0522D',
    'Public Administration': '#2E8B57',
    'Education': '#1E90FF',
    'Health & Social Services': '#FF69B4',
    'Arts & Entertainment': '#DB7093',
    'Other Services': '#696969',
    'Household Activities': '#778899',  # light slate gray
    'Extraterritorial Organizations': '#556B2F'  # dark olive green
}

# === Handle Unknown Sectors for Labels and Colors ===
def translate_sector(sector):
    return sector_translation.get(sector, sector.split(' ', 1)[-1][:40] + ('...' if len(sector) > 40 else ''))

included_labels = [translate_sector(s) for s in included.index]
excluded_labels = [(translate_sector(s), pct) for s, pct in excluded.items()]
colors = [sector_color_dict.get(translate_sector(s), '#CCCCCC') for s in included.index]

# === Use raw values to define slice sizes ===
included_raw = sector_data[included.index]

# === Custom % label inside the chart, using total economy ===
def format_pct(value):
    absolute = value * included_raw.sum() / 100
    true_pct = 100 * absolute / total_economy
    return f"{true_pct:.1f}%"

# === Plot ===
fig, ax = plt.subplots(figsize=(9, 9))
ax.pie(included_raw, labels=included_labels, colors=colors,
       autopct=format_pct, startangle=90)
ax.set_title(
    f"Spain – Employment by Sector : {sex_title} (Annual Average, {selected_year})",
    fontsize=14
)

# === Excluded Sector Text Box ===
excluded_text = "Excluded Sectors (<2.5%):\n" + "\n".join(
    f"- {label}: {pct:.2f}%" for label, pct in excluded_labels
)
props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9)
fig.text(0.01, 0.01, excluded_text, fontsize=9, va='bottom', bbox=props)

plt.show()
