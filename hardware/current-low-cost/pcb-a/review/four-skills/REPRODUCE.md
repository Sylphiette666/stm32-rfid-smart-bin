# 审查复现说明

本目录保留2026-10-12审查时的原始输出和适配脚本。脚本属于方法记录，需要按自己的KiCad/Python路径配置，不能直接在生产目录运行布局生成或修复。

先用Git提交8eca04c恢复初始A1到临时baseline目录，再把当前A1复制到同级working。将本目录适配脚本复制到它们的父目录，安装四套技能及相应隔离依赖。run_review.py默认分析baseline；REVIEW_VARIANT=working分析working。KiCad原生后端与IPC后端不得同时写同一板；stitch_ipc.py只能在确认临时working板打开且尚无GND过孔时执行。

常规再验收无需重做布局：直接对当前工程运行KiCad ERC、带重新铺铜及原理图一致性的DRC；用当前GerberZIP的9个文件运行gerber_audit，执行review/check_drill_alignment.py核孔。设计源修改后所有旧报告失效，必须重新生成。

ngspice DLL适配仅做无载分压直流计算。热/生命周期自动工具的零评估结果不是PASS。before中的native-dnp-fix空列表表示没有需要改写的DNP，9个原生DNP标记已正确；happy统计未识别它们。

mixed-directory-audit记录了工具将drill-report.txt误当钻孔文件的提示；gerber-audit.txt针对实际上传ZIP中的9个文件，0错误0警告。
