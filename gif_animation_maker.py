import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import unicodedata
import json
import shutil

# 定数の定義
THUMBNAIL_SIZE = (28, 28)  # 画像のサムネイルサイズ

def generate_gif(delay_times, image_files, use_twitch_emotes):
    image_folder = 'images'

    if use_twitch_emotes:
        temp_dir = 'temp_images'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        resized_image_files = []
        for file_name in image_files:
            image_path = os.path.join(image_folder, file_name)
            img = Image.open(image_path)
            img = img.convert('RGBA')
            img = img.resize((112, 112), Image.LANCZOS)

            base_name = os.path.splitext(file_name)[0]
            temp_image_name = base_name + '.png'
            temp_image_path = os.path.join(temp_dir, temp_image_name)

            img.save(temp_image_path, format='PNG')
            resized_image_files.append(temp_image_name)

        processing_folder = temp_dir
        processing_files = resized_image_files
    else:
        processing_folder = image_folder
        processing_files = image_files

    frames = []
    for idx, file_name in enumerate(processing_files):
        image_path = os.path.join(processing_folder, file_name)
        img = Image.open(image_path).convert('RGBA')

        # アルファチャンネルの取得とマスク作成
        alpha = img.split()[3]
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)

        # パレットモードに変換（255色に減色）
        img_rgb = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)

        # マスク部分を255番目のパレット色に設定
        img_rgb.paste(255, mask)

        # フレーム情報の設定（disposal=2で背景色での塗りつぶし）
        img_rgb.info['disposal'] = 2
        img_rgb.info['duration'] = delay_times[idx]  # 遅延時間

        frames.append(img_rgb)

    # GIFの保存
    output_path = 'output.gif'
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        transparency=255,  # 透過色として255番目のパレットインデックスを指定
        background=255,    # 背景色として透明色を指定
        loop=0
    )

    # 遅延時間とファイル名を config.json に保存
    config_data = {}
    for idx, file_name in enumerate(image_files):
        config_data[file_name] = delay_times[idx]

    with open('config.json', 'w') as f:
        json.dump(config_data, f, indent=4)

    # 処理が終わったらテンポラリディレクトリを削除
    if use_twitch_emotes and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    messagebox.showinfo("完了", f"GIFアニメーションを '{output_path}' に保存しました。")

def main():
    # 画像フォルダの指定
    image_folder = 'images'
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    # 画像ファイルの取得とソート
    image_files = [f for f in os.listdir(image_folder)
                   if f.lower().endswith(('.png', '.bmp', '.gif'))]
    image_files.sort()

    if not image_files:
        messagebox.showerror("エラー", f"フォルダ '{image_folder}' に画像ファイルが見つかりません。")
        return

    # config.json から遅延時間を読み込む
    config_data = {}
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            config_data = json.load(f)

    # GUIの設定
    root = tk.Tk()
    root.title("GIF Generator Tool")

    # ウィンドウサイズの変更に追従するための設定
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    frame = ttk.Frame(root, padding=10)
    frame.grid(row=0, column=0, sticky="nsew")

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # キャンバスとスクロールバーの設定
    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # スクロール可能なフレームをキャンバスに配置
    scrollable_frame = ttk.Frame(canvas)

    # キャンバスにスクロール可能なフレームを配置し、そのIDを取得
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # スクロール領域を更新
    def on_scrollable_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_scrollable_frame_configure)

    # キャンバスサイズ変更時にフレームの幅を更新
    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind('<Configure>', on_canvas_configure)

    canvas.configure(yscrollcommand=scrollbar.set)

    # スクロール可能なフレーム内のレイアウト設定
    scrollable_frame.columnconfigure(0, weight=0)
    scrollable_frame.columnconfigure(1, weight=1)
    scrollable_frame.columnconfigure(2, weight=0)

    # GUI要素の作成
    ttk.Label(scrollable_frame, text="各フレームの遅延時間をミリ秒で入力してください。") \
        .grid(row=0, column=0, columnspan=3, sticky="w")

    delay_entries = []
    image_thumbnails = []

    for idx, file_name in enumerate(image_files):
        # 画像の読み込みとリサイズ
        image_path = os.path.join(image_folder, file_name)
        img = Image.open(image_path)
        img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        image_thumbnails.append(img_tk)  # 参照を保持

        # 画像の表示
        image_label = ttk.Label(scrollable_frame, image=img_tk)
        image_label.grid(row=idx+1, column=0, sticky="w")

        # ファイル名の表示
        ttk.Label(scrollable_frame, text=file_name).grid(row=idx+1, column=1, sticky="w")

        # 遅延時間の入力
        default_delay = config_data.get(file_name, 100)
        delay_var = tk.StringVar(value=str(default_delay))
        entry = ttk.Entry(scrollable_frame, textvariable=delay_var, width=10)
        entry.grid(row=idx+1, column=2, sticky="e")
        delay_entries.append(delay_var)

    # Twitchエモート用のチェックボックスを追加（デフォルトはFalse）
    use_twitch_emotes = tk.BooleanVar(value=False)
    ttk.Checkbutton(scrollable_frame, text="Twitchエモート用",
                    variable=use_twitch_emotes).grid(row=len(image_files)+1, column=0, columnspan=3, sticky="w")

    # GIF生成ボタン
    generate_button = ttk.Button(scrollable_frame, text="GIFを生成", command=lambda: on_generate())
    generate_button.grid(row=len(image_files)+2, column=0, columnspan=3, pady=10)

    def on_generate():
        try:
            delay_times = []
            for var in delay_entries:
                value = var.get().strip()
                if not value:
                    raise ValueError("遅延時間が入力されていません。")
                # 全角数字を半角に変換
                value = unicodedata.normalize('NFKC', value)
                delay_times.append(int(value))
            generate_gif(delay_times, image_files, use_twitch_emotes.get())
        except ValueError as e:
            messagebox.showerror("エラー", f"遅延時間には整数を入力してください。\n詳細: {e}")

    root.mainloop()

if __name__ == "__main__":
    main()
