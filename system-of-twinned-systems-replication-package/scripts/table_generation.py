import argparse
from collections import defaultdict
import os
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib import transforms as mtransforms
from pathlib import Path

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 10,     
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,   
    "mathtext.fontset": "cm",                
    "mathtext.rm": "serif",                  
})


__author__ = "Feyi Adesanya"
__copyright__ = "Copyright 2024, Sustainable Systems and Methods Lab (SSM)"
__license__ = "GPL-3.0"

# data_path = "../data/Data extraction sheet.xlsx"
# results_path = "./output/tables"
# bar_charts_output = ""

BASE_DIR = Path(__file__).resolve().parent.parent
# Input data file
data_path = BASE_DIR / "data" / "Data extraction sheet.xlsx"

# Output tables directory
results_path = BASE_DIR / "output" / "tables"
results_path.mkdir(parents=True, exist_ok=True)

# Bar charts subdirectory inside output/tables
BAR_CHART_DIR = results_path / "bar_charts"
BAR_CHART_DIR.mkdir(parents=True, exist_ok=True)

class Analysis:
    observation_map = {
        1: "motivationsTable", #RQ1
        2: "intentsTable", #RQ1
        3: "domainsTable", #RQ1
        6: "constituentUnitsTable", #RQ2
        7: "autonomyTable", #RQ3
        9: "emergenceTable", #RQ4
        10: "sots_classificationTable", #RQ2
        11: "trlTable", #RQ5
        13: "standardsTable", #RQ5
        14: "contributionTypeTable", #RQ5
        15: "dtServicesTable", #RQ3
        16: "programmingLangaugesTables", #RQ2
        17: "generate_frameworks_table", #RQ3
        18: "dtOrSoSRelated", # RQ5
        20: "securityTable", 
        21: "reliabilityTable",
        23: "generate_structured_eval_table",
        24: "generate_formalisms_methods_table",
        25: "generate_challenges_table",
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
        # Sort by the citation order before creating tables, will match with latex citations
        df = df.sort_values(by=["Citation Order", "Citation Code"], kind="mergesort").reset_index(drop=True)
        df["Paper ID"] = [f"T{i+1:02d}" for i in range(len(df))]
        return df
    

# =======================
# Bar Chart Generator
# =======================    

    def custom_title(self, s, overrides={"dt": "DT", "dt)":"DT)", "(dt":"(DT", "trl": "TRL", "sos": "SoS", "(sos":"(SoS",  "sos)":"SoS)", "sots": "SoTS"}):
        words = s.split()
        out = []
        for w in words:
            lw = w.lower()
            if lw in overrides:
                out.append(overrides[lw])
            else:
                out.append(w.capitalize())
        return " ".join(out)

    def save_hbar_from_table(
        self, summary_df, category_col, count_col="Paper_Count",
        ylabel="", outfile="bar.pdf", bar_color="#89CFF0",
        *, 
        custom_order=None,                 
        total_studies = 80,
        bar_height=0.2,
        pad_between_bars = 0.28,
        top_pad=0, bottom_pad=0,
        fig_width=3, label_fontsize=9.0
    ):
        if summary_df.empty:
            os.makedirs(os.path.dirname(outfile), exist_ok=True)
            return

        df = summary_df[[category_col, count_col]].dropna(subset=[category_col]).copy()
        df[count_col] = pd.to_numeric(df[count_col], errors="coerce").fillna(0).astype(int)


        if custom_order:
            ordered = list(custom_order)[::-1]
            df[category_col] = pd.Categorical(df[category_col].astype(str),
                                          categories=ordered,
                                          ordered=True)
            df = df.sort_values(by=[category_col], kind="mergesort").reset_index(drop=True)
        else:
            # Highest amount at the top moving downwards
            df = df.sort_values(by=count_col, ascending=True, kind="mergesort").reset_index(drop=True)


        other_mask = df[category_col].astype(str).str.strip().str.casefold().eq("other")
        if other_mask.any():
            df = pd.concat([df.loc[other_mask], df.loc[~other_mask]], ignore_index=True)


        total = total_studies
        widths = df[count_col] / total
        xlim = 1.0

        labels = [
            f"{str(cat)} — {cnt} ({cnt/total*100:.2f}%)"
            for cat, cnt in zip(df[category_col], df[count_col])
        ]

        n = len(df)
        content_h = n * bar_height + max(0, n - 1) * 0.025
        fig_h = max(1.1, top_pad + content_h + bottom_pad)

        fig, ax = plt.subplots(figsize=(fig_width, fig_h), constrained_layout=False)
        y = np.arange(n) * pad_between_bars

        ax.barh(y, widths, height=bar_height, color=bar_color, edgecolor="none")

        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.tick_params(axis="y", direction="out", pad=-8, length=0)
        for t in ax.get_yticklabels():
            t.set_ha("left")
            t.set_fontsize(label_fontsize)

        ax.set_xlim(0, xlim)
        ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
        if n:
            ax.set_ylim(y[0] - bar_height/2, y[-1] + bar_height/2)

        ax.set_title(self.custom_title(ylabel), fontsize=10, loc="center", pad=5)
        for s in ("top", "right", "bottom", "left"):
            ax.spines[s].set_visible(False)


        fig.tight_layout()
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        max_tick_w_in = max((t.get_window_extent(renderer=renderer).width for t in ax.get_yticklabels()), default=0) / fig.dpi


        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        fig.savefig(outfile, dpi=300, bbox_inches="tight")
        plt.close(fig)


    def save_hierarchical_hbar(
        self,
        rows,
        ylabel,
        outfile,
        *,
        total_studies=80,
        fig_width=3.6,
        bar_height_top=0.22,
        bar_height_sub=0.18,
        gap_between_rows=0.28,
        sub_alpha=0.55, # colouring for sub-level bars
        bar_color="#89CFF0",
        label_fontsize=9.0,
        title_x=0.02,    
        indent_sub=0.06,   
        title_pad=0.01       
    ):
        
        n = len(rows)
        content_h = n * bar_height_sub + 0.02 * max(0, n - 1)
        fig_h = max(1.0, content_h + 0.1)

        fig, ax = plt.subplots(figsize=(fig_width, fig_h))


        # row settings
        y = np.arange(n) * gap_between_rows
        total = float(total_studies) if total_studies else float(max(1, sum(r["count"] for r in rows)))
        widths = [r["count"]/total for r in rows]
        heights = [bar_height_top if r["level"] == "top" else bar_height_sub for r in rows]
        alphas  = [1.0 if r["level"] == "top" else sub_alpha for r in rows]

        # Bars
        for yy, w, h, a in zip(y, widths, heights, alphas):
            ax.barh(yy, w, height=h, color=bar_color, edgecolor="none", alpha=a)

        ax.set_yticks(y)
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)

        ax.margins(x=0, y=0)
        top_edge    = y[0] - heights[0]
        bottom_edge = y[-1] + heights[-1]
        ax.set_ylim(top_edge, bottom_edge)

        # Fixed x positions in axes fraction for labels
        txt_trans = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
        x_top = title_x
        x_sub = title_x + indent_sub

        # labels
        for yy, w, r in zip(y, widths, rows):
            pct = (r["count"]/total*100 if total else 0.0)
            label = f"{r['label']} — {r['count']} ({pct:.2f}%)"
            x_here = x_top if r["level"] == "top" else x_sub
            ax.text(
                x_here, yy, label.replace("\\&", "&"),
                transform=txt_trans, va="center", ha="left",
                fontsize=label_fontsize, color="black", clip_on=False
            )

        ax.set_title(self.custom_title(ylabel), fontsize=10, pad=title_pad)

        ax.set_xlim(0, 1.0)
        ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
        ax.invert_yaxis()
        for i, r in enumerate(rows):
            if r["level"] == "top" and i > 0:
                ax.hlines(y[i] - gap_between_rows/2, 0, 1.0, lw=0.4, color="0.85")
        for s in ("top", "right", "bottom", "left"):
            ax.spines[s].set_visible(False)

        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        fig.savefig(outfile, dpi=600, bbox_inches="tight")
        plt.close(fig)



# =======================
# Table Generator
# =======================    
    def generate_latex_table(self, summary_df, caption, label, tabular_size, first_column_name):
            # tabular_size_formatted = f"@{{}} {tabular_size} @{{}}"
            tabular_size_formatted = r"@{}p{4cm}l p{8.5cm}@{}" # Fixed size
            latex_table = f"""\\begin{{table*}}[]
            \\centering
            \\footnotesize
            \\caption{{{caption}}}
            \\label{{tab:{label}}}
            \\begin{{tabular}}{{{tabular_size_formatted}}}
            \\toprule
            \\multicolumn{{1}}{{c}}{{\\textbf{{{first_column_name}}}}} & 
            \\multicolumn{{1}}{{c}}{{\\textbf{{Frequency}}}} & 
            \\multicolumn{{1}}{{c}}{{\\textbf{{Studies}}}} \\\\ 
            \\midrule
            """
            for _, row in summary_df.iterrows():
                category = row.iloc[0]
                paper_count = row["Paper_Count"]
                citations = row["Citations"]
                latex_table += f"{category} & \\maindatabar{{{paper_count}}} & {citations} \\\\\n"

            latex_table += """\\bottomrule
            \\end{tabular}
            \\end{table*}"""
            return latex_table
        
    # For simple tables with one item per row  
    def generate_summary_table(self, column, caption, label, tabular_size, first_column_name, save_location, custom_order=None):
        df = self.df.copy()
        summary_df = df.groupby(column).agg(
            Paper_Count=("Paper ID", "count"),
            # Citations=("Citation Code", lambda x: ", ".join(f"\\cite{{{cite}}}" for cite in x.dropna().unique()) if x.dropna().any() else "\\cite{placeholder}")
            Citations=("Citation Code",
           lambda x: f"\\cite{{{','.join(x.dropna().unique())}}}"
                     if x.dropna().any()
                     else "\\cite{placeholder}")
        ).reset_index()
        
        if custom_order:
            summary_df[column] = pd.Categorical(summary_df[column], categories=custom_order, ordered=True)
            summary_df = summary_df.sort_values(by=column)

        else:
            summary_df = summary_df.sort_values(by="Paper_Count", ascending=False)

        latex_table = self.generate_latex_table(summary_df, caption, label, tabular_size, first_column_name)
        self.saveLatex(f"{save_location}", latex_table)

        chart_name = save_location.replace(" ", "_").replace("-", "_") + ".pdf"
        chart_outfile = os.path.join(BAR_CHART_DIR, chart_name)

        self.save_hbar_from_table(
            summary_df=summary_df,
            category_col=column,
            count_col="Paper_Count",
            ylabel=caption,
            outfile=chart_outfile,
            custom_order=custom_order
        )
                
    # For tables with multiple items per row seperated by a delimiter
    def generate_delimiter_table(
        self, column, caption, label, tabular_size, first_column_name, save_location,
        delimiter=",", custom_order=None
    ):
        df = self.df.copy()
        citation_column = "Citation Code"
        rows = []

        for _, row in df.iterrows():
            main_values = row[column]
            if pd.isna(main_values):
                continue
            main_values_list = [s.strip() for s in str(main_values).split(delimiter) if s.strip()]
            for val in main_values_list:
                rows.append({
                    "Value": val,
                    "Paper ID": row["Paper ID"],
                    "Citation Code": row[citation_column] if citation_column in row else None
                })

        exploded_df = pd.DataFrame(rows)

        summary_df = exploded_df.groupby("Value").agg(
            Paper_Count=("Paper ID", "nunique"),
            # Citations=(citation_column, lambda x: ", ".join([f"\\cite{{{cite}}}"
            #                                                 for cite in x.dropna().unique()])
            #                             if not x.dropna().empty else "\\cite{placeholder}")
            Citations=(citation_column, lambda x: f"\\cite{{{','.join(x.dropna().unique())}}}"
                                        if not x.dropna().empty else "\\cite{placeholder}")
        ).reset_index()

        # Apply optional custom order, else sort by count desc
        if custom_order:
            summary_df["Value"] = pd.Categorical(summary_df["Value"], categories=custom_order, ordered=True)
            summary_df = summary_df.sort_values(by="Value", kind="mergesort").reset_index(drop=True)
        else:
            summary_df = summary_df.sort_values(by="Paper_Count", ascending=False, kind="mergesort")

        # LaTeX
        latex_table = self.generate_latex_table(summary_df, caption, label, tabular_size, first_column_name)
        self.saveLatex(save_location, latex_table)

        chart_name = save_location.replace(" ", "_").replace("-", "_") + ".pdf"
        chart_outfile = os.path.join(BAR_CHART_DIR, chart_name)
        self.save_hbar_from_table(
            summary_df=summary_df,
            category_col="Value",
            count_col="Paper_Count",
            ylabel=caption,
            outfile=chart_outfile,
            custom_order=custom_order,  
        )

        
    # for tables with multiple items per row and need an other category based on a frequency threshold
    def generate_other_cat_table(
    self, group_by_col, latex_caption, latex_label, latex_tabular_size, latex_first_column,
    latex_filename, delimiter=", ", threshold=2, custom_order=None
    ):
        df = self.df.copy()
        citation_col = "Citation Code"
        count_col = "Paper ID"

        # def format_citations(citations):
        #     seen = set()
        #     ordered_unique = []
        #     for cite in citations:
        #         if pd.notna(cite) and cite not in seen:
        #             seen.add(cite)
        #             ordered_unique.append(cite)
        #     return ", ".join(f"\\cite{{{c}}}" for c in ordered_unique) if ordered_unique else "\\cite{placeholder}"
        def format_citations(citations):
            unique = sorted({c for c in citations if pd.notna(c)})
            return f"\\cite{{{','.join(unique)}}}" if unique else "\\cite{placeholder}"


        # Explode multi-value cells
        rows = []
        for _, row in df.iterrows():
            cell_value = row[group_by_col]
            if pd.isna(cell_value):
                continue
            values = [v.strip() for v in str(cell_value).split(delimiter)] if delimiter else [str(cell_value).strip()]
            for value in values:
                rows.append({
                    group_by_col: value,
                    "Paper ID": row[count_col],
                    "Citation Code": row.get(citation_col)
                })

        exploded_df = pd.DataFrame(rows)

        agg_funcs = {
            "Paper_Count": ("Paper ID", "nunique"),
            "Citations": ("Citation Code", lambda x: format_citations(x))
        }
        summary_df = exploded_df.groupby(group_by_col).agg(**agg_funcs).reset_index()

        mask = summary_df["Paper_Count"] <= threshold

        other_row = None
        if mask.any() and not mask.all():
            other_citations = exploded_df.loc[
                exploded_df[group_by_col].isin(summary_df[mask][group_by_col]),
                citation_col
            ]
            other_row = {
                group_by_col: "Other",
                "Paper_Count": other_citations.nunique(),
                "Citations": format_citations(other_citations)
            }
            summary_df = summary_df[~mask] 

       
        if custom_order:
            summary_df[group_by_col] = pd.Categorical(summary_df[group_by_col],
                                                    categories=custom_order, ordered=True)
            summary_df = summary_df.sort_values(by=group_by_col, kind="mergesort")
        else:
            summary_df = summary_df.sort_values(by="Paper_Count", ascending=False, kind="mergesort")

        # Add "Other" last (
        if other_row is not None:
            summary_df = pd.concat([summary_df, pd.DataFrame([other_row])], ignore_index=True)

        # LaTeX
        latex_table = self.generate_latex_table(
            summary_df, latex_caption, latex_label, latex_tabular_size, latex_first_column
        )
        self.saveLatex(latex_filename, latex_table)

        chart_name = latex_filename.replace(" ", "_").replace("-", "_") + ".pdf"
        chart_outfile = os.path.join(BAR_CHART_DIR, chart_name)

        self.save_hbar_from_table(
            summary_df=summary_df,
            category_col=group_by_col,
            count_col="Paper_Count",
            ylabel=latex_caption,
            outfile=chart_outfile,
            custom_order=custom_order,        
        )


            
        
    def generate_hierarchical_table(self, category_list, caption, label, filename, column_label, threshold=2, latex_friendly_names=None):
        df = self.df.copy()
        citation_col = "Citation Code"

        hierarchy = defaultdict(lambda: defaultdict(lambda: {"citations": set(), "count": 0}))

        for _, row in df.iterrows():
            citation = row[citation_col]
            for category in category_list:
                if pd.isna(row.get(category)):
                    continue
                submethods = [s.strip() for s in str(row[category]).split(",") if s.strip()]
                for method in submethods:
                    hierarchy[category][method]["count"] += 1
                    if pd.notna(citation):
                        hierarchy[category][method]["citations"].add(citation)

        latex_lines = [
            "\\begin{table*}[]",
            "\\centering",
            "\\setlength{\\tabcolsep}{1em}",
            f"\\caption{{{caption}}}",
            f"\\label{{tab:{label}}}",
            "\\scriptsize",
            "\\begin{tabular}{@{}p{5cm} l p{7.5cm}@{}}",
            "\\toprule",
            f"\\textbf{{{column_label}}} & \\textbf{{Frequency}} & \\textbf{{Studies}} \\\\",
            "\\midrule"
        ]

        rows = [] 

        category_totals = []
        for category in category_list:
            submethods = hierarchy.get(category, {})
            all_citations = set().union(*(v["citations"] for v in submethods.values())) if submethods else set()
            category_totals.append((category, len(all_citations)))

        sorted_categories = sorted(category_totals, key=lambda x: x[1], reverse=True)
        for category, total_cites in sorted_categories:
            submethods = hierarchy.get(category, {})
            if not submethods:
                continue

            above = {k: v for k, v in submethods.items() if len(v["citations"]) >= threshold}
            below = {k: v for k, v in submethods.items() if len(v["citations"]) < threshold}

            label_name = latex_friendly_names.get(category, category) if latex_friendly_names else category
            latex_lines.append(f"\\textbf{{{label_name}}} & \\textbf{{\\maindatabar{{{total_cites}}}}} & \\\\")
  
            rows.append({"level":"top","label":label_name,"count":total_cites,"group":category})

            for method, data in sorted(above.items(), key=lambda item: len(item[1]["citations"]), reverse=True):
                count = len(data["citations"])
                # cites = ", ".join(f"\\cite{{{c}}}" for c in sorted(data["citations"]))
                cites = f"\\cite{{{','.join(sorted(data['citations']))}}}"
                latex_lines.append(f"\\;\\;\\corner{{}} {method} & \\subdatabar{{{count}}} & {cites} \\\\")
   
                rows.append({"level":"sub","label":method,"count":count,"group":category})

            if below:
                all_below_cites = set().union(*[v["citations"] for v in below.values()])
                count = len(all_below_cites)
                # cites = ", ".join(f"\\cite{{{c}}}" for c in sorted(all_below_cites))
                cites = f"\\cite{{{','.join(sorted(all_below_cites))}}}"
                latex_lines.append(f"\\;\\;\\corner{{}} \\textit{{Other}} & \\subdatabar{{{count}}} & {cites} \\\\")
           
                rows.append({"level":"sub","label":"Other","count":count,"group":category,"is_other":True})

        latex_lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
        self.saveLatex(filename, "\n".join(latex_lines))

   
        chart_name = filename.replace(" ", "_").replace("-", "_") + ".pdf"
        chart_outfile = os.path.join(BAR_CHART_DIR, chart_name)
        total_studies = self.df["Paper ID"].nunique()
        self.save_hierarchical_hbar(
            rows=rows,
            ylabel=caption,
            outfile=chart_outfile,
            total_studies=total_studies
        )


        
# =======================
# RQ 1 
# =======================          
    def motivationsTable(self):
        self.generate_summary_table("Motivation (Clustered)", "Motivations for combining DT and SoS", "motivations-table", "p{2.5cm} l p{13cm}", "Motivation", "rq1/motivations")
        
    def intentsTable(self):
        self.generate_summary_table("Intent", "Intents of combining DT and SoS", "intents-table", "p{4cm} l p{11.5cm}", "Intent", "rq1/intentsTable")
        
    def domainsTable(self):
        self.generate_other_cat_table(
            group_by_col="Domain (Aggregated)",
            latex_caption="Application domains",
            latex_label="domains-table",
            latex_tabular_size="p{4cm} l p{11.5cm}",
            latex_first_column="Domain",
            latex_filename="rq1/domainsTable",
            delimiter=None,
            threshold=2,
        )
        
    def generate_challenges_table(self):
        df = pd.read_excel(data_path, sheet_name="Challenges Separated")
        eval_col = "Challenges"
        expanded_col = "Further Categorization"
        citation_col = "Citation Code"

        hierarchy = {}

        for _, row in df.iterrows():
            eval_type = str(row[eval_col]).title() if pd.notna(row[eval_col]) else None
            if pd.isna(eval_type):
                continue

            expanded_items = [s.strip().title() for s in str(row[expanded_col]).split(",") if s.strip()]
            citation = row[citation_col]

            if eval_type not in hierarchy:
                hierarchy[eval_type] = {}

            for item in expanded_items:
                if item not in hierarchy[eval_type]:
                    hierarchy[eval_type][item] = set()
                if pd.notna(citation):
                    hierarchy[eval_type][item].add(citation)

        # Start LaTeX table
        latex_lines = [
            "\\begin{table*}[]",
            "\\centering",
            "\\setlength{\\tabcolsep}{1em}",
            "\\caption{Challenges}",
            "\\label{tab:challenges-table}",
            "\\footnotesize",
            "\\begin{tabular}{@{}p{4cm} l p{8cm}@{}}", 
            "\\toprule",
            "\\textbf{Challenge} & \\textbf{Frequency} & \\textbf{Studies} \\\\",
            "\\midrule"
        ]
        
        sorted_hierarchy = sorted(
            hierarchy.items(),
            key=lambda item: len(set().union(*item[1].values())),
            reverse=True
        )

        for eval_type, submethods in sorted_hierarchy:
            total_cites = set().union(*submethods.values())
            total_count = len(total_cites)
            # Top-level row: no citations
            latex_lines.append(f"\\textbf{{{eval_type}}} & \\textbf{{\maindatabar{{{total_count}}}}} & \\\\")

            # Submethods with citations
            for method, citations in sorted(submethods.items(), key=lambda item: len(item[1]), reverse=True):
                count = len(citations)
                # citation_str = ", ".join(f"\\cite{{{c}}}" for c in sorted(citations))
                citation_str = f"\\cite{{{','.join(sorted(citations))}}}"
                latex_lines.append(f"\\;\;\\corner{{}} {method} & \subdatabar{{{count}}} & {citation_str} \\\\")

        latex_lines.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table*}"
        ])

        self.saveLatex("rq1/challenges_table", "\n".join(latex_lines))
    
        

# =======================
# RQ 2
# =======================
    def constituentUnitsTable(self):
        self.generate_summary_table("Constituent unit (higher level aggregation)", "Constituent units", "constituent-units-table", "p{5cm} l p{10.5cm}", "Constituent Unit", "rq2/constituentUnitsTable")
        
    def sots_classificationTable(self):
        self.generate_summary_table("SoTS Classification", "SoTS Type", "sots-type-table", "p{2.5cm} l p{13cm}", "SoTS", "rq2/sotsTypeTable")
    
# =======================
# RQ 3 
# =======================
    def autonomyTable(self):
        self.generate_summary_table("DT Class", "Levels of autonomy", "autonomy-table", "p{5cm} l p{10.5cm}", "Autonomy", "rq3/autonomyTable")

    def dtServicesTable(self):
        self.generate_delimiter_table(
        column="Services (Cleaned)", 
        caption="DT services supported", 
        label="dt-services-table", 
        tabular_size="p{3.5cm} l p{12cm}", 
        first_column_name="Service", 
        save_location="rq3/dtServicesTable"
        )


    def generate_formalisms_methods_table(self, threshold=2):
        self.generate_hierarchical_table(
            category_list=[
                "Mathematical and Statistical",
                "Formal and State Based Methods",
                "Discrete-Event Simulation",
                "Continuous Simulation",
                "Agent-Based Simulation",
                "Ontological and Knowledge Representation",
                "Architectural and Structural",
                "Spatial and Visual Modeling",
                "AI and Machine Learning"
            ],
            caption="Modeling and simulation formalisms",
            label="modeling-methods-structured-table",
            filename="rq3/hierarchicalModelingMethodsTable",
            column_label="Category",
            threshold=threshold
        )


    
# =======================
# RQ 4 
# =======================   
    def sosTypeTable(self):
            self.generate_summary_table("Type of SoS", "SoS Type", "sos-type-table", "p{2.5cm} l p{13cm}", "SoS", "rq4/sosTypeTable")

    def emergenceTable(self):
        self.generate_summary_table("Emergence", "Emergence type", "emergence-type-table", "p{2.5cm} l p{13cm}", "Emergence", "rq4/emergenceTable", ["Not Addressed", "Simple", "Weak", "Strong"])
            
    
# =======================
# RQ 5
# =======================
    def securityTable(self):
        custom_order = [
            "Not Addressed",
            "Mentioned",
            "Architecturally Addressed",
            "Explicitly Modeled",
            "Evaluated or Validated"
        ]
        self.generate_summary_table("Security/Confidentiality Level", "Security", "security-table", "p{4cm} l p{11.5cm}", "Context", "rq5/securityTable", custom_order)
        
    def reliabilityTable(self):
        custom_order = [
            "Not Addressed",
            "Mentioned",
            "Architecturally Addressed",
            "Explicitly Modeled",
            "Evaluated or Validated"
        ]
        self.generate_summary_table("Reliability Level", "Reliability", "reliability-table", "p{4cm} l p{11.5cm}", "Context", "rq5/reliabilityTable", custom_order)
     
     
# =======================
# RQ 6
# =======================
    def trlTable(self):
        custom_order = [
            "Initial",
            "Proof-of-Concept",
            "Demo Prototype",
            "Deployed Prototype",
            "Operational"
        ]
        self.generate_summary_table("TRL", "TRL", "trl-table", "p{3.5cm} l p{12cm}", "TRL", "rq6/trlTable", custom_order)            
            
    def generate_structured_eval_table(self, threshold=1, latex_friendly_names=None):
        df = self.df.copy()
        eval_col = "Evaluation"
        expanded_col = "Eval/Val Expanded"
        citation_col = "Citation Code"

        hierarchy = {}
        for _, row in df.iterrows():
            eval_type = str(row[eval_col]).strip().title() if pd.notna(row[eval_col]) else None
            if not eval_type:
                continue
            expanded_items = [s.strip().title()
                            for s in str(row[expanded_col]).split(",")
                            if pd.notna(row[expanded_col]) and s.strip()]
            cite = row.get(citation_col)
            if eval_type not in hierarchy:
                hierarchy[eval_type] = {}
            for item in expanded_items or ["(Unspecified)"]:
                if item not in hierarchy[eval_type]:
                    hierarchy[eval_type][item] = set()
                if pd.notna(cite):
                    hierarchy[eval_type][item].add(cite)

        # Sort categories by total unique citations
        category_totals = []
        for cat, sub in hierarchy.items():
            total_cites = set().union(*sub.values()) if sub else set()
            category_totals.append((cat, len(total_cites)))
        sorted_categories = sorted(category_totals, key=lambda x: x[1], reverse=True)

        caption = "Validation and evaluation approaches"
        label = "evaluation-structured-table"
        latex_lines = [
            "\\begin{table*}[]",
            "\\centering",
            "\\setlength{\\tabcolsep}{1em}",
            f"\\caption{{{caption}}}",
            f"\\label{{tab:{label}}}",
            "\\footnotesize",
            "\\begin{tabular}{@{}p{5cm} l p{7cm}@{}}",
            "\\toprule",
            "\\textbf{Evaluation Category} & \\textbf{Frequency} & \\textbf{Studies} \\\\",
            "\\midrule"
        ]

        rows = []

        for category, _total in sorted_categories:
            submethods = hierarchy.get(category, {})
            if not submethods:
                continue

            above = {k: v for k, v in submethods.items() if len(v) >= threshold}
            below = {k: v for k, v in submethods.items() if len(v) < threshold}

            # Top-level row
            top_total = len(set().union(*submethods.values())) if submethods else 0
            cat_label = (latex_friendly_names or {}).get(category, category)
            latex_lines.append(f"\\textbf{{{cat_label}}} & \\textbf{{\\maindatabar{{{top_total}}}}} & \\\\")
            rows.append({"level": "top", "label": cat_label, "count": top_total, "group": category})

            # Submethods w/ combined citations
            for method, cites in sorted(above.items(), key=lambda kv: len(kv[1]), reverse=True):
                cnt = len(cites)
                citation_str = f"\\cite{{{','.join(sorted(cites))}}}"
                latex_lines.append(f"\\;\\;\\corner{{}} {method} & \\subdatabar{{{cnt}}} & {citation_str} \\\\")
                rows.append({"level": "sub", "label": method, "count": cnt, "group": category})

            # Other (combined)
            if below:
                other_cites = set().union(*below.values())
                cnt = len(other_cites)
                citation_str = f"\\cite{{{','.join(sorted(other_cites))}}}"
                latex_lines.append(f"\\;\\;\\corner{{}} \\textit{{Other}} & \\subdatabar{{{cnt}}} & {citation_str} \\\\")
                rows.append({"level": "sub", "label": "Other", "count": cnt, "group": category, "is_other": True})

        latex_lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
        self.saveLatex("rq6/hierarchicalEvaluationTable", "\n".join(latex_lines))

        chart_outfile = os.path.join(BAR_CHART_DIR, "rq6_hierarchicalEvaluationTable.pdf")
        os.makedirs(os.path.dirname(chart_outfile), exist_ok=True)
        total_studies = self.df["Paper ID"].nunique()
        self.save_hierarchical_hbar(
            rows=rows,
            ylabel=caption,
            outfile=chart_outfile,
            total_studies=total_studies
        )


    def contributionTypeTable(self):
        self.generate_summary_table("Contribution type", "Contribution type", "contribution-type-table", "p{2cm} l p{13.5cm}", "Contribution", "rq6/contributionTypeTable")
                  
    def standardsTable(self, threshold=2):
        self.generate_other_cat_table(
            group_by_col="Standards Used (Cleaned Up)",
            latex_caption="Standards",
            latex_label="standards-table",
            latex_tabular_size="p{6.5cm} l p{9cm}",
            latex_first_column="Standard",
            latex_filename="rq6/standards",
            delimiter=";",             
            threshold=threshold,
            )

        
    def dtOrSoSRelated(self):
        self.generate_summary_table("Do The Studies Use Standards in More of an SoS or DT context", "Standards usage context (DT vs. SoS)", "dt-or-sos-related-table", "p{2cm} l p{13.5cm}", "Context", "rq6/dtOrSoSRelated")
        
        
# =======================
# RQ 7
# =======================   
    def programmingLangaugesTables(self, threshold=0):
        self.generate_hierarchical_table(
            category_list=[
                "General Purpose",
                "Markup and Styling",
                "Data Representation"
            ],
            caption="Programming languages and data formats",
            label="programming-languages-structured-table",
            filename="rq7/hierarchicalProgrammingLanguagesTable",
            column_label="Category",
            threshold=threshold
        )

    
    def generate_frameworks_table(self, threshold=2):
        self.generate_hierarchical_table(
            category_list=[
                "Digital Twin & IoT", "Modeling & Simulation", "AI, Data Analytics & Machine Learning",
                "Cloud, Edge, and DevOps", "Systems Engineering & Architecture",
                "Data Management", "Geospatial & Visualization Technologies",
                "Application Development & Web Technologies"
            ],
            caption="Tools and frameworks",
            label="frameworks-structured-table",
            filename="rq7/hierarchicalFrameworksTable",
            column_label="Category",
            threshold=threshold,
            latex_friendly_names={
                "Digital Twin & IoT": "Digital Twin \\& IoT",
                "Modeling & Simulation": "Modeling \\& Simulation",
                "AI, Data Analytics & Machine Learning": "AI, Data Analytics \\& ML",
                "Cloud, Edge, and DevOps": "Cloud, Edge, and DevOps",
                "Systems Engineering & Architecture": "Systems Eng. \\& Architecture",
                "Data Management": "Data Management",
                "Geospatial & Visualization Technologies": "Geospatial \\& Visualization",
                "Application Development & Web Technologies": "App/Web Technologies",
            }
        )

                     
# =======================
# Saving and Running Script 
# =======================        
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
            getattr(self, func_name)()

    def run_one(self, observation_id):
        if observation_id in self.observation_map:
            func_name = self.observation_map[observation_id]
            print(f"Running observation {observation_id}: {func_name} ...")
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
