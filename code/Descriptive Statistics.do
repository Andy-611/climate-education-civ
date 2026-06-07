* 导入数据
import delimited "C:\Users\ASUS\Desktop\Master Thesis\Data of My Thesis\Education Data\important!!\Process Check\all_data_final_with_IMR_rename.csv", clear

egen normr1h = std(r1h)
egen normrfh = std(rfh)
egen normr3h = std(r3h)

egen normfluctmonth = std(fluctmonth)
egen normfluctintra = std(fluctintra)
egen normflucttendays = std(flucttendays)


display "{hline}"
display "主要变量描述性统计"
* 定义变量宏，方便后续调用
local myvars passrate excellencerate r1h r3h fluctmonth gender schtype schlocation imr
// * 基础描述性统计 (观测值数量、均值、标准差、最小值、最大值)
// summarize `myvars'
* 详细的描述性统计表格 (包含中位数 p50)
tabstat `myvars', statistics(n mean sd min p25 p50 p75 max) columns(statistics)
* 针对分类变量 (如 SchType, SchLocation, Gender) 进行频率分布统计
tab1 schtype schlocation gender

* 查看学年和年级的频率分布及百分比
tab1 schyear grade
display "{hline}"




display "{hline}"
display "主要变量间相关性分析"
// local myvars2 normr1h heavyrain lowrain extrefluctmonth extrefluctintra schtype schlocation gender imr niveau2 niveau3 niveau4 niveau5 niveau6
local myvars2 normr1h normr3h normfluctmonth schtype schlocation gender imr
pwcorr `myvars2', sig star(0.05)
display "{hline}"



display "{hline}"
display "方差膨胀因子 (VIF) 分析(因变量为passrate)"
* vif为“后估计”命令，在其之前必须先执行 regress
regress passrate `myvars2'
vif
display "{hline}"

