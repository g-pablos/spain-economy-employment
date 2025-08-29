import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib as mpl
mpl.rcParams['font.weight'] = 'normal'

# === CONFIGURATION ===
sexo = "Mujeres"  # Change to "Hombres" or "Ambos sexos" or "Mujeres" to switch dataset

# Map from CSV 'Sexo' values to English words for the title
sex_title_map = {
    'Mujeres': 'Women',
    'Hombres': 'Men',
    'Ambos sexos': 'Both sexes'
}
sexo_en = sex_title_map.get(sexo, sexo)  # fallback to original if unmapped

# === Load and Clean Percentage Data ===
file_path = '[file path]'
df = pd.read_csv(file_path, sep='\t', encoding='latin1')
df['Total'] = df['Total'].replace('..', np.nan).str.replace(',', '.').astype(float)
df['Year'] = df['Periodo'].str[:4]
df = df[(df['Sexo'] == sexo) & (df['Unidad'] == 'Porcentaje')]

# === Load Absolute Employment Data ===
abs_file_path = f"[file path]"
abs_df = pd.read_csv(abs_file_path, sep='\t', encoding='latin1')

abs_df = abs_df[
    (abs_df['Rama de actividad CNAE 2009'] == 'Total') &
    (abs_df['Sexo'] == sexo) &
    (abs_df['Unidad'] == 'Valor absoluto')
].copy()

# Convert 'Total' to float
abs_df['Total'] = (
    abs_df['Total']
    .replace('..', np.nan)
    .str.replace('.', '', regex=False)  # remove thousand separator
    .str.replace(',', '.')              # decimal comma to dot
    .astype(float)
)

# Extract year and average quarterly values
abs_df['Year'] = abs_df['Periodo'].str[:4].astype(int)
annual_abs_total = abs_df.groupby('Year')['Total'].mean()

# === Group and Pivot Percentage Data ===
annual_avg_pct = df.groupby(['Year', 'Rama de actividad CNAE 2009'])['Total'].mean().reset_index()
pivot_pct_df = annual_avg_pct.pivot(index='Year', columns='Rama de actividad CNAE 2009',
                                    values='Total').sort_index().fillna(0)

# Align indices
pivot_pct_df.index = pivot_pct_df.index.astype(int)
annual_abs_total.index = annual_abs_total.index.astype(int)

# === Convert % to Absolute Counts ===
pivot_abs_df = pivot_pct_df.mul(annual_abs_total, axis=0) / 100

# === Translations and Color Map ===
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
    'Household Activities': '#778899',
    'Extraterritorial Organizations': '#556B2F'
}

def translate_sector(sector):
    return sector_translation.get(sector,
           sector.split(' ', 1)[-1][:40] + ('...' if len(sector) > 40 else ''))

# === Split Columns by 3% Threshold ===
threshold = 3
above = pivot_pct_df.columns[(pivot_pct_df >= threshold).any()]
below = pivot_pct_df.columns[~pivot_pct_df.columns.isin(above)]

# === Plotting Function ===
def plot_sector_stackplot_with_labels(abs_df, pct_df, sectors, title,
                                      y_max=None, y_label="Employment (thousands)"):
    avg_abs = abs_df[sectors].mean()
    ordered = avg_abs.sort_values(ascending=False).index

    print("=== Sectors being graphed and their values ===")
    for sector in ordered:
        latest_val = abs_df[sector].iloc[-1]
        print(f"{translate_sector(sector)}: {latest_val:,.0f}")

    abs_df = abs_df[ordered]
    pct_df = pct_df[ordered]

    colors = [sector_color_dict.get(translate_sector(s), '#CCCCCC') for s in ordered]
    years = abs_df.index.astype(int)

    fig, ax = plt.subplots(figsize=(12, 7))
    stacked_data = abs_df.values.T
    ax.stackplot(years, stacked_data,
                 labels=[translate_sector(c) for c in ordered], colors=colors)

    # --- Start and end labels ---
    start_year, end_year = years[0], years[-1]
    start_bases = np.cumsum(abs_df.iloc[0].values) - abs_df.iloc[0].values
    end_bases   = np.cumsum(abs_df.iloc[-1].values) - abs_df.iloc[-1].values

    min_sep = 30  # y-axis units (thousands)
    last_start_y = None
    last_end_y = None

    for i, sector in enumerate(ordered):
        start_abs = abs_df.iloc[0, i]
        end_abs   = abs_df.iloc[-1, i]
        start_pct = pct_df.iloc[0, i]
        end_pct   = pct_df.iloc[-1, i]

        if start_abs > 0:
            y_pos_start = start_bases[i] + start_abs / 2

            if last_start_y is not None and abs(y_pos_start - last_start_y) < min_sep:
                y_pos_start = last_start_y + min_sep
            last_start_y = y_pos_start

            ax.text(start_year - 2.0, y_pos_start,
                    f"{start_pct:.1f}% ({start_abs*1000:,.0f})",
                    va='center', ha='right', fontsize=10,
                    color='darkred', fontweight='normal')

        if end_abs > 0:
            y_pos_end = end_bases[i] + end_abs / 2

            if last_end_y is not None and abs(y_pos_end - last_end_y) < min_sep:
                y_pos_end = last_end_y + min_sep
            last_end_y = y_pos_end

            ax.text(end_year + 1.0, y_pos_end,
                    f"{end_pct:.1f}% ({end_abs*1000:,.0f})",
                    va='center', ha='left', fontsize=10,
                    color='darkred', fontweight='normal')


    # --- Midpoint sector names (separate loop) ---
    mid_idx = len(years) // 2
    mid_year = years[mid_idx]
    cum_mid = np.zeros(len(years))
    smallest_mid_idx = np.argmin(abs_df.iloc[mid_idx].values)
    min_sep = 30  # y-axis units (thousands)
    last_mid_y = None

    for i, sector in enumerate(ordered):
        mid_val = abs_df.iloc[mid_idx, i]
        mid_pct = pct_df.iloc[mid_idx, i]

        if mid_val > 0 or i == smallest_mid_idx:
            y_pos = cum_mid[mid_idx] + max(mid_val, 0.0) / 2 

            # Enforce min separation only for the smallest slice
            if i == smallest_mid_idx and last_mid_y is not None and abs(y_pos - last_mid_y) < min_sep:
                y_pos = last_mid_y + min_sep

            # Dynamic colour if needed
            text_color = 'black'
            if translate_sector(sector) != "Other Services" and mid_pct > 2:
                rgb = mcolors.to_rgb(sector_color_dict.get(translate_sector(sector), '#CCCCCC'))
                brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                if brightness < 0.5:
                    text_color = 'white'

            ax.text(
                mid_year, y_pos,
                translate_sector(sector),
                ha='center', va='center',
                fontsize=9,
                color=text_color,
                fontweight='normal'
            )

            last_mid_y = y_pos

        cum_mid += abs_df.iloc[:, i].values

    # --- Final plot adjustments ---
    ax.set_xlim(years[0], years[-1])
    ax.set_xticks(np.arange(years[0], years[-1] + 1, 4))
    if y_max:
        ax.set_ylim(0, y_max)
    ax.set_title(title, fontsize=14)
    ax.set_ylabel(y_label)
    ax.set_xlabel("Year")
    plt.tight_layout()
    plt.show()

# === Example calls ===
plot_sector_stackplot_with_labels(
    pivot_abs_df, pivot_pct_df, above,
    f"Employment by Sector over Time (>3%) - {sexo_en}",
    y_max=pivot_abs_df[above].sum(axis=1).max()
)

plot_sector_stackplot_with_labels(
    pivot_abs_df, pivot_pct_df, below,
    f"Employment by Sector over Time (<3%) - {sexo_en}",
    y_max=pivot_abs_df[below].sum(axis=1).max()
)
