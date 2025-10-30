import argparse
from datetime import datetime
from itertools import cycle
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter
from matplotlib import font_manager
import json
from upsetplot import UpSet, from_memberships
import matplotlib as mpl
from pathlib import Path

base_font_size = 9
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": base_font_size,     
    "axes.titlesize": base_font_size + 1,
    "axes.labelsize": base_font_size,
    "xtick.labelsize": base_font_size - 1,
    "ytick.labelsize": base_font_size - 1,
    "legend.fontsize": base_font_size - 1,   
    "mathtext.fontset": "cm",                
    "mathtext.rm": "serif",                  
})



__author__ = "Feyi Adesanya"
__copyright__ = "Copyright 2024, Sustainable Systems and Methods Lab (SSM)"
__license__ = "GPL-3.0"


warnings.filterwarnings("ignore", category=FutureWarning, module="upsetplot.plotting")
warnings.filterwarnings("ignore", category=FutureWarning, module="upsetplot.data")

BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)
data_path = BASE_DIR / "data" / "Data extraction sheet.xlsx"
results_path = BASE_DIR / "output" / "figures"
results_path.mkdir(parents=True, exist_ok=True)
color_path = BASE_DIR / "data" / "colour_coding.json"

with open(color_path, "r") as f:
    colour_coding = json.load(f)

class Analysis:
    observation_map = {
        1: "intentOfSoSDT", # RQ1
        2: "sosDimensions", # RQ4
        3: "trlVsContributionType", #RQ6
        4: "dtServices", #RQ3,
        5: "plot_timeline_by_category",
    }
    
    def __init__(self):
        if not os.path.exists(results_path):
            os.makedirs(results_path)
        self.df = self.load_data()

    def load_data(self):
        df = pd.read_excel(data_path, sheet_name="Sheet1")
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

        df["Publication year"] = pd.to_numeric(df["Publication year"], errors="coerce")
        df["Quality score"] = pd.to_numeric(df["Quality score"], errors="coerce")

        # Make sure we don't grab data from anything where the quality score is blank or has a 0
        columns_to_check = [
            "Q1: SoS is clear",
            "Q2: DT is clear",
            "Q3: Tangible contributions",
            "Q4: Reporting clarity"
        ]
        df[columns_to_check] = df[columns_to_check].apply(pd.to_numeric, errors="coerce")
        df = df.dropna(subset=columns_to_check)
        df = df[~(df[columns_to_check] == 0).any(axis=1)]
        return df
  
        
# =======================
# RQ 1 
# =======================  
        
    def intentOfSoSDT(self):
        df = self.df.copy()
        services_column = "Domain (Aggregated)"
        intent_col = "Intent"

        intent_domain_counts = df.groupby([intent_col, services_column], observed=True).size().reset_index(name="Count")
        pivot_df = intent_domain_counts.pivot(index=services_column, columns=intent_col, values="Count").fillna(0)

        dt_col, sos_col = pivot_df.columns[:2].tolist()
        pivot_df["total"] = pivot_df[dt_col] + pivot_df[sos_col]
        pivot_df = pivot_df.sort_values(by="total", ascending=True)

        y_categories = pivot_df.index.tolist()
        y_pos = np.arange(len(y_categories))

        fig, ax = plt.subplots(figsize=(10, 8))

        # Bar values
        dt_values = -pivot_df[dt_col].values  # Negative for mirrored effect
        sos_values = pivot_df[sos_col].values

        ax.barh(y_pos, dt_values, color=colour_coding["red"], label=dt_col)
        ax.barh(y_pos, sos_values, color=colour_coding["blue"], label=sos_col)

        for i, (dt, sos) in enumerate(zip(dt_values, sos_values)):
            if dt != 0:
                ax.text(dt - 0.5, i, f"{-int(dt)}", va='center', ha='right', fontsize=24)
            if sos != 0:
                ax.text(sos + 0.5, i, f"{int(sos)}", va='center', ha='left', fontsize=24)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_categories, fontsize=24)
        ax.set_xlabel("# of Studies", fontsize=24)
        ax.set_xlim(-30, 10)
        ax.set_xticks(range(-30, 15, 5))
        ax.set_xticklabels([str(abs(x)) for x in range(-30, 15, 5)], fontsize=24)
        
        ax.tick_params(axis='y', which='both', length=0, labelsize=24) 
        # ax.grid(True, axis='x', linestyle='--', linewidth=0.5)
        # ax.axvline(0, color='black', linewidth=1)
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.set_title("Intent of SoTS Studies by Domain", fontsize=28, pad=15, x=0.25)

        plt.tight_layout()

        # Save
        self.savefig("intentOfSoSDT", upper_folder="RQ1")
        plt.close()
        


# =======================
# RQ 3 
# =======================
    def dtServices(self):
        df = self.df.copy()
        services_column = "Services (Cleaned)"

        df_services = df[[services_column]]

        combo_counts = {}
        
        for entry in df_services[services_column]:
            items = entry.split(",")
            cleaned = {str(i).strip() for i in items if i.strip()}
            sorted_combo = tuple(sorted(cleaned))
           
            if sorted_combo in combo_counts:
                combo_counts[sorted_combo] += 1
            else:
                combo_counts[sorted_combo] = 1

        upset_data = from_memberships(
        memberships=list(combo_counts.keys()),
        data=list(combo_counts.values())
        )

        plt.figure(figsize=(12, 9))
        plt.rcParams.update({
            "font.size": 23,
            "axes.titlesize": 21,
            "axes.labelsize": 22,
            "xtick.labelsize": 22,
            "ytick.labelsize": 22,
            "legend.fontsize": 20
        })
        UpSet(upset_data, show_counts=True, sort_by='cardinality').plot()
        plt.suptitle("Combinations of DT Services Across Studies")
        
        for text in plt.gcf().findobj(match=plt.Text):
            if text.get_text().isdigit():
                text.set_fontsize(23)


        self.savefig("dtServices", upper_folder="RQ3")
        plt.close()
        
# =======================
# RQ 4 
# =======================   
    def sosDimensions(self):
        df = self.df.copy()
        sos_dimensions = [col for col in df.columns if isinstance(col, str) and col.startswith("SoS:")]
        
        likert_options = ["No", "Partial", "Yes"]
        counts = {col: df[col].value_counts().reindex(likert_options, fill_value=0) for col in sos_dimensions}
        counts_df = pd.DataFrame(counts).T
        
        total_responses = df.shape[0]
        percentages = counts_df.div(total_responses) * 100
        percentages.index = [col.replace("SoS: ", "") for col in percentages.index]
        
        rename_map = {
            "Dynamic Reconfiguration": "Reconfiguration",
            "Autonomy of Constituents": "Autonomy",
            "Emergence of Behaviour": "Emergence"
        }
        percentages.rename(index=rename_map, inplace=True)
        percentages = percentages.sort_values(by="No", ascending=False)
        
        no_vals = percentages["No"]
        partial_vals = percentages["Partial"]
        yes_vals = percentages["Yes"]

        # positions of bars
        left_no      = -no_vals - (partial_vals / 2.0)
        left_partial = -partial_vals / 2.0
        left_yes     =  (partial_vals / 2.0)

        # Figure/axes
        bar_height = 0.8 # controls bar height
        # fig, ax = plt.subplots(figsize=(30, len(percentages)*1)) # controls space between bars
        fig, ax = plt.subplots(figsize=(12, 6*(0.8)))
        plt.subplots_adjust(left=0.25, right=0.95)
        y_pos = np.arange(len(percentages))
        
        ax.barh(y_pos, no_vals,      left=left_no,      height=bar_height, color=colour_coding["red"],  label="No")
        ax.barh(y_pos, partial_vals, left=left_partial, height=bar_height, color=colour_coding["grey"], label="Partial")
        ax.barh(y_pos, yes_vals,     left=left_yes,     height=bar_height, color=colour_coding["blue"], label="Yes")

        # Styling
        ax.set_facecolor("#ffffff")
        ax.set_yticks(y_pos)
        font_prop = font_manager.FontProperties(size=12)
        ax.set_yticklabels(percentages.index, fontproperties=font_prop)
        ax.tick_params(axis='y', pad=15)
        ax.set_xlabel("Percentage", fontsize=17)
        ax.set_title("SoS Dimensions", fontsize=19)
        ax.tick_params(axis='both', labelsize=17)
        ax.axvline(0, color='black', linewidth=0.5, linestyle=':')
        ax.set_xlim(-100, 100)
        ax.xaxis.set_major_locator(MultipleLocator(20))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{abs(x):.0f}%"))

        # Labels
        min_width = 5  # threshold for showing internal labels
        font_weight = 500
        font_size = 13
        for i in range(len(percentages.index)):
            # "No"
            if no_vals.iloc[i] > 0:
                xpos = left_no.iloc[i] + no_vals.iloc[i] / 2.0
                if no_vals.iloc[i] >= min_width:
                    ax.text(xpos, i, f"{no_vals.iloc[i]:.2f}%", va='center', ha='center',
                            color='black', fontsize=font_size, weight=font_weight)

            # "Partial"
            if partial_vals.iloc[i] >= min_width:
                ax.text(0, i, f"{partial_vals.iloc[i]:.2f}%", va='center', ha='center',
                        color='black', fontsize=font_size, weight=font_weight)
            # else: nudged overlapping "partial" label slightly downwards
            #     ax.text(0, y_pos[i] - 0.3,
            #             f"{partial_vals.iloc[i]:.2f}%", va='center', ha='center',
            #             color='black', fontsize=font_size, weight=font_weight)

            # "Yes"
            if yes_vals.iloc[i] > 0:
                xpos = left_yes.iloc[i] + yes_vals.iloc[i] / 2.0
                if yes_vals.iloc[i] >= min_width:
                    ax.text(xpos, i, f"{yes_vals.iloc[i]:.2f}%", va='center', ha='center',
                            color='black', fontsize=font_size, weight=font_weight)

        plt.tight_layout()
        self.savefig("sosDimensions", upper_folder="RQ4")

            
       
       
# =======================
# RQ 6 
# =======================
    def trlVsContributionType(self):
        df = self.df.copy()
        trl_order = [
            "Initial",
            "Proof-Of-Concept",
            "Demo Prototype",
            "Deployed Prototype",
            "Operational"
        ]
        df["TRL"] = df["TRL"].str.title()
        df["TRL"] = pd.Categorical(df["TRL"], categories=trl_order, ordered=True)

        df_unique = df.drop_duplicates(subset=["Citation Code", "TRL", "Contribution type"])
        grouped = df_unique.groupby(["TRL", "Contribution type"], observed=True)["Citation Code"].nunique().reset_index(name="Count")

        pivot_df = grouped.pivot(index="TRL", columns="Contribution type", values="Count").fillna(0).astype(int)
        pivot_df = pivot_df.reindex(trl_order)

        contribution_types = ["Conceptual", "Technical", "Case Study"]
        colors = {
            "Conceptual": colour_coding["red"],
            "Technical": colour_coding["blue"],
            "Case Study": colour_coding["grey"],
        }

        x = np.arange(len(pivot_df))
        width = 0.27

        fig, ax = plt.subplots(figsize=(12, 6))
        total_studies = df["Citation Code"].nunique()

        for i, contrib in enumerate(contribution_types):
            values = pivot_df[contrib] if contrib in pivot_df else [0]*len(pivot_df)
            bars = ax.bar(x + (i - 1) * width, values, width, label=contrib, color=colors[contrib])

            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    label = f"{int(height)}"

                    offset = 5
                    ax.annotate(
                                label,
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, offset),
                                textcoords="offset points",
                                ha='center', va='bottom',
                                fontsize=18)

        ax.set_ylabel("Number of Papers", fontsize=18)
        ax.set_xlabel("Contribution Type", fontsize=18)
        ax.tick_params(axis='y', labelsize=18)
        ax.set_xticks(x)
        
        trl_totals = df_unique.groupby("TRL", observed=True)["Citation Code"].nunique().reindex(trl_order).fillna(0).astype(int)
        trl_percents = (trl_totals / total_studies * 100)

        x_labels = [
            f"{trl}\n{count} ({percent:.2f}%)"
            for trl, count, percent in zip(trl_order, trl_totals, trl_percents)
        ]
        ax.set_xticklabels(x_labels, rotation=15, fontsize=17)
        ax.set_title("Contribution Types by TRL Level", fontsize=20, pad=10)
        ax.set_ylim(0, pivot_df.values.max() + 10) 
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        plt.tight_layout()
        self.savefig("trlVsContributionType", upper_folder="rq6")


# =======================
# RQ Timeline 
# =======================   
    def plot_timeline_by_category(
        self,
        category_col = "SoTS Classification",
        year_col = "Publication year",
        title = None,
        min_year = None,
        max_year = 2023,
        ):

        df = self.df.dropna(subset=[year_col, category_col]).copy()
        df[year_col] = pd.to_numeric(df[year_col], errors="coerce").dropna().astype(int)

        counts = (
            df.groupby([year_col, category_col])
            .size()
            .unstack(fill_value=0)
            .sort_index()
        )

        # Year bounds
        y_min = counts.index.min() if min_year is None else int(min_year)
        y_max = counts.index.max() if max_year is None else int(max_year)
        years = pd.Index(range(y_min, y_max + 1), name=year_col)
        counts = counts.reindex(index=years, fill_value=0)
        
        ordered_cols = ["Directed SoTS", "Acknowledged SoTS", "Collaborative SoTS", "Virtual SoTS"]
        counts = counts.reindex(columns=ordered_cols, fill_value=0)


        # Colours
        palette = [
            colour_coding["red"],  
            colour_coding["blue"], 
            colour_coding["green"],
            colour_coding["orange"],
        ]
        
        # Plot
        fig, ax = plt.subplots(figsize=(3.45, 2.3))
        counts.plot(ax=ax, color=palette) 

        font_size_default = 10
        ax.set_xlabel("Publication Year", fontsize=font_size_default)
        ax.set_ylabel("Frequency", fontsize=font_size_default)
        ax.set_title(title or f"Studies per Year by SoTS Type", pad=5, fontsize=font_size_default)
        ax.tick_params(axis='both', labelsize=font_size_default-1)
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.grid(True, which="both", axis="y", linewidth=0.5, alpha=0.4)
        ax.grid(True, which="major", axis="x", linewidth=0.3, alpha=0.2)

        ax.legend(title=None, fontsize=font_size_default-2)
        # fig.tight_layout()

        self.savefig("timeline_by_sots_category")

               
# =======================
# Saving and Running Script 
# =======================
    def savefig(self, func_name, file_type="pdf", upper_folder="overall"):
        filename = func_name.replace(" ", "_").replace("-", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
        folder_path = os.path.join(results_path, upper_folder)

        # Ensure the folder exists
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, f"{filename}.{file_type}")

        # Remove any existing file with the same name
        for existing_file in os.listdir(folder_path):
            if existing_file.startswith(filename):
                os.remove(os.path.join(folder_path, existing_file))

        plt.savefig(file_path, dpi=600, bbox_inches="tight")  
        plt.close()
        
    def saveLatex(self, func_name, html_content):
        output_folder = results_path
        os.makedirs(output_folder, exist_ok=True)

        filename = func_name.replace(" ", "_").replace("-", "_") + ".tex"
        file_path = os.path.join(output_folder, filename)

        # Remove any existing file with the same name
        for existing_file in os.listdir(output_folder):
            if existing_file.startswith(filename):
                os.remove(os.path.join(output_folder, existing_file))

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)



    def run_all(self):
        print("Running all observations...\n")
        for obs_id, func_name in self.observation_map.items():
            print(f"Running observation {obs_id}: {func_name} ...")
            plt.clf()
            getattr(self, func_name)()

    def run_one(self, observation_id):
        if observation_id in self.observation_map:
            func_name = self.observation_map[observation_id]
            print(f"Running observation {observation_id}: {func_name} ...")
            plt.clf()
            getattr(self, func_name)()
        else:
            print(f"Error: Observation {observation_id} is not valid. Choose from {list(self.observation_map.keys())}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--observation", help="Observation Mapping ID", type=int, nargs="?")
    args = parser.parse_args()

    analysis = Analysis()

    if args.observation:
        analysis.run_one(args.observation)
    else:
        analysis.run_all()
