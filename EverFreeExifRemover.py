import os
import threading
import locale
import sys
from tkinter import Button, Label, filedialog, messagebox, Toplevel
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image
import piexif

# 언어 설정 확인
system_language, _ = locale.getdefaultlocale()
is_korean = system_language and system_language.startswith('ko')

# 다국어 문자열
strings = {
    'title': "ever Free EXIF Remover" if is_korean else "ever Free EXIF Remover",
    'drag_instruction': "JPG 파일 또는 폴더를 드래그하거나 버튼을 클릭하세요." if is_korean else "Drag JPG files or folders, or click buttons.",
    'select_folder': "폴더 선택" if is_korean else "Select Folder",
    'select_file': "파일 선택" if is_korean else "Select Files",
    'progress_title': "진행 상황" if is_korean else "Progress",
    'processing': "처리 중..." if is_korean else "Processing...",
    'progress': "진행률: [{} / {}]" if is_korean else "Progress: [{} / {}]",
    'complete': "완료" if is_korean else "Complete",
    'complete_message': "{}개 파일의 메타데이터 처리가 완료되었습니다." if is_korean else "Metadata processing for {} files has been completed.",
    'notice': "알림" if is_korean else "Notice",
    'no_jpeg': "처리할 JPEG 파일을 찾지 못했습니다." if is_korean else "No JPEG files found to process."
}

def remove_metadata_except_orientation(file_path):
    try:
        image = Image.open(file_path)
        exif_dict = piexif.load(image.info['exif'])
        orientation = exif_dict['0th'].get(piexif.ImageIFD.Orientation, None)
        exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}}
        if orientation is not None:
            exif_dict['0th'][piexif.ImageIFD.Orientation] = orientation
        exif_bytes = piexif.dump(exif_dict)
        image.save(file_path, "jpeg", exif=exif_bytes)
        print(f"Processed: {file_path}")
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")

def process_files(file_paths):
    def count_jpg_files(path):
        if os.path.isdir(path):
            count = 0
            for root, dirs, files in os.walk(path):
                count += sum(1 for file in files if file.lower().endswith(('.jpg', '.jpeg')))
            return count
        elif os.path.isfile(path) and path.lower().endswith(('.jpg', '.jpeg')):
            return 1
        else:
            return 0

    total_files = sum(count_jpg_files(path) for path in file_paths)
    processed_files = []
    
    progress_window = Toplevel(root)
    progress_window.title(strings['progress_title'])
    progress_label = Label(progress_window, text=strings['processing'])
    progress_label.pack(pady=10)
    
    def update_progress(current, total):
        progress_label.config(text=strings['progress'].format(current, total))
        if current == total:
            progress_window.destroy()
            messagebox.showinfo(strings['complete'], strings['complete_message'].format(total))

    def process_thread():
        current = 0
        for path in file_paths:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg')):
                            full_path = os.path.join(root, file)
                            remove_metadata_except_orientation(full_path)
                            processed_files.append(full_path)
                            current += 1
                            progress_window.after(0, update_progress, current, total_files)
            elif os.path.isfile(path) and path.lower().endswith(('.jpg', '.jpeg')):
                remove_metadata_except_orientation(path)
                processed_files.append(path)
                current += 1
                progress_window.after(0, update_progress, current, total_files)
        
        if not processed_files:
            progress_window.destroy()
            messagebox.showinfo(strings['notice'], strings['no_jpeg'])

    threading.Thread(target=process_thread, daemon=True).start()

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        process_files([folder_path])

def select_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("JPEG files", "*.jpg;*.jpeg")])
    if file_paths:
        process_files(file_paths)

def drag_and_drop(event):
    file_paths = root.tk.splitlist(event.data)
    process_files(file_paths)

root = TkinterDnD.Tk()

#icon 설정
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
elif __file__:
    application_path = os.path.dirname(__file__)
icon_path = os.path.join(application_path, 'icon.ico')
root.iconbitmap(icon_path)

root.title(strings['title'])

label = Label(root, text=strings['drag_instruction'])
label.pack(pady=10)

folder_button = Button(root, text=strings['select_folder'], command=select_folder)
folder_button.pack(pady=5)

file_button = Button(root, text=strings['select_file'], command=select_files)
file_button.pack(pady=5)

root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', drag_and_drop)

root.mainloop()