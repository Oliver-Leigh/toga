from ctypes import windll

gdi32 = windll.GDI32

GetTextExtentPoint32W = gdi32.GetTextExtentPoint32W
SelectObject = gdi32.SelectObject
