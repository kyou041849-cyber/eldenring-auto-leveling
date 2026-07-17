@echo off
echo Mode: full reference XML replay.
echo Stop command: press Ctrl+C in this window.
echo After Ctrl+C, the virtual controller stays neutral for 3 seconds before exit.
echo If Windows asks to terminate the batch job, press Y then Enter.
call "%~dp0start_xml_macro.cmd" --loops 0
