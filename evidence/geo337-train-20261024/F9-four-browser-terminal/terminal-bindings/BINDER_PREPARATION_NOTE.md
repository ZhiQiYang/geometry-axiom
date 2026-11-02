首次 metadata 綁定命令 exit 1：`KeyError: 'exit_code'`。原因是 documents/materialize（其後另三份 materialize 相同）用 yielded host 封裝，真返回值位於 `actual_tool_result.exit_code`；plan 則是頂層 `exit_code`。首次在讀取第二份小型 FINAL 時停止，尚未寫出 TERMINAL_PINS.json、未執行 collector、未讀 SHM／產品源。

原 12 份 FINAL 未修改。以下修正版只區分兩個真 host JSON 封裝，並核對原 job／phase／result 路徑；不改原退出碼、不重測。原四job collector 同一個 schema 假設已另存 v3 作最小修補，v2 原件保留，待獨立 delta 審查。
