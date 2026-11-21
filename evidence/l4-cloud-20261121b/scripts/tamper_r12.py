# 產生錯包：把已保存專案 manifest 裡第一個模型的斷面拉伸件材料總量改掉（其餘 bytes 不動），用來核對「錯包拒絕、不換目前專案」。
import json, sys, zipfile
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(src) as z, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as o:
    for info in z.infolist():
        data = z.read(info.filename)
        if info.filename == 'manifest.json':
            m = json.loads(data)
            s = m['models'][0]['result']['summary']
            s['profile_material_volume_mm3'] = str(int(s.get('profile_material_volume_mm3', '0')) + 1)
            data = json.dumps(m, ensure_ascii=False).encode()
        o.writestr(info, data)
print('tampered', dst)
