import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# === File path ===
file_path = '/mnt/c/Users/Guille/Desktop/stuff_pc/py_projects/20250606_data_analysis/NEW DATA/VAB_sector.csv'

# === Load and clean data ===
df = pd.read_csv(file_path, sep='\t', encoding='latin1')
df = df[df['CNAE Agrupación A10'].notna() & (df['CNAE Agrupación A10'] != '')]

df = df.rename(columns={
    'CNAE Agrupación A10': 'Sector',
    'Periodo': 'Year',
    'Total': 'VAB'
})
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df['VAB'] = (
    df['VAB'].astype(str)
    .str.replace('.', '', regex=False)  # remove thousand sep
    .str.replace(',', '.', regex=False) # decimal comma to dot
    .astype(float)
)

# === Pivot absolute values ===
pivot_abs = df.pivot(index='Year', columns='Sector', values='VAB').sort_index().fillna(0)

# === Calculate shares (%) ===
total_vab = pivot_abs.sum(axis=1)
pivot_pct = pivot_abs.divide(total_vab, axis=0) * 100

# === Sector translations ===
sector_name_dict = {
    'A Agricultura, ganadería, silvicultura y pesca': 'Agriculture & Fishing',
    'BDE Industrias extractivas; suministro de energía eléctrica, gas, vapor y aire acondicionado; suministro de agua, actividades de saneamiento, gestión de residuos y descontaminación': 'Extractive, Energy, Water & Waste',
    'C Industria manufacturera': 'Manufacturing',
    'F Construcción': 'Construction',
    'GHI Comercio al por mayor y al por menor; reparación de vehículos de motor y motocicletas; transporte y almacenamiento; hostelería': 'Trade, Transport & Hospitality',
    'J Información y comunicaciones': 'Information & Comms',
    'K Actividades financieras y de seguros': 'Finance & Insurance',
    'L Actividades inmobiliarias': 'Real Estate',
    'MN Actividades profesionales, científicas y técnicas; actividades administrativas y servicios auxiliares': 'Professional & Admin Services',
    'OPQ Administración pública y defensa; seguridad social obligatoria; educación; actividades sanitarias y de servicios sociales': 'Public Services (Admin, Education, Health)',
    'RSTU Actividades artísticas, recreativas y de entretenimiento; otras actividades de servicios; actividades de los hogares como empleadores de personal doméstico; actividades de los hogares como productores de bienes y servicios para uso propio': 'Arts, Other & Household Services'
}
pivot_abs = pivot_abs.rename(columns=sector_name_dict)
pivot_pct = pivot_pct.rename(columns=sector_name_dict)

# === Color scheme ===
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
    'Public Services (Admin, Education, Health)': '#2E8B57',
    'Arts, Other & Household Services': '#DB7093'
}
default_color = '#B0B0B0'

# === Split sectors by threshold ===
max_share = pivot_pct.max()
major_sectors = max_share[max_share >= 3].index.tolist()
minor_sectors = max_share[max_share < 3].index.tolist()

# === Plotting function ===
def plot_stack(abs_df, pct_df, sectors, title, filename):
    abs_df = abs_df[sectors].copy()
    pct_df = pct_df[sectors].copy()

    # Order by average absolute size
    ordered = abs_df.mean().sort_values(ascending=False).index
    abs_df = abs_df[ordered]
    pct_df = pct_df[ordered]

    fig, ax = plt.subplots(figsize=(12, 14))
    colors = [sector_color_dict.get(col, default_color) for col in abs_df.columns]
    ax.stackplot(abs_df.index, abs_df.T, labels=abs_df.columns, colors=colors)
    start_year, end_year = abs_df.index[0], abs_df.index[-1]

    # Base heights at start and end years
    start_bases = np.cumsum(abs_df.iloc[0].values) - abs_df.iloc[0].values
    end_bases   = np.cumsum(abs_df.iloc[-1].values) - abs_df.iloc[-1].values

    # === Labels at start and end ===
    for i, sector in enumerate(abs_df.columns):
        start_abs = abs_df.iloc[0, i]
        end_abs   = abs_df.iloc[-1, i]
        start_pct = pct_df.iloc[0, i]
        end_pct   = pct_df.iloc[-1, i]

        # Determine background brightness for this sector
        rgb = mcolors.to_rgb(colors[i])
        brightness = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
        text_color = 'black'

        if start_abs > 0:
            y_pos_start = start_bases[i] + start_abs / 2
            ax.text(start_year - 0.4, y_pos_start,
                    f"{start_pct:.1f}% ({start_abs:,.0f} M€)",
                    va='center', ha='right', fontsize=10, color=text_color)

        if end_abs > 0:
            y_pos_end = end_bases[i] + end_abs / 2
            ax.text(end_year + 0.4, y_pos_end,
                    f"{end_pct:.1f}% ({end_abs:,.0f} M€)",
                    va='center', ha='left', fontsize=10, color=text_color)

            
    # === Midpoint sector names with color switching ===
    mid_idx = len(abs_df) // 2
    mid_year = abs_df.index[mid_idx]
    cum_mid = np.zeros(len(abs_df))

    for i, sector in enumerate(abs_df.columns):
        mid_val = abs_df.iloc[mid_idx, i]
        if mid_val > 0:
            y_pos = cum_mid[mid_idx] + mid_val / 2

            rgb = mcolors.to_rgb(sector_color_dict.get(sector, default_color))
            brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
            text_color = 'white' if brightness < 0.5 else 'black'

            ax.text(mid_year, y_pos, sector,
                    ha='center', va='center', fontsize=9, color=text_color)

        cum_mid += abs_df.iloc[:, i].values

    # === Axes, limits ===
    ax.set_xlim(abs_df.index[0], abs_df.index[-1])
    ax.set_xticks(range(abs_df.index.min(), abs_df.index.max() + 1, 4))
    ax.set_ylim(0, abs_df.sum(axis=1).max() * 1)  # generous headroom
    ax.set_title(title, fontsize=14)
    ax.set_ylabel("Gross Value Added (Millions of €)", fontsize=14)
    ax.set_xlabel("Year", fontsize=14)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    plt.tight_layout()
    plt.savefig(filename)
    plt.show()


# === Plot charts ===
if major_sectors:
    plot_stack(pivot_abs, pivot_pct, major_sectors, 'GVA by Major Sectors in Spain over Time', 'gva_major.png')

if minor_sectors:
    plot_stack(pivot_abs, pivot_pct, minor_sectors, 'GVA by Minor Sectors in Spain (<3%)', 'gva_minor.png')
else:
    print("No minor sectors found under the 3% threshold.")

