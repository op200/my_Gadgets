import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk
import numpy as np
# from math import floor

from threading import Thread

import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'
import webbrowser
def hyperlink_jump(hyperlink:str):
    webbrowser.open(hyperlink)
import shutil
import subprocess

PROGRAM_NAME = "生成GIF"
VERSION = "0.1.1"
HOME_LINK = "https://github.com/op200/my_Gadgets"

#日志
class log:
    num = 0
    
    @staticmethod
    def output(info:str):
        log_Text.insert(tk.END,info+'\n')
        log_Text.see(tk.END)
        print(info)

    @staticmethod
    def error(info:str):
        log.output(f"[ERROR] {info}")

    @staticmethod
    def warning(info:str):
        log.output(f"[WARNING] {info}")

    @staticmethod
    def info(info:str):
        log.output(f"[INFO] {info}")


import platform
#判断系统对应路径
os_type = platform.system()
if os_type == 'Windows':
    config_dir = os.path.join(os.getenv('APPDATA'), '生成GIF')
elif os_type == 'Linux' or os_type == 'Darwin':
    config_dir = os.path.join(os.path.expanduser('~'), '.config', '生成GIF')
else:
    config_dir = ""
    log.warning("无法确认系统")

os.makedirs(config_dir, exist_ok=True)

ocr_choice:int = 1

import configparser
#不存在配置则写入默认配置
config = configparser.ConfigParser()
config_file_pathname = os.path.join(config_dir, 'config.ini')
if not os.path.exists(config_file_pathname) or config.read(config_file_pathname) and config.get("DEFAULT","version")!=VERSION:
    config["DEFAULT"] = {
        "version" : VERSION,
        "output_path" : r".\output.gif",

        "is_scale" : 0,
        "scale_width" : 0,
        "scale_height" : 0,

        "is_change_fps" : 0,
        "new_fps" : 6,

        "is_change_PTS" : 0,
        "new_PTS" : 1
    }
    with open(config_file_pathname, 'w') as config_file:
        config.write(config_file)


def save_config():
    config["DEFAULT"]["output_path"] = set_outPath_Entry.get()

    config["DEFAULT"]["is_scale"] = str(1 if set_outScale_Tkbool.get() else 0)
    config["DEFAULT"]["scale_width"] = set_outScale_width_Entry.get()
    config["DEFAULT"]["scale_height"] = set_outScale_height_Entry.get()

    # config["DEFAULT"]["is_change_fps"] = str(1 if set_outFPS_Tkbool.get() else 0)
    config["DEFAULT"]["new_fps"] = set_outFPS_Entry.get()

    config["DEFAULT"]["is_change_PTS"] = str(1 if set_outPTS_Tkbool.get() else 0)
    config["DEFAULT"]["new_PTS"] = set_outPTS_Entry.get()
    
    try:
        with open(config_file_pathname, 'w') as configfile:
            config.write(configfile)
    except FileNotFoundError:
        pass



input_path:str
scale, frame_height, frame_width, new_frame_height, new_frame_width = False, int,int,int,int
right_x,right_y,left_x,left_y = 0,0,0,0
fps:int
difference_list:list
VIDEO_FRAME_IMG_HEIGHT = 6


root_Tk = tk.Tk()
root_Tk.title(PROGRAM_NAME)
def root_Tk_Close():
    save_config()
    root_Tk.destroy()
root_Tk.protocol("WM_DELETE_WINDOW", root_Tk_Close)


#样式
from tkinter import font as tkfont
TkDefaultFont = tkfont.nametofont("TkDefaultFont").actual()['family']
underline_font = tkfont.Font(family=TkDefaultFont, size=tkfont.nametofont("TkDefaultFont").actual()['size'], underline=True)


#菜单
menu_Menu = tk.Menu(root_Tk)

menu_setting_Menu = tk.Menu(menu_Menu, tearoff=0)

def open_temp():
    log.info("'打开缓存位置'功能暂时未做")

def remove_config_dir():
    if os.path.exists(config_dir):
        shutil.rmtree(config_dir)
        log.info("已删除"+config_dir)
    else:
        log.error("未找到配置文件目录"+config_dir)

menu_Menu.add_cascade(label="设置",menu=menu_setting_Menu)
menu_setting_Menu.add_command(label="打开缓存位置", command=open_temp)
def remove_config_dir():
    if os.path.exists(config_dir):
        shutil.rmtree(config_dir)
        log.info("已删除"+config_dir)
    else:
        log.error("未找到配置文件目录"+config_dir)
menu_setting_Menu.add_command(label="清除配置文件", command=remove_config_dir)


def create_help_about_Toplevel():
    about_Toplevel = tk.Toplevel(root_Tk,width=20,height=15)
    about_Toplevel.geometry('320x160')
    about_Toplevel.title("About")
    frame = ttk.Frame(about_Toplevel)
    frame.pack(expand=True)
    ttk.Label(frame,text=f"{PROGRAM_NAME}  v{VERSION}\n\n").pack()

    hyperlink_Label = ttk.Label(frame,text=HOME_LINK, cursor="hand2", foreground="blue", font=underline_font)
    hyperlink_Label.bind("<Button-1>",lambda _:hyperlink_jump(HOME_LINK))
    hyperlink_Label.pack()
    
menu_help_Menu = tk.Menu(menu_Menu, tearoff=0)
menu_help_Menu.add_command(label="关于",command=create_help_about_Toplevel)
menu_Menu.add_cascade(label="帮助",menu=menu_help_Menu)


root_Tk.config(menu=menu_Menu)

#左侧控件
left_Frame = ttk.Frame(root_Tk, cursor="tcross")
left_Frame.grid(row=0,column=0,padx=5,pady=5)
#右侧控件
right_Frame = ttk.Frame(root_Tk)
right_Frame.grid(row=0,column=1,padx=5,pady=5)


#左侧控件

#视频预览控件
video_review_Label = ttk.Label(left_Frame, cursor="target")

#进度条控件
video_Progressbar = ttk.Progressbar(left_Frame)


def draw_video_frame_Label_frameColor(frame_num:int, color:tuple[int,int,int]):
    global video_frame_img
    x = round(new_frame_width*frame_num/(frame_count-1))-1
    if x<0:
        x=0
    video_frame_img[:VIDEO_FRAME_IMG_HEIGHT-1, x] = color

def flush_video_frame_Label():
    photo = ImageTk.PhotoImage(Image.fromarray(video_frame_img))
    video_frame_Label.config(image=photo)
    video_frame_Label.image = photo

def draw_video_frame_Label_range(start_frame:int, end_frame:int, color:tuple[int,int,int]):
    global video_frame_img
    video_frame_img[-1,:,:]=0
    video_frame_img[-1, max(round(new_frame_width*start_frame/(frame_count-1))-1, 0):max(round(new_frame_width*end_frame/(frame_count-1))-1, 0) + 1] = color


video_frame_Label = ttk.Label(left_Frame)

frame_count = 0
frame_now = 0

#跳转当前帧
def jump_to_frame():
    global scale,frame_now,frame_count
    main_rendering_Cap.set(cv2.CAP_PROP_POS_FRAMES,frame_now)
    _, frame = main_rendering_Cap.read()
    try:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    except cv2.error:
        log.warning(f"[{frame_now}]该帧无法读取(应检查视频封装)")
    else:
        #重新绘制选框
        if scale:
            frame = cv2.resize(frame,(new_frame_width,new_frame_height))
        cv2.rectangle(frame,(right_x, right_y, left_x-right_x, left_y-right_y), color=(0,255,255),thickness=1)

        
        video_Progressbar["value"] = frame_now/(frame_count-1)*100
        
        photo = ImageTk.PhotoImage(Image.fromarray(frame))
        video_review_Label.config(image=photo)
        video_review_Label.image = photo

        #set frame_now
        frame_now_Tkint.set(frame_now)

#进度条的滚轮事件
def video_progressbar_mousewheel(event):
    global frame_now,frame_count
    frame_now += (1 if event.delta<0 else -1)
    if frame_now<0:
        frame_now=0
    if frame_now>=frame_count:
        frame_now=frame_count-1
    
    jump_to_frame()
video_review_Label.bind("<MouseWheel>", video_progressbar_mousewheel)
video_Progressbar.bind("<MouseWheel>", video_progressbar_mousewheel)
video_frame_Label.bind("<MouseWheel>", video_progressbar_mousewheel)

#进度条鼠标点击事件
def video_progressbar_leftDrag(event):
    ratio = event.x / video_Progressbar.winfo_width()
    if ratio>1:
        ratio=1
    if ratio<0:
        ratio=0
    # video_Progressbar["value"] = ratio*100
    global frame_now,frame_count
    frame_now = int((frame_count-1)*ratio)
    jump_to_frame()
video_Progressbar.bind("<B1-Motion>", video_progressbar_leftDrag)
video_Progressbar.bind("<Button-1>", video_progressbar_leftDrag)
video_frame_Label.bind("<B1-Motion>", video_progressbar_leftDrag)
video_frame_Label.bind("<Button-1>", video_progressbar_leftDrag)

#输入路径 初始化
def submit_path(_):
    set_outScale_Checkbutton_Click()
    # set_outFPS_Checkbutton_Click()
    set_outPTS_Checkbutton_Click()

    global input_path,scale,main_rendering_Cap,sec_rendering_Cap,frame_count,frame_height,frame_width,new_frame_height,new_frame_width,fps,difference_list,frame_now
    input_path = input_video_Entry.get()
    #渲染控件
    frame_num_Frame.grid(row=2,column=0)

    draw_box_frame.grid(row=4,column=0,pady=15)
    createGIF_set_Frame.grid(row=7,column=0,pady=15)

    output_setup_frame.grid(row=5,column=0)

    # set_ocr_Frame.grid(row=1,column=0,pady=10)
    
    log_Frame.grid(row=8,column=0,pady=10)

    sec_rendering_Cap = cv2.VideoCapture(input_path)
    main_rendering_Cap = cv2.VideoCapture(input_path)
    main_rendering_Cap.set(cv2.CAP_PROP_POS_FRAMES,0)
    ret, frame = main_rendering_Cap.read()
    if ret:
        #获取尺寸 判断缩放
        frame_height, frame_width, _ = frame.shape
        video_size_Label.config(text=str(frame_width)+" x "+str(frame_height))
        fps = main_rendering_Cap.get(cv2.CAP_PROP_FPS)
        video_fps_Label.config(text=str(fps)+" FPS")
        video_size_Label.grid(row=0,column=0)
        video_fps_Label.grid(row=0,column=1,padx=8)
        if frame_height > root_Tk.winfo_screenheight()*5/6 or frame_width > root_Tk.winfo_screenwidth()*4/5:
            scale = max((1.2*frame_height+100)/root_Tk.winfo_screenheight(), (1.2*frame_width+500)/root_Tk.winfo_screenwidth(), 1.5)
            new_frame_width,new_frame_height = int(frame_width/scale),int(frame_height/scale)
            frame = cv2.resize(frame,(new_frame_width,new_frame_height))
            log.info(f"视频画幅过大 预览画面已缩小(1/{scale:.2f}-->{new_frame_width}x{new_frame_height})")
        else:
            new_frame_width,new_frame_height = frame_width,frame_height
            scale = False

        #重写进度条
        video_review_Label.grid(row=0,column=0,pady=5)

        video_Progressbar.config(length=new_frame_width)
        video_Progressbar.grid(row=2,column=0)


        #渲染进度
        frame_now = 0
        jump_to_frame()

        #初始化右侧控件
        frame_count = int(main_rendering_Cap.get(cv2.CAP_PROP_FRAME_COUNT))
        difference_list = [-1]*frame_count#初始化差值表
        frame_count_Label.config(text = f" / {frame_count-1:9d}")
        frame_now_Tkint.set(0)
        video_path_review_text = input_video_Entry.get()
        if len(video_path_review_text)>49:
            video_path_review_text = video_path_review_text[0:49]+"\n"+video_path_review_text[49:]
        if len(video_path_review_text)>99:
            video_path_review_text = video_path_review_text[0:99]+"\n"+video_path_review_text[99:]
        if len(video_path_review_text)>149:
            video_path_review_text = video_path_review_text[0:149]+"\n"+video_path_review_text[149:]
        video_path_review_Label.config(text=video_path_review_text)


        #绘制进度条的帧提示
        global video_frame_img
        video_frame_img = np.ones((VIDEO_FRAME_IMG_HEIGHT,new_frame_width,3), np.uint8) * 224
        video_frame_img[-1,:,:] = 1
        for frame_num in range(0,frame_count):
            draw_video_frame_Label_frameColor(frame_num, (0,0,0))
        flush_video_frame_Label()

        video_frame_Label.grid(row=3,column=0)

    else:
        log.error("无法打开"+input_path)
    
    root_Tk.focus_set()

#右侧控件

#路径输入
input_video_Frame = ttk.Frame(right_Frame)
input_video_Frame.grid(row=1,column=0,pady=15)

video_path_review_Label = ttk.Label(input_video_Frame,text="输入视频路径名")
video_path_review_Label.grid(row=1,column=0,columnspan=2,pady=8)

input_video_Entry = ttk.Entry(input_video_Frame,width=40)
input_video_Entry.grid(row=2,column=0)
input_video_Entry.focus_set()

input_video_Entry.bind("<Return>", submit_path)
                
input_video_Button = ttk.Button(input_video_Frame, text="提交", width=4, command=lambda:submit_path(None))
input_video_Button.grid(row=2,column=1,padx=5)

#帧数
frame_num_Frame = ttk.Frame(right_Frame)

def enter_to_change_frame_now(_):
    global frame_now,frame_count

    frame_now = int(frame_now_Entry.get())
    if frame_now<0:
        frame_now=0
    if frame_now>=frame_count:
        frame_now=frame_count-1

    jump_to_frame()
    root_Tk.focus_set()

frame_now_Frame = ttk.Frame(frame_num_Frame)
frame_now_Frame.grid(row=0,column=0)

frame_now_Tkint = tk.IntVar()
frame_now_Entry = ttk.Entry(frame_now_Frame,textvariable=frame_now_Tkint,width=5)
frame_now_Entry.bind("<Return>", enter_to_change_frame_now)
frame_now_Entry.grid(row=0,column=0)

frame_count_Label = ttk.Label(frame_now_Frame,text=" / NULL")
frame_count_Label.grid(row=0,column=1)

#帧数区间
frame_range_Frame = ttk.Frame(frame_num_Frame)
frame_range_Frame.grid(row=1,column=0)

def set_start_frame_num_Click(frame1_Tkint:tk.IntVar, frame2_Tkint:tk.IntVar, flush_frame_now:int=None):
    if flush_frame_now:
        global frame_now
        frame_now = flush_frame_now
        jump_to_frame()

    frame1_Tkint.set(frame_now_Tkint.get())
    if start_frame_num_Tkint.get() > end_frame_num_Tkint.get():
        frame2_Tkint.set(frame1_Tkint.get())
    draw_video_frame_Label_range(start_frame_num_Tkint.get(),end_frame_num_Tkint.get(),(228,12,109))
    flush_video_frame_Label()

start_frame_num_Tkint = tk.IntVar()
start_frame_num_Entry = ttk.Entry(frame_range_Frame,width=11,textvariable=start_frame_num_Tkint)
start_frame_num_Entry.bind("<Return>", lambda _:set_start_frame_num_Click(start_frame_num_Tkint,end_frame_num_Tkint,start_frame_num_Tkint.get()))
set_start_frame_num_Button = ttk.Button(frame_range_Frame,text="设为开始帧",command=lambda:set_start_frame_num_Click(start_frame_num_Tkint,end_frame_num_Tkint))
start_frame_num_Entry.grid(row=0,column=0,padx=14,pady=5)
set_start_frame_num_Button.grid(row=1,column=0)

end_frame_num_Tkint = tk.IntVar()
end_frame_num_Entry = ttk.Entry(frame_range_Frame,width=11,textvariable=end_frame_num_Tkint)
end_frame_num_Entry.bind("<Return>", lambda _:set_start_frame_num_Click(end_frame_num_Tkint,start_frame_num_Tkint,end_frame_num_Tkint.get()))
set_end_frame_num_Button = ttk.Button(frame_range_Frame,text="设为结束帧",command=lambda:set_start_frame_num_Click(end_frame_num_Tkint,start_frame_num_Tkint))
end_frame_num_Entry.grid(row=0,column=1,padx=14)
set_end_frame_num_Button.grid(row=1,column=1)

#视频信息
video_info_Frame = ttk.Frame(right_Frame)
video_info_Frame.grid(row=3,column=0,pady=10)

video_size_Label = ttk.Label(video_info_Frame)
video_fps_Label = ttk.Label(video_info_Frame)

#选框位置
draw_box_frame = ttk.Frame(right_Frame)

left_x_text,left_y_text,right_x_text,right_y_text = tk.IntVar(),tk.IntVar(),tk.IntVar(),tk.IntVar()

draw_box_left_x,draw_box_left_y = ttk.Entry(draw_box_frame,textvariable=left_x_text,width=5),ttk.Entry(draw_box_frame,textvariable=left_y_text,width=5)
draw_box_right_x,draw_box_right_y = ttk.Entry(draw_box_frame,textvariable=right_x_text,width=5),ttk.Entry(draw_box_frame,textvariable=right_y_text,width=5)
draw_box_left_x.grid(row=0,column=0,padx=15)
draw_box_left_y.grid(row=0,column=1,padx=15)
draw_box_right_x.grid(row=0,column=2,padx=15)
draw_box_right_y.grid(row=0,column=3,padx=15)

def enter_to_change_draw_box(_):
    global scale,right_x,right_y,left_x,left_y,difference_list
    
    difference_list = [-1]*frame_count

    if left_x_text.get() < 0:
        left_x_text.set(0)
    if left_y_text.get() < 0:
        left_y_text.set(0)
    if right_x_text.get() >= frame_width:
        right_x_text.set(frame_width)
    if right_y_text.get() >= frame_height:
        right_y_text.set(frame_height)

    if scale:
        right_x = int(left_x_text.get()*new_frame_width/frame_width)
        right_y = int(left_y_text.get()*new_frame_width/frame_width)
        left_x = int(right_x_text.get()*new_frame_width/frame_width)
        left_y = int(right_y_text.get()*new_frame_width/frame_width)
    else:
        right_x = left_x_text.get()
        right_y = left_y_text.get()
        left_x = right_x_text.get()
        left_y = right_y_text.get()
    
    main_rendering_Cap.set(cv2.CAP_PROP_POS_FRAMES,frame_now)
    _, frame = main_rendering_Cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if scale:
        frame = cv2.resize(frame,(new_frame_width,new_frame_height))
    cv2.rectangle(frame,(right_x, right_y, left_x-right_x, left_y-right_y), color=(0,255,255),thickness=1)
    photo = ImageTk.PhotoImage(Image.fromarray(frame))
    video_review_Label.config(image=photo)
    video_review_Label.image = photo
    root_Tk.focus_set()

draw_box_left_x.bind("<Return>", enter_to_change_draw_box)
draw_box_left_y.bind("<Return>", enter_to_change_draw_box)
draw_box_right_x.bind("<Return>", enter_to_change_draw_box)
draw_box_right_y.bind("<Return>", enter_to_change_draw_box)

#输出相关控件
output_setup_frame = ttk.Frame(right_Frame)

set_outPath_Frame = ttk.Frame(output_setup_frame)
set_outPath_Frame.grid(row=0,column=0,pady=10)

set_outPath_Label = ttk.Label(set_outPath_Frame,text="输出位置:")
set_outPath_Label.grid(row=0,column=0)

set_outPath_Entry = ttk.Entry(set_outPath_Frame)
set_outPath_Entry.insert(0,config.get("DEFAULT","output_path"))
set_outPath_Entry.grid(row=0,column=1)


#缩放
set_outScale_Frame = ttk.Frame(output_setup_frame)
set_outScale_Frame.grid(row=1,pady=10)

set_outScale_weight_Label = ttk.Label(set_outScale_Frame,text="宽:")
set_outScale_weight_Label.grid(row=0,column=0)

set_outScale_width_Entry = ttk.Entry(set_outScale_Frame,width=4)
set_outScale_width_Entry.insert(0,config.get("DEFAULT","scale_width"))
set_outScale_width_Entry.grid(row=0,column=1)

ttk.Frame(set_outScale_Frame).grid(row=0,column=2,padx=10)

set_outScale_height_Label = ttk.Label(set_outScale_Frame,text="高:")
set_outScale_height_Label.grid(row=0,column=3)

set_outScale_height_Entry = ttk.Entry(set_outScale_Frame,width=4)
set_outScale_height_Entry.insert(0,config.get("DEFAULT","scale_height"))
set_outScale_height_Entry.grid(row=0,column=4)

def set_outScale_Checkbutton_Click():
    if set_outScale_Tkbool.get():
        set_outScale_width_Entry.config(state=tk.NORMAL)
        set_outScale_height_Entry.config(state=tk.NORMAL)
    else:
        set_outScale_width_Entry.config(state=tk.DISABLED)
        set_outScale_height_Entry.config(state=tk.DISABLED)
set_outScale_Tkbool = tk.BooleanVar()
set_outScale_Tkbool.set(bool(int(config.get("DEFAULT","is_scale"))))
set_outScale_Checkbutton = ttk.Checkbutton(set_outScale_Frame,text="重缩放",var=set_outScale_Tkbool,command=set_outScale_Checkbutton_Click)
set_outScale_Checkbutton.grid(row=0,column=5,padx=15)


#帧率
set_outFPS_Frame = ttk.Frame(output_setup_frame)
set_outFPS_Frame.grid(row=2,pady=10)

set_outFPS_Label = ttk.Label(set_outFPS_Frame,text="输出帧率:      ")
set_outFPS_Label.grid(row=0,column=0)

set_outFPS_Entry = ttk.Entry(set_outFPS_Frame,width=14)
set_outFPS_Entry.insert(0,config.get("DEFAULT","new_fps"))
set_outFPS_Entry.grid(row=0,column=1)


#PTS
set_outPTS_Frame = ttk.Frame(output_setup_frame)
set_outPTS_Frame.grid(row=3,pady=10)

set_outPTS_Entry = ttk.Entry(set_outPTS_Frame,width=16)
set_outPTS_Entry.insert(0,config.get("DEFAULT","new_PTS"))
set_outPTS_Entry.grid(row=0,column=0)

def set_outPTS_Checkbutton_Click():
    if set_outPTS_Tkbool.get():
        set_outPTS_Entry.config(state=tk.NORMAL)
    else:
        set_outPTS_Entry.config(state=tk.DISABLED)
set_outPTS_Tkbool = tk.BooleanVar()
set_outPTS_Tkbool.set(bool(int(config.get("DEFAULT","is_change_PTS"))))
set_outPTS_Checkbutton = ttk.Checkbutton(set_outPTS_Frame,text="重设PTS倍率",var=set_outPTS_Tkbool,command=set_outPTS_Checkbutton_Click)
set_outPTS_Checkbutton.grid(row=0,column=5,padx=15)


createGIF_set_Frame = ttk.Frame(right_Frame)


start_createGIF_Frame = tk.Frame(createGIF_set_Frame)
start_createGIF_Frame.grid(row=1,column=0,pady=15)

start_createGIF_Button = ttk.Button(start_createGIF_Frame,text="生成GIF")
start_createGIF_Button.grid(row=0,column=0,padx=15)



log_Frame = ttk.Frame(right_Frame)

log_vScrollbar = ttk.Scrollbar(log_Frame)
log_vScrollbar.grid(row=0,column=1,sticky='ns')

log_Text = tk.Text(log_Frame,width=45,height=10, yscrollcommand=log_vScrollbar.set)
log_Text.grid(row=0,column=0,sticky='nsew')


log_vScrollbar.config(command=log_Text.yview)
#读取配置
config.read(config_file_pathname)
# if config.get("DEFAULT","") == "":



#选框
start_x,start_y,end_x,end_y = 0,0,0,0

def draw_box():
    global scale,frame_now,start_x,start_y,end_x,end_y,right_x,right_y,left_x,left_y
    main_rendering_Cap.set(cv2.CAP_PROP_POS_FRAMES,frame_now)
    _, frame = main_rendering_Cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    right_x = min(start_x,end_x)
    right_y = min(start_y,end_y)
    left_x = max(start_x,end_x)
    left_y = max(start_y,end_y)

    if right_x < 0:
        right_x = 0
    if right_y < 0:
        right_y = 0
    if left_x >= video_review_Label.winfo_width()-4:
        left_x = video_review_Label.winfo_width()-4
    if left_y >= video_review_Label.winfo_height()-4:
        left_y = video_review_Label.winfo_height()-4
    if scale:
        frame = cv2.resize(frame,(new_frame_width,new_frame_height))
    cv2.rectangle(frame,(right_x, right_y, left_x-right_x, left_y-right_y), color=(0,255,255),thickness=1)

    if scale:
        left_x_text.set(int(right_x*frame_width/new_frame_width))
        left_y_text.set(int(right_y*frame_width/new_frame_width))
        right_x_text.set(int(left_x*frame_width/new_frame_width))
        right_y_text.set(int(left_y*frame_width/new_frame_width))
    else:
        left_x_text.set(right_x)
        left_y_text.set(right_y)
        right_x_text.set(left_x)
        right_y_text.set(left_y)

    photo = ImageTk.PhotoImage(Image.fromarray(frame))
    video_review_Label.config(image=photo)
    video_review_Label.image = photo

def draw_video_review_MouseDown(event):
    global start_x, start_y
    start_x,start_y = event.x, event.y
video_review_Label.bind("<Button-1>", draw_video_review_MouseDown)

def draw_video_review_MouseDrag(event):
    global end_x, end_y
    end_x,end_y = event.x, event.y
    draw_box()
video_review_Label.bind("<B1-Motion>", draw_video_review_MouseDrag)




    

def start_to_ready():
    global end_all_thread,difference_list
    end_all_thread=False

    difference_list = [-1]*frame_count

    save_config()

    input_video_Entry.config(state=tk.DISABLED)
    input_video_Button.config(state=tk.DISABLED)
    frame_now_Entry.config(state=tk.DISABLED)
    draw_box_left_x.config(state=tk.DISABLED)
    draw_box_left_y.config(state=tk.DISABLED)
    draw_box_right_x.config(state=tk.DISABLED)
    draw_box_right_y.config(state=tk.DISABLED)

    set_outPath_Entry.config(state=tk.DISABLED)

    start_frame_num_Entry.config(state=tk.DISABLED)
    set_start_frame_num_Button.config(state=tk.DISABLED)
    end_frame_num_Entry.config(state=tk.DISABLED)
    set_end_frame_num_Button.config(state=tk.DISABLED)

    set_outScale_width_Entry.config(state=tk.DISABLED)
    set_outScale_height_Entry.config(state=tk.DISABLED)
    set_outScale_Checkbutton.config(state=tk.DISABLED)
    set_outFPS_Entry.config(state=tk.DISABLED)
    # set_outFPS_Checkbutton.config(state=tk.DISABLED)
    set_outPTS_Entry.config(state=tk.DISABLED)
    set_outPTS_Checkbutton.config(state=tk.DISABLED)


    start_createGIF_Button.config(text="终止",command=cancel_encoding)

    
    video_review_Label.unbind("<MouseWheel>")
    video_review_Label.unbind("<B1-Motion>")
    video_review_Label.unbind("<Button-1>")

    video_Progressbar.unbind("<MouseWheel>")
    video_Progressbar.unbind("<B1-Motion>")
    video_Progressbar.unbind("<Button-1>")

    video_frame_Label.unbind("<MouseWheel>")
    video_frame_Label.unbind("<B1-Motion>")
    video_frame_Label.unbind("<Button-1>")

    start_encoding()



def end_to_ready():
    global ocr_reader,srt,is_Listener_threshold_value_Entry,frame_now,end_all_thread

    end_all_thread=True
    frame_now=end_num#关闭阈值检测和绘制线程
    is_Listener_threshold_value_Entry=False#关闭监听

    input_video_Entry.config(state=tk.NORMAL)
    input_video_Button.config(state=tk.NORMAL)
    frame_now_Entry.config(state=tk.NORMAL)
    draw_box_left_x.config(state=tk.NORMAL)
    draw_box_left_y.config(state=tk.NORMAL)
    draw_box_right_x.config(state=tk.NORMAL)
    draw_box_right_y.config(state=tk.NORMAL)

    set_outPath_Entry.config(state=tk.NORMAL)

    start_frame_num_Entry.config(state=tk.NORMAL)
    set_start_frame_num_Button.config(state=tk.NORMAL)
    end_frame_num_Entry.config(state=tk.NORMAL)
    set_end_frame_num_Button.config(state=tk.NORMAL)

    
    set_outScale_Checkbutton.config(state=tk.NORMAL)
    set_outFPS_Entry.config(state=tk.NORMAL)
    # set_outFPS_Checkbutton.config(state=tk.DISABLED)
    set_outPTS_Checkbutton.config(state=tk.NORMAL)
    set_outScale_Checkbutton_Click()
    # set_outFPS_Checkbutton_Click()
    set_outPTS_Checkbutton_Click()


    video_review_Label.bind("<MouseWheel>", video_progressbar_mousewheel)
    video_review_Label.bind("<B1-Motion>", draw_video_review_MouseDrag)
    video_review_Label.bind("<Button-1>", draw_video_review_MouseDown)

    video_Progressbar.bind("<MouseWheel>", video_progressbar_mousewheel)
    video_Progressbar.bind("<B1-Motion>", video_progressbar_leftDrag)
    video_Progressbar.bind("<Button-1>", video_progressbar_leftDrag)

    video_frame_Label.bind("<B1-Motion>", video_progressbar_leftDrag)
    video_frame_Label.bind("<Button-1>", video_progressbar_leftDrag)
    video_frame_Label.bind("<MouseWheel>", video_progressbar_mousewheel)

    start_createGIF_Button.config(text="生成GIF",command=start_to_ready,state=tk.NORMAL)



start_createGIF_Button.config(command=start_to_ready)
# restart_threshold_detection_Button.config(command=findThreshold_end)



def Thread_encoding():
    global process_ffmpeg
    log.info("开始编码GIF")
    
    set_crop = f"crop={right_x_text.get()-left_x_text.get()}:{right_y_text.get()-left_y_text.get()}:{left_x_text.get()}:{left_y_text.get()},"
    set_scale = f"scale={set_outScale_width_Entry.get()}x{set_outScale_height_Entry.get()}," if set_outScale_Tkbool.get() else ""
    set_pts = f"setpts={set_outPTS_Entry.get()}*PTS," if set_outPTS_Tkbool.get() else ""
    set_fps = f"fps={set_outFPS_Entry.get()},"

    process_ffmpeg = subprocess.Popen([
        'ffmpeg', '-y',
        '-ss', str(start_frame_num_Tkint.get() / fps),
        '-to', str(end_frame_num_Tkint.get() / fps),
        '-i', str(input_path),
        '-map', '0:v',
        '-vf', f"{set_crop}{set_scale}{set_pts}{set_fps}split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        (set_outPath_Entry.get() if set_outPath_Entry.get()[-4:]==".gif" else set_outPath_Entry.get()+".gif")
    ])

    process_ffmpeg.wait()

    log.info("编码完成")
    end_to_ready()




def start_encoding():
    global frame_count,frame_now,start_num,end_num

    if right_x_text.get()<4 or right_y_text.get()<4:
        right_x_text.set(frame_width)
        right_y_text.set(frame_height)
        left_x_text.set(0)
        left_y_text.set(0)

    #获取帧范围
    start_num,end_num = int(start_frame_num_Entry.get()),int(end_frame_num_Entry.get())
    if start_num<0:
        start_num=0
    if end_num>frame_count-1:
        end_num=frame_count-1
    if start_num>end_num:
        start_num=end_num
    draw_video_frame_Label_range(start_num, end_num, (27, 241, 255))
    flush_video_frame_Label()

    sec_rendering_Cap.set(cv2.CAP_PROP_POS_FRAMES,start_num)
    frame_now = start_num


    Thread(target=Thread_encoding).start()



def cancel_encoding():
    log.warning("手动强制终止")
    process_ffmpeg.kill()
    end_to_ready()



root_Tk.mainloop()