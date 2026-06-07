"""
Output-focused version of `CausalForest Model 4.ipynb`.

This script keeps the data processing and CausalForestDML settings the same as
the notebook, then adds:
1. one Excel workbook collecting the six group-effect tables;
2. one 6-panel CATE frequency distribution figure;
3. one 6-panel group CATE mean +/- 1 SE figure;
4. one feature-importance heatmap.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from econml.dml import CausalForestDML
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler


DATA_PATH = Path(
    r"C:\Users\ASUS\Desktop\Master Thesis\Data of My Thesis\Education Data"
    r"\important!!\Process Check\all_data_final_with_IMR_rename.csv"
)
OUTPUT_DIR = DATA_PATH.parent / "CausalForest_Model4_Final_Outputs"

REQUIRED_COLS = [
    "ExcellenceRate",
    "PassRate",
    "r1h",
    "rfh",
    "r3h",
    "FluctMonth",
    "FluctIntra",
    "FluctTenDays",
    "SchType",
    "SchLocation",
    "Gender",
    "IMR",
    "Grade",
    "District",
    "Date",
    "SchYear",
]

Y_COLS = ["PassRate", "ExcellenceRate"]
T_COLS = ["Normr1h", "Normr3h", "NormFluctMonth"]
X_COLS = ["SchType", "SchLocation", "Gender"]


def set_plot_style() -> None:
    sns.set_theme(style="whitegrid", font_scale=0.95)
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def load_model4_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=REQUIRED_COLS)

    scaler = StandardScaler()
    for var in ["r1h", "r3h", "FluctMonth"]:
        df[f"Norm{var}"] = scaler.fit_transform(df[[var]])

    return pd.get_dummies(
        df,
        columns=["Grade", "District", "Date", "SchYear"],
        drop_first=True,
    )


def w_cols_for_treatment(df: pd.DataFrame, t_var: str) -> list[str]:
    fixed_effect_cols = [
        c for c in df.columns if any(p in c for p in ["Grade_", "District_", "Date_"])
    ]
    if t_var == "Normr1h":
        return ["IMR", "Normr3h", "NormFluctMonth"] + fixed_effect_cols
    if t_var == "Normr3h":
        return ["IMR", "Normr1h", "NormFluctMonth"] + fixed_effect_cols
    return ["IMR", "Normr1h", "Normr3h"] + fixed_effect_cols


def make_estimator(seed: int = 32) -> CausalForestDML:
    return CausalForestDML(
        model_y=LassoCV(random_state=seed),
        model_t=LassoCV(random_state=seed),
        discrete_treatment=False,
        n_estimators=2000,
        min_samples_leaf=100,
        min_var_fraction_leaf=0.1,
        cv=3,
        random_state=seed,
        n_jobs=-1,
    )


def describe_case(row: pd.Series) -> str:
    sch_type = "私立" if row["SchType"] == 1 else "公立"
    location = "城市" if row["SchLocation"] == 1 else "农村"
    gender = "男生" if row["Gender"] == 1 else "女生"
    return f"{sch_type}-{location}-{gender}"


def pair_label(y_col: str, t_var: str, sep: str = "-") -> str:
    return f"{y_col}{sep}{t_var}"


def build_group_table(est: CausalForestDML, df: pd.DataFrame, y_col: str, t_var: str) -> pd.DataFrame:
    combinations = list(itertools.product([0, 1], repeat=len(X_COLS)))
    df_comb = pd.DataFrame(combinations, columns=X_COLS)

    inf_comb = est.effect_inference(df_comb)
    df_comb["treatment_effect"] = np.asarray(est.effect(df_comb)).ravel()
    df_comb["std_error"] = np.asarray(inf_comb.stderr).ravel()
    df_comb["p_value"] = np.asarray(inf_comb.pvalue()).ravel()
    df_comb["Group_Desc"] = df_comb.apply(describe_case, axis=1)

    group_share = df.groupby(X_COLS).size().reset_index(name="Group_Count")
    group_share["Sample_Share"] = (
        group_share["Group_Count"] / len(df) * 100
    ).map(lambda x: f"{x:.2f}%")

    df_comb = df_comb.merge(group_share[X_COLS + ["Sample_Share"]], on=X_COLS, how="left")
    df_comb.insert(0, "Pair", pair_label(y_col, t_var, "-"))
    df_comb.insert(1, "Y", y_col)
    df_comb.insert(2, "T", t_var)

    ordered_cols = [
        "Pair",
        "Y",
        "T",
        "Group_Desc",
        "Sample_Share",
        "treatment_effect",
        "std_error",
        "p_value",
        *X_COLS,
    ]
    return df_comb[ordered_cols]


def run_all_models() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = load_model4_data()
    cate_tables = []
    group_tables = []
    importance_rows = []

    for y_col in Y_COLS:
        for t_var in T_COLS:
            plot_name = pair_label(y_col, t_var, "~")
            print(f"\n==================== 正在分析: {plot_name} ====================")

            est = make_estimator(seed=32)
            est.fit(
                df[y_col],
                df[t_var],
                X=df[X_COLS],
                W=df[w_cols_for_treatment(df, t_var)],
            )

            hte_values = np.asarray(est.effect(df[X_COLS])).ravel()
            cate_tables.append(
                pd.DataFrame(
                    {
                        "Pair": pair_label(y_col, t_var, "-"),
                        "Plot_Name": plot_name,
                        "Y": y_col,
                        "T": t_var,
                        "CATE": hte_values,
                    }
                )
            )

            group_table = build_group_table(est, df, y_col, t_var)
            group_tables.append(group_table)
            print(group_table[["Group_Desc", "Sample_Share", "treatment_effect", "p_value"]])

            for feature, importance in zip(X_COLS, est.feature_importances_):
                importance_rows.append(
                    {
                        "Pair": pair_label(y_col, t_var, "-"),
                        "Plot_Name": plot_name,
                        "Y": y_col,
                        "T": t_var,
                        "feature": feature,
                        "importance": float(importance),
                    }
                )

    return (
        pd.concat(cate_tables, ignore_index=True),
        pd.concat(group_tables, ignore_index=True),
        pd.DataFrame(importance_rows),
    )


def save_excel(group_df: pd.DataFrame, importance_df: pd.DataFrame, cate_df: pd.DataFrame) -> Path:
    excel_path = OUTPUT_DIR / "Causal_Forest_Model4_Group_Effects.xlsx"
    cate_summary = (
        cate_df.groupby(["Pair", "Plot_Name", "Y", "T"])["CATE"]
        .agg(["count", "mean", "std", "min", "max"])
        .reset_index()
    )

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        group_df.to_excel(writer, sheet_name="group_effects", index=False)
        for pair, sub_df in group_df.groupby("Pair", sort=False):
            sub_df.to_excel(writer, sheet_name=pair[:31], index=False)
        importance_df.to_excel(writer, sheet_name="feature_importance", index=False)
        cate_summary.to_excel(writer, sheet_name="cate_summary", index=False)

    return excel_path


def plot_cate_histograms(cate_df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(3, 2, figsize=(12, 12), constrained_layout=True)
    plot_order = [pair_label(y, t, "~") for t in T_COLS for y in Y_COLS]
    for ax, plot_name in zip(axes.ravel(), plot_order):
        sub_df = cate_df[cate_df["Plot_Name"] == plot_name]
        sns.histplot(sub_df["CATE"], bins=35, color="#4C78A8", edgecolor="white", ax=ax)
        ax.axvline(sub_df["CATE"].mean(), color="#D62728", linewidth=1.6)
        ax.set_title(plot_name)
        ax.set_xlabel("CATE")
        ax.set_ylabel("频数")

    out_path = OUTPUT_DIR / "Figure1_CATE_Frequency_Distribution.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_group_effects(group_df: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(3, 2, figsize=(16, 13), constrained_layout=True)
    palette = ["#4C78A8", "#59A14F", "#F28E2B", "#E15759", "#76B7B2", "#B07AA1", "#EDC948", "#9C755F"]

    plot_order = [pair_label(y, t, "-") for t in T_COLS for y in Y_COLS]
    for ax, pair in zip(axes.ravel(), plot_order):
        sub_df = group_df[group_df["Pair"] == pair]
        plot_name = pair.replace("-", "~", 1)
        x = np.arange(len(sub_df))
        y = sub_df["treatment_effect"].to_numpy()
        se = sub_df["std_error"].to_numpy()

        ax.bar(x, y, color=palette[: len(sub_df)], width=0.68)
        ax.errorbar(x, y, yerr=se, fmt="none", ecolor="black", elinewidth=1.3, capsize=5)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(plot_name)
        ax.set_xticks(x)
        ax.set_xticklabels(sub_df["Group_Desc"], rotation=35, ha="right")
        ax.set_ylabel("CATE")
        ax.set_xlabel("")

    out_path = OUTPUT_DIR / "Figure2_Group_CATE_Mean_1SE.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_feature_importance_heatmap(importance_df: pd.DataFrame) -> Path:
    heatmap_df = importance_df.pivot(index="Plot_Name", columns="feature", values="importance")
    heatmap_df = heatmap_df.loc[
        [pair_label(y, t, "~") for y in Y_COLS for t in T_COLS],
        X_COLS,
    ]

    fig, ax = plt.subplots(figsize=(8, 5.8), constrained_layout=True)
    sns.heatmap(
        heatmap_df,
        annot=True,
        fmt=".4f",
        cmap="YlGnBu",
        linewidths=0.6,
        linecolor="white",
        cbar_kws={"label": "Feature Importance"},
        ax=ax,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")

    out_path = OUTPUT_DIR / "Figure3_Feature_Importance_Heatmap.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    set_plot_style()

    cate_df, group_df, importance_df = run_all_models()

    cate_csv = OUTPUT_DIR / "Causal_Forest_Model4_CATE_Per_Observation.csv"
    cate_df.to_csv(cate_csv, index=False, encoding="utf-8-sig")

    excel_path = save_excel(group_df, importance_df, cate_df)
    fig1 = plot_cate_histograms(cate_df)
    fig2 = plot_group_effects(group_df)
    fig3 = plot_feature_importance_heatmap(importance_df)

    print("\n全部输出完成：")
    print(f"Excel: {excel_path}")
    print(f"CATE明细: {cate_csv}")
    print(f"图1: {fig1}")
    print(f"图2: {fig2}")
    print(f"图3: {fig3}")


if __name__ == "__main__":
    main()
