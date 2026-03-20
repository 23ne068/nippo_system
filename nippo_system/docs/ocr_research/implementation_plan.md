# 螳溯｣・ｨ育判譖ｸ: GPU縺ｪ縺励・繝ｫ繝√Δ繝ｼ繝繝ｫ繝ｻ繝・・繧ｿ蜿朱寔繧ｷ繧ｹ繝・Β

譛ｬ險育判譖ｸ縺ｯ縲・*GPU髱樊政霈峨・PC**蜷代￠縺ｫ譛驕ｩ蛹悶＆繧後◆繝ｭ繝ｼ繧ｫ繝ｫ繝・・繧ｿ蜿朱寔繧ｷ繧ｹ繝・Β縺ｮ髢狗匱譁ｹ驥昴ｒ縺ｾ縺ｨ繧√◆繧ゅ・縺ｧ縺吶Ａreport.md`縺ｫ險倩ｼ峨＆繧後◆繧｢繝ｼ繧ｭ繝・け繝√Ε縺ｫ蝓ｺ縺･縺阪∵怙繧りｻｽ驥上↑謚陦捺ｧ区・繧呈治逕ｨ縺励※縺・∪縺吶・

## 逶ｮ逧・
逕ｻ髱｢荳翫・繝・く繧ｹ繝茨ｼ・CR・峨・浹螢ｰ・・SR・峨∫黄逅・・蜉帙√♀繧医・繝ｦ繝ｼ繧ｶ繝ｼ縺ｮ迥ｶ諷九ｒ繝ｭ繝ｼ繧ｫ繝ｫ迺ｰ蠅・〒蜿朱寔縺励∵律蝣ｱ逕滓・縺ｫ蠢・ｦ√↑繝・・繧ｿ繧定塘遨阪☆繧九す繧ｹ繝・Β繧呈ｧ狗ｯ峨＠縺ｾ縺吶よｨ呎ｺ也噪縺ｪCPU縺ｮ縺ｿ縺ｧ蜉ｹ邇・噪縺ｫ蜍穂ｽ懊☆繧九％縺ｨ繧呈怙蜆ｪ蜈医→縺励∪縺吶・

## 繧｢繝ｼ繧ｭ繝・け繝√Ε驕ｸ螳・(CPU譛驕ｩ蛹・

繝ｬ繝昴・繝医↓蝓ｺ縺･縺阪∽ｻ･荳九・縲瑚ｻｽ驥・OS繝阪う繝・ぅ繝悶阪ヱ繧ｿ繝ｼ繝ｳ繧呈治逕ｨ縺励∪縺吶・

1.  **逕ｻ髱｢OCR**: **繝代ち繝ｼ繝ｳA (OpenCV + Tesseract)**
    *   **逅・罰**: WinRT (biosdk) 縺ｮPython 3.13迺ｰ蠅・〒縺ｮ繝薙Ν繝峨′蝗ｰ髮｣縺縺｣縺溘◆繧√∝ｮ牙ｮ壹＠縺鬱esseract繧呈治逕ｨ縺励∪縺吶５esseract縺ｯ繧ｻ繝・ヨ繧｢繝・・縺悟ｿ・ｦ√〒縺吶′縲∵ｱ守畑諤ｧ縺碁ｫ倥＞縺ｧ縺吶・
    *   **莉｣譖ｿ譯・*: 蟆・擂逧・↓PaddleOCR縺ｸ縺ｮ遘ｻ陦後ｂ讀懆ｨ主庄閭ｽ縺ｧ縺吶′縲√∪縺壹・Tesseract縺ｧ螳溯｣・＠縺ｾ縺吶・

2.  **髻ｳ螢ｰ隱崎ｭ・(ASR)**: **繝代ち繝ｼ繝ｳ: Vosk**
    *   **逅・罰**: 霆ｽ驥上↑CPU謗ｨ隲悶↓迚ｹ蛹悶＠縺ｦ險ｭ險医＆繧後※縺・∪縺吶・aster-Whisper縺ｯ邊ｾ蠎ｦ縺碁ｫ倥＞縺ｧ縺吶′縲，PU繧ｹ繝壹ャ繧ｯ縺ｫ繧医▲縺ｦ縺ｯ驥阪＞縺溘ａ縲√∪縺壹・Vosk・域律譛ｬ隱槭Δ繝・Ν・峨°繧蛾幕蟋九＠縺ｾ縺吶・

3.  **繝励Ο繧ｻ繧ｹ邂｡逅・*: **繝代ち繝ｼ繝ｳ1 (Multiprocessing)**
    *   **逅・罰**: ZeroMQ縺ｪ縺ｩ縺ｮ霑ｽ蜉繧､繝ｳ繝輔Λ繧貞ｿ・ｦ√→縺帙★縲∝腰荳縺ｮ繝ｭ繝ｼ繧ｫ繝ｫ繧｢繝励Μ縺ｨ縺励※螳檎ｵ舌＆縺帙ｋ縺溘ａ縺ｫ譛繧ゅす繝ｳ繝励Ν縺ｧ蜊∝・縺ｪ讒区・縺ｧ縺吶・

4.  **繝ｦ繝ｼ繧ｶ繝ｼ迥ｶ諷・*: **YOLOv8n-pose (CPU)**
    *   **逅・罰**: "Nano"繝｢繝・Ν縺ｯ髱槫ｸｸ縺ｫ霆ｽ驥上〒縺吶・PU雋闕ｷ繧帝∩縺代ｋ縺溘ａ縲∝ｸｸ譎ら屮隕悶〒縺ｯ縺ｪ縺・*雜・ｽ薩PS・井ｾ・ 5縲・0遘偵↓1蝗橸ｼ・*縺ｧ螳溯｡後＠縺ｾ縺吶・

5.  **繝・・繧ｿ菫晏ｭ・*: **SQLite (In-Memory/File)**
    *   **逅・罰**: 讓呎ｺ也噪縺ｧ霆ｽ驥上°縺､菫｡鬆ｼ諤ｧ縺碁ｫ倥＞繝・・繧ｿ繝吶・繧ｹ縺ｧ縺吶・

## 謠先｡医☆繧句､画峩蜀・ｮｹ

### 繝・ぅ繝ｬ繧ｯ繝医Μ讒区・
```
nippo_system/
笏懌楳笏 main.py                 # 繧ｨ繝ｳ繝医Μ繝昴う繝ｳ繝医√・繝ｭ繧ｻ繧ｹ邂｡逅・
笏懌楳笏 config.py               # 險ｭ螳夲ｼ・PS縲・明蛟､縲ゝTL遲会ｼ・
笏懌楳笏 modules/
笏・  笏懌楳笏 __init__.py
笏・  笏懌楳笏 input_monitor.py    # 繧ｭ繝ｼ繝懊・繝・繝槭え繧ｹ/繧ｦ繧｣繝ｳ繝峨え逶｣隕・(pynput, pywin32)
笏・  笏懌楳笏 audiolistener.py    # 繝槭う繧ｯ -> VAD -> Vosk -> 繝・く繧ｹ繝亥喧
笏・  笏懌楳笏 screen_ocr.py       # 逕ｻ髱｢繧ｭ繝｣繝励メ繝｣ -> 蟾ｮ蛻・､懷・ -> WinRT OCR
笏・  笏懌楳笏 user_state.py       # Web繧ｫ繝｡繝ｩ -> YOLOv8n (菴薩PS)
笏・  笏披楳笏 storage.py          # SQLite邂｡逅・ｼ・TL讖溯・莉倥″・・
笏披楳笏 utils/
    笏懌楳笏 image_utils.py      # 逕ｻ蜒丞ｷｮ蛻・・逅・Ο繧ｸ繝・け
    笏披楳笏 privacy.py          # 蛟倶ｺｺ諠・ｱ・・II・峨・繧ｹ繧ｭ繝ｳ繧ｰ繝ｭ繧ｸ繝・け
```

### 1. 迚ｩ逅・・蜉帙→繧ｦ繧｣繝ｳ繝峨え逶｣隕・(`modules/input_monitor.py`)
-   **繝ｩ繧､繝悶Λ繝ｪ**: `pynput`, `pywin32`
-   **繝ｭ繧ｸ繝・け**:
    -   繧ｭ繝ｼ繝懊・繝峨→繝槭え繧ｹ縺ｮ繧､繝吶Φ繝医ｒ繝輔ャ繧ｯ縺励∪縺吶・
    -   謇馴嵯謨ｰ・・PM・峨↑縺ｩ繧偵き繧ｦ繝ｳ繝医＠縺ｾ縺吶′縲・*螳滄圀縺ｮ蜈･蜉帙く繝ｼ縺ｯ險倬鹸縺励∪縺帙ｓ**・医く繝ｼ繝ｭ繧ｬ繝ｼ蛹夜亟豁｢・峨・
    -   `GetForegroundWindow` 繧偵・繝ｼ繝ｪ繝ｳ繧ｰ縺励※繧｢繧ｯ繝・ぅ繝悶↑繧｢繝励Μ蜷阪ｒ蜿門ｾ励＠縺ｾ縺吶・
    -   **繝励Λ繧､繝舌す繝ｼ**: 繧ｦ繧｣繝ｳ繝峨え繧ｿ繧､繝医Ν縺ｫ縲後ヱ繧ｹ繝ｯ繝ｼ繝峨阪ｄ縲碁橿陦後阪↑縺ｩ縺悟性縺ｾ繧後ｋ蝣ｴ蜷医√Ο繧ｰ蜿門ｾ励ｒ荳譎ょ●豁｢縺励∪縺吶・

### 2. 髻ｳ螢ｰ蜿朱寔 (`modules/audiolistener.py`)
-   **繝ｩ繧､繝悶Λ繝ｪ**: `sounddevice`, `vosk`, `scipy` (縺ｾ縺溘・ `webrtcvad`)
-   **繝ｭ繧ｸ繝・け**:
    -   髻ｳ螢ｰ繧偵せ繝医Μ繝ｼ繝溘Φ繧ｰ縺励∪縺吶・
    -   VAD・育匱隧ｱ蛹ｺ髢捺､懷・・峨ｒ驕ｩ逕ｨ縺励∝｣ｰ縺後＠縺ｦ縺・ｋ譎ゅ□縺大・逅・＠縺ｾ縺吶・
    -   螢ｰ縺梧､懃衍縺輔ｌ縺溘ｉ繝舌ャ繝輔ぃ繧歎osk縺ｫ騾√ｊ縲√ユ繧ｭ繧ｹ繝亥・蜉帙→繧ｿ繧､繝繧ｹ繧ｿ繝ｳ繝励ｒ菫晏ｭ倥＠縺ｾ縺吶・

### 3. 逕ｻ髱｢OCR (`modules/screen_ocr.py`)
-   **繝ｩ繧､繝悶Λ繝ｪ**: `pytesseract` (Tesseract譛ｬ菴薙′蠢・ｦ・, `opencv-python`, `mss`
-   **繝ｭ繧ｸ繝・け**:
    -   X遘偵＃縺ｨ・井ｾ・ 5遘抵ｼ峨↓逕ｻ髱｢繧偵く繝｣繝励メ繝｣縺励∪縺吶・
    -   蜑榊屓縺ｮ繝輔Ξ繝ｼ繝縺ｨ `cv2.absdiff` 縺ｧ蟾ｮ蛻・ｒ險育ｮ励＠縺ｾ縺吶・
    -   螟牙喧驥上′髢ｾ蛟､繧定ｶ・∴縺溷ｴ蜷・
        -   OpenCV逕ｻ蜒上ヰ繝・ヵ繧｡繧・`image_to_string` 縺ｫ貂｡縺励※OCR繧貞ｮ溯｡後＠縺ｾ縺吶・
    -   驥崎､・＠縺ｪ縺・ユ繧ｭ繧ｹ繝医〒縺ゅｌ縺ｰ菫晏ｭ倥＠縺ｾ縺吶・

### Phase 5.1: OCR Output Optimization (Structuring & Deduplication)
The user requested to prioritize **structuring text into sentences** over simple deduplication. Lab experiments (Exp 1i) confirmed that artificial line separation is critical for Tesseract accuracy in Dark Mode.

**New Workflow (Verified in Lab):**
1.  **Line-wise Spacing (Pre-processing) [NEW]**:
    -   Group detected changes into horizontal lines.
    -   Composite these lines into a single image with **80px vertical gaps**.
    -   **Result**: +119% word detection improvement (416 words vs 190).

2.  **Smart Deduplication [SECOND]**:
    -   Compare detected Lines against the cache.
    -   **Static/Motion Filter**: If a line with the *same text* exists in the cache, **IGNORE IT**.
    -   **New Content**: Only log lines that are truly new or changed text.

### Phase 5.2: OCR Lab Results & Backport
Lab experiments in `ocr_lab` provided following finalized parameters:
- **Padding**: 40px (Optimal for character edge detection).
- **Background**: Solid Black (Higher stability than complementary/inverted).
- **Spacing**: 80px between lines (Record-breaking accuracy boost).
- **Language**: `jpn` (Stable for mixed Japanese/English).

**Outcome**: These verified logic improvements will be backported to `nippo_system/modules/screen_ocr.py`.

### 4. 繝ｦ繝ｼ繧ｶ繝ｼ迥ｶ諷・(`modules/user_state.py`)
-   **繝ｩ繧､繝悶Λ繝ｪ**: `ultralytics` (YOLO), `opencv-python`
-   **繝ｭ繧ｸ繝・け**:
    -   Web繧ｫ繝｡繝ｩ縺ｮ繝輔Ξ繝ｼ繝繧・*10縲・0遘偵↓1蝗・*繧ｭ繝｣繝励メ繝｣縺励∪縺吶・
    -   YOLOv8n-pose繧貞ｮ溯｡後＠縺ｾ縺吶・
    -   繝偵Η繝ｼ繝ｪ繧ｹ繝・ぅ繝・け蛻､螳・
        -   謇九′鬘斐・霑代￥縺ｫ縺ゅｋ -> 縲瑚・∴荳ｭ縲・
        -   閧ｩ縺梧､懷・縺輔ｌ繧・-> 縲檎捩蟶ｭ荳ｭ縲・
        -   繧ｹ繝槭・縺梧､懷・縺輔ｌ繧・-> 縲後せ繝槭・謫堺ｽ應ｸｭ縲・

### 繝峨Λ繧､繝舌・迚ｹ螳壹・菫ｮ蠕ｩ
繝上・繝峨え繧ｧ繧｢ID繧堤峩謗･隱ｭ縺ｿ蜿悶ｊ縲∽ｸ榊ｮ牙ｮ壹↑讓呎ｺ悶ラ繝ｩ繧､繝舌ｒ繝｡繝ｼ繧ｫ繝ｼ謠蝉ｾ帷沿縺ｫ蟾ｮ縺玲崛縺医∪縺吶・
*   [x] 繧ｪ繝ｼ繝・ぅ繧ｪ: Realtek ALC256 (UAD迚医∈縺ｮ譖ｴ譁ｰ縺ｧ繧ｸ繝｣繝・け讀懃衍菫ｮ豁｣)
*   [/] 繝阪ャ繝医Ρ繝ｼ繧ｯ: WiFi/Ethernet (蛻・妙蝠城｡後∬・蜍墓磁邯壻ｸ崎憶縺ｮ菫ｮ豁｣)
*   [ ] 繧ｫ繝｡繝ｩ: Realtek/Sonix (謗･邯壻ｸ榊ｮ牙ｮ壹・菫ｮ豁｣)

---

## 讀懆ｨｼ險育判
### 閾ｪ蜍輔ユ繧ｹ繝・
*   蜷・Δ繧ｸ繝･繝ｼ繝ｫ縺ｮ蜊倅ｽ薙ユ繧ｹ繝亥ｮ溯｡・
*   `driver_finder.py` 縺ｫ繧医ｋID謨ｴ蜷域ｧ遒ｺ隱・

### 謇句虚讀懆ｨｼ
1.  繧､繝､繝帙Φ繧ｸ繝｣繝・け縺ｮ謚懊″蟾ｮ縺励↓繧医ｋ閾ｪ蜍募・繧頑崛縺育｢ｺ隱搾ｼ域ｸ茨ｼ・
2.  WiFi/Ethernet縺ｮ螳牙ｮ壽ｧ縺ｨ閾ｪ蜍墓磁邯壹・遒ｺ隱・
3.  繧ｫ繝｡繝ｩ縺ｮ髟ｷ譎る俣繝励Ξ繝薙Η繝ｼ繝・せ繝・

### 5. 繝・・繧ｿ菫晏ｭ・(`modules/storage.py`)
-   **繝ｩ繧､繝悶Λ繝ｪ**: `sqlite3`
-   **繝ｭ繧ｸ繝・け**:
    -   繝・・繝悶Ν: `logs (id, timestamp, type, content, metadata)`
    -   繝舌ャ繧ｯ繧ｰ繝ｩ繧ｦ繝ｳ繝峨せ繝ｬ繝・ラ縺ｧ `DELETE FROM logs WHERE timestamp < NOW - 24h` 繧貞ｮ壽悄螳溯｡後＠縲∝商縺・ョ繝ｼ繧ｿ繧定・蜍募炎髯､縺励∪縺吶・

## 讀懆ｨｼ險育判
1.  **CPU逶｣隕・*: 讓呎ｺ也噪縺ｪ繝・Η繧｢繝ｫ/繧ｯ繧｢繝・ラ繧ｳ繧｢繝弱・繝・C縺ｧ縲∝・菴薙・CPU菴ｿ逕ｨ邇・′30-50%莉･荳九↓蜿弱∪繧九％縺ｨ繧堤｢ｺ隱阪＠縺ｾ縺吶・
2.  **繝励Λ繧､繝舌す繝ｼ繝√ぉ繝・け**: 縲後Γ繝｢蟶ｳ縲阪〒縺ｮ蜈･蜉帙→縲√ヱ繧ｹ繝ｯ繝ｼ繝牙・蜉帶ｬ・〒縺ｮ謖吝虚繧呈ｯ碑ｼ・＠縲√ヱ繧ｹ繝ｯ繝ｼ繝峨′險倬鹸縺輔ｌ縺ｪ縺・ｼ医∪縺溘・繝槭せ繧ｯ縺輔ｌ繧具ｼ峨％縺ｨ繧堤｢ｺ隱阪＠縺ｾ縺吶・
3.  **OCR繝√ぉ繝・け**: 繝峨く繝･繝｡繝ｳ繝医ｒ髢九＞縺ｦ譁・ｭ励ｒ蜈･蜉帙＠縲√◎縺ｮ蠅怜・繝・く繧ｹ繝医′豁｣縺励￥OCR縺輔ｌ繧九°遒ｺ隱阪＠縺ｾ縺吶・

## Phase 6: 譌･蝣ｱ逕滓・繧ｪ繝ｼ繝医Γ繝ｼ繧ｷ繝ｧ繝ｳ (Reporter)
### 逶ｮ逧・
闢・ｩ阪＆繧後◆OCR繝ｭ繧ｰ (`ocr_results_YYYY-MM-DD.txt`) 繧定ｧ｣譫舌＠縲・譌･縺ｮ豢ｻ蜍輔ｒ隕∫ｴ・＠縺櫪arkdown繝ｬ繝昴・繝医ｒ閾ｪ蜍慕函謌舌＠縺ｾ縺吶ゅΘ繝ｼ繧ｶ繝ｼ縺梧焔蜍輔〒陦後▲縺櫚LM蠖ｹ・育ｿｻ險ｳ繝ｻ隕∫ｴ・ｼ峨・荳驛ｨ繧偵√Ν繝ｼ繝ｫ繝吶・繧ｹ縺ｨ繝偵Η繝ｼ繝ｪ繧ｹ繝・ぅ繝・け縺ｧ閾ｪ蜍募喧縺励∪縺吶・

### 莉墓ｧ・(`modules/reporter.py`)
1.  **蜈･蜉・*: `data/ocr_results_YYYY-MM-DD.txt` (JSON Lines蠖｢蠑・
2.  **蜃ｦ逅・Ο繧ｸ繝・け**:
    *   **繝代・繧ｹ**: JSON繧定ｪｭ縺ｿ霎ｼ縺ｿ縲√ち繧､繝繧ｹ繧ｿ繝ｳ繝励→繝・く繧ｹ繝医∝ｺｧ讓吶ｒ螻暮幕縲・
    *   **繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ**:
        *   繧ｷ繧ｹ繝・Β繝ｭ繧ｰ ("Debug", "Trace"縺ｪ縺ｩ) 縺ｮ髯､螟悶・
        *   遏ｭ縺吶℃繧九ユ繧ｭ繧ｹ繝医∵э蜻ｳ縺ｮ縺ｪ縺・枚蟄怜・縺ｮ髯､螟悶・
    *   **繧ｯ繝ｩ繧ｹ繧ｿ繝ｪ繝ｳ繧ｰ**:
        *   譎る俣譫・井ｾ・ 15蛻・＃縺ｨ・峨〒繧｢繧ｯ繝・ぅ繝薙ユ繧｣繧偵げ繝ｫ繝ｼ繝怜喧縲・
        *   繧ｭ繝ｼ繝ｯ繝ｼ繝牙・迴ｾ鬆ｻ蠎ｦ縺九ｉ縲御ｸｻ隕√↑繝医ヴ繝・け縲阪ｒ謗ｨ螳・(e.g., "Gmail", "VS Code", "Meeting").
    *   **隕∫ｴ・函謌・*:
        *   繧ｿ繧､繝繝ｩ繧､繝ｳ蠖｢蠑上〒豢ｻ蜍輔ｒ蜃ｺ蜉帙・
        *   讀懷・縺輔ｌ縺滄㍾隕√く繝ｼ繝ｯ繝ｼ繝峨ｒ繝ｪ繧ｹ繝医い繝・・縲・
3.  **蜃ｺ蜉・*: `data/report_YYYY-MM-DD.md`

## 繝輔ぉ繝ｼ繧ｺ7: 繝・・繝ｭ繧､繝｡繝ｳ繝・(EXE蛹・
### 逶ｮ逧・
髢狗匱螳御ｺ・ｾ後√Θ繝ｼ繧ｶ繝ｼ縺後Ρ繝ｳ繧ｯ繝ｪ繝・け縺ｧ襍ｷ蜍輔・蟶ｸ鬧舌〒縺阪ｋ繧医≧縺ｫ蜊倅ｸ縺ｮ螳溯｡後ヵ繧｡繧､繝ｫ縺ｫ繝代ャ繧ｱ繝ｼ繧ｸ繝ｳ繧ｰ縺吶ｋ縲・

### 謚陦薙せ繧ｿ繝・け
- **繝・・繝ｫ**: `PyInstaller`
- **讒区・**:
    - `onefile` 繝｢繝ｼ繝会ｼ亥腰荳繝輔ぃ繧､繝ｫ蛹厄ｼ峨∪縺溘・ `onedir` 繝｢繝ｼ繝会ｼ郁ｵｷ蜍暮溷ｺｦ驥崎ｦ厄ｼ・
    - `noconsole` 繧ｪ繝励す繝ｧ繝ｳ・磯ｻ偵＞逕ｻ髱｢繧貞・縺輔↑縺・ｼ・
    - 繝医Ξ繧､繧｢繧､繧ｳ繝ｳ讖溯・・・pystray` 繝ｩ繧､繝悶Λ繝ｪ繧定ｿｽ蜉讀懆ｨ趣ｼ峨〒縲檎ｵゆｺ・阪瑚ｨｭ螳壹阪ｒ謠蝉ｾ・

### 謇矩・
1. `pyinstaller main.spec` 縺ｮ菴懈・縺ｨ萓晏ｭ倬未菫ゑｼ・esseract繝代せ遲会ｼ峨・險倩ｿｰ
2. 蜍穂ｽ懃｢ｺ隱搾ｼ井ｻｮ諠ｳ迺ｰ蠅・､悶〒縺ｮ螳溯｡後ユ繧ｹ繝茨ｼ・
3. 繧ｹ繧ｿ繝ｼ繝医い繝・・逋ｻ骭ｲ逕ｨ繝舌ャ繝√ヵ繧｡繧､繝ｫ縺ｮ菴懈・
