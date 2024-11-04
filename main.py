import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import os


class ImageMarkerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Marker")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.image = None
        self.photo = None
        self.circles = []
        self.current_image_path = None

        self.setup_ui()

    def setup_ui(self):
        # 버튼 프레임
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        button_frame.grid_columnconfigure(3, weight=1)

        # 버튼들
        load_btn = tk.Button(button_frame, text="Load Image", command=self.load_image)
        undo_btn = tk.Button(button_frame, text="Undo", command=self.undo_last_circle)
        export_btn = tk.Button(button_frame, text="Export", command=self.export_coordinates)

        load_btn.grid(row=0, column=0, padx=5)
        undo_btn.grid(row=0, column=1, padx=5)
        export_btn.grid(row=0, column=2, padx=5)

        self.status_label = tk.Label(button_frame, text="No image loaded", anchor='e')
        self.status_label.grid(row=0, column=3, sticky='e', padx=5)

        # 이미지 캔버스 프레임
        canvas_frame = tk.Frame(self.root)
        canvas_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # 이미지 캔버스
        self.canvas = tk.Canvas(canvas_frame, bg='white', width=800, height=600)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.bind("<Button-1>", self.add_circle)
        self.canvas.bind("<Configure>", self.on_canvas_resize)  # 캔버스 크기 변경 이벤트 바인딩

        # 스크롤바
        scrollbar_y = tk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        scrollbar_x = tk.Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)

        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')

    def on_canvas_resize(self, event):
        if self.current_image_path:
            self.display_image()

    def calculate_image_size(self, image, canvas_width, canvas_height):
        # 원본 이미지 크기
        img_width, img_height = image.size

        # 이미지와 캔버스의 가로세로 비율 계산
        canvas_ratio = canvas_width / canvas_height
        image_ratio = img_width / img_height

        if image_ratio > canvas_ratio:
            # 이미지가 더 와이드한 경우
            new_width = canvas_width
            new_height = int(canvas_width / image_ratio)
        else:
            # 이미지가 더 길쭉한 경우
            new_height = canvas_height
            new_width = int(canvas_height * image_ratio)

        return new_width, new_height

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            self.current_image_path = file_path
            self.circles = []
            self.display_image()
            self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")

    def display_image(self):
        if not self.current_image_path:
            return

        # 원본 이미지 로드 및 크기 저장
        image = Image.open(self.current_image_path)
        self.original_image_size = image.size

        # 캔버스의 현재 크기 얻기
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 새 이미지 크기 계산
        new_width, new_height = self.calculate_image_size(image, canvas_width, canvas_height)

        # 이미지 크기 조정
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.image = resized_image
        self.photo = ImageTk.PhotoImage(resized_image)

        # 이미지 크기 비율 계산
        self.scale_x = new_width / self.original_image_size[0]
        self.scale_y = new_height / self.original_image_size[1]

        # 캔버스 초기화 및 이미지 표시
        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            image=self.photo,
            anchor=tk.CENTER
        )

        # 이미지 경계 저장
        self.image_bbox = self.canvas.bbox(self.image_id)

        # 스크롤 영역 설정
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # 모든 원 그리기
        self.draw_circles()

    def draw_circles(self):
        if not self.image or not hasattr(self, 'image_bbox'):
            return

        # 이미지 경계 가져오기
        ix1, iy1, ix2, iy2 = self.image_bbox

        # 모든 원 지우기 (이미지 제외)
        for item in self.canvas.find_all():
            if item != self.image_id:
                self.canvas.delete(item)

        # 원 그리기
        for x, y in self.circles:
            # 원본 좌표를 현재 이미지 크기에 맞게 조정
            canvas_x = ix1 + (x * self.scale_x)
            canvas_y = iy1 + (y * self.scale_y)

            self.canvas.create_oval(
                canvas_x - 5, canvas_y - 5,
                canvas_x + 5, canvas_y + 5,
                outline="red",
                width=2
            )

    def add_circle(self, event):
        if not self.image or not hasattr(self, 'image_bbox'):
            return

        # 캔버스의 스크롤 위치 고려
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # 이미지 경계 가져오기
        ix1, iy1, ix2, iy2 = self.image_bbox

        # 클릭이 이미지 영역 내부인지 확인
        if ix1 <= x <= ix2 and iy1 <= y <= iy2:
            # 캔버스 좌표를 원본 이미지 좌표로 변환
            original_x = int((x - ix1) / self.scale_x)
            original_y = int((y - iy1) / self.scale_y)

            # 좌표 저장 및 원 그리기
            self.circles.append((original_x, original_y))
            self.draw_circles()
            self.status_label.config(text=f"Added circle at ({original_x}, {original_y})")

    def undo_last_circle(self):
        if self.circles:
            x, y = self.circles.pop()
            self.draw_circles()
            self.status_label.config(text=f"Removed circle at ({x}, {y})")

    def export_coordinates(self):
        if self.circles:
            with open("output.txt", "w") as f:
                for i, (x, y) in enumerate(self.circles, 1):
                    f.write(f"Circle {i}: ({x}, {y})\n")
            self.status_label.config(text="Coordinates exported to output.txt")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageMarkerApp(root)
    root.mainloop()