* 导入数据
import excel "C:\Users\ASUS\Desktop\Master Thesis\Data of My Thesis\Education Data\important!!\Process Check\Ecoles_primaires_2024_2025_Tagged_n_IMR.xlsx", sheet("Sheet1") firstrow clear

// 论文中变量名和原文件中变量名的对应关系：
// # is_in_project->IfProject
// # Milieu_ecole->SchLocation
// # Statut->SchType
// # ecole_electrifie_Y_N->ElectrifiedSch
// # salle_multimedia_y_n->MultimediaRoom
// # Connexion_internet_Y_N->InternetSch
// # project_density_by_iepp->ProjectDensity

display "{hline}"
display "主要变量描述性统计"
* 定义变量宏，方便后续调用
local myvars is_in_project Statut Milieu_ecole ecole_electrifie_Y_N salle_multimedia_y_n Connexion_internet_Y_N project_density_by_iepp IMR
// * 基础描述性统计 (观测值数量、均值、标准差、最小值、最大值)
// summarize `myvars'
* 详细的描述性统计表格 (包含中位数 p50)
tabstat `myvars', statistics(n mean sd min p25 p50 p75 max) columns(statistics)



display "{hline}"
display "主要变量间相关性分析"
local myvars2 Statut Milieu_ecole ecole_electrifie_Y_N salle_multimedia_y_n Connexion_internet_Y_N project_density_by_iepp
pwcorr `myvars2', sig star(0.05)
display "{hline}"



display "{hline}"
display "方差膨胀因子 (VIF) 分析(因变量为is_in_project)"
* vif为"后估计"命令，在其之前必须先执行 regress
regress is_in_project `myvars2'
vif
display "{hline}"

