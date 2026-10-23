#323 F64 交接（未執行項保留未跑）

受驗產品：f64d638f15c48d2b9723b7ae9d230fb5dacb82d9。三套50/0/0；36 timings與4 profiles原數值全綠；memo真撤回／恢復0/1/0；isolated175/350全tuple等價。原b74跨功能ABC三個stdout及stderr診斷差異仍紅。

下列精確template只準備，尚未由此owner執行；<FINAL_FULL40>填根代理最終固定SHA，<FINAL_CLEAN_CHECKOUT>填其乾淨snapshot，<FRESH_FINAL_REMAINING_OUT>用新out且三stage共用同一最終SHA。

```sh
env -u NODE_OPTIONS -u PYTHONOPTIMIZE -u LD_PRELOAD python3 -B /tmp/geo323-train337-lineage-20261024/acceptance-tools-v4-scene-binding/run.py --repo <FINAL_CLEAN_CHECKOUT> --sha <FINAL_FULL40> --base b74f9a2ae7ade1555b9be45283adecc097fb76e3 --main adbaebf9c73ea6801d7b4d5214e4b846b132923b --out <FRESH_FINAL_REMAINING_OUT> --heavy-lock /tmp/g261r3/heavy.lock --stage required-eight
```

```sh
env -u NODE_OPTIONS -u PYTHONOPTIMIZE -u LD_PRELOAD python3 -B /tmp/geo323-train337-lineage-20261024/acceptance-tools-v4-scene-binding/run.py --repo <FINAL_CLEAN_CHECKOUT> --sha <FINAL_FULL40> --base b74f9a2ae7ade1555b9be45283adecc097fb76e3 --main adbaebf9c73ea6801d7b4d5214e4b846b132923b --out <FRESH_FINAL_REMAINING_OUT> --heavy-lock /tmp/g261r3/heavy.lock --stage pf3
```

```sh
env -u NODE_OPTIONS -u PYTHONOPTIMIZE -u LD_PRELOAD python3 -B /tmp/geo323-train337-lineage-20261024/acceptance-tools-v4-scene-binding/run.py --repo <FINAL_CLEAN_CHECKOUT> --sha <FINAL_FULL40> --base b74f9a2ae7ade1555b9be45283adecc097fb76e3 --main adbaebf9c73ea6801d7b4d5214e4b846b132923b --out <FRESH_FINAL_REMAINING_OUT> --heavy-lock /tmp/g261r3/heavy.lock --stage native
```

原driver自己持R3／reaper／16MiB stack，別在外層雙鎖。PATH前綴沿/workspace/geo261-environment/bin；不改counts或門檻。

Root最後統一fullnative可供完整native原receipt；standalone PF3未被run_all註冊，仍需原獨立receipt。不要以50 partial、166 scenes或175 ABC冒完整native。

原包仍cloud-only；MANIFEST與每part逐member完整bytes/hash已驗。公開E與Git roundtrip尚待root封存，一般push，無force。

細節、六份獨立peer、缺口與完整退出碼見同目錄DELIVERY.json。
