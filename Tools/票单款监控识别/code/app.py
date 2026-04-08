import os
import sys
import time
import json
import base64
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import configparser
import urllib.request
import urllib.error
import ssl
import re

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def read_ini():
    ini_path = os.path.join(get_base_path(), "setup.ini")
    cfg = {"base_url": "", "api_key": "", "model": "", "template": "{date}__{item}__{paid}", "provider": "", "tesseract_cmd": "", "watch_folder": ""}
    if os.path.exists(ini_path):
        p = configparser.ConfigParser()
        p.read(ini_path, encoding="utf-8")
        section = "order-llm" if p.has_section("order-llm") else ("llm" if p.has_section("llm") else None)
        if section:
            cfg["base_url"] = p.get(section, "base_url", fallback=cfg["base_url"]).rstrip("/")
            cfg["api_key"] = p.get(section, "api_key", fallback=cfg["api_key"])
            cfg["model"] = p.get(section, "model", fallback=cfg["model"])
            cfg["template"] = p.get(section, "template", fallback=cfg["template"])
            cfg["provider"] = p.get(section, "provider", fallback=cfg["provider"]).lower()
            cfg["tesseract_cmd"] = p.get(section, "tesseract_cmd", fallback=cfg["tesseract_cmd"])
            cfg["watch_folder"] = p.get(section, "watch_folder", fallback=cfg["watch_folder"])
    if not cfg["base_url"]:
        if cfg["provider"] == "deepseek":
            cfg["base_url"] = "https://api.deepseek.com"
        elif cfg["provider"] == "kimi":
            cfg["base_url"] = "https://api.moonshot.cn"
        elif cfg["provider"] == "qwen":
            cfg["base_url"] = "https://dashscope.aliyuncs.com/compatible-mode"
    return cfg

def read_ini_pay():
    ini_path = os.path.join(get_base_path(), "setup.ini")
    cfg = {"base_url": "", "api_key": "", "model": "", "template": "{date}__{method}__{paid}", "provider": "", "tesseract_cmd": "", "watch_folder": "", "purpose": "pay"}
    if os.path.exists(ini_path):
        p = configparser.ConfigParser()
        p.read(ini_path, encoding="utf-8")
        section = "pay-llm" if p.has_section("pay-llm") else ("pay_llm" if p.has_section("pay_llm") else None)
        if section:
            cfg["base_url"] = p.get(section, "base_url", fallback=cfg["base_url"]).rstrip("/")
            cfg["api_key"] = p.get(section, "api_key", fallback=cfg["api_key"])
            cfg["model"] = p.get(section, "model", fallback=cfg["model"])
            cfg["template"] = p.get(section, "template", fallback=cfg["template"])
            cfg["provider"] = p.get(section, "provider", fallback=cfg["provider"]).lower()
            cfg["tesseract_cmd"] = p.get(section, "tesseract_cmd", fallback=cfg["tesseract_cmd"])
            cfg["watch_folder"] = p.get(section, "watch_folder", fallback=cfg["watch_folder"])
    if not cfg["base_url"]:
        if cfg["provider"] == "deepseek":
            cfg["base_url"] = "https://api.deepseek.com"
        elif cfg["provider"] == "kimi":
            cfg["base_url"] = "https://api.moonshot.cn"
        elif cfg["provider"] == "qwen":
            cfg["base_url"] = "https://dashscope.aliyuncs.com/compatible-mode"
    return cfg

def read_ini_rep():
    ini_path = os.path.join(get_base_path(), "setup.ini")
    cfg = {"base_url": "", "api_key": "", "model": "", "template": "{date}-{amount}", "provider": "", "tesseract_cmd": "", "watch_folder": "", "purpose": "invoice"}
    if os.path.exists(ini_path):
        p = configparser.ConfigParser()
        p.read(ini_path, encoding="utf-8")
        section = "rep-llm" if p.has_section("rep-llm") else ("rep_llm" if p.has_section("rep_llm") else None)
        if section:
            cfg["base_url"] = p.get(section, "base_url", fallback=cfg["base_url"]).rstrip("/")
            cfg["api_key"] = p.get(section, "api_key", fallback=cfg["api_key"])
            cfg["model"] = p.get(section, "model", fallback=cfg["model"])
            cfg["template"] = p.get(section, "template", fallback=cfg["template"])
            cfg["provider"] = p.get(section, "provider", fallback=cfg["provider"]).lower()
            cfg["tesseract_cmd"] = p.get(section, "tesseract_cmd", fallback=cfg["tesseract_cmd"])
            cfg["watch_folder"] = p.get(section, "watch_folder", fallback=cfg["watch_folder"])
    if not cfg["base_url"]:
        if cfg["provider"] == "deepseek":
            cfg["base_url"] = "https://api.deepseek.com"
        elif cfg["provider"] == "kimi":
            cfg["base_url"] = "https://api.moonshot.cn"
        elif cfg["provider"] == "qwen":
            cfg["base_url"] = "https://dashscope.aliyuncs.com/compatible-mode"
    return cfg

def sanitize_filename(name):
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    name = name.strip().strip(".")
    if not name:
        name = "untitled"
    return name

def currency_to_yen(s):
    t = s.replace("￥", "¥")
    t = t.replace("RMB", "¥")
    t = t.replace("CNY", "¥")
    return t

def pdf_to_image_b64(path):
    try:
        import fitz
        doc = fitz.open(path)
        if doc.page_count < 1:
            return None
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        data = pix.tobytes("png")
        return base64.b64encode(data).decode("ascii")
    except Exception as e:
        return None

def prepare_image_b64(img_path, max_px=1600, jpeg_quality=85, max_bytes=900000):
    if img_path.lower().endswith(".pdf"):
        res = pdf_to_image_b64(img_path)
        if res:
            return res
        raise Exception("PDF conversion failed")

    try:
        from PIL import Image
        img = Image.open(img_path)
        img = img.convert("RGB")
        w, h = img.size
        scale = 1.0
        if max(w, h) > max_px:
            scale = max_px / float(max(w, h))
            img = img.resize((int(w * scale), int(h * scale)))
        import io
        q = jpeg_quality
        while True:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=q)
            data = buf.getvalue()
            if len(data) <= max_bytes or q <= 60:
                break
            q -= 5
        return base64.b64encode(data).decode("ascii")
    except Exception:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")

def try_parse_json_text(txt):
    try:
        return json.loads(txt)
    except Exception:
        pass
    s = txt.strip()
    if s.startswith("```"):
        try:
            s = s.strip("`")
        except:
            pass
    m = re.search(r"\{[\s\S]*?\"filename\"[\s\S]*?\}", s)
    if m:
        return json.loads(m.group(0))
    m2 = re.search(r"filename\s*[:：]\s*\"?([^\"\n\r]+)\"?", s, re.IGNORECASE)
    if m2:
        return {"filename": m2.group(1).strip()}
    return {"filename": s.strip()}

def extract_ocr_text(img_path, cfg):
    try:
        from PIL import Image
        import pytesseract
        if cfg.get("tesseract_cmd"):
            pytesseract.pytesseract.tesseract_cmd = cfg["tesseract_cmd"]
        
        # Simple PDF OCR handling not implemented here, assuming VLM for PDF
        if img_path.lower().endswith(".pdf"):
            return ""

        img = Image.open(img_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) < 1200:
            img = img.resize((w * 2, h * 2))
        text = pytesseract.image_to_string(img, lang="chi_sim+eng")
        return text.strip()
    except Exception:
        return ""

def call_llm_rename(img_path, cfg, log_func=None):
    try:
        b64 = prepare_image_b64(img_path)
    except Exception as e:
        return None, f"读取文件失败: {e}", {"error": str(e)}
    if not cfg["base_url"] or not cfg["api_key"] or not cfg["model"]:
        return None, "LLM配置不完整", {"error": "missing_config"}
    url = cfg["base_url"] + "/v1/chat/completions"
    
    if cfg.get("purpose") == "pay":
        prompt = (
            "你是文件重命名助手。识别截图中的日期、支付卡信息与实际付款金额，生成文件名，"
            "格式为模板：" + cfg["template"] + "。第二段为支付方式（method）："
            "当为卡类（信用卡/储蓄卡）时，并识别后四位卡号，直接追加method中，如“信用卡”“储蓄卡”；"
            "非卡类（余额/微信/支付宝/白条/等）直接使用方式名，如“微信”“支付宝”。"
            "日期用YYYY-MM-DD，金额必须保留两位小数并使用“¥”，选择“最终需支付”的金额。"
            "仅返回JSON：{\"filename\": \"...\"}，不要额外文本。"
        )
    elif cfg.get("purpose") == "invoice":
        prompt = (
            "你是文件重命名助手。识别发票中的开票日期和开票总金额（Total Amount）。"
            "文件名格式模板：" + cfg["template"] + "（如 {date}-{amount}）。"
            "日期用YYYY-MM-DD，金额保留两位小数使用“¥”。"
            "仅返回JSON：{\"filename\": \"...\"}，不要额外文本。"
        )
    else:
        prompt = (
            "你是文件重命名助手。识别截图中的订单日期、采购内容与实付金额，生成文件名，"
            "格式为模板：" + cfg["template"] + "，日期用YYYY-MM-DD，实付金额必须严格按截图保留两位小数（如¥123.45/ $19.99），"
            "不要四舍五入或取整；若截图金额为整数则输出 .00。若存在多个金额，选择“最终需支付”的金额，即：实付款/真实付款/最终付款/需付款/应付中的值。"
            "采购内容必须是中文2-5个字，去掉修饰词、用途、商家/品牌，只保留真实物品名。仅返回JSON：{\"filename\": \"...\"}，不要额外文本。"
        )
        
    # Log prompt immediately if callback provided
    if log_func:
        p_show = prompt.replace("\n", " ")
        if len(p_show) > 80: p_show = p_show[:80] + "..."
        log_func(f">> 发送 Prompt: {p_show}")

    debug = {"prompt": prompt, "model": cfg["model"], "base_url": cfg["base_url"], "provider": cfg.get("provider", "")}
    body_image = {
        "model": cfg["model"],
        "temperature": 0,
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": "严格输出JSON且仅一个对象"}]},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + b64},
                    },
                ],
            },
        ],
    }
    data = json.dumps(body_image).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "Authorization": "Bearer " + cfg["api_key"],
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    raw = None
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as e:
            try:
                raw = e.read().decode("utf-8", errors="replace")
            except Exception:
                raw = str(e)
            debug["response_raw"] = raw
            if "unknown variant `image_url`" in raw or "expected `text`" in raw:
                # If model doesn't support image, try OCR (only for images, skip PDF OCR fallback for now)
                if img_path.lower().endswith(".pdf"):
                     return None, "该模型不支持PDF/图像输入", debug

                ocr_txt = extract_ocr_text(img_path, cfg)
                if not ocr_txt:
                    return None, "该模型不支持图像输入且OCR不可用", debug
                body_text = {
                    "model": cfg["model"],
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": "严格输出JSON且仅一个对象"},
                        {"role": "user", "content": prompt + "\nOCR文本：\n" + ocr_txt},
                    ],
                }
                data2 = json.dumps(body_text).encode("utf-8")
                req2 = urllib.request.Request(url, data=data2, headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(req2, timeout=90, context=ctx) as resp2:
                        raw = resp2.read().decode("utf-8", errors="replace")
                        debug["response_raw"] = raw
                    break
                except Exception as e2:
                    if i == 2:
                        return None, f"网络错误: {e2}", {"error": str(e2)}
                    time.sleep(2 * (i + 1))
                    continue
            else:
                return None, f"HTTP错误: {raw}", debug
        except Exception as e:
            debug.setdefault("attempts", []).append(str(e))
            if i == 2:
                return None, f"网络错误: {e}", {"error": str(e)}
            time.sleep(2 * (i + 1))
            continue
    try:
        j = json.loads(raw)
        txt = j["choices"][0]["message"]["content"]
        debug["model_content"] = txt
    except Exception as e:
        return None, f"解析响应失败: {e}", {"response_raw": raw}
    try:
        obj = try_parse_json_text(txt)
        debug["parsed"] = obj
        name = currency_to_yen(sanitize_filename(obj.get("filename", "")))
        if not name:
            return None, "LLM未返回文件名", debug
        ext = os.path.splitext(img_path)[1] or ".png"
        return name + ext, None, debug
    except Exception as e:
        return None, f"JSON格式错误: {e}", {"model_content": txt}

class OrderWatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("订单/支付/发票 监控重命名")
        self.root.geometry("800x600")
        self.cfg = read_ini()
        self.pay_cfg = read_ini_pay()
        self.rep_cfg = read_ini_rep()
        self.folder = ""
        self.pay_folder = ""
        self.rep_folder = ""
        self.running = False
        self.pay_running = False
        self.rep_running = False
        self.thread = None
        self.pay_thread = None
        self.rep_thread = None
        self.order_token = None
        self.pay_token = None
        self.rep_token = None
        self.seen = {}
        self.pay_seen = {}
        self.rep_seen = {}
        self.baseline = set()
        self.pay_baseline = set()
        self.rep_baseline = set()
        self.ignored = set()
        self.pay_ignored = set()
        self.rep_ignored = set()
        self.state_path = os.path.join(get_base_path(), "watch_state.json")
        self.log_path = os.path.join(get_base_path(), "watch.log")
        self.log_queue = queue.Queue()
        self.retry_delays = {}
        
        # Row 1: Order
        top = tk.Frame(root, bg="#ddd")
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        tk.Label(top, text="订单截图文件夹").pack(side=tk.LEFT, padx=5)
        self.path_var = tk.StringVar()
        self.entry = tk.Entry(top, textvariable=self.path_var, width=60)
        self.entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="更换文件夹", command=self.choose_folder).pack(side=tk.LEFT, padx=5)
        self.btn = tk.Button(top, text="开始监控", bg="#f7a57b", command=self.toggle)
        self.btn.pack(side=tk.LEFT, padx=5)
        self.cv_order, self.c_order = self.create_indicator(top)
        
        # Row 2: Pay
        top2 = tk.Frame(root, bg="#ddd")
        top2.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        tk.Label(top2, text="支付截图文件夹").pack(side=tk.LEFT, padx=5)
        self.pay_path_var = tk.StringVar()
        self.pay_entry = tk.Entry(top2, textvariable=self.pay_path_var, width=60)
        self.pay_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top2, text="更换文件夹", command=self.choose_pay_folder).pack(side=tk.LEFT, padx=5)
        self.pay_btn = tk.Button(top2, text="开始监控", bg="#8bc34a", command=self.toggle_pay)
        self.pay_btn.pack(side=tk.LEFT, padx=5)
        self.cv_pay, self.c_pay = self.create_indicator(top2)
        
        # Row 3: Invoice (Rep)
        top3 = tk.Frame(root, bg="#ddd")
        top3.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        tk.Label(top3, text="发票文件文件夹").pack(side=tk.LEFT, padx=5)
        self.rep_path_var = tk.StringVar()
        self.rep_entry = tk.Entry(top3, textvariable=self.rep_path_var, width=60)
        self.rep_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top3, text="更换文件夹", command=self.choose_rep_folder).pack(side=tk.LEFT, padx=5)
        self.rep_btn = tk.Button(top3, text="开始监控", bg="#64b5f6", command=self.toggle_rep)
        self.rep_btn.pack(side=tk.LEFT, padx=5)
        self.cv_rep, self.c_rep = self.create_indicator(top3)
        
        self.log = ScrolledText(root, height=20)
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        clr_btn = tk.Button(self.log, text="清除日志", command=self.clear_log, bg="#ffcccb", font=("Microsoft YaHei", 8))
        clr_btn.place(relx=0.97, y=5, anchor="ne")

        if self.cfg.get("watch_folder") and os.path.isdir(self.cfg["watch_folder"]):
            self.folder = self.cfg["watch_folder"]
            self.path_var.set(self.folder)
        if self.pay_cfg.get("watch_folder") and os.path.isdir(self.pay_cfg["watch_folder"]):
            self.pay_folder = self.pay_cfg["watch_folder"]
            self.pay_path_var.set(self.pay_folder)
        if self.rep_cfg.get("watch_folder") and os.path.isdir(self.rep_cfg["watch_folder"]):
            self.rep_folder = self.rep_cfg["watch_folder"]
            self.rep_path_var.set(self.rep_folder)

        self.blink_state = False
        self.run_blink_animation()
        self.process_log_queue()

    def create_indicator(self, parent):
        cv = tk.Canvas(parent, width=20, height=20, bg="#ddd", highlightthickness=0)
        c = cv.create_oval(5, 5, 15, 15, fill="gray", outline="gray")
        cv.pack(side=tk.LEFT, padx=5)
        return cv, c

    def run_blink_animation(self):
        self.blink_state = not self.blink_state
        c_run = "#ff0000" if self.blink_state else "#ff9999" # Red <-> Light Red
        c_stop = "gray"
        
        self.cv_order.itemconfig(self.c_order, fill=c_run if self.running else c_stop, outline=c_run if self.running else c_stop)
        self.cv_pay.itemconfig(self.c_pay, fill=c_run if self.pay_running else c_stop, outline=c_run if self.pay_running else c_stop)
        self.cv_rep.itemconfig(self.c_rep, fill=c_run if self.rep_running else c_stop, outline=c_run if self.rep_running else c_stop)
        
        self.root.after(800, self.run_blink_animation)

    def process_log_queue(self):
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.log.insert(tk.END, msg)
                self.log.see(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self.process_log_queue)

    def save_watch_folder(self):
        self._save_ini_folder("order-llm", self.folder)

    def save_pay_watch_folder(self):
        self._save_ini_folder("pay-llm", self.pay_folder)
    
    def save_rep_watch_folder(self):
        self._save_ini_folder("rep-llm", self.rep_folder)

    def _save_ini_folder(self, section_name, folder_path):
        ini_path = os.path.join(get_base_path(), "setup.ini")
        p = configparser.ConfigParser()
        if os.path.exists(ini_path):
            p.read(ini_path, encoding="utf-8")
        
        # Handle variations like pay_llm vs pay-llm if they exist
        target_section = section_name
        if not p.has_section(section_name):
             if p.has_section(section_name.replace("-", "_")):
                 target_section = section_name.replace("-", "_")
             else:
                 p.add_section(section_name)
        
        p.set(target_section, "watch_folder", folder_path)
        with open(ini_path, "w", encoding="utf-8") as f:
            p.write(f)

    def clear_log(self):
        self.log.delete("1.0", tk.END)

    def choose_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder = path
            self.path_var.set(path)
            try: self.save_watch_folder()
            except: pass

    def choose_pay_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.pay_folder = path
            self.pay_path_var.set(path)
            try: self.save_pay_watch_folder()
            except: pass

    def choose_rep_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.rep_folder = path
            self.rep_path_var.set(path)
            try: self.save_rep_watch_folder()
            except: pass

    def toggle(self):
        if not self.running:
            if not self.folder or not os.path.isdir(self.folder):
                messagebox.showerror("错误", "请选择有效的文件夹")
                return
            self.start_monitoring(self.folder, "order")
        else:
            self.stop_monitoring("order")

    def toggle_pay(self):
        if not self.pay_running:
            if not self.pay_folder or not os.path.isdir(self.pay_folder):
                messagebox.showerror("错误", "请选择有效的文件夹")
                return
            self.start_monitoring(self.pay_folder, "pay")
        else:
            self.stop_monitoring("pay")
            
    def toggle_rep(self):
        if not self.rep_running:
            if not self.rep_folder or not os.path.isdir(self.rep_folder):
                messagebox.showerror("错误", "请选择有效的文件夹")
                return
            self.start_monitoring(self.rep_folder, "rep")
        else:
            self.stop_monitoring("rep")

    def _add_existing_to_baseline(self, folder, baseline):
        if not os.path.isdir(folder): return
        count = 0
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isfile(path):
                    baseline.add(path)
                    count += 1
            if count > 0:
                self.log_insert(f"忽略现有文件: {count} 个")
        except Exception as e:
            self.log_insert(f"初始化忽略文件失败: {e}")

    def start_monitoring(self, folder, type_):
        # Conflict Check
        active_folders = []
        if self.running: active_folders.append(os.path.normpath(self.folder))
        if self.pay_running: active_folders.append(os.path.normpath(self.pay_folder))
        if self.rep_running: active_folders.append(os.path.normpath(self.rep_folder))
        
        tgt = os.path.normpath(folder)
        # If restarting the same type, exclude itself from check (though logic below handles restart)
        # But here we haven't set running=True yet, so self.running refers to current state.
        # If I am 'order' and already running, I'm in active_folders. But toggle() calls stop() first?
        # Let's check toggle logic.
        # toggle() calls start_monitoring only if NOT running. So self.running is False.
        # But wait, if pay is running on folder X, and I start order on folder X.
        
        if tgt in active_folders:
            messagebox.showerror("错误", "该文件夹已被其他任务监控，请选择不同文件夹以避免冲突。")
            return

        self.load_state()
        if type_ == "order":
            self.running = True
            self.order_token = object()
            self.btn.configure(text="停止监控")
            self.baseline = set(self.ignored)
            self._add_existing_to_baseline(folder, self.baseline)
            self.log_insert(f"开始监控订单: {folder}")
            self.thread = threading.Thread(target=self.loop, args=(self.order_token,), daemon=True)
            self.thread.start()
        elif type_ == "pay":
            self.pay_running = True
            self.pay_token = object()
            self.pay_btn.configure(text="停止监控")
            self.pay_baseline = set(self.pay_ignored)
            self._add_existing_to_baseline(folder, self.pay_baseline)
            self.log_insert(f"开始监控支付: {folder}")
            self.pay_thread = threading.Thread(target=self.pay_loop, args=(self.pay_token,), daemon=True)
            self.pay_thread.start()
        elif type_ == "rep":
            self.rep_running = True
            self.rep_token = object()
            self.rep_btn.configure(text="停止监控")
            self.rep_baseline = set(self.rep_ignored)
            self._add_existing_to_baseline(folder, self.rep_baseline)
            self.log_insert(f"开始监控发票: {folder}")
            self.rep_thread = threading.Thread(target=self.rep_loop, args=(self.rep_token,), daemon=True)
            self.rep_thread.start()

    def stop_monitoring(self, type_):
        if type_ == "order":
            self.running = False
            self.order_token = None
            self.btn.configure(text="开始监控")
            self.log_insert("已停止订单监控")
        elif type_ == "pay":
            self.pay_running = False
            self.pay_token = None
            self.pay_btn.configure(text="开始监控")
            self.log_insert("已停止支付监控")
        elif type_ == "rep":
            self.rep_running = False
            self.rep_token = None
            self.rep_btn.configure(text="开始监控")
            self.log_insert("已停止发票监控")

    def loop(self, token):
        while self.running and self.order_token is token:
            try: self.scan_once()
            except Exception as e: self.log_insert("扫描错误: " + str(e))
            time.sleep(2)

    def pay_loop(self, token):
        while self.pay_running and self.pay_token is token:
            try: self.pay_scan_once()
            except Exception as e: self.log_insert("扫描错误: " + str(e))
            time.sleep(2)

    def rep_loop(self, token):
        while self.rep_running and self.rep_token is token:
            try: self.rep_scan_once()
            except Exception as e: self.log_insert("扫描错误: " + str(e))
            time.sleep(2)

    def scan_once(self):
        self._scan_generic(self.folder, self.baseline, self.seen, self.process_file, [".png", ".jpg", ".jpeg", ".bmp", ".webp"])

    def pay_scan_once(self):
        self._scan_generic(self.pay_folder, self.pay_baseline, self.pay_seen, self.pay_process_file, [".png", ".jpg", ".jpeg", ".bmp", ".webp"])

    def rep_scan_once(self):
        self._scan_generic(self.rep_folder, self.rep_baseline, self.rep_seen, self.rep_process_file, [".png", ".jpg", ".jpeg", ".bmp", ".webp", ".pdf"])

    def _scan_generic(self, folder, baseline, seen_map, process_func, allowed_exts):
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if not os.path.isfile(path): continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in allowed_exts: continue
            if self.is_final_name(name): continue
            if path in baseline: continue
            
            # Retry logic: skip if in cooling period
            if path in self.retry_delays:
                if time.time() < self.retry_delays[path]:
                    continue

            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            key = (size, int(mtime))
            prev = seen_map.get(path)
            if prev == key: continue
            
            # Try process
            if process_func(path):
                seen_map[path] = key
                if path in self.retry_delays: del self.retry_delays[path]
            else:
                # Failed, schedule retry
                self.retry_delays[path] = time.time() + 60
                self.log_insert(f"处理失败，60秒后重试: {os.path.basename(path)}")

    def process_file(self, path):
        return self._process_file_generic(path, self.cfg, self.folder, self.baseline, self.ignored, self.seen)

    def pay_process_file(self, path):
        return self._process_file_generic(path, self.pay_cfg, self.pay_folder, self.pay_baseline, self.pay_ignored, self.pay_seen)

    def rep_process_file(self, path):
        return self._process_file_generic(path, self.rep_cfg, self.rep_folder, self.rep_baseline, self.rep_ignored, self.rep_seen)

    def _process_file_generic(self, path, cfg, folder, baseline, ignored, seen_map):
        filename = os.path.basename(path)
        self.log_insert(f"发现文件: {filename}")
        self.log_insert(f"正在请求 LLM 识别...")
        
        t0 = time.time()
        newname, err, dbg = call_llm_rename(path, cfg, self.log_insert)
        dt = time.time() - t0
        self.log_insert(f"LLM 响应耗时: {dt:.1f}s")

        if dbg:
            # Log Raw Response
            if "response_raw" in dbg:
                r_show = str(dbg["response_raw"]).replace("\n", " ")
                if len(r_show) > 300: r_show = r_show[:300] + "..."
                self.log_insert(f"<< 原始响应: {r_show}")
            elif "model_content" in dbg:
                c_show = str(dbg["model_content"]).replace("\n", " ")
                if len(c_show) > 200: c_show = c_show[:200] + "..."
                self.log_insert(f"<< 模型内容: {c_show}")
        
        if err:
            self.log_insert(f"LLM 失败: {err}")
            return False
            
        try:
            target = os.path.join(folder, newname)
            target = self.unique_path_item(target)
            os.rename(path, target)
            self.log_insert(f"成功重命名为: {os.path.basename(target)}")
            baseline.add(target)
            ignored.add(target)
            try:
                k = (os.path.getsize(target), int(os.path.getmtime(target)))
                seen_map[target] = k
            except: pass
            self.save_state()
            return True
        except Exception as e:
            self.log_insert(f"文件重命名操作失败: {e}")
            return False

    def unique_path_item(self, p):
        if not os.path.exists(p):
            return p
        d = os.path.dirname(p)
        fname = os.path.basename(p)
        base, ext = os.path.splitext(fname)
        
        # Check if it matches Order/Pay format (split by __)
        parts = base.split("__")
        if len(parts) >= 3:
            date = parts[0]
            item = parts[1]
            paid = "__".join(parts[2:])
            i = 1
            while True:
                candidate = f"{date}__{item}-{i}__{paid}{ext}"
                q = os.path.join(d, candidate)
                if not os.path.exists(q): return q
                i += 1
        
        # Fallback for Invoice or other formats
        i = 1
        while True:
            q = os.path.join(d, f"{base}_{i}{ext}")
            if not os.path.exists(q): return q
            i += 1

    def log_insert(self, s):
        ts = time.strftime("%H:%M:%S")
        msg = f"[{ts}] {s}\n"
        self.log_queue.put(msg)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(msg)
        except: pass

    def is_final_name(self, fname):
        base, ext = os.path.splitext(fname)
        
        # Check for Invoice format: YYYY-MM-DD-¥XX.XX
        # Regex: ^\d{4}-\d{2}-\d{2}-[¥A-Z]{1,3}\d+\.\d{2}$
        if re.match(r"^\d{4}-\d{2}-\d{2}-[¥A-Z]{1,3}\d+\.\d{2}$", base):
            return True

        # Check for Order/Pay format: YYYY-MM-DD__...__¥XX.XX
        parts = base.split("__")
        if len(parts) < 3:
            return False
        date = parts[0]
        paid = parts[-1]
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return False
        if not re.match(r"^(?:[A-Z]{3}|¥)\d+\.\d{2}$", paid):
            return False
        return True

    def load_state(self):
        try:
            if not os.path.exists(self.state_path): return
            with open(self.state_path, "r", encoding="utf-8") as f:
                j = json.load(f)
            folders = j.get("folders", {})
            
            def load_one(fpath, ign, sn):
                if not fpath: return
                d = folders.get(fpath, {})
                ign.clear()
                ign.update(d.get("ignored", []))
                sn.clear()
                for p, v in d.get("seen", {}).items():
                    sn[p] = tuple(v)
            
            load_one(self.folder, self.ignored, self.seen)
            load_one(self.pay_folder, self.pay_ignored, self.pay_seen)
            load_one(self.rep_folder, self.rep_ignored, self.rep_seen)
            
        except:
            self.ignored = set(); self.seen = {}
            self.pay_ignored = set(); self.pay_seen = {}
            self.rep_ignored = set(); self.rep_seen = {}

    def save_state(self):
        try:
            data = {}
            if os.path.exists(self.state_path):
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            folders = data.get("folders", {})
            
            def save_one(fpath, ign, sn):
                if not fpath: return
                folders[fpath] = {
                    "ignored": list(ign),
                    "seen": {p: list(v) for p, v in sn.items()},
                }
            
            save_one(self.folder, self.ignored, self.seen)
            save_one(self.pay_folder, self.pay_ignored, self.pay_seen)
            save_one(self.rep_folder, self.rep_ignored, self.rep_seen)
            
            data["folders"] = folders
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = OrderWatcherApp(root)
    root.mainloop()
