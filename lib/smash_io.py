import tkinter

def prompt_file():
    root = tkinter.Tk()
    root.withdraw()
    return tkinter.filedialog.askopenfilename()
