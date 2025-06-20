import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
import subprocess
import os
import time
from tkinter import ttk

class LivePocketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LivePocket URL Checker")
        self.csv_path = tk.StringVar()
        self.mode = tk.StringVar(value="normal")  # normal / tor / auto

        # ファイル選択
        tk.Label(root, text="CSVファイル:").pack(anchor='w')
        frame = tk.Frame(root)
        frame.pack(fill='x', padx=5)
        tk.Entry(frame, textvariable=self.csv_path, width=50).pack(side='left', fill='x', expand=True)
        tk.Button(frame, text="参照", command=self.select_csv).pack(side='left', padx=5)

        # モード選択
        tk.Label(root, text="実行モード:").pack(anchor='w', padx=5)
        mode_frame = tk.Frame(root)
        mode_frame.pack(anchor='w', padx=15)
        tk.Radiobutton(mode_frame, text="通常モード", variable=self.mode, value="normal").pack(anchor='w')
        tk.Radiobutton(mode_frame, text="Tor接続モード", variable=self.mode, value="tor").pack(anchor='w')
        tk.Radiobutton(mode_frame, text="自動切り替えモード", variable=self.mode, value="auto").pack(anchor='w')

        # 実行と停止
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="▶ スキャン実行", command=self.run_scan).pack(side='left', padx=10)
        tk.Button(button_frame, text="⏹ 停止", command=self.stop_scan).pack(side='left')

        # ログ出力
        self.log = scrolledtext.ScrolledText(root, height=20)
        self.log.pack(fill='both', expand=True, padx=5, pady=5)
        self.log.insert(tk.END, "LivePocket URL チェックツール\n")

        # ステータス
        self.status_label = tk.Label(root, text="🔲 待機中", anchor='w', fg='blue')
        self.status_label.pack(fill='x', padx=5, pady=(0, 2))

        # 実行時間
        self.time_label = tk.Label(root, text="実行時間: 0.0秒", anchor='w', fg='gray')
        self.time_label.pack(fill='x', padx=5, pady=(0, 2))

        # プログレスバー
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(fill='x', padx=5, pady=(0, 5))

        self.start_time = None
        self.timer_running = False
        self.process = None
        self.pause = False
        self.pause_log = False

    def select_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSVファイル", "*.csv")])
        if file_path:
            self.csv_path.set(file_path)

    def run_scan(self):
        csv_file = self.csv_path.get()
        if not os.path.exists(csv_file):
            self.log.insert(tk.END, "❌ CSVファイルが見つかりません\n")
            self.status_label.config(text="❌ CSVファイルが見つかりません", fg='red')
            return

        self.log.insert(tk.END, f"✅ スキャン開始: {csv_file}\n")
        self.status_label.config(text="⏳ 実行中...", fg='orange')
        self.start_time = time.time()
        self.timer_running = True
        self.update_timer()
        self.progress.start()

        threading.Thread(target=self.run_async_task, args=(csv_file, self.mode.get()), daemon=True).start()

    def stop_scan(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log.insert(tk.END, "⏹ スキャン停止しました\n")
            self.status_label.config(text="⏹ 停止", fg='red')
            self.timer_running = False
            self.progress.stop()
            if self.pause:
                self.resume_from_pause()  # 制限待機解除
    def update_timer(self):
        if self.timer_running:
            elapsed = time.time() - self.start_time
            self.time_label.config(text=f"実行時間: {elapsed:.1f}秒")
            self.root.after(500, self.update_timer)

    def resume_from_pause(self):
        self.status_label.config(text="⏳ 実行中...", fg='orange')
        self.progress.start()
        self.pause = False
        self.pause_log = False

    def run_async_task(self, csv_file, mode):
        script_path = os.path.abspath("Pokemon_LivePocket_URL_Checker.py")
        if not os.path.exists(script_path):
            self.log.insert(tk.END, f"❌ スクリプトが見つかりません\n")
            self.status_label.config(text="❌ スクリプトが見つかりません", fg='red')
            self.timer_running = False
            self.progress.stop()
            return

        try:
            args = ["python", script_path, "--csv", csv_file, "--mode", mode]

            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in self.process.stdout:
                if "[GUI_WAIT_300]" in line:
                    self.status_label.config(text="⏸ サイト制限待機中...", fg='purple')
                    self.progress.stop()
                    self.pause = True
                    self.pause_log = True
                    self.root.after(300000, self.resume_from_pause)
                    continue

                if not self.pause_log:
                    self.log.insert(tk.END, line)
                    self.log.see(tk.END)

                if "HIT" in line:
                    self.status_label.config(text="✨ HIT 検出", fg='green')
                    def revert_status():
                        current = self.status_label.cget("text")
                        if "完了" not in current and "停止" not in current and "エラー" not in current:
                            self.status_label.config(text="⏳ 実行中...", fg='orange')
                    self.root.after(5000, revert_status)

                elif "完了" in line:
                    self.status_label.config(text="✅ 完了", fg='green')

            self.process.wait()
            if self.process.returncode == 0:
                self.status_label.config(text="✅ スキャン完了", fg='green')
            else:
                self.status_label.config(text="❌ エラーが発生しました", fg='red')
        except Exception as e:
            self.log.insert(tk.END, f"❌ 実行エラー: {e}\n")
            self.status_label.config(text="❌ 実行失敗", fg='red')
        finally:
            if not self.pause:
                self.timer_running = False
                self.progress.stop()

if __name__ == '__main__':
    root = tk.Tk()
    app = LivePocketGUI(root)
    root.mainloop()
